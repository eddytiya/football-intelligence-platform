import { test } from "node:test";
import assert from "node:assert/strict";
import { readForecastArchive, archiveForecast, classifyForecast, scoreForecasts, reconcileForecasts, ARCHIVE_KEY } from "../src/utils/forecastTracker.js";
import { buildCalendar } from "../src/utils/calendarExport.js";

const snapshot = (id, probabilities = { home: .6, draw: .3, away: .1 }) => ({ leakage_protocol_version:1,training_data_through:"2026-08-01",history_through:"2026-08-31", match_id: id, saved_at: "2026-09-01T08:00:00Z", utc_date: "2026-09-01T15:00:00Z", probabilities });
const match = (id, home = 2, away = 0) => ({ id, utc_date: "2026-09-01T15:00:00Z", status: "FINISHED", home_score: home, away_score: away });
const storage = () => { const data = new Map(); return { getItem: (key) => data.get(key), setItem: (key,value) => data.set(key,value) }; };

test("unverified and same-day training cannot count, and a verified forecast supersedes an unsafe browser record", () => {
  const legacy = { ...snapshot(1), leakage_protocol_version: undefined };
  assert.equal(classifyForecast(legacy, match(1)).state, "excluded");
  assert.equal(classifyForecast({ ...snapshot(1), training_data_through: "2026-09-01" }, match(1)).state, "excluded");
  const store = storage();
  archiveForecast(legacy, store);
  archiveForecast(snapshot(1), store);
  assert.equal(readForecastArchive(store)[0].leakage_protocol_version, 1);
});

test("known completed predictions yield multiclass accuracy, log loss, draw recall and precision", () => {
  const rows = [classifyForecast(snapshot(1), match(1)), classifyForecast(snapshot(2, {home:.2,draw:.5,away:.3}),match(2,1,1)), classifyForecast(snapshot(3),match(3,0,0))];
  const metrics = scoreForecasts(rows);
  assert.equal(metrics.accuracy, 2/3);
  assert.ok(Math.abs(metrics.logLoss - (-Math.log(.6)-Math.log(.5)-Math.log(.3))/3) < 1e-12);
  assert.equal(metrics.drawRecall,.5); assert.equal(metrics.drawPrecision,1);
  assert.equal(scoreForecasts([]).accuracy,null); assert.equal(scoreForecasts([]).drawRecall,null);
});
test("late snapshots, future finished records, invalid scores and changed identities cannot count", () => {
  assert.equal(classifyForecast({...snapshot(1),saved_at:"2026-09-02T08:00:00Z"},match(1)).state,"excluded");
  assert.equal(classifyForecast(snapshot(1),match(1),new Date("2026-08-01").getTime()).state,"excluded");
  assert.equal(classifyForecast(snapshot(1),match(1,null,0)).state,"excluded");
  assert.equal(classifyForecast({...snapshot(1),home_team_id:10},{...match(1),home_team_id:11}).state,"excluded");
  assert.equal(classifyForecast(snapshot(1),{...match(1),status:"POSTPONED"}).state,"pending");
  assert.equal(classifyForecast(snapshot(1),null).state,"unavailable");
  assert.equal(classifyForecast(snapshot(1),{...match(1),utc_date:"2026-09-01T07:00:00Z"}).state,"excluded");
});
test("archive keeps earliest snapshot, rejects corrupt probabilities and survives recent-history clearing", () => {
  const store=storage();
  store.setItem("prediction-history",JSON.stringify([snapshot(1),{...snapshot(2),probabilities:{home:1,draw:1,away:1}}]));
  archiveForecast({...snapshot(1),saved_at:"2026-09-01T09:00:00Z"},store);
  assert.equal(readForecastArchive(store).length,1);
  assert.equal(readForecastArchive(store)[0].saved_at,snapshot(1).saved_at);
  store.setItem("prediction-history","[]");
  assert.equal(readForecastArchive(store).length,1);
  assert.ok(store.getItem(ARCHIVE_KEY));
});
test("zero probability stays finite and exact ties follow declared order", () => {
  const zero=classifyForecast(snapshot(1,{home:1,draw:0,away:0}),match(1,0,0));
  assert.equal(zero.loss,-Math.log(1e-15));
  const tie=classifyForecast(snapshot(1,{home:.4,draw:.4,away:.2}),match(1));
  assert.equal(tie.picked,"home"); assert.equal(tie.tied,true);
});
test("result reconciliation limits concurrency and preserves failed rows", async () => {
  let active=0, maximum=0;
  const rows=await reconcileForecasts(Array.from({length:12},(_,id)=>snapshot(id+1)),async (id)=>{
    active++;maximum=Math.max(maximum,active); await new Promise(resolve=>setTimeout(resolve,2));active--;
    if(id===4)throw new Error("offline");return match(id);
  });
  assert.equal(maximum,4);assert.equal(rows.length,12);assert.equal(rows[3].state,"unavailable");
});
test("calendar uses UTC, escapes injection, folds UTF-8 and omits past/cancelled fixtures", () => {
  const fixture={id:1,utc_date:"2026-10-25T15:00:00",status:"SCHEDULED",home_team_name:"É".repeat(60)+", FC",away_team_name:"Away;Club",venue:"A\nBEGIN:VEVENT"};
  const output=buildCalendar([fixture,fixture,{...fixture,id:2,status:"CANCELLED"},{...fixture,id:3,utc_date:"2025-01-01T15:00:00Z"}],new Date("2026-10-01T00:00:00Z"));
  assert.ok(output.includes("DTSTART:20261025T150000Z\r\n"));
  assert.equal(output.match(/BEGIN:VEVENT/g).length,2); // event plus escaped text in LOCATION, not another content line
  assert.ok(output.includes("LOCATION:A\\nBEGIN:VEVENT"));
  assert.ok(output.includes("Away\\;Club"));
  assert.ok(output.split("\r\n").every(line=>Buffer.byteLength(line,"utf8")<=75));
  assert.equal(output.split("\r\n").filter(line=>line==="BEGIN:VEVENT").length,1);
  assert.equal(buildCalendar([],new Date()),null);
});
