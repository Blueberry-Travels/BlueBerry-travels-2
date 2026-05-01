from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def retrain_scoring_models(self):
    try:
        from engine_meta.ml.scoring_models import _retrain_if_ready
        _retrain_if_ready()
        return {'status': 'retrained'}
    except Exception as e:
        logger.error(f'Scheduled retrain failed: {e}')
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def invalidate_engine_config(self):
    try:
        from blueberry_backend.communications import invalidate_engine_config_cache
        invalidate_engine_config_cache()
        return {'status': 'invalidated'}
    except Exception as e:
        raise self.retry(exc=e)