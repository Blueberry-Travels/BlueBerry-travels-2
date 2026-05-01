"""
AbhiBus API client.
Identical flow to RedBus — wraps RedBusClient with AbhiBus credentials.
"""

import logging
from engine_b2c.redbus import RedBusClient, RedBusDisabledError, RedBusAPIError

logger = logging.getLogger(__name__)


class AbhiBusClient(RedBusClient):
    """
    AbhiBus uses the same API structure as RedBus.
    Only credentials and base_url differ.
    Inherits all methods: search_buses, get_seat_map, block_seats,
    book_seats, get_booking, cancel_booking.
    """
    def __init__(self):
        super().__init__(provider_key='abhibus')


def get_bus_client():
    """
    Returns whichever bus client is active.
    Tries RedBus first, falls back to AbhiBus.
    If neither active, raises an error with admin guidance.
    """
    from engine_meta.models import ThirdPartyAPIConfig

    redbus_on  = ThirdPartyAPIConfig.is_enabled('redbus')
    abhibus_on = ThirdPartyAPIConfig.is_enabled('abhibus')

    if redbus_on:
        return RedBusClient()
    if abhibus_on:
        return AbhiBusClient()

    raise RedBusDisabledError(
        'No bus API is enabled. '
        'Enable RedBus or AbhiBus in Admin → Third-Party APIs.')