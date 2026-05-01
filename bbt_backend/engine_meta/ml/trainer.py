"""
Trainer for the Blueberry RF scorer.

Usage:
    python manage.py shell -c "from engine_meta.ml.trainer import train; train()"

Or with a custom path:
    python manage.py shell -c "
    from engine_meta.ml.trainer import train
    train(data_path='/some/other/path/BLUEBERRY TRAINING DATA.md')
    "

Output:
    Trained model saved to engine_meta/ml/trained_model.json
    Validation metrics printed to stdout.
"""

import os
import json
import random
import logging

logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
DEFAULT_DATA_PATH  = '/home/worker_007/Desktop/BLUEBERRY TRAINING DATA.md'
DEFAULT_MODEL_PATH = os.path.join(
    os.path.dirname(__file__), 'trained_model.json'
)

# ── Training data field names (pipe-delimited, first 20 cols) ─────────────────
FIELDS = [
    'itinerary_id', 'location', 'trip_length_days', 'travel_style',
    'day', 'time', 'activity_name', 'category', 'tone', 'effort',
    'reward', 'duration_hrs', 'is_fixed_time', 'is_filler',
    'sequence_position', 'day_position', 'arc_phase', 'quality_score',
    'weather_score', 'weather_bias',
]


# ── Data loader ───────────────────────────────────────────────────────────────

