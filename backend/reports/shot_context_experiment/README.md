# Shot context experiment

Existing free local CSVs; no downloads or paid services.

Full validation seasons 2023–2025 use expanding chronological training. The website blend remains 50% classifier, 25% Elo and 25% goal-based Poisson. Only lagged shot context and the goal objective change.

| Variant | Matches | Accuracy | Log loss |
| --- | ---: | ---: | ---: |
| control | 8748 | 52.19% | 0.98262 |
| opponent_adjusted | 8748 | 52.22% | 0.98253 |
| venue_form | 8748 | 51.95% | 0.98242 |
| poisson_goals | 8748 | 52.17% | 0.98223 |
| combined | 8748 | 51.99% | 0.98220 |

Selected by pooled rolling log loss: **combined**.

Partial 2026 check (previously inspected data, not a fresh prospective holdout):

| Variant | Matches | Accuracy | Log loss |
| --- | ---: | ---: | ---: |
| control | 559 | 51.34% | 0.98490 |
| combined | 559 | 51.52% | 0.98451 |

Neither target (55% overall accuracy and log loss below 0.95) was achieved. The serving artifact remains unchanged; the control reproduced earlier probability forecasts within 1e-12.

The selected combined variant reduces pooled log loss by about 0.00042 but loses 18 correct outcomes. Opponent adjustment alone adds just two correct outcomes. These results do not justify claiming a meaningful accuracy improvement.

Uncertainty intervals (candidate minus control; calendar-week bootstrap, descriptive only):

```json
{
  "opponent_adjusted": {
    "log_loss_delta_95_interval": [
      -0.0006746008956676983,
      0.0004508575888999734
    ],
    "accuracy_delta_95_interval": [
      -0.0020696802715657625,
      0.002641145156048006
    ],
    "note": "Paired calendar-week bootstrap; descriptive, not adjusted for selecting among variants."
  },
  "venue_form": {
    "log_loss_delta_95_interval": [
      -0.000902428078333828,
      0.00045048331770749877
    ],
    "accuracy_delta_95_interval": [
      -0.0051326398823755455,
      0.0006814352543538785
    ],
    "note": "Paired calendar-week bootstrap; descriptive, not adjusted for selecting among variants."
  },
  "poisson_goals": {
    "log_loss_delta_95_interval": [
      -0.0012242521632253678,
      0.00043025244923644313
    ],
    "accuracy_delta_95_interval": [
      -0.0020333145762191636,
      0.0015938296151334812
    ],
    "note": "Paired calendar-week bootstrap; descriptive, not adjusted for selecting among variants."
  },
  "combined": {
    "log_loss_delta_95_interval": [
      -0.0013752949664403722,
      0.0006203340490250051
    ],
    "accuracy_delta_95_interval": [
      -0.004738675257461497,
      0.000896340923628629
    ],
    "note": "Paired calendar-week bootstrap; descriptive, not adjusted for selecting among variants."
  }
}
```

Opponent adjustment normalizes shots by the opponent’s previous ten-match attacking/defensive rate, shrunk toward prior league averages with five pseudo-observations. League averages are frozen within each match day. Venue features summarize the last five/ten fixtures at the relevant venue. Missing statistics stay missing. Poisson heads predict positive expected goals using exponentiated raw scores.

Previously inspected historical periods, not fresh prospective validation.
Selection by pooled log loss; accuracy is reported separately.
Partial 2026 is small and was previously inspected.
Bootstrap intervals are descriptive, without multiple-selection correction.

Validation: 50 unit tests passed; a real CatBoost Poisson smoke check confirmed exponentiated expected-goal predictions. No paid data, purchases or downloads.
