"""
Transit node insertion.

After the main candidate loop fills all open slots, this module:
  1. Queries OSRM for travel time between consecutive activity pairs.
  2. Inserts a transit node where travel time > transit_threshold_min.
  3. Transit nodes are non-negotiable — users can swap transport mode
     but cannot remove the node.

OSRM self-hosted at OSRM_BASE_URL (settings.py).
Falls back to straight-line distance estimate if OSRM unavailable.
"""

import math
import logging
import urllib.request
import urllib.parse
import json

from django.conf import settings
from blueberry_backend.communications import get_engine_config

logger = logging.getLogger(__name__)

TRANSIT_FIXED_SCORE = 4.5   # Display score for transit nodes (filler-level)
EARTH_RADIUS_KM     = 6371.0
AVG_ROAD_SPEED_KMH  = 30.0  # conservative for mountain regions


class TransitNode:
    """Lightweight transit node — not a DB Activity, inserted by pipeline only."""

    def __init__(self, from_activity, to_activity,
                 travel_time_min: float, transport_options: list):
        self.id              = None          # no DB id
        self.name            = f'Transit: {_short(from_activity)} → {_short(to_activity)}'
        self.category        = 'transit'
        self.tone            = 'both'
        self.effort_score    = 0.10
        self.duration_hrs    = round(travel_time_min / 60.0, 2)
        self.reward_score    = TRANSIT_FIXED_SCORE / 10.0
        self.is_filler       = False
        self.is_transit      = True
        self.node_type       = 'transit'
        self.travel_time_min = travel_time_min
        self.transport_options = transport_options  # ['cab', 'bus', 'train']
        self.from_activity   = from_activity
        self.to_activity     = to_activity

    def __repr__(self):
        return f'<TransitNode {self.name} {self.travel_time_min:.0f}min>'


def insert_transit_nodes(
    ordered_activities: list,
    config: dict = None,
) -> list:
    """
    Takes the ordered list of Activity instances (post pipeline loop).
    Returns a new list with TransitNode objects inserted where needed.

    config — EngineConfig dict; if None, fetched from cache.
    """
    if not ordered_activities or len(ordered_activities) < 2:
        return ordered_activities

    if config is None:
        config = get_engine_config()

    threshold_min = int(config.get('transit_threshold_min', 45))
    result        = [ordered_activities[0]]

    for i in range(1, len(ordered_activities)):
        prev = ordered_activities[i - 1]
        curr = ordered_activities[i]

        travel_min = _get_travel_time(prev, curr)

        if travel_min > threshold_min:
            options = _transport_options(travel_min)
            node    = TransitNode(prev, curr, travel_min, options)
            result.append(node)
            logger.debug(
                f'Transit inserted: {prev.name} → {curr.name} '
                f'({travel_min:.0f} min, options={options})'
            )

        result.append(curr)

    return result


def _get_travel_time(from_act, to_act) -> float:
    """
    Returns estimated travel time in minutes between two activities.
    Tries OSRM first, falls back to straight-line estimate.
    """
    lat1 = getattr(from_act, 'lat', None)
    lon1 = getattr(from_act, 'lng', None)
    lat2 = getattr(to_act,   'lat', None)
    lon2 = getattr(to_act,   'lng', None)

    if None in (lat1, lon1, lat2, lon2):
        # No GPS — assume no transit needed
        return 0.0

    if lat1 == lat2 and lon1 == lon2:
        return 0.0

    try:
        return _osrm_travel_time(lat1, lon1, lat2, lon2)
    except Exception as e:
        logger.debug(f'OSRM failed ({e}), using straight-line estimate')
        return _straight_line_time(lat1, lon1, lat2, lon2)


def _osrm_travel_time(lat1, lon1, lat2, lon2) -> float:
    """Query self-hosted OSRM for driving duration in minutes."""
    base = getattr(settings, 'OSRM_BASE_URL', 'http://router.project-osrm.org')
    url  = (f'{base}/route/v1/driving/'
            f'{lon1},{lat1};{lon2},{lat2}'
            f'?overview=false&steps=false')
    req  = urllib.request.Request(url, headers={'User-Agent': 'Blueberry/1.0'})
    with urllib.request.urlopen(req, timeout=3) as resp:
        data = json.loads(resp.read())
    duration_s = data['routes'][0]['duration']
    return duration_s / 60.0


def _straight_line_time(lat1, lon1, lat2, lon2) -> float:
    """Haversine distance → estimated driving time."""
    dlat  = math.radians(lat2 - lat1)
    dlon  = math.radians(lon2 - lon1)
    a     = (math.sin(dlat / 2) ** 2
             + math.cos(math.radians(lat1))
             * math.cos(math.radians(lat2))
             * math.sin(dlon / 2) ** 2)
    dist_km = 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))
    # Mountain road factor: actual road distance ≈ 1.5x straight line
    road_km = dist_km * 1.5
    return (road_km / AVG_ROAD_SPEED_KMH) * 60.0


def _transport_options(travel_time_min: float) -> list:
    """
    Returns viable transport modes based on travel time.
    User can swap between these on the frontend — cannot remove the node.
    """
    options = ['cab']
    if travel_time_min > 60:
        options.append('bus')
    if travel_time_min > 120:
        options.append('train')
    return options


def _short(activity) -> str:
    name = getattr(activity, 'name', 'Unknown')
    return name[:20] + ('…' if len(name) > 20 else '')