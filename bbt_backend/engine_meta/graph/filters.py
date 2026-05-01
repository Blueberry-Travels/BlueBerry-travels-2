"""
L1 — Hard filters.
Removes candidates that are impossible, unavailable, or disrupted.
Applies real-time disruption flags from cache.
"""

import logging
from blueberry_backend.communications import get_disruption

logger = logging.getLogger(__name__)


def apply_hard_filters(
    candidates: list,
    trip_dates: list,
    region_id: str,
    user_gear_class: int = 0,
    user_has_permit: bool = False,
) -> list:
    """
    candidates     — list of Activity instances from L0
    trip_dates     — list of datetime.date objects for the trip
    region_id      — UUID string, used to fetch disruption flags
    user_gear_class— highest gear class the user confirmed having (0–3)
    user_has_permit— True if user has confirmed permit acquisition

    Returns filtered list. Activities are modified in-place for
    weather overrides (disruption severity medium/low).
    """
    if not candidates:
        return []

    disruption = get_disruption(str(region_id))
    disrupted_ids, weather_overrides = _parse_disruption(disruption)

    filtered = []
    for activity in candidates:
        # ── Date availability ─────────────────────────────────────────
        if trip_dates:
            available = any(activity.is_available_on(d) for d in trip_dates)
            if not available:
                logger.debug(f'L1 date filter: {activity.name}')
                continue

        # ── Gear class ────────────────────────────────────────────────
        if activity.gear_class > user_gear_class:
            logger.debug(f'L1 gear filter: {activity.name} '
                         f'(needs {activity.gear_class}, user has {user_gear_class})')
            continue

        # ── Permit ────────────────────────────────────────────────────
        if activity.permit_required and not user_has_permit:
            logger.debug(f'L1 permit filter: {activity.name}')
            continue

        # ── Disruption: critical → remove entirely ────────────────────
        if str(activity.id) in disrupted_ids:
            logger.debug(f'L1 disruption critical: {activity.name}')
            continue

        # ── Disruption: medium/low → adjust weather scores ────────────
        if str(activity.id) in weather_overrides:
            override = weather_overrides[str(activity.id)]
            _apply_weather_override(activity, override)

        filtered.append(activity)

    logger.debug(f'L1 output: {len(filtered)}/{len(candidates)} candidates')
    return filtered


def _parse_disruption(disruption: dict) -> tuple:
    """
    Returns:
        disrupted_ids    — set of activity id strings to remove
        weather_overrides— dict of {activity_id: penalty_float}
    """
    if not disruption:
        return set(), {}

    disrupted_ids     = set()
    weather_overrides = {}

    severity           = disruption.get('severity', 'low')
    affected           = disruption.get('affected_activity_ids', [])
    category_wildcards = disruption.get('affected_categories', [])

    # For now severity drives the action; category wildcards are stored
    # and used in pipeline.py where we have access to all candidates
    if severity == 'critical':
        for aid in affected:
            disrupted_ids.add(str(aid))
    elif severity == 'high':
        for aid in affected:
            weather_overrides[str(aid)] = 0.30
    elif severity in ('medium', 'low'):
        for aid in affected:
            weather_overrides[str(aid)] = 0.15

    return disrupted_ids, weather_overrides


def _apply_weather_override(activity, penalty: float) -> None:
    """
    Reduces weather_score on seasonal_availability in-place.
    Does not persist to DB — runtime adjustment only.
    """
    try:
        updated = {}
        for season, vals in activity.seasonal_availability.items():
            updated[season] = {
                'score': max(0.0, vals.get('score', 0.75) - penalty),
                'bias':  max(0.0, vals.get('bias',  0.20) - penalty * 0.5),
            }
        activity.seasonal_availability = updated
    except Exception as e:
        logger.debug(f'Weather override failed for {activity.name}: {e}')


def apply_style_hard_gate(
    candidates: list,
    travel_style: float,
    recent_yang_count: int,
) -> list:
    """
    Removes activities that would violate the yang consecutive limit.
    A yin traveller (style <= 0.25) cannot have more than 1 yang activity
    in a row. Mixed (0.5) allows 2. Yang (>= 0.75) no limit.

    recent_yang_count — number of consecutive yang activities just placed.
    """
    if travel_style >= 0.75:
        return candidates

    max_consecutive = 1 if travel_style <= 0.25 else 2
    if recent_yang_count < max_consecutive:
        return candidates

    filtered = [
        a for a in candidates
        if str(a.tone) != 'yang'
    ]
    logger.debug(
        f'Style gate: removed {len(candidates)-len(filtered)} yang candidates '
        f'(style={travel_style}, recent_yang={recent_yang_count})'
    )
    return filtered