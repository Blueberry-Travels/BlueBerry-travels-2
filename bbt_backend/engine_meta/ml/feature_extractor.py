"""
Feature extractor for the Blueberry graph pipeline RF scorer.

Two public functions:
  extract_from_training_row(row: dict) -> list[float]
      Used by trainer.py — takes a row dict from BLUEBERRY_TRAINING_DATA.md
  extract_from_activity(activity, context: dict) -> list[float]
      Used by scorer.py at inference time in the graph pipeline

Both produce an identical 48-dim float vector in the same layout.
validate_vector(vector) raises ValueError if anything is wrong.

VECTOR LAYOUT
─────────────────────────────────────────────────────────────
[0:14]   F01  category one-hot          14 dims  (alphabetical)
[14:27]  F16  region one-hot            13 dims  (alphabetical)
[27]     F02  tone_enc                  yin=0.0  both=0.5  yang=1.0
[28]     F03  effort_score              0.0–1.0
[29]     F05  duration_norm             duration_hrs / 16.0
[30]     F06  is_fixed_route            0.0 or 1.0
[31]     F07  weather_score             0.0–1.0
[32]     F08  weather_bias              0.0–1.0
[33]     F_risk                         0.0–1.0
[34]     F_altitude                     altitude_m / 6000.0
[35]     F_gear                         gear_class / 3.0
[36]     F_permit                       0.0 or 1.0
[37]     F_time_window                  window_minutes / 1440.0
[38]     F09  time_of_day               (h*60+m) / 1440.0
[39]     F11  travel_style              0.0–1.0
[40]     F12  daily_arc_phase           rising=0.0  peak=0.5  falling=1.0
[41]     F13  itn_arc_pos               slot / total_slots
[42]     F14  trip_length_norm          days / 14.0
[43]     F_lat                          normalised latitude
[44]     F_lon                          normalised longitude
[45]     F_momentum                     (delta_effort + 1.0) / 2.0
[46]     F_is_holiday                   0.0 or 1.0
[47]     F_is_weekend                   0.0 or 1.0
─────────────────────────────────────────────────────────────
"""

import math

# ── Canonical ordered lists — ORDER IS IMMUTABLE ────────────────────────────
# Any change here breaks all trained models. Do not reorder.

CATEGORIES = [
    'adventure_sports',
    'camping',
    'cultural',
    'food',
    'heritage',
    'hobbyist',
    'meditation',
    'photography',
    'rafting',
    'rest',
    'transit',
    'trekking',
    'water_sports',
    'wildlife',
]

REGIONS = [
    'ARP',  # Arunachal Pradesh
    'ASM',  # Assam
    'GHW',  # Garhwal
    'HPS',  # HP Spiti/Manali/Kullu
    'HRY',  # Haryana
    'HSD',  # HP Shimla/Kinnaur/Dharamshala
    'KMN',  # Kumaon
    'LDK',  # Ladakh/Kashmir
    'MEG',  # Meghalaya
    'NEM',  # NE Mixed
    'PNJ',  # Punjab
    'RAJ',  # Rajasthan
    'SKM',  # Sikkim
]

VECTOR_SIZE = 48

# Maps each named slice to its start index — for debugging and tests
FEATURE_INDEX = {
    'category':        (0,  14),
    'region':          (14, 27),
    'tone':            (27, 28),
    'effort':          (28, 29),
    'duration_norm':   (29, 30),
    'is_fixed_route':  (30, 31),
    'weather_score':   (31, 32),
    'weather_bias':    (32, 33),
    'risk_level':      (33, 34),
    'altitude_norm':   (34, 35),
    'gear_class_norm': (35, 36),
    'permit':          (36, 37),
    'time_window':     (37, 38),
    'time_of_day':     (38, 39),
    'travel_style':    (39, 40),
    'daily_arc_phase': (40, 41),
    'itn_arc_pos':     (41, 42),
    'trip_length_norm':(42, 43),
    'lat_norm':        (43, 44),
    'lon_norm':        (44, 45),
    'momentum_shift':  (45, 46),
    'is_holiday':      (46, 47),
    'is_weekend':      (47, 48),
}

