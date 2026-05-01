"""
L2 — Travel style fit scorer.

Computes a style_fit multiplier [0.0, 1.0] for each candidate
based on the user's travel_style and the activity's tone.

This is a soft filter — it adjusts push_score weight, not a hard cut.
Hard style gates (consecutive yang limit) are in filters.py.
"""


def style_fit(activity_tone: str, travel_style: float) -> float:
    """
    Returns how well the activity tone matches the user's style.

    travel_style: 0.0 = pure yin, 1.0 = pure yang
    tone:         yin=0.0, both=0.5, yang=1.0

    Logic:
      - 'both' activities always score 1.0 (universally compatible)
      - 'yin' activities score higher for yin travellers
      - 'yang' activities score higher for yang travellers
      - Mismatch is penalised but not zeroed — a yin traveller can
        still have occasional yang nodes
    """
    tone = str(activity_tone).strip().lower()

    if tone == 'both':
        return 1.0

    if tone == 'yin':
        # Perfect for yin (0.0), tolerable for yang (1.0) = 0.40
        return round(max(0.40, 1.0 - travel_style * 0.60), 3)

    if tone == 'yang':
        # Perfect for yang (1.0), tolerable for yin (0.0) = 0.40
        return round(max(0.40, travel_style * 0.60 + 0.40), 3)

    return 0.80   # unknown tone — neutral


def apply_style_scores(candidates: list, travel_style: float) -> list:
    """
    Attaches a _style_fit attribute to each candidate.
    The pipeline multiplies push_score by this value at L5.
    Returns the same list (mutated in-place).
    """
    for activity in candidates:
        activity._style_fit = style_fit(activity.tone, travel_style)
    return candidates