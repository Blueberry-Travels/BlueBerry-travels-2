"""
L4 — Arc scorer (pure formula, no ML).

Computes arc_fit score for a candidate at a specific itinerary position.
Based on the ideal reward arc derived from training data analysis.
"""


def ideal_reward(itn_arc_pos: float, travel_style: float) -> float:
    """
    Ideal reward at a given arc position.
    Derived from training data Step 1 analysis:
        first third:  0.80 + style * 0.04
        mid third:    0.88 + style * 0.06
        last third:   0.86 + style * 0.02
    """
    if itn_arc_pos < 0.33:
        return 0.80 + travel_style * 0.04
    if itn_arc_pos < 0.66:
        return 0.88 + travel_style * 0.06
    return 0.86 + travel_style * 0.02


def arc_fit_score(predicted_reward: float,
                  itn_arc_pos: float,
                  travel_style: float) -> float:
    """
    Returns arc_fit in [0, 1].
    1.0 = perfect match to ideal arc.
    0.0 = maximum deviation.

    arc_penalty = (predicted - ideal)²
    arc_fit     = 1 - arc_penalty (normalised, clamped)
    """
    ideal   = ideal_reward(itn_arc_pos, travel_style)
    penalty = (predicted_reward - ideal) ** 2
    # Max possible penalty = (1.0 - 0.0)² = 1.0, so no scaling needed.
    return max(0.0, 1.0 - penalty)


def daily_arc_phase(day_position: int, slots_per_day: int = 5) -> str:
    """
    Returns 'rising' | 'peak' | 'falling' based on position within the day.
    day_position is 1-indexed.
    """
    frac = (day_position - 1) / max(slots_per_day - 1, 1)
    if frac < 0.33:
        return 'rising'
    if frac < 0.66:
        return 'peak'
    return 'falling'