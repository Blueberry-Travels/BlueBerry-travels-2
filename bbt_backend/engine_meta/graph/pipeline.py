"""
Graph Pipeline Orchestrator — L0 through L5 + filler + transit.

Entry point:
    from engine_meta.graph.pipeline import build_itinerary
    result = build_itinerary(request_data)

request_data keys:
    region_id       str      UUID of Region
    travel_style    float    0.0–1.0
    trip_days       int      1–14
    trip_dates      list     [datetime.date, ...]
    primary_ids     list     [UUID str, ...]  activities user picked
    season          str      'summer' | 'winter' | 'monsoon'
    user_gear_class int      0–3
    user_has_permit bool
    is_holiday      bool
    is_weekend      bool

Returns ItineraryResult dataclass.
"""

import logging
from dataclasses import dataclass, field
from datetime import date as DateType

logger = logging.getLogger(__name__)


@dataclass
class ItineraryNode:
    activity:          object          # Activity or TransitNode
    day:               int
    position:          int
    slot_time:         str
    predicted_reward:  float
    push_score:        float
    is_locked:         bool            # True = user-picked primary
    is_filler:         bool
    is_transit:        bool
    user_can_remove:   bool            # True for fillers only


@dataclass
class ItineraryResult:
    nodes:             list = field(default_factory=list)
    days:              int  = 0
    region_id:         str  = ''
    travel_style:      float= 0.5
    season:            str  = 'summer'
    total_activities:  int  = 0
    filler_count:      int  = 0
    transit_count:     int  = 0
    noc_required:      list = field(default_factory=list)  # activity names
    warnings:          list = field(default_factory=list)


