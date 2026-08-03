# Prediction model stack

The platform intentionally uses **five trained models only**.

1. Calibrated logistic-regression outcome classifier.
2. LightGBM outcome classifier.
3. CatBoost outcome classifier (the selected outcome model when its chronological validation log loss is best).
4. CatBoost home-goals regressor.
5. CatBoost away-goals regressor.

Training is chronological: the oldest 80% of historical fixtures trains each candidate and the newest 20% validates it. The current saved artifact was trained on 37,743 matches and validated on 9,436. The evaluation keeps log loss, balanced accuracy and expected-goal MAE for maintenance; no public accuracy percentage is shown.

ELO strength and Poisson score conversion are transparent deterministic calculations over those model outputs. They are shown as separate signals, not counted as extra machine-learning models.

## Data boundaries

- Match events, line-ups, venue and referee appear only when stored by a source.
- Weather, TV coverage, live injuries, transfer contracts and external news are intentionally marked as provider-dependent until a licensed source is connected.
- Player profiles use current stored squads and match statistics. They do not claim a player is injured, available, transferred or a confirmed starter without source data.
