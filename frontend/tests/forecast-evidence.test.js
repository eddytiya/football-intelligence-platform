import { test } from "node:test";
import assert from "node:assert/strict";
import { calibrationBins, gameSummary, recordObservation, readObservations } from "../src/utils/forecastEvidence.js";
import { archiveForecast, readForecastArchive } from "../src/utils/forecastTracker.js";
const store=()=>{const values=new Map();return {getItem:key=>values.get(key),setItem:(key,value)=>values.set(key,value)};};
const snapshot=(at,home=.6)=>({leakage_protocol_version:1,training_data_through:"2026-10-01",history_through:"2026-10-17",match_id:1,utc_date:"2027-01-01T15:00:00Z",saved_at:at,model_version:"v1",probabilities:{home,draw:.3,away:1-home-.3}});

test("observations deduplicate strict-mode visits but preserve later unchanged and changed forecasts",()=>{
  const storage=store(),now=new Date("2026-10-18T08:10:00Z").getTime();
  recordObservation(snapshot("2026-10-18T08:00:00Z"),storage,now);
  recordObservation(snapshot("2026-10-18T08:00:01Z"),storage,now);
  assert.equal(readObservations(storage).length,1);
  recordObservation(snapshot("2026-10-18T08:02:00Z"),storage,now);
  recordObservation(snapshot("2026-10-18T08:02:01Z",.5),storage,now);
  assert.equal(readObservations(storage).length,3);
});
test("movement capture never replaces original tracker probabilities or accepts post-kickoff observations",()=>{
  const storage=store(),original=snapshot("2026-10-18T08:00:00Z"),now=new Date("2026-10-18T08:10:00Z").getTime();
  archiveForecast(original,storage);recordObservation(original,storage,now);
  recordObservation(snapshot("2026-10-18T08:02:00Z",.5),storage,now);
  assert.equal(readForecastArchive(storage)[0].probabilities.home,.6);
  assert.equal(recordObservation({...original,utc_date:"2026-01-01T15:00:00Z"},storage,now),false);
});
test("calibration bins use actual probabilities, frequencies, boundaries and completed fixtures",()=>{
  const rows=[{state:"settled",actual:"home",probabilities:{home:.6,draw:.3,away:.1}},{state:"settled",actual:"away",probabilities:{home:.6,draw:.3,away:.1}},{state:"pending",actual:"home",probabilities:{home:1,draw:0,away:0}}];
  const bins=calibrationBins(rows,"home");
  assert.equal(bins[6].count,2);assert.equal(bins[6].observed,.5);assert.equal(bins[6].expected,.6);
  assert.equal(calibrationBins([{state:"settled",actual:"home",probabilities:{home:1,draw:0,away:0}}],"top")[9].count,1);
  assert.equal(calibrationBins([],"draw")[0].observed,null);
});
test("paired game metrics compare both sides on the same fixtures",()=>{
  const summary=gameSummary([{state:"settled",fan_correct:true,model_correct:false},{state:"settled",fan_correct:false,model_correct:true},{state:"settled",fan_correct:true},{state:"pending",fan_correct:true,model_correct:true}]);
  assert.deepEqual(summary,{total:3,correct:2,paired:2,pairedFanCorrect:1,pairedModelCorrect:1});
});
