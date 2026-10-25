"""Calendar-day boundaries shared by training, calibration and inference."""
import numpy as np
import pandas as pd

PROTOCOL_VERSION = 1


def chronological_splits(dates):
    days = pd.DatetimeIndex(pd.to_datetime(dates)).normalize()
    unique = days.unique().sort_values()
    if len(unique) < 15:
        raise ValueError('At least 15 distinct match days are required for chronological evaluation.')
    validation_start = unique[int(len(unique) * .6)]
    test_start = unique[int(len(unique) * .8)]
    return np.flatnonzero(days < validation_start), np.flatnonzero((days >= validation_start) & (days < test_start)), np.flatnonzero(days >= test_start)


def calibration_folds(dates):
    days = pd.DatetimeIndex(pd.to_datetime(dates)).normalize()
    blocks = np.array_split(days.unique().sort_values(), 4)
    if any(len(block) == 0 for block in blocks):
        raise ValueError('Not enough distinct days for forward calibration.')
    return [(np.flatnonzero(days < block[0]), np.flatnonzero(days.isin(block))) for block in blocks[1:]]


def verified_cutoffs(payload, kickoff):
    """Fail closed for artifacts/snapshots created before cutoff metadata existed."""
    try:
        day = pd.Timestamp(kickoff).date()
        return (payload.get('leakage_protocol_version') == PROTOCOL_VERSION
                and pd.Timestamp(payload['training_data_through']).date() < day
                and pd.Timestamp(payload['history_through']).date() < day)
    except (KeyError, ValueError, TypeError):
        return False