def load_training_data(data_path: str) -> tuple:
    """
    Parses BLUEBERRY TRAINING DATA.md.
    Returns (X, y, itinerary_ids) where:
        X    — list of 48-dim vectors
        y    — list of float reward targets
        ids  — list of itinerary_id strings (for train/val split)

    Rules (from handover doc):
        - Skip blank lines and lines starting with #
        - Skip lines with fewer than 21 pipe-separated parts
        - Skip rows where is_filler == 'True'
        - target = float(reward)
        - quality_score is NOT used
    """
    from engine_meta.ml.feature_extractor import (
        extract_from_training_row, validate_vector
    )

    X   = []
    y   = []
    ids = []

    skipped_malformed = 0
    skipped_filler    = 0
    errors            = 0
    total_seen        = 0

    with open(data_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split('|')
            if len(parts) < 21:
                skipped_malformed += 1
                continue

            total_seen += 1
            row          = dict(zip(FIELDS, parts[:20]))
            row['notes'] = '|'.join(parts[20:])

            # Extract region code from itinerary_id e.g. ITN-GHW-001 → GHW
            itn_id = row.get('itinerary_id', '')
            parts2 = itn_id.split('-')
            row['region'] = parts2[1] if len(parts2) > 1 else 'GHW'

            # Skip fillers — train on non-filler only
            if row.get('is_filler', 'False').strip() == 'True':
                skipped_filler += 1
                continue

            try:
                reward = float(row['reward'])
            except (KeyError, ValueError):
                errors += 1
                continue

            try:
                vector = extract_from_training_row(row)
                validate_vector(vector)
            except Exception as e:
                errors += 1
                logger.debug(f'Vector error on row {itn_id}: {e}')
                continue

            X.append(vector)
            y.append(reward)
            ids.append(itn_id)

    print(f'Loaded:   {len(X)} training rows')
    print(f'Skipped:  {skipped_filler} fillers | '
          f'{skipped_malformed} malformed | {errors} errors')
    print(f'Total lines seen: {total_seen}')
    return X, y, ids


# ── Train / val split by itinerary ────────────────────────────────────────────

def split_by_itinerary(X, y, ids, val_fraction=0.20, seed=42):
    """
    Splits by itinerary — keeps all rows of an itinerary in the same set.
    This prevents data leakage (reward patterns within one itinerary
    would inflate validation metrics if rows were split individually).
    """
    unique_itns = list(set(ids))
    rng         = random.Random(seed)
    rng.shuffle(unique_itns)

    n_val    = max(1, int(len(unique_itns) * val_fraction))
    val_set  = set(unique_itns[:n_val])
    train_set= set(unique_itns[n_val:])

    X_train, y_train = [], []
    X_val,   y_val   = [], []

    for vec, target, itn_id in zip(X, y, ids):
        if itn_id in train_set:
            X_train.append(vec)
            y_train.append(target)
        else:
            X_val.append(vec)
            y_val.append(target)

    print(f'Split:    {len(train_set)} train itineraries ({len(X_train)} rows) | '
          f'{len(val_set)} val itineraries ({len(X_val)} rows)')
    return X_train, y_train, X_val, y_val


# ── Metrics ───────────────────────────────────────────────────────────────────

def _mae(y_true, y_pred):
    return sum(abs(a - b) for a, b in zip(y_true, y_pred)) / len(y_true)


def _rmse(y_true, y_pred):
    return (sum((a - b) ** 2 for a, b in zip(y_true, y_pred)) / len(y_true)) ** 0.5


def _r2(y_true, y_pred):
    mean_true = sum(y_true) / len(y_true)
    ss_tot = sum((v - mean_true) ** 2 for v in y_true)
    ss_res = sum((a - b) ** 2 for a, b in zip(y_true, y_pred))
    return 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0


def evaluate(rf, X, y, label='Validation'):
    preds = rf.predict_batch(X)
    mae   = _mae(y, preds)
    rmse  = _rmse(y, preds)
    r2    = _r2(y, preds)
    print(f'{label}: MAE={mae:.4f}  RMSE={rmse:.4f}  R²={r2:.4f}  n={len(y)}')
    return {'mae': mae, 'rmse': rmse, 'r2': r2, 'n': len(y)}


# ── Main train function ───────────────────────────────────────────────────────

def train(
    data_path:  str = DEFAULT_DATA_PATH,
    model_path: str = DEFAULT_MODEL_PATH,
    n_trees:    int = None,
    max_depth:  int = None,
    min_samples_leaf: int = None,
):
    """
    Full training run:
      1. Load data
      2. Split by itinerary (80/20)
      3. Train RF (hyperparams from EngineConfig or defaults)
      4. Evaluate on val set
      5. Save model to JSON
      6. Update ScoringModel record in DB
    """
    from engine_meta.ml.random_forest import RandomForest

    # Pull hyperparams from EngineConfig if not overridden
    if n_trees is None or max_depth is None or min_samples_leaf is None:
        try:
            from engine_meta.models import EngineConfig
            cfg = EngineConfig.objects.get(id=1)
            n_trees          = n_trees          or cfg.rf_n_trees
            max_depth        = max_depth        or cfg.rf_max_depth
            min_samples_leaf = min_samples_leaf or cfg.rf_min_samples_leaf
        except Exception:
            n_trees          = n_trees          or 100
            max_depth        = max_depth        or 10
            min_samples_leaf = min_samples_leaf or 5

    print('=' * 60)
    print('Blueberry RF Trainer')
    print(f'Data:       {data_path}')
    print(f'Model out:  {model_path}')
    print(f'RF config:  {n_trees} trees | depth {max_depth} | '
          f'min_leaf {min_samples_leaf}')
    print('=' * 60)

    # 1. Load
    X, y, ids = load_training_data(data_path)
    if len(X) < 100:
        raise ValueError(f'Too few training rows: {len(X)}. Check data path.')

    # 2. Split
    X_train, y_train, X_val, y_val = split_by_itinerary(X, y, ids)

    # 3. Train
    print(f'\nTraining RF ({n_trees} trees)...')
    rf = RandomForest(
        n_trees=n_trees,
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
    )
    rf.fit(X_train, y_train)
    print('Training complete.')

    # 4. Evaluate
    print()
    train_metrics = evaluate(rf, X_train, y_train, label='Train    ')
    val_metrics   = evaluate(rf, X_val,   y_val,   label='Validation')

    # 5. Save model
    rf.save(model_path)
    model_size_kb = os.path.getsize(model_path) / 1024
    print(f'\nModel saved: {model_path} ({model_size_kb:.1f} KB)')

    # 6. Update DB record
    try:
        from django.utils import timezone
        from engine_meta.models import ScoringModel
        ScoringModel.objects.update_or_create(
            score_type='reward_score',
            defaults={
                'is_trained':       True,
                'training_samples': len(X_train),
                'last_trained_at':  timezone.now(),
                'model_json':       json.dumps({
                    'model_path':   model_path,
                    'n_trees':      n_trees,
                    'max_depth':    max_depth,
                    'min_leaf':     min_samples_leaf,
                    'train_rows':   len(X_train),
                    'val_rows':     len(X_val),
                    **{f'train_{k}': v for k, v in train_metrics.items()},
                    **{f'val_{k}':   v for k, v in val_metrics.items()},
                }),
            }
        )
        print('DB record updated.')
    except Exception as e:
        logger.warning(f'DB update skipped: {e}')

    print('=' * 60)
    print('Done.')
    return rf, val_metrics