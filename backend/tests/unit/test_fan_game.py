from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.api import fan_game as game
from app.db.base import Base
from app.models import User, Team, Match, Competition


@pytest.fixture
def setup_game(monkeypatch):
    engine=create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session=sessionmaker(bind=engine)()
    user=User(email="fan@example.test",password_hash="unused")
    other=User(email="other@example.test",password_hash="unused")
    home=Team(name="Home");away=Team(name="Away")
    competition=Competition(api_id=1,name="Test league",code="QA",type="LEAGUE",area_name="Test",area_code="TST")
    session.add_all([user,other,home,away,competition]);session.commit()
    match=Match(api_id="qa-fan-game",competition_id=competition.id,home_team_id=home.id,away_team_id=away.id,status="SCHEDULED",utc_date=datetime.now(timezone.utc).replace(tzinfo=None)+timedelta(days=1))
    session.add(match);session.commit()
    app=FastAPI();app.include_router(game.router)
    app.dependency_overrides[game.get_db]=lambda:session
    app.dependency_overrides[game.current_user]=lambda:user
    monkeypatch.setattr(game,"get_historical_prediction",lambda *args:{"prediction_status":"ready","home_win_probability":.6,"draw_probability":.3,"away_win_probability":.1,"model_version":"frozen-v1"})
    yield TestClient(app),session,user,other,match,app
    session.close();engine.dispose()


def test_picks_persist_once_and_remain_account_private(setup_game):
    client,db,user,other,match,app=setup_game
    response=client.post('/fan-game/picks',json={"match_id":match.id,"outcome":"draw"})
    assert response.status_code==201,response.text
    assert response.json()['model_version']=="frozen-v1"
    assert client.post('/fan-game/picks',json={"match_id":match.id,"outcome":"home"}).status_code==409
    assert len(client.get('/fan-game/picks').json())==1
    app.dependency_overrides[game.current_user]=lambda:other
    assert client.get('/fan-game/picks').json()==[]


def test_kickoff_and_status_lock_checked_again_after_inference(setup_game,monkeypatch):
    client,db,user,other,match,app=setup_game
    def delayed(*args):
        match.utc_date=datetime.now(timezone.utc).replace(tzinfo=None)-timedelta(seconds=1)
        db.flush()
        return {"prediction_status":"ready","home_win_probability":.6,"draw_probability":.3,"away_win_probability":.1}
    monkeypatch.setattr(game,"get_historical_prediction",delayed)
    assert client.post('/fan-game/picks',json={"match_id":match.id,"outcome":"draw"}).status_code==409
    assert db.query(game.FanPick).count()==0


def test_unavailable_model_does_not_fabricate_paired_forecast(setup_game,monkeypatch):
    client,db,user,other,match,app=setup_game
    monkeypatch.setattr(game,"get_historical_prediction",lambda *args: {})
    response=client.post('/fan-game/picks',json={"match_id":match.id,"outcome":"home"})
    assert response.status_code==201
    assert response.json()['model_probabilities'] is None


def test_fixture_identity_change_during_inference_rejects_pick(setup_game,monkeypatch):
    client,db,user,other,match,app=setup_game
    def changed(*args):
        match.home_team_id,match.away_team_id=match.away_team_id,match.home_team_id
        db.flush()
        return {"prediction_status":"ready","home_win_probability":.6,"draw_probability":.3,"away_win_probability":.1}
    monkeypatch.setattr(game,"get_historical_prediction",changed)
    assert client.post('/fan-game/picks',json={"match_id":match.id,"outcome":"draw"}).status_code==409
    assert db.query(game.FanPick).count()==0


def test_scoring_uses_frozen_model_and_same_verified_result():
    now=datetime.now(timezone.utc)
    row=SimpleNamespace(match_id=1,outcome="draw",created_at=now-timedelta(days=2),kickoff_at_capture=now-timedelta(days=1),home_team_id=1,away_team_id=2,model_probabilities={"home":.6,"draw":.3,"away":.1},model_version="historical-season-v3-fixture")
    match=SimpleNamespace(home_team=SimpleNamespace(name="A"),away_team=SimpleNamespace(name="B"),utc_date=now-timedelta(days=1),competition=None,status="FINISHED",home_score=1,away_score=1,home_team_id=1,away_team_id=2)
    result=game.pick_payload(row,match,now)
    assert result['fan_correct'] and not result['model_correct']
    row.model_version = 'legacy-unverified'
    assert 'model_correct' not in game.pick_payload(row,match,now)
    match.utc_date=now+timedelta(days=1)
    assert game.pick_payload(row,match,now)['state']=="excluded"
    match.utc_date=now-timedelta(days=1);match.away_team_id=99
    assert game.pick_payload(row,match,now)['state']=="excluded"


def test_requires_authentication():
    app=FastAPI();app.include_router(game.router)
    assert TestClient(app).get('/fan-game/picks').status_code==401


def test_club_feed_omits_elapsed_scheduled_fixtures_and_includes_timed(setup_game):
    from app.api.team import get_team_profile
    client,db,user,other,match,app=setup_game
    past=Match(api_id="qa-past",competition_id=match.competition_id,home_team_id=match.home_team_id,away_team_id=match.away_team_id,status="SCHEDULED",utc_date=datetime.now(timezone.utc).replace(tzinfo=None)-timedelta(days=5))
    timed=Match(api_id="qa-timed",competition_id=match.competition_id,home_team_id=match.home_team_id,away_team_id=match.away_team_id,status="TIMED",utc_date=match.utc_date+timedelta(days=1))
    db.add_all([past,timed]);db.commit()
    profile=get_team_profile(match.home_team_id,db)
    assert [fixture['id'] for fixture in profile['upcoming_fixtures']]==[match.id,timed.id]
