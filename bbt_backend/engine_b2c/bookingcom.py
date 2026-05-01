"""
Booking.com Demand API fallback for hotel stays.

Flow:
  1. Pipeline checks if region has verified platform hotels for dates.
  2. If yes → platform hotels used, Booking.com never called.
  3. If no → this module is called.
  4. Admin can disable globally via EngineConfig.bookingcom_enabled.

Booking.com Demand API (affiliate):
  Base: https://distribution-xml.booking.com/2.9/json
  Auth: HTTP Basic — affiliate_id:api_key

All results are labelled "Powered by Booking.com" — non-negotiable.
Confirmation mechanism:
  - instant_confirm=True  → API handles booking directly, PNR returned
  - instant_confirm=False → coordinator notified, contacts property,
                            confirms or rejects within 6h SLA
"""

import json
import logging
import urllib.request
import urllib.parse
import base64

from blueberry_backend.communications import get_engine_config

logger = logging.getLogger(__name__)

BOOKINGCOM_BASE = 'https://distribution-xml.booking.com/2.9/json'


class BookingComClient:
    """
    Thin wrapper around the Booking.com Demand API.
    Credentials pulled from EngineConfig — never hardcoded.
    """

    def __init__(self):
        config           = get_engine_config()
        self.enabled     = config.get('bookingcom_enabled', True)
        self.api_key     = config.get('bookingcom_api_key', '')
        self.affiliate   = config.get('bookingcom_affiliate', '')
        self._auth_header = self._build_auth()

    def _build_auth(self) -> str:
        if not self.affiliate or not self.api_key:
            return ''
        raw = f'{self.affiliate}:{self.api_key}'.encode()
        return 'Basic ' + base64.b64encode(raw).decode()

    def _get(self, endpoint: str, params: dict) -> dict:
        """Makes a GET request to Booking.com API. Returns parsed JSON."""
        if not self.enabled:
            raise BookingComDisabledError(
                'Booking.com fallback is disabled by admin.')
        if not self._auth_header:
            raise BookingComConfigError(
                'Booking.com credentials not configured. '
                'Set bookingcom_api_key and bookingcom_affiliate in EngineConfig.')

        qs  = urllib.parse.urlencode(params)
        url = f'{BOOKINGCOM_BASE}/{endpoint}?{qs}'
        req = urllib.request.Request(url, headers={
            'Authorization': self._auth_header,
            'Accept':        'application/json',
            'User-Agent':    'Blueberry/1.0',
        })
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            logger.error(f'Booking.com HTTP {e.code}: {e.reason} — {url}')
            raise BookingComAPIError(f'Booking.com API error {e.code}: {e.reason}')
        except Exception as e:
            logger.error(f'Booking.com request failed: {e}')
            raise BookingComAPIError(f'Booking.com request failed: {e}')

    def search_hotels(
        self,
        checkin:   str,    # 'YYYY-MM-DD'
        checkout:  str,    # 'YYYY-MM-DD'
        city_id:   str,    # Booking.com city ID
        adults:    int = 2,
        rooms:     int = 1,
        currency:  str = 'INR',
        language:  str = 'en-gb',
        rows:      int = 20,
    ) -> list:
        """
        Search available hotels.
        Returns a list of normalised hotel dicts.
        """
        params = {
            'checkin':      checkin,
            'checkout':     checkout,
            'city_ids':     city_id,
            'guest_qty':    adults,
            'room_qty':     rooms,
            'currency':     currency,
            'language':     language,
            'rows':         rows,
            'offset':       0,
            'extras':       'hotel_info,hotel_photos,hotel_facilities,room_info',
        }
        raw = self._get('hotels', params)
        return [_normalise_hotel(h) for h in raw.get('result', [])]

    def get_room_availability(
        self,
        hotel_id:  str,
        checkin:   str,
        checkout:  str,
        adults:    int = 2,
        rooms:     int = 1,
        currency:  str = 'INR',
    ) -> list:
        """
        Returns available room types for a specific hotel.
        """
        params = {
            'hotel_ids':  hotel_id,
            'checkin':    checkin,
            'checkout':   checkout,
            'guest_qty':  adults,
            'room_qty':   rooms,
            'currency':   currency,
            'extras':     'room_info,hotel_photos',
        }
        raw = self._get('hotels', params)
        results = raw.get('result', [])
        if not results:
            return []
        return [_normalise_room(r) for r in results[0].get('room_data', [])]

    def is_available(self) -> bool:
        """Quick connectivity check."""
        if not self.enabled or not self._auth_header:
            return False
        try:
            self._get('countries', {'languages': 'en-gb', 'rows': 1})
            return True
        except Exception:
            return False


# ── Platform override check ───────────────────────────────────────────────────

def should_use_bookingcom(region_id: str, checkin: str, checkout: str) -> bool:
    """
    Returns True if Booking.com fallback should be used.
    Returns False (use platform) if:
      - Booking.com is disabled globally
      - Platform has verified hotels available for these dates
    """
    config = get_engine_config()
    if not config.get('bookingcom_enabled', True):
        logger.info('Booking.com disabled by admin — using platform only.')
        return False

    try:
        from datetime import date
        from engine_b2c.models import Activity
        y1, m1, d1 = map(int, checkin.split('-'))
        y2, m2, d2 = map(int, checkout.split('-'))
        checkin_date  = date(y1, m1, d1)
        checkout_date = date(y2, m2, d2)

        # Check real room availability across requested dates
        from engine_b2c.models import RoomAvailability
        if RoomAvailability.is_available_for_region(region_id, checkin, checkout):
            logger.info(
                f'Platform rooms available for {region_id} '
                f'{checkin}→{checkout} — Booking.com not needed.')
            return False

    except Exception as e:
        logger.error(f'Platform hotel check failed: {e}')
        # On error, fall through to Booking.com
        pass

    logger.info(f'No platform hotels for {region_id} — using Booking.com fallback.')
    return True


