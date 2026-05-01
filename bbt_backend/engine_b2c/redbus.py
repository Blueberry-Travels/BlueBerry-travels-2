"""
RedBus API client.
AbhiBus uses identical flow with different base_url and credentials —
see abhibus.py which wraps this client.

RedBus flow:
  1. search_buses()     → list of available buses for route + date
  2. get_seat_map()     → seat layout for a specific trip
  3. block_seats()      → temporary hold (must complete within timeout)
  4. book_seats()       → confirmed booking, returns PNR
  5. get_booking()      → booking status and ticket details
  6. cancel_booking()   → cancellation + refund initiation

NueGo and Laxmi Travels appear as operators in RedBus inventory automatically.
No separate integration needed.
"""

import json
import logging
import urllib.request
import urllib.parse

logger = logging.getLogger(__name__)


class RedBusClient:

    def __init__(self, provider_key: str = 'redbus'):
        from engine_meta.models import ThirdPartyAPIConfig
        config = ThirdPartyAPIConfig.get(provider_key)
        if not config or not config.is_active:
            raise RedBusDisabledError(
                f'{provider_key} is not enabled. '
                f'Configure credentials in the Admin → Third-Party APIs panel.')
        self.api_key   = config.get_credential('api_key')
        self.source_id = config.get_credential('source_id')
        self.base_url  = config.get_credential(
            'base_url', 'https://api.redbus.in').rstrip('/')
        self.provider  = provider_key

    def _get(self, endpoint: str, params: dict) -> dict:
        params['apiKey']   = self.api_key
        params['sourceId'] = self.source_id
        qs  = urllib.parse.urlencode(params)
        url = f'{self.base_url}/{endpoint}?{qs}'
        req = urllib.request.Request(url, headers={
            'Accept':     'application/json',
            'User-Agent': 'Blueberry/1.0',
        })
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            _check_redbus_error(data)
            return data
        except RedBusAPIError:
            raise
        except Exception as e:
            logger.error(f'{self.provider} GET {endpoint} failed: {e}')
            raise RedBusAPIError(f'{self.provider} request failed: {e}')

    def _post(self, endpoint: str, payload: dict) -> dict:
        payload['apiKey']   = self.api_key
        payload['sourceId'] = self.source_id
        url  = f'{self.base_url}/{endpoint}'
        body = json.dumps(payload).encode()
        req  = urllib.request.Request(url, data=body, headers={
            'Content-Type': 'application/json',
            'Accept':       'application/json',
            'User-Agent':   'Blueberry/1.0',
        }, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
            _check_redbus_error(data)
            return data
        except RedBusAPIError:
            raise
        except Exception as e:
            logger.error(f'{self.provider} POST {endpoint} failed: {e}')
            raise RedBusAPIError(f'{self.provider} request failed: {e}')

    def search_buses(
        self,
        origin_id:   str,
        dest_id:     str,
        travel_date: str,   # 'DD-MMM-YYYY' e.g. '15-Dec-2025'
    ) -> list:
        """
        Returns list of available buses for origin → destination on date.
        Each bus has: trip_id, operator, departure, arrival, seats_available,
                      fare, bus_type, boarding_points, dropping_points
        """
        raw = self._get('search', {
            'srcId':     origin_id,
            'destId':    dest_id,
            'doj':       travel_date,
        })
        buses = raw.get('result', {}).get('seatsAvailability', [])
        return [_normalise_bus(b) for b in buses]

    def get_seat_map(self, trip_id: str, src_id: str, dst_id: str) -> dict:
        """Returns seat layout for a specific trip."""
        raw = self._get('seatmap', {
            'tripId': trip_id,
            'srcId':  src_id,
            'dstId':  dst_id,
        })
        return raw.get('result', {})

    def block_seats(
        self,
        trip_id:          str,
        seat_names:       list,
        boarding_point_id:str,
        dropping_point_id:str,
        src_id:           str,
        dst_id:           str,
        passenger_details:list,  # [{name, age, gender, id_type, id_number}]
    ) -> dict:
        """
        Temporary seat hold. Must be followed by book_seats() within timeout.
        Returns block_key needed for booking.
        """
        raw = self._post('block', {
            'tripId':            trip_id,
            'seatNames':         seat_names,
            'boardingPointId':   boarding_point_id,
            'droppingPointId':   dropping_point_id,
            'srcId':             src_id,
            'dstId':             dst_id,
            'passengerDetails':  passenger_details,
        })
        return raw.get('result', {})

    def book_seats(
        self,
        block_key:   str,
        payment_mode:str = 'online',
    ) -> dict:
        """
        Confirms booking after successful payment.
        Returns PNR, ticket URL, passenger list.
        """
        raw = self._post('book', {
            'blockKey':    block_key,
            'paymentMode': payment_mode,
        })
        result = raw.get('result', {})
        return {
            'pnr':         result.get('tin'),
            'ticket_url':  result.get('ticketUrl', ''),
            'operator':    result.get('travels', ''),
            'departure':   result.get('doj', ''),
            'status':      'confirmed',
            'raw':         result,
        }

    def get_booking(self, tin: str) -> dict:
        """Fetch booking status by TIN (PNR)."""
        raw = self._get('getbooking', {'tin': tin})
        return raw.get('result', {})

    def cancel_booking(self, tin: str, seat_names: list) -> dict:
        """
        Cancel seats on a booking.
        Returns refund amount.
        """
        raw = self._post('cancel', {
            'tin':       tin,
            'seatNames': seat_names,
        })
        return raw.get('result', {})


def _check_redbus_error(data: dict):
    if data.get('status') and str(data['status']) not in ('success', '200', '0'):
        raise RedBusAPIError(
            f"RedBus API error: {data.get('message', data.get('status', 'unknown'))}")


def _normalise_bus(raw: dict) -> dict:
    return {
        'source':           'redbus',
        'trip_id':          str(raw.get('id', '')),
        'operator':         raw.get('travels', ''),
        'bus_type':         raw.get('busType', ''),
        'departure':        raw.get('departureTime', ''),
        'arrival':          raw.get('arrivalTime', ''),
        'duration_mins':    raw.get('duration', 0),
        'seats_available':  raw.get('availableSeats', 0),
        'fare':             raw.get('fare', {}).get('publishedFare', 0),
        'currency':         'INR',
        'boarding_points':  raw.get('boardingTimes', []),
        'dropping_points':  raw.get('droppingTimes', []),
        'cancellation_policy': raw.get('cancellationPolicy', ''),
        'rating':           raw.get('rating', 0),
    }


class RedBusDisabledError(Exception):
    pass


class RedBusAPIError(Exception):
    pass