# ── Region bounding boxes for lat/lon normalisation ──────────────────────────
# (lat_min, lat_max, lon_min, lon_max)
# These are approximate — RegionConfig DB records take priority at inference time.
# Trainer uses these fallbacks since training data has no GPS.
_REGION_BBOX = {
    'ARP': (26.5, 29.5, 91.5, 97.5),
    'ASM': (24.0, 28.0, 89.5, 96.5),
    'GHW': (29.5, 31.5, 78.0, 80.5),
    'HPS': (31.0, 33.5, 76.5, 79.0),
    'HRY': (27.5, 30.5, 74.5, 77.5),
    'HSD': (30.5, 33.0, 75.5, 78.5),
    'KMN': (28.5, 30.5, 78.5, 81.5),
    'LDK': (32.0, 36.0, 73.5, 80.5),
    'MEG': (24.5, 26.5, 89.5, 93.5),
    'NEM': (22.0, 27.5, 91.0, 97.0),
    'PNJ': (29.5, 32.5, 73.5, 77.0),
    'RAJ': (23.0, 30.5, 69.5, 78.5),
    'SKM': (27.0, 28.5, 87.5, 89.5),
}


# ── Internal helpers ─────────────────────────────────────────────────────────

def _one_hot(value: str, choices: list) -> list:
    """Returns a one-hot list. Unknown value → all zeros (silent — RF handles it)."""
    return [1.0 if value == c else 0.0 for c in choices]


def _tone_enc(tone: str) -> float:
    return {'yin': 0.0, 'both': 0.5, 'yang': 1.0}.get(str(tone).strip().lower(), 0.5)


def _arc_phase_enc(phase: str) -> float:
    return {'rising': 0.0, 'peak': 0.5, 'falling': 1.0}.get(
        str(phase).strip().lower(), 0.0)


def _time_norm(time_str: str) -> float:
    """'HH:MM' or '0' → fraction of day [0, 1)."""
    try:
        parts = str(time_str).strip().split(':')
        if len(parts) == 2:
            h, m = int(parts[0]), int(parts[1])
        else:
            return 0.0
        return min((h * 60 + m) / 1440.0, 1.0)
    except Exception:
        return 0.0


def _normalise_lat(lat, region_code: str) -> float:
    if lat is None:
        return 0.5
    try:
        lat = float(lat)
        bbox = _REGION_BBOX.get(region_code)
        if bbox:
            lat_min, lat_max = bbox[0], bbox[1]
            r = lat_max - lat_min
            return max(0.0, min((lat - lat_min) / r, 1.0)) if r else 0.5
    except Exception:
        pass
    return 0.5


def _normalise_lon(lon, region_code: str) -> float:
    if lon is None:
        return 0.5
    try:
        lon = float(lon)
        bbox = _REGION_BBOX.get(region_code)
        if bbox:
            lon_min, lon_max = bbox[2], bbox[3]
            r = lon_max - lon_min
            return max(0.0, min((lon - lon_min) / r, 1.0)) if r else 0.5
    except Exception:
        pass
    return 0.5


def _risk_tier_to_float(risk_tier: str) -> float:
    return {
        'casual':   0.10,
        'moderate': 0.35,
        'high':     0.55,
        'extreme':  0.80,
    }.get(str(risk_tier).strip().lower(), 0.10)


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


# ── Training-data field derivations ─────────────────────────────────────────
# The training data has no altitude, gear_class, permit, lat, lon, risk_tier.
# These are approximated from category + effort + weather_score for training.
# At inference the Activity model provides the real admin-registered values.

def _derive_risk_from_training(category: str, effort: float) -> float:
    base = {
        'trekking': 0.35, 'adventure_sports': 0.55,
        'rafting': 0.45,  'camping': 0.15,
        'wildlife': 0.10, 'cultural': 0.05,
        'heritage': 0.05, 'meditation': 0.02,
        'photography': 0.08, 'food': 0.03,
        'hobbyist': 0.10, 'water_sports': 0.40,
        'rest': 0.01,     'transit': 0.05,
    }.get(category, 0.10)
    return _clamp(base + max(0.0, effort - 0.40) * 0.3)


def _derive_altitude_norm(category: str, weather_score: float) -> float:
    # High-altitude activities tend to have lower weather_score.
    if category in ('trekking', 'camping', 'adventure_sports'):
        altitude_proxy = _clamp((1.0 - weather_score) * 0.7)
    else:
        altitude_proxy = 0.05
    return altitude_proxy


def _derive_gear_class(category: str, effort: float) -> float:
    gc = {
        'adventure_sports': 2, 'trekking': 2,
        'rafting': 2,          'camping': 1,
        'water_sports': 1,     'wildlife': 1,
        'photography': 1,      'hobbyist': 1,
        'cultural': 0,         'heritage': 0,
        'meditation': 0,       'food': 0,
        'rest': 0,             'transit': 0,
    }.get(category, 0)
    if effort > 0.70:
        gc = min(gc + 1, 3)
    return gc / 3.0


def _derive_permit(category: str, weather_score: float) -> float:
    # Trekking + wildlife in remote regions (low weather_score) often needs permit.
    if category in ('trekking', 'wildlife', 'camping') and weather_score < 0.60:
        return 1.0
    return 0.0