def get_hotels_for_region(
    region_id: str,
    checkin:   str,
    checkout:  str,
    adults:    int = 2,
    rooms:     int = 1,
) -> dict:
    """
    Main entry point called by the itinerary builder for stay nodes.

    Returns:
    {
        'source':  'platform' | 'bookingcom' | 'none',
        'hotels':  [...],
        'powered_by_label': 'Powered by Booking.com' | None,
    }
    """
    if not should_use_bookingcom(region_id, checkin, checkout):
        return {
            'source':          'platform',
            'hotels':          [],
            'powered_by_label': None,
        }

    # Get Booking.com city_id for this region
    city_id = _region_to_city_id(region_id)
    if not city_id:
        logger.warning(f'No Booking.com city_id mapped for region {region_id}')
        return {'source': 'none', 'hotels': [], 'powered_by_label': None}

    try:
        client = BookingComClient()
        hotels = client.search_hotels(
            checkin=checkin, checkout=checkout,
            city_id=city_id, adults=adults, rooms=rooms,
        )
        return {
            'source':          'bookingcom',
            'hotels':          hotels,
            'powered_by_label': 'Powered by Booking.com',
        }
    except BookingComDisabledError:
        return {'source': 'none', 'hotels': [], 'powered_by_label': None}
    except (BookingComConfigError, BookingComAPIError) as e:
        logger.error(f'Booking.com fallback failed: {e}')
        return {'source': 'none', 'hotels': [], 'powered_by_label': None}


# ── Region → Booking.com city ID map ─────────────────────────────────────────
# Admin extends this via EngineConfig.custom_coefficients['bookingcom_city_ids']
# until a proper RegionConfig field is added.

_DEFAULT_CITY_IDS = {
    'GHW': '-2109373',   # Rishikesh
    'KMN': '-2092819',   # Nainital
    'HPS': '-2092406',   # Manali
    'HSD': '-2092391',   # Shimla
    'LDK': '-2112228',   # Leh
    'RAJ': '-2092654',   # Jaipur
    'PNJ': '-2092561',   # Amritsar
    'HRY': '-2092488',   # Chandigarh
    'ASM': '-2092312',   # Guwahati
    'MEG': '-2112312',   # Shillong
    'ARP': '-2112298',   # Itanagar
    'SKM': '-2092889',   # Gangtok
    'NEM': '-2112445',   # Kohima
}


def _region_to_city_id(region_id: str) -> str:
    """
    Maps a Region UUID to a Booking.com city ID.
    First checks admin-configured custom_coefficients, then default map.
    """
    try:
        config    = get_engine_config()
        custom    = config.get('custom_coefficients', {})
        city_map  = custom.get('bookingcom_city_ids', {})
        # Also try by region code
        from engine_b2c.models import Region
        region = Region.objects.get(id=region_id)
        code   = region.region_code
        return city_map.get(code) or city_map.get(str(region_id)) or _DEFAULT_CITY_IDS.get(code, '')
    except Exception as e:
        logger.debug(f'city_id lookup failed: {e}')
        return ''


# ── Normalisers ───────────────────────────────────────────────────────────────

def _normalise_hotel(raw: dict) -> dict:
    """Converts Booking.com hotel result to Blueberry standard shape."""
    return {
        'source':          'bookingcom',
        'powered_by':      'Booking.com',
        'hotel_id':        str(raw.get('hotel_id', '')),
        'name':            raw.get('hotel_name', ''),
        'address':         raw.get('address', ''),
        'city':            raw.get('city', ''),
        'country':         raw.get('country_code', ''),
        'lat':             raw.get('location', {}).get('latitude'),
        'lng':             raw.get('location', {}).get('longitude'),
        'star_rating':     raw.get('class', 0),
        'review_score':    raw.get('review_score', 0),
        'review_count':    raw.get('review_nr', 0),
        'price_from':      raw.get('min_total_price', 0),
        'currency':        raw.get('currency_code', 'INR'),
        'photo_url':       (raw.get('photos') or [{}])[0].get('url_original', ''),
        'booking_url':     raw.get('url', ''),
        'instant_confirm': raw.get('is_genius_deal', False),
        'facilities':      raw.get('hotel_facilities', []),
    }


def _normalise_room(raw: dict) -> dict:
    """Converts Booking.com room result to Blueberry standard shape."""
    return {
        'source':          'bookingcom',
        'room_id':         str(raw.get('room_id', '')),
        'name':            raw.get('room_name', ''),
        'max_persons':     raw.get('nr_adults', 2),
        'bed_config':      raw.get('bed_configurations', ''),
        'price_per_night': raw.get('price', {}).get('gross_price', 0),
        'currency':        raw.get('price', {}).get('currency', 'INR'),
        'meal_plan':       raw.get('mealplan', ''),
        'cancellation':    raw.get('policies', {}).get('cancellation', ''),
        'instant_confirm': raw.get('is_last_minute_deal', False),
    }


# ── Exceptions ────────────────────────────────────────────────────────────────

class BookingComDisabledError(Exception):
    """Raised when Booking.com is disabled via admin toggle."""
    pass


class BookingComConfigError(Exception):
    """Raised when credentials are missing."""
    pass


class BookingComAPIError(Exception):
    """Raised on API errors."""
    pass