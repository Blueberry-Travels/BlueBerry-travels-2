"""
L5 — Push scorer.

Combines RF reward prediction + arc fit + novelty decay + weather fit
into a single push_score that determines candidate selection.

Weights sourced from EngineConfig (w_reward / w_arc / w_novelty / w_weather).
"""

import logging
from blueberry_backend.communications import get_engine_config

logger = logging.getLogger(__name__)

# Novelty decay: how fast reward decays when a category repeats
_NOVELTY_DECAY = {
    0: 1.00,   # first use of this category
    1: 0.85,   # seen once before
    2: 0.65,   # seen twice
    3: 0.45,   # seen three times
    4: 0.25,   # four+ times — heavily penalised
}


def novelty_score(category: str, category_counts: dict) -> float:
    """
    Returns a novelty multiplier based on how many times this category
    has already appeared in the itinerary so far.

    category_counts — dict of {category_str: int} built by the pipeline loop.
    """
    count = category_counts.get(category, 0)
    decay = _NOVELTY_DECAY.get(count, 0.20)
    return decay


def weather_fit_score(activity, season: str) -> float:
    """
    weather_fit = weather_bias * weather_score for the current season.
    High bias + high score = activity is weather-special and conditions are good.
    """
    try:
        bias  = activity.weather_bias(season)
        score = activity.weather_score(season)
        return min(bias * score, 1.0)
    except Exception:
        return 0.20


def compute_push_score(
    predicted_reward: float,
    arc_fit:          float,
    category:         str,
    activity,
    season:           str,
    category_counts:  dict,
    config:           dict = None,
) -> float:
    """
    push_score = (
        w_reward * predicted_reward
      + w_arc    * arc_fit
      + w_novelty* novelty_score
      + w_weather* weather_fit
    )

    Returns float in approximately [0, 1].
    """
    if config is None:
        config = get_engine_config()

    w_reward  = float(config.get('w_reward',  0.40))
    w_arc     = float(config.get('w_arc',     0.25))
    w_novelty = float(config.get('w_novelty', 0.20))
    w_weather = float(config.get('w_weather', 0.15))

    ns  = novelty_score(category, category_counts)
    wfs = weather_fit_score(activity, season)

    score = (
        w_reward  * predicted_reward
        + w_arc   * arc_fit
        + w_novelty * ns
        + w_weather * wfs
    )
    return round(score, 6)


def select_top_candidate(
    candidates:      list,
    predicted_rewards: list,
    arc_fits:        list,
    season:          str,
    category_counts: dict,
    config:          dict = None,
) -> tuple:
    """
    Scores all candidates and returns (best_activity, best_push_score, scores_list).
    scores_list — list of (activity, push_score) for all candidates, sorted desc.
    """
    if not candidates:
        return None, 0.0, []

    scored = []
    for activity, pred, arc in zip(candidates, predicted_rewards, arc_fits):
        ps = compute_push_score(
            predicted_reward=pred,
            arc_fit=arc,
            category=activity.category,
            activity=activity,
            season=season,
            category_counts=category_counts,
            config=config,
        )
        scored.append((activity, ps))

    scored.sort(key=lambda x: -x[1])
    best_activity, best_score = scored[0]
    return best_activity, best_score, scored