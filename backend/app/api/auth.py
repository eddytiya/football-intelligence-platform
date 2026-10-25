import re
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User, UserFavourite, UserWatchlist
from app.models.match import Match
from app.models.team import Team
from app.utils.auth_security import create_access_token, decode_access_token, hash_password, verify_password


router = APIRouter(prefix="/auth", tags=["Authentication"])


class Credentials(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    # Login verifies an existing password; creation policy belongs to registration.
    password: str = Field(min_length=1, max_length=128)


class RegistrationCredentials(Credentials):
    password: str = Field(min_length=8, max_length=128)


def account_payload(user: User):
    return {"id": user.id, "email": user.email, "created_at": user.created_at, "is_admin": user.is_admin}


def token_payload(user: User):
    return {"access_token": create_access_token(user.id, user.email), "token_type": "bearer", "user": account_payload(user)}


def current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> User:
    token = authorization.removeprefix("Bearer ").strip() if authorization else ""
    payload = decode_access_token(token)
    user = db.query(User).filter(User.id == payload.get("sub")).first() if payload else None
    if user is None:
        raise HTTPException(status_code=401, detail="Sign in to use personal features.")
    return user


def admin_user(user: User = Depends(current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Administrator access is required.")
    return user


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(credentials: RegistrationCredentials, db: Session = Depends(get_db)):
    email = credentials.email.lower().strip()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise HTTPException(status_code=422, detail="Enter a valid email address.")
    user = User(email=email, password_hash=hash_password(credentials.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    db.refresh(user)
    return token_payload(user)


@router.post("/login")
def login(credentials: Credentials, db: Session = Depends(get_db)):
    email = credentials.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=401, detail="This email is not registered. Create an account first.")
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect password. Please try again.")
    user.last_login_at = datetime.utcnow()
    db.commit()
    return token_payload(user)


class FavouriteInput(BaseModel):
    entity_type: str = Field(pattern="^(team|competition)$")
    entity_id: int = Field(ge=1)


class WatchlistInput(BaseModel):
    match_id: int = Field(ge=1)
    reminder_minutes: int = Field(default=60, ge=0, le=10080)


@router.get("/me")
def get_me(user: User = Depends(current_user)):
    return account_payload(user)


@router.get("/favourites")
def get_favourites(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(UserFavourite).filter(UserFavourite.user_id == user.id).order_by(UserFavourite.created_at.desc()).all()
    return [{"entity_type": row.entity_type, "entity_id": row.entity_id, "created_at": row.created_at} for row in rows]


@router.post("/favourites", status_code=status.HTTP_201_CREATED)
def save_favourite(payload: FavouriteInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    row = db.query(UserFavourite).filter_by(user_id=user.id, entity_type=payload.entity_type, entity_id=payload.entity_id).first()
    if row is None:
        row = UserFavourite(user_id=user.id, entity_type=payload.entity_type, entity_id=payload.entity_id)
        db.add(row); db.commit(); db.refresh(row)
    return {"entity_type": row.entity_type, "entity_id": row.entity_id, "created_at": row.created_at}


@router.delete("/favourites/{entity_type}/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favourite(entity_type: str, entity_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.query(UserFavourite).filter_by(user_id=user.id, entity_type=entity_type, entity_id=entity_id).delete()
    db.commit()


@router.get("/watchlist")
def get_watchlist(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(UserWatchlist, Match, Team.name, Team.crest).join(Match, Match.id == UserWatchlist.match_id).join(
        Team, Team.id == Match.home_team_id,
    ).filter(UserWatchlist.user_id == user.id).order_by(Match.utc_date).all()
    return [{"match_id": row.match_id, "reminder_minutes": row.reminder_minutes, "created_at": row.created_at,
             "home_team": home_name, "home_crest": home_crest,
             "away_team": match.away_team.name if match.away_team else "Away team", "away_crest": match.away_team.crest if match.away_team else None,
             "utc_date": match.utc_date, "status": match.status} for row, match, home_name, home_crest in rows]


@router.post("/watchlist", status_code=status.HTTP_201_CREATED)
def save_watchlist(payload: WatchlistInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    row = db.query(UserWatchlist).filter_by(user_id=user.id, match_id=payload.match_id).first()
    if row is None:
        row = UserWatchlist(user_id=user.id, match_id=payload.match_id, reminder_minutes=payload.reminder_minutes)
        db.add(row)
    else:
        row.reminder_minutes = payload.reminder_minutes
    db.commit(); db.refresh(row)
    return {"match_id": row.match_id, "reminder_minutes": row.reminder_minutes, "created_at": row.created_at}


@router.delete("/watchlist/{match_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_watchlist(match_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.query(UserWatchlist).filter_by(user_id=user.id, match_id=match_id).delete()
    db.commit()