def _derive_time_window(is_fixed_time: bool, time_str: str) -> float:
    if not is_fixed_time:
        return 1.0
    # Fixed-time events have narrow windows — default 45 min = 0.031
    return 45.0 / 1440.0


# ── Public API ───────────────────────────────────────────────────────────────

def extract_from_training_row(row: dict) -> list:
    """
    Build the 48-dim vector from a training data row dict.

    Expected keys (from BLUEBERRY_TRAINING_DATA.md parser):
        itinerary_id, region, travel_style, category, tone, effort,
        reward, duration_hrs, is_fixed_time, sequence_position,
        day_position, arc_phase, weather_score, weather_bias,
        trip_length_days, notes, time  (HH:MM string)

    Missing keys default gracefully — no KeyError.
    """
    category     = str(row.get('category', 'cultural')).strip().lower()
    region_code  = str(row.get('region', 'GHW')).strip().upper()
    tone         = str(row.get('tone', 'both')).strip().lower()
    effort       = _clamp(float(row.get('effort', 0.5)))
    duration_hrs = float(row.get('duration_hrs', 1.0))
    weather_score= _clamp(float(row.get('weather_score', 0.75)))
    weather_bias = _clamp(float(row.get('weather_bias', 0.20)))
    travel_style = _clamp(float(row.get('travel_style', 0.5)))
    arc_phase    = str(row.get('arc_phase', 'rising')).strip().lower()
    trip_days    = int(float(row.get('trip_length_days', 4)))
    time_str     = str(row.get('time', '09:00'))

    # is_fixed_time in training data is a string 'True'/'False'
    raw_fixed = row.get('is_fixed_time', 'False')
    is_fixed  = raw_fixed is True or str(raw_fixed).strip() == 'True'

    # itn_arc_pos = sequence_position / total_nodes
    # training data has sequence_position; we approximate total from trip_length
    seq_pos    = int(float(row.get('sequence_position', 0)))
    total_nodes= max(trip_days * 5, seq_pos + 1)
    arc_pos    = _clamp(seq_pos / total_nodes)

    # Derived fields (training data has no GPS, altitude, gear, permit)
    risk_level   = _derive_risk_from_training(category, effort)
    altitude_norm= _derive_altitude_norm(category, weather_score)
    gear_norm    = _derive_gear_class(category, effort)
    permit       = _derive_permit(category, weather_score)
    time_window  = _derive_time_window(is_fixed, time_str)

    # Context fields not present in training rows — use neutral defaults
    momentum_shift = 0.5     # no previous node known in isolation
    is_holiday     = 0.0
    is_weekend     = 0.0

    vector = (
        _one_hot(category, CATEGORIES)          # [0:14]
        + _one_hot(region_code, REGIONS)         # [14:27]
        + [
            _tone_enc(tone),                     # [27]
            effort,                              # [28]
            _clamp(duration_hrs / 16.0),         # [29]
            1.0 if is_fixed else 0.0,            # [30]
            weather_score,                       # [31]
            weather_bias,                        # [32]
            risk_level,                          # [33]
            altitude_norm,                       # [34]
            gear_norm,                           # [35]
            permit,                              # [36]
            time_window,                         # [37]
            _time_norm(time_str),                # [38]
            travel_style,                        # [39]
            _arc_phase_enc(arc_phase),           # [40]
            arc_pos,                             # [41]
            _clamp(trip_days / 14.0),            # [42]
            0.5,                                 # [43] lat — no GPS in training
            0.5,                                 # [44] lon — no GPS in training
            momentum_shift,                      # [45]
            is_holiday,                          # [46]
            is_weekend,                          # [47]
        ]
    )
    return vector