def build_itinerary(request_data: dict) -> ItineraryResult:
    """Full L0–L5 pipeline + filler insertion + transit insertion."""
    from engine_meta.ml.scorer import get_scorer
    from engine_meta.graph.activity_pool import get_activity_pool, get_filler_pool
    from engine_meta.graph.filters import apply_hard_filters, apply_style_hard_gate
    from engine_meta.graph.placement import (
        build_slot_grid, place_primaries, _make_context, SLOTS_PER_DAY
    )
    from engine_meta.graph.arc_scorer import arc_fit_score, daily_arc_phase
    from engine_meta.graph.push_scorer import compute_push_score, select_top_candidate
    from engine_meta.graph.style_scorer import apply_style_scores
    from engine_meta.graph.transit import insert_transit_nodes
    from engine_b2c.models import Activity
    from blueberry_backend.communications import get_engine_config

    config        = get_engine_config()
    scorer        = get_scorer()
    result        = ItineraryResult()

    # ── Unpack request ────────────────────────────────────────────────────
    region_id      = str(request_data['region_id'])
    travel_style   = float(request_data.get('travel_style', 0.5))
    trip_days      = int(request_data.get('trip_days', 2))
    trip_dates     = request_data.get('trip_dates', [])
    primary_ids    = [str(i) for i in request_data.get('primary_ids', [])]
    season         = request_data.get('season', 'summer')
    user_gear      = int(request_data.get('user_gear_class', 0))
    user_permit    = bool(request_data.get('user_has_permit', False))
    is_holiday     = bool(request_data.get('is_holiday', False))
    is_weekend     = bool(request_data.get('is_weekend', False))

    result.region_id    = region_id
    result.travel_style = travel_style
    result.season       = season
    result.days         = trip_days

    # ── Fetch primaries from DB ───────────────────────────────────────────
    primaries = list(Activity.objects.filter(
        id__in=primary_ids
    ).select_related('region')) if primary_ids else []

    # ── L0: Activity pool ─────────────────────────────────────────────────
    candidates = get_activity_pool(region_id, primary_ids)

    # ── L1: Hard filters ──────────────────────────────────────────────────
    candidates = apply_hard_filters(
        candidates, trip_dates, region_id, user_gear, user_permit)

    # ── Placement phase: lock primaries into slots ────────────────────────
    grid = build_slot_grid(trip_days, config)
    grid = place_primaries(primaries, grid, travel_style, season, trip_days, scorer)

    # ── L2 + L3 + L4 + L5: Fill open slots ───────────────────────────────
    category_counts    = {}
    recent_yang_count  = 0
    prev_effort        = 0.5

    # Seed category counts from primaries
    for s in grid.locked_slots():
        if s.activity:
            cat = s.activity.category
            category_counts[cat] = category_counts.get(cat, 0) + 1

    for slot in grid.slots:
        if slot.is_locked:
            # Still update tracking state
            if slot.activity:
                if slot.activity.tone == 'yang':
                    recent_yang_count += 1
                else:
                    recent_yang_count = 0
                prev_effort = float(getattr(slot.activity, 'effort_score', 0.5))
            continue

        # L2: Style soft scores + hard gate
        pool = apply_style_hard_gate(candidates, travel_style, recent_yang_count)
        pool = apply_style_scores(pool, travel_style)

        if not pool:
            logger.warning(f'No candidates for slot D{slot.day}S{slot.position}')
            continue

        # L3: RF score all candidates at this slot context
        region_config = _get_region_config(region_id)
        contexts = [
            {
                'travel_style':     travel_style,
                'itn_arc_pos':      slot.itn_arc_pos,
                'daily_arc_phase':  slot.arc_phase,
                'slot_time':        slot.slot_time,
                'trip_length_days': trip_days,
                'season':           season,
                'prev_effort':      prev_effort,
                'is_holiday':       is_holiday,
                'is_weekend':       is_weekend,
                'region_config':    region_config,
            }
            for _ in pool
        ]
        predicted_rewards = scorer.score_batch(pool, contexts)

        # Apply style_fit multiplier to predicted rewards
        predicted_rewards = [
            pr * getattr(a, '_style_fit', 1.0)
            for pr, a in zip(predicted_rewards, pool)
        ]

        # L4: Arc fit scores
        arc_fits = [
            arc_fit_score(pr, slot.itn_arc_pos, travel_style)
            for pr in predicted_rewards
        ]

        # L5: Push score + select
        best, best_score, _ = select_top_candidate(
            pool, predicted_rewards, arc_fits, season, category_counts, config)

        if best is None:
            continue

        # Lock into slot
        slot.activity         = best
        slot.is_locked        = True
        slot.predicted_reward = predicted_rewards[pool.index(best)]

        # Update tracking
        cat = best.category
        category_counts[cat] = category_counts.get(cat, 0) + 1
        recent_yang_count    = recent_yang_count + 1 if best.tone == 'yang' else 0
        prev_effort          = float(best.effort_score)

        # Remove from pool so it can't be selected again
        candidates = [c for c in candidates if str(c.id) != str(best.id)]

    # ── Filler insertion ──────────────────────────────────────────────────
    _insert_fillers(grid, region_id, config)

    # ── Build ordered activity list from grid ─────────────────────────────
    ordered = [s.activity for s in grid.slots if s.activity is not None]

    # ── Transit insertion ─────────────────────────────────────────────────
    ordered_with_transit = insert_transit_nodes(ordered, config)

    # ── Build result nodes ────────────────────────────────────────────────
    noc_list = []
    for idx, item in enumerate(ordered_with_transit):
        is_transit = getattr(item, 'is_transit', False)
        is_filler  = getattr(item, 'is_filler', False)

        # Find matching slot for day/position info
        slot_match = _find_slot(grid, item)

        node = ItineraryNode(
            activity=item,
            day=slot_match.day if slot_match else ((idx // SLOTS_PER_DAY) + 1),
            position=idx,
            slot_time=slot_match.slot_time if slot_match else '09:00',
            predicted_reward=getattr(item, 'reward_score', 0.75),
            push_score=0.0,
            is_locked=not is_filler and not is_transit,
            is_filler=is_filler,
            is_transit=is_transit,
            user_can_remove=is_filler,
        )
        result.nodes.append(node)

        if not is_transit and not is_filler:
            if getattr(item, 'noc_required', False) or getattr(item, 'noc_auto_flag', lambda: False)():
                noc_list.append(item.name)

    result.total_activities = sum(
        1 for n in result.nodes if not n.is_transit and not n.is_filler)
    result.filler_count  = sum(1 for n in result.nodes if n.is_filler)
    result.transit_count = sum(1 for n in result.nodes if n.is_transit)
    result.noc_required  = noc_list

    logger.info(
        f'Pipeline complete: {result.total_activities} activities, '
        f'{result.filler_count} fillers, {result.transit_count} transits, '
        f'{len(noc_list)} NOC flags'
    )
    return result


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_region_config(region_id: str):
    try:
        from engine_b2c.models import Region
        region = Region.objects.select_related().get(id=region_id)
        if region.region_code:
            from engine_meta.models import RegionConfig
            return RegionConfig.objects.get(code=region.region_code)
    except Exception:
        pass
    return None


def _insert_fillers(grid, region_id: str, config: dict) -> None:
    """
    Scans the day for energy gaps and inserts fillers.
    Gap = two consecutive high-effort slots (effort > 0.50).
    Target filler rate: filler_rate_min–filler_rate_max from config.
    """
    from engine_meta.graph.activity_pool import get_filler_pool
    fillers = get_filler_pool(region_id)
    if not fillers:
        return

    filler_min = float(config.get('filler_rate_min', 0.10))
    filler_max = float(config.get('filler_rate_max', 0.18))
    total      = len(grid.slots)
    current_fillers = 0
    filler_idx = 0

    for i, slot in enumerate(grid.slots[:-1]):
        if current_fillers / max(total, 1) >= filler_max:
            break
        curr_act = slot.activity
        next_act = grid.slots[i + 1].activity
        if curr_act is None or next_act is None:
            continue
        curr_effort = float(getattr(curr_act, 'effort_score', 0))
        next_effort = float(getattr(next_act, 'effort_score', 0))
        # Insert filler between two high-effort slots
        if curr_effort > 0.50 and next_effort > 0.50:
            if filler_idx < len(fillers):
                f = fillers[filler_idx % len(fillers)]
                f.is_filler   = True
                f._is_filler  = True
                slot._filler_after = f
                filler_idx   += 1
                current_fillers += 1


def _find_slot(grid, activity):
    """Find the slot that holds this activity instance."""
    for s in grid.slots:
        if s.activity is activity:
            return s
    return None