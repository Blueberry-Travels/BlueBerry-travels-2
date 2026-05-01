"""
Placement phase — runs before the main candidate loop.

Responsibility:
  1. Assign fixed-time primaries to their natural time slots.
  2. Score flexible primaries across candidate arc positions
     and assign each to the slot where arc penalty is minimised.

Returns a SlotGrid — a list of Day objects, each with ordered slots.
Locked slots (primaries) are marked and skipped by the candidate loop.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

SLOTS_PER_DAY   = 5
DEFAULT_START_H = 7   # 07:00
SLOT_DURATION_H = 2   # approximate hours between slot starts


@dataclass
class Slot:
    day:          int             # 1-indexed
    position:     int             # 1-indexed within day
    slot_time:    str             # 'HH:MM'
    itn_arc_pos:  float           # 0.0–1.0
    arc_phase:    str             # 'rising' | 'peak' | 'falling'
    activity:     Optional[object] = None   # Activity instance if locked
    is_locked:    bool            = False   # True = primary, skip in loop
    predicted_reward: float       = 0.0


@dataclass
class SlotGrid:
    days:         int
    slots:        list = field(default_factory=list)   # flat list of Slot

    def open_slots(self):
        return [s for s in self.slots if not s.is_locked]

    def locked_slots(self):
        return [s for s in self.slots if s.is_locked]

    def total_slots(self):
        return len(self.slots)


def _slot_time(day: int, position: int, config: dict) -> str:
    """Returns 'HH:MM' for a given day/position using day_start_time from config."""
    try:
        start_parts = str(config.get('day_start_time', '07:00')).split(':')
        start_h = int(start_parts[0])
    except Exception:
        start_h = DEFAULT_START_H
    hour = start_h + (position - 1) * SLOT_DURATION_H
    hour = min(hour, 22)
    return f'{hour:02d}:00'


def _arc_phase(position: int, total: int) -> str:
    frac = position / total
    if frac < 0.33:
        return 'rising'
    if frac < 0.66:
        return 'peak'
    return 'falling'


def build_slot_grid(trip_days: int, config: dict) -> SlotGrid:
    """Build an empty SlotGrid for trip_days × SLOTS_PER_DAY slots."""
    grid  = SlotGrid(days=trip_days)
    total = trip_days * SLOTS_PER_DAY
    idx   = 0
    for day in range(1, trip_days + 1):
        for pos in range(1, SLOTS_PER_DAY + 1):
            itn_arc_pos = idx / total
            grid.slots.append(Slot(
                day=day,
                position=pos,
                slot_time=_slot_time(day, pos, config),
                itn_arc_pos=itn_arc_pos,
                arc_phase=_arc_phase(idx, total),
            ))
            idx += 1
    return grid


def _arc_penalty(predicted_reward: float, itn_arc_pos: float,
                 travel_style: float) -> float:
    """MSE of predicted_reward against ideal arc at this position."""
    if itn_arc_pos < 0.33:
        ideal = 0.80 + travel_style * 0.04
    elif itn_arc_pos < 0.66:
        ideal = 0.88 + travel_style * 0.06
    else:
        ideal = 0.86 + travel_style * 0.02
    return (predicted_reward - ideal) ** 2


def place_primaries(
    primaries: list,
    grid: SlotGrid,
    travel_style: float,
    season: str,
    trip_days: int,
    scorer,
) -> SlotGrid:
    """
    primaries — list of Activity instances the user picked.
    scorer    — RFScorer singleton.

    Fixed-time primaries are assigned to their natural time slot first.
    Flexible primaries are assigned to the open slot with lowest arc penalty.
    """
    open_slots = grid.open_slots()

    # ── Pass 1: fixed-time primaries ─────────────────────────────────────
    for activity in primaries:
        if not activity.is_fixed_route:
            continue
        # Find the slot whose time best matches the activity's preferred window
        best_slot = None
        best_diff = float('inf')
        for slot in open_slots:
            if slot.is_locked:
                continue
            slot_h = int(slot.slot_time.split(':')[0])
            act_h  = _preferred_hour(activity)
            diff   = abs(slot_h - act_h)
            if diff < best_diff:
                best_diff = diff
                best_slot = slot
        if best_slot:
            context = _make_context(best_slot, travel_style, season,
                                    trip_days, prev_effort=0.5)
            pred    = scorer.score_node(activity, context)
            best_slot.activity         = activity
            best_slot.is_locked        = True
            best_slot.predicted_reward = pred
            logger.debug(
                f'Fixed-time placed: {activity.name} → '
                f'D{best_slot.day}S{best_slot.position} pred={pred:.3f}'
            )

    # ── Pass 2: flexible primaries ────────────────────────────────────────
    for activity in primaries:
        if activity.is_fixed_route:
            continue
        best_slot    = None
        best_penalty = float('inf')
        best_pred    = 0.75

        for slot in grid.slots:
            if slot.is_locked:
                continue
            context = _make_context(slot, travel_style, season,
                                    trip_days, prev_effort=0.5)
            pred    = scorer.score_node(activity, context)
            penalty = _arc_penalty(pred, slot.itn_arc_pos, travel_style)
            if penalty < best_penalty:
                best_penalty = penalty
                best_slot    = slot
                best_pred    = pred

        if best_slot:
            best_slot.activity         = activity
            best_slot.is_locked        = True
            best_slot.predicted_reward = best_pred
            logger.debug(
                f'Flexible placed: {activity.name} → '
                f'D{best_slot.day}S{best_slot.position} '
                f'pred={best_pred:.3f} penalty={best_penalty:.4f}'
            )

    return grid


def _preferred_hour(activity) -> int:
    """Returns preferred start hour from activity's time windows."""
    try:
        windows = activity.preferred_time_windows
        if windows:
            h, _ = map(int, windows[0]['start'].split(':'))
            return h
    except Exception:
        pass
    # Defaults by category
    return {
        'cultural': 19, 'heritage': 9, 'trekking': 6,
        'wildlife': 6,  'meditation': 6, 'rafting': 9,
        'adventure_sports': 9,
    }.get(str(activity.category), 9)


def _make_context(slot: Slot, travel_style: float, season: str,
                  trip_days: int, prev_effort: float) -> dict:
    return {
        'travel_style':     travel_style,
        'itn_arc_pos':      slot.itn_arc_pos,
        'daily_arc_phase':  slot.arc_phase,
        'slot_time':        slot.slot_time,
        'trip_length_days': trip_days,
        'season':           season,
        'prev_effort':      prev_effort,
        'is_holiday':       False,
        'is_weekend':       False,
        'region_config':    None,
    }