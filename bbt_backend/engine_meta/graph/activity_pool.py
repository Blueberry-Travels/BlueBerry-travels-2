"""
L0 — Activity Pool fetch.
Retrieves all registered, approved, active activities for a region.
Excludes primaries (already locked in the slot grid).
"""

import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)

POOL_CACHE_TTL = 300   # 5 minutes


def get_activity_pool(region_id: str, primary_ids: list) -> list:
    """
    Returns a list of Activity instances for the region,
    excluding any activities already selected as primaries.

    region_id    — UUID string of the Region
    primary_ids  — list of UUID strings to exclude
    """
    cache_key = f'pool:{region_id}'
    pool      = cache.get(cache_key)

    if pool is None:
        try:
            from engine_b2c.models import Activity
            pool = list(
                Activity.objects.filter(
                    region_id=region_id,
                    is_active=True,
                    content_approved=True,
                    is_filler=False,
                    node_type='activity',
                ).select_related('region')
            )
            cache.set(cache_key, pool, timeout=POOL_CACHE_TTL)
            logger.debug(f'L0 pool fetched: {len(pool)} activities for {region_id}')
        except Exception as e:
            logger.error(f'L0 pool fetch failed: {e}')
            return []

    # Exclude primaries
    primary_set = set(str(i) for i in primary_ids)
    filtered    = [a for a in pool if str(a.id) not in primary_set]
    logger.debug(f'L0 after primary exclusion: {len(filtered)} candidates')
    return filtered


def get_filler_pool(region_id: str) -> list:
    """
    Returns filler activities for a region.
    Used after the main pipeline to fill energy gaps.
    """
    cache_key = f'fillers:{region_id}'
    fillers   = cache.get(cache_key)
    if fillers is None:
        try:
            from engine_b2c.models import Activity
            fillers = list(
                Activity.objects.filter(
                    region_id=region_id,
                    is_active=True,
                    content_approved=True,
                    is_filler=True,
                ).select_related('region')
            )
            cache.set(cache_key, fillers, timeout=POOL_CACHE_TTL)
        except Exception as e:
            logger.error(f'Filler pool fetch failed: {e}')
            return []
    return fillers