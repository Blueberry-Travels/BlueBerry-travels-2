"""
RF Scorer — loaded once at startup, called at L3 of the graph pipeline.

Usage:
    scorer = RFScorer()           # loads trained_model.json from disk
    score = scorer.score_node(activity, context)  # returns float 0.0–1.0

The scorer is a singleton — import get_scorer() everywhere in the pipeline.
"""

import os
import logging
import threading

logger = logging.getLogger(__name__)

DEFAULT_MODEL_PATH = os.path.join(
    os.path.dirname(__file__), 'trained_model.json'
)


class RFScorer:
    """
    Wraps the trained RandomForest.
    Thread-safe: one instance shared across all pipeline calls.
    """

    def __init__(self, model_path: str = DEFAULT_MODEL_PATH):
        self.model_path = model_path
        self._rf        = None
        self._lock      = threading.Lock()
        self._load()

    def _load(self):
        from engine_meta.ml.random_forest import RandomForest
        if not os.path.exists(self.model_path):
            logger.warning(
                f'Trained model not found at {self.model_path}. '
                f'Run trainer.train() to generate it. '
                f'Scorer will return neutral 0.75 until model is available.'
            )
            return
        try:
            self._rf = RandomForest.load(self.model_path)
            logger.info(
                f'RF model loaded: {self._rf.n_trees} trees from {self.model_path}'
            )
        except Exception as e:
            logger.error(f'Failed to load RF model: {e}')
            self._rf = None

    def reload(self):
        """Hot-reload the model from disk without restarting the server."""
        with self._lock:
            logger.info('Reloading RF model...')
            self._load()

    @property
    def is_ready(self) -> bool:
        return self._rf is not None and self._rf.is_trained

    def score_node(self, activity, context: dict) -> float:
        """
        Score a single activity at a specific pipeline slot.

        activity — engine_b2c.models.Activity instance
        context  — dict (see feature_extractor.extract_from_activity)

        Returns predicted reward float 0.0–1.0.
        Falls back to activity.reward_score if model unavailable.
        """
        if not self.is_ready:
            return float(getattr(activity, 'reward_score', 0.75))

        try:
            from engine_meta.ml.feature_extractor import (
                extract_from_activity, validate_vector
            )
            vector = extract_from_activity(activity, context)
            validate_vector(vector)

            with self._lock:
                return self._rf.predict(vector)

        except Exception as e:
            logger.error(
                f'score_node failed for activity {getattr(activity, "id", "?")} '
                f'context={context}: {e}'
            )
            return float(getattr(activity, 'reward_score', 0.75))

    def score_batch(self, activities: list, contexts: list) -> list:
        """
        Score a list of (activity, context) pairs.
        Returns list of floats in the same order.
        Used by the pipeline to score all candidates at a slot in one call.
        """
        if not self.is_ready:
            return [float(getattr(a, 'reward_score', 0.75)) for a in activities]

        results = []
        for activity, context in zip(activities, contexts):
            results.append(self.score_node(activity, context))
        return results


# ── Singleton ─────────────────────────────────────────────────────────────────
# One instance per process. Import this everywhere in the pipeline.

_scorer_instance = None
_scorer_lock     = threading.Lock()


def get_scorer(model_path: str = DEFAULT_MODEL_PATH) -> RFScorer:
    """
    Returns the singleton RFScorer instance.
    Creates it on first call, reuses on subsequent calls.
    """
    global _scorer_instance
    if _scorer_instance is None:
        with _scorer_lock:
            if _scorer_instance is None:
                _scorer_instance = RFScorer(model_path)
    return _scorer_instance


def reload_scorer():
    """
    Force a hot-reload of the model.
    Called by the Celery retrain task after a new model is saved.
    """
    global _scorer_instance
    with _scorer_lock:
        if _scorer_instance is not None:
            _scorer_instance.reload()
        else:
            _scorer_instance = RFScorer()