def extract_from_activity(activity, context: dict) -> list:
    """
    Build the 48-dim vector from a live Activity model instance + pipeline context.

    activity  — engine_b2c.models.Activity instance
    context   — dict with keys:
        travel_style    float  0.0–1.0
        itn_arc_pos     float  slot / total_slots
        daily_arc_phase str    'rising' | 'peak' | 'falling'
        slot_time       str    'HH:MM'  scheduled start time for this slot
        trip_length_days int
        season          str    'summer' | 'winter' | 'monsoon'
        prev_effort     float  effort of previous node (0.5 if first slot)
        is_holiday      bool
        is_weekend      bool
        region_config   RegionConfig instance or None
    """
    # ── Activity fields ──────────────────────────────────────────────────
    category     = str(activity.category).strip().lower()
    region_code  = str(activity.region.region_code).strip().upper()
    tone         = str(activity.tone).strip().lower()
    effort       = _clamp(float(activity.effort_score))
    duration_hrs = float(activity.duration_hrs)
    risk_level   = _clamp(float(activity.risk_level()))
    altitude_norm= _clamp(float(activity.altitude_norm()))
    gear_norm    = _clamp(float(activity.gear_class_norm()))
    permit       = 1.0 if activity.permit_required else 0.0
    time_window  = _clamp(float(activity.time_window_width()))
    is_fixed     = 1.0 if activity.is_fixed_route else 0.0

    # ── Seasonal weather ─────────────────────────────────────────────────
    season        = context.get('season', 'summer')
    weather_score = _clamp(float(activity.weather_score(season)))
    weather_bias  = _clamp(float(activity.weather_bias(season)))

    # ── GPS normalisation ─────────────────────────────────────────────────
    rc = context.get('region_config')
    if rc and activity.lat is not None and activity.lng is not None:
        try:
            lat_norm = _clamp(float(rc.normalise_lat(activity.lat)))
            lon_norm = _clamp(float(rc.normalise_lon(activity.lng)))
        except Exception:
            lat_norm = _normalise_lat(activity.lat, region_code)
            lon_norm = _normalise_lon(activity.lng, region_code)
    else:
        lat_norm = _normalise_lat(activity.lat, region_code)
        lon_norm = _normalise_lon(activity.lng, region_code)

    # ── Context fields ────────────────────────────────────────────────────
    travel_style = _clamp(float(context.get('travel_style', 0.5)))
    arc_pos      = _clamp(float(context.get('itn_arc_pos', 0.5)))
    arc_phase    = str(context.get('daily_arc_phase', 'rising')).strip().lower()
    slot_time    = str(context.get('slot_time', '09:00'))
    trip_days    = int(context.get('trip_length_days', 4))
    prev_effort  = _clamp(float(context.get('prev_effort', 0.5)))

    momentum_shift = _clamp((effort - prev_effort + 1.0) / 2.0)
    is_holiday     = 1.0 if context.get('is_holiday') else 0.0
    is_weekend     = 1.0 if context.get('is_weekend') else 0.0

    vector = (
        _one_hot(category, CATEGORIES)          # [0:14]
        + _one_hot(region_code, REGIONS)         # [14:27]
        + [
            _tone_enc(tone),                     # [27]
            effort,                              # [28]
            _clamp(duration_hrs / 16.0),         # [29]
            is_fixed,                            # [30]
            weather_score,                       # [31]
            weather_bias,                        # [32]
            risk_level,                          # [33]
            altitude_norm,                       # [34]
            gear_norm,                           # [35]
            permit,                              # [36]
            time_window,                         # [37]
            _time_norm(slot_time),               # [38]
            travel_style,                        # [39]
            _arc_phase_enc(arc_phase),           # [40]
            arc_pos,                             # [41]
            _clamp(trip_days / 14.0),            # [42]
            lat_norm,                            # [43]
            lon_norm,                            # [44]
            momentum_shift,                      # [45]
            is_holiday,                          # [46]
            is_weekend,                          # [47]
        ]
    )
    return vector


# ── Validator ────────────────────────────────────────────────────────────────

def validate_vector(vector: list) -> None:
    """
    Raises ValueError with a descriptive message if the vector is malformed.
    Call this in trainer.py and scorer.py before passing to the RF.
    """
    if not isinstance(vector, list):
        raise ValueError(f'Vector must be a list, got {type(vector)}')

    if len(vector) != VECTOR_SIZE:
        raise ValueError(
            f'Vector length {len(vector)} != expected {VECTOR_SIZE}')

    for i, v in enumerate(vector):
        if v is None or (isinstance(v, float) and math.isnan(v)):
            name = _dim_name(i)
            raise ValueError(f'NaN/None at dim [{i}] ({name})')

        if not isinstance(v, (int, float)):
            name = _dim_name(i)
            raise ValueError(
                f'Non-numeric value {v!r} at dim [{i}] ({name})')

        v = float(v)

        # One-hot dims: must be exactly 0.0 or 1.0
        if i < 27:
            if v not in (0.0, 1.0):
                name = _dim_name(i)
                raise ValueError(
                    f'One-hot dim [{i}] ({name}) must be 0.0 or 1.0, got {v}')
        else:
            # Scalar dims: must be in [0, 1]
            if not (0.0 <= v <= 1.0):
                name = _dim_name(i)
                raise ValueError(
                    f'Scalar dim [{i}] ({name}) out of range [0,1]: {v}')


def _dim_name(i: int) -> str:
    """Returns the feature name for a given dimension index."""
    if 0 <= i < 14:
        return f'category[{CATEGORIES[i]}]'
    if 14 <= i < 27:
        return f'region[{REGIONS[i - 14]}]'
    for name, (start, end) in FEATURE_INDEX.items():
        if start <= i < end:
            return name
    return 'unknown'