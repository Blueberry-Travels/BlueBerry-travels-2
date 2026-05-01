"""
IRCTC TSP (Tourism Service Provider) API client.

STATUS: Coming Soon.

IRCTC requires BBT to register as a TSP agent before API access is granted.
Until credentials are configured, all endpoints return a coming_soon response.

Registration:
  https://www.irctc.co.in/nget/train-search — B2B / TSP section.
  Once approved: paste agent_id and api_key in
  Admin → Third-Party APIs → IRCTC.

Mandatory at booking time (IRCTC requirement):
  Every passenger must provide one of: Aadhaar, PAN, Passport.

IRCTC flow (mirrors RedBus):
  1. search_trains()    → available trains for route + date
  2. get_availability() → class-wise seat availability
  3. block_seats()      → passenger details + temp hold
  4. book_seats()       → PNR issued (requires prior payment)
  5. get_pnr_status()   → live PNR status
  6. cancel_ticket()    → cancellation + TDR filing
"""

import json
import logging
import urllib.request
import urllib.parse

logger = logging.getLogger(__name__)

COMING_SOON_RESPONSE = {
    'available':     False,
    'coming_soon':   True,
    'message':       (
        'Train booking is coming soon. '
        'We are in the process of IRCTC TSP registration. '
        'Book directly at irctc.co.in for now.'
    ),
    'irctc_url':     'https://www.irctc.co.in/nget/train-search',
}


def is_irctc_available() -> bool:
    from engine_meta.models import ThirdPartyAPIConfig
    return ThirdPartyAPIConfig.is_enabled('irctc')


def get_coming_soon_response() -> dict:
    """Returns the coming soon payload for frontend display."""
    from engine_meta.models import ThirdPartyAPIConfig
    config = ThirdPartyAPIConfig.get('irctc')
    note   = ''
    if config and config.coming_soon_note:
        note = config.coming_soon_note
    return {**COMING_SOON_RESPONSE, 'admin_note': note}


