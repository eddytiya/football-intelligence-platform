# Prediction model stack

The platform intentionally uses **five trained models only**.

1. Calibrated logistic-regression outcome classifier.
2. LightGBM outcome classifier.
3. CatBoost outcome classifier (the selected outcome model when its chronological validation log loss is best).
4. CatBoost home-goals regressor.
5. CatBoost away-goals regressor.

Training is chronological, with all fixtures on a match date kept together. The current artifact's comparison trains on 38,187 matches and validates on 9,551; serving estimators are then refitted on all 47,738 accepted results. Feature schema v2 resets seasonal counters and ranks only that season's league members while retaining Elo and recent form as separate historical signals. Evaluation keeps log loss, balanced accuracy and expected-goal MAE for maintenance.

The exact website forecast (50% outcome classifier, 25% Elo, 25% goal-model Poisson) is also evaluated on the chronological validation period: accuracy 51.8375%, log loss 0.985998. These are historical validation metrics, not live guarantees. See `data_repairs/README.md` for scope and limitations, and `/predictions/model/status` for the active artifact's metrics.

Current-season CSV history refreshes daily from the provider, with schema/date/score checks and atomic replacement. Model/state caches invalidate when accepted history changes. Forecasts require verified club identities, current-season membership, recent results, and an upcoming kickoff. Invalid database results are quarantined with recovery snapshots; database scores are not automatically trusted as training inputs.

ELO strength and Poisson score conversion are transparent deterministic calculations over those model outputs. They are shown as separate signals, not counted as extra machine-learning models.

## Data boundaries

- Match events, line-ups, venue and referee appear only when stored by a source.
- Weather, TV coverage, live injuries, transfer contracts and external news are intentionally marked as provider-dependent until a licensed source is connected.
- Player profiles use current stored squads and match statistics. They do not claim a player is injured, available, transferred or a confirmed starter without source data.
