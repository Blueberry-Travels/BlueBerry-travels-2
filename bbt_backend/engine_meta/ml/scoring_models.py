"""
Scoring models stub.
Exposes suggest_scores(), add_training_sample(), _retrain_if_ready(), SCORE_MODELS.
These will be replaced by the full RF implementation in Phase 1 ML build.
"""
import logging

logger = logging.getLogger(__name__)

SCORE_MODELS = [
    'effort_score',
    'reward_score',
    'recovery_coeff',
    'significance_score',
    'tone',
    'is_filler',
    'quality_score',
]

# Simple rule-based suggestions until RF is trained.
_EFFORT_BY_CATEGORY = {
    'trekking':        0.60,
    'adventure_sports':0.75,
    'rafting':         0.65,
    'camping':         0.25,
    'wildlife':        0.20,
    'cultural':        0.10,
    'heritage':        0.15,
    'meditation':      0.05,
    'photography':     0.15,
    'food':            0.08,
    'hobbyist':        0.20,
    'water_sports':    0.50,
    'rest':            0.02,
    'transit':         0.10,
}

_TONE_BY_CATEGORY = {
    'trekking':        'both',
    'adventure_sports':'yang',
    'rafting':         'yang',
    'camping':         'yin',
    'wildlife':        'yin',
    'cultural':        'yin',
    'heritage':        'yin',
    'meditation':      'yin',
    'photography':     'yin',
    'food':            'yin',
    'hobbyist':        'yin',
    'water_sports':    'yang',
    'rest':            'yin',
    'transit':         'both',
}

_EFFORT_BY_RISK = {
    'casual':   0.00,
    'moderate': 0.20,
    'high':     0.40,
    'extreme':  0.60,
}


def suggest_scores(activity_data: dict) -> dict:
    """
    Rule-based score suggestion for admin activity registration.
    Returns a dict with suggested field values that admins can override.
    """
    category  = activity_data.get('category', 'cultural')
    risk_tier = activity_data.get('risk_tier', 'casual')
    duration  = float(activity_data.get('duration_hrs', 1.0))
    is_fixed  = activity_data.get('is_fixed_route', False)
    has_time  = activity_data.get('time_of_day_sensitivity', False)
    tools     = activity_data.get('tools', [])

    base_effort   = _EFFORT_BY_CATEGORY.get(category, 0.30)
    risk_effort   = _EFFORT_BY_RISK.get(risk_tier, 0.0)
    tool_effort   = min(len(tools) * 0.05, 0.20)
    effort_score  = min(round(base_effort + risk_effort + tool_effort, 2), 1.0)

    # Reward heuristic: fixed route or time-sensitive = potentially higher reward
    base_reward  = 0.75
    if is_fixed or has_time:
        base_reward += 0.05
    if duration >= 3.0:
        base_reward -= 0.03      # longer = slightly lower per-node reward
    if category in ('wildlife', 'cultural', 'heritage', 'photography'):
        base_reward += 0.05
    reward_score = min(round(base_reward, 2), 1.0)

    recovery_coeff  = round(max(0.0, effort_score - 0.30), 2)
    significance    = round(min(reward_score + (0.10 if is_fixed else 0.0), 1.0), 2)
    tone            = _TONE_BY_CATEGORY.get(category, 'both')
    is_filler_guess = (effort_score < 0.10 and not is_fixed)

    return {
        'effort_score':      effort_score,
        'reward_score':      reward_score,
        'recovery_coeff':    recovery_coeff,
        'significance_score':significance,
        'tone':              tone,
        'is_filler':         is_filler_guess,
    }


def add_training_sample(features: dict, targets: dict) -> None:
    """
    Persist a confirmed admin-labelled sample for future RF retraining.
    """
    try:
        from engine_meta.models import ScoringTrainingSample
        ScoringTrainingSample.objects.create(
            features=features,
            effort_score=targets.get('effort_score'),
            reward_score=targets.get('reward_score'),
            recovery_coeff=targets.get('recovery_coeff'),
            significance_score=targets.get('significance_score'),
            tone=targets.get('tone'),
        )
    except Exception as e:
        logger.error(f'add_training_sample failed: {e}')


def _retrain_if_ready() -> None:
    """
    Retrain scoring models when enough samples are available.
    Threshold: 10 samples minimum (will increase as real data accumulates).
    Stub — full RF implementation replaces this in Phase 1 ML build.
    """
    try:
        from engine_meta.models import ScoringTrainingSample, ScoringModel
        from django.utils import timezone

        total = ScoringTrainingSample.objects.count()
        if total < 10:
            logger.info(f'Retrain skipped: {total}/10 samples.')
            return

        # Placeholder — marks models as "trained" so MLModelStatusView shows progress
        for score_type in SCORE_MODELS:
            ScoringModel.objects.update_or_create(
                score_type=score_type,
                defaults={
                    'is_trained':       True,
                    'training_samples': total,
                    'last_trained_at':  timezone.now(),
                    'model_json':       '{"stub": true}',
                },
            )
        logger.info(f'Stub retrain complete. {total} samples, {len(SCORE_MODELS)} models marked.')
    except Exception as e:
        logger.error(f'_retrain_if_ready failed: {e}')