class IRCTCClient:

    def __init__(self):
        from engine_meta.models import ThirdPartyAPIConfig
        config = ThirdPartyAPIConfig.get('irctc')
        if not config or not config.is_active:
            raise IRCTCNotAvailableError()
        if config.is_coming_soon:
            raise IRCTCComingSoonError()
        self.agent_id = config.get_credential('agent_id')
        self.api_key  = config.get_credential('api_key')
        self.base_url = config.get_credential('base_url', '').rstrip('/')
        if not all([self.agent_id, self.api_key, self.base_url]):
            raise IRCTCConfigError(
                'IRCTC credentials incomplete. '
                'Set agent_id, api_key, base_url in Admin → Third-Party APIs → IRCTC.')

    def _post(self, endpoint: str, payload: dict) -> dict:
        payload['agentId'] = self.agent_id
        payload['apiKey']  = self.api_key
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
            if not data.get('success', True):
                raise IRCTCAPIError(data.get('message', 'IRCTC API error'))
            return data
        except IRCTCAPIError:
            raise
        except Exception as e:
            logger.error(f'IRCTC POST {endpoint} failed: {e}')
            raise IRCTCAPIError(f'IRCTC request failed: {e}')

    def _get(self, endpoint: str, params: dict) -> dict:
        params['agentId'] = self.agent_id
        params['apiKey']  = self.api_key
        qs  = urllib.parse.urlencode(params)
        url = f'{self.base_url}/{endpoint}?{qs}'
        req = urllib.request.Request(url, headers={
            'Accept':     'application/json',
            'User-Agent': 'Blueberry/1.0',
        })
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read())
        except Exception as e:
            logger.error(f'IRCTC GET {endpoint} failed: {e}')
            raise IRCTCAPIError(f'IRCTC request failed: {e}')

    def search_trains(
        self,
        src_station: str,   # station code e.g. 'NDLS'
        dst_station: str,   # station code e.g. 'LKO'
        travel_date: str,   # 'YYYYMMDD'
        quota:       str = 'GN',  # GN=General, TQ=Tatkal, PT=Premium Tatkal
    ) -> list:
        raw = self._get('trains/search', {
            'fromStation': src_station,
            'toStation':   dst_station,
            'trainDate':   travel_date,
            'quota':       quota,
        })
        return [_normalise_train(t) for t in raw.get('trains', [])]

    def get_availability(
        self,
        train_number: str,
        src_station:  str,
        dst_station:  str,
        travel_date:  str,
        travel_class: str,  # '1A','2A','3A','SL','CC','EC'
        quota:        str = 'GN',
    ) -> dict:
        raw = self._get('availability', {
            'trainNumber':  train_number,
            'fromStation':  src_station,
            'toStation':    dst_station,
            'trainDate':    travel_date,
            'travelClass':  travel_class,
            'quota':        quota,
        })
        return {
            'train_number':     train_number,
            'travel_class':     travel_class,
            'availability':     raw.get('availability', 'NA'),
            'fare':             raw.get('fare', 0),
            'tatkal_fare':      raw.get('tatkalFare', 0),
            'quota':            quota,
        }

    def block_seats(
        self,
        train_number: str,
        src_station:  str,
        dst_station:  str,
        travel_date:  str,
        travel_class: str,
        quota:        str,
        passengers:   list,  # mandatory: [{name, age, gender, id_type, id_number}]
        boarding_station: str = '',
    ) -> dict:
        """
        Temporary hold. IRCTC requires full passenger ID at this step.
        id_type: 'AADHAAR' | 'PAN' | 'PASSPORT'
        """
        for p in passengers:
            if not p.get('id_number'):
                raise IRCTCPassengerIDError(
                    f'Passenger {p.get("name", "?")} must provide '
                    f'Aadhaar, PAN, or Passport number. IRCTC requirement.')
        raw = self._post('booking/block', {
            'trainNumber':    train_number,
            'fromStation':    src_station,
            'toStation':      dst_station,
            'trainDate':      travel_date,
            'travelClass':    travel_class,
            'quota':          quota,
            'passengers':     passengers,
            'boardingStation':boarding_station or src_station,
        })
        return raw.get('result', {})

    def book_seats(self, block_id: str, payment_ref: str) -> dict:
        """Confirms booking after Razorpay payment. Returns PNR."""
        raw = self._post('booking/confirm', {
            'blockId':    block_id,
            'paymentRef': payment_ref,
        })
        result = raw.get('result', {})
        return {
            'pnr':      result.get('pnr'),
            'status':   result.get('bookingStatus', 'confirmed'),
            'chart_prepared': result.get('chartPrepared', False),
            'raw':      result,
        }

    def get_pnr_status(self, pnr: str) -> dict:
        """Live PNR status from IRCTC."""
        raw = self._get('pnr/status', {'pnr': pnr})
        return raw.get('result', {})

    def cancel_ticket(self, pnr: str, passengers: list) -> dict:
        """
        Cancel ticket. passengers = list of passenger indices (0-based).
        Returns refund amount.
        """
        raw = self._post('booking/cancel', {
            'pnr':        pnr,
            'passengers': passengers,
        })
        return raw.get('result', {})


def _normalise_train(raw: dict) -> dict:
    return {
        'source':        'irctc',
        'train_number':  raw.get('trainNumber', ''),
        'train_name':    raw.get('trainName', ''),
        'departure':     raw.get('departureTime', ''),
        'arrival':       raw.get('arrivalTime', ''),
        'duration':      raw.get('duration', ''),
        'src_station':   raw.get('fromStation', ''),
        'dst_station':   raw.get('toStation', ''),
        'run_days':      raw.get('runningDays', []),
        'available_classes': raw.get('availableClasses', []),
        'distance_km':   raw.get('distance', 0),
    }


class IRCTCNotAvailableError(Exception):
    pass

class IRCTCComingSoonError(Exception):
    pass

class IRCTCConfigError(Exception):
    pass

class IRCTCPassengerIDError(Exception):
    pass

class IRCTCAPIError(Exception):
    pass