"""
Razorpay client wrapper.
Credentials pulled from ThirdPartyAPIConfig — never hardcoded.
All amounts in paise (INR × 100) or lowest currency unit.
"""

import json
import hmac
import hashlib
import logging
import urllib.request
import urllib.parse
import base64

logger = logging.getLogger(__name__)

RAZORPAY_BASE = 'https://api.razorpay.com/v1'


class RazorpayClient:

    def __init__(self):
        from engine_meta.models import ThirdPartyAPIConfig
        config = ThirdPartyAPIConfig.get('razorpay')
        if not config or not config.is_active:
            raise RazorpayNotConfiguredError(
                'Razorpay not configured. '
                'Set key_id and key_secret in Admin → Third-Party APIs → Razorpay.')
        self.key_id     = config.get_credential('key_id')
        self.key_secret = config.get_credential('key_secret')
        self.webhook_secret = config.get_credential('webhook_secret', '')
        if not self.key_id or not self.key_secret:
            raise RazorpayNotConfiguredError(
                'Razorpay key_id or key_secret missing.')
        self._auth = base64.b64encode(
            f'{self.key_id}:{self.key_secret}'.encode()).decode()

    def _request(self, method: str, endpoint: str,
                 payload: dict = None) -> dict:
        url  = f'{RAZORPAY_BASE}/{endpoint}'
        body = json.dumps(payload).encode() if payload else None
        req  = urllib.request.Request(
            url, data=body,
            headers={
                'Authorization': f'Basic {self._auth}',
                'Content-Type':  'application/json',
                'Accept':        'application/json',
            },
            method=method,
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
            return data
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            logger.error(f'Razorpay {method} {endpoint} → HTTP {e.code}: {body}')
            raise RazorpayAPIError(f'Razorpay error {e.code}: {body}')
        except Exception as e:
            logger.error(f'Razorpay request failed: {e}')
            raise RazorpayAPIError(f'Razorpay request failed: {e}')

    # ── Orders ────────────────────────────────────────────────────────────

    def create_order(
        self,
        amount_paise:  int,
        currency:      str = 'INR',
        receipt:       str = '',
        notes:         dict = None,
    ) -> dict:
        """
        Creates a Razorpay order.
        amount_paise = total × 100 (e.g. ₹1500 → 150000)
        Returns order dict with id, amount, currency, status.
        """
        payload = {
            'amount':   amount_paise,
            'currency': currency,
            'receipt':  receipt or f'bbtrec_{amount_paise}',
            'notes':    notes or {},
            'payment_capture': 1,
        }
        order = self._request('POST', 'orders', payload)
        logger.info(f'Razorpay order created: {order.get("id")} '
                    f'amount={amount_paise} {currency}')
        return order

    def fetch_order(self, order_id: str) -> dict:
        return self._request('GET', f'orders/{order_id}')

    def fetch_order_payments(self, order_id: str) -> dict:
        return self._request('GET', f'orders/{order_id}/payments')

    # ── Payments ──────────────────────────────────────────────────────────

    def fetch_payment(self, payment_id: str) -> dict:
        return self._request('GET', f'payments/{payment_id}')

    def capture_payment(self, payment_id: str, amount_paise: int,
                        currency: str = 'INR') -> dict:
        return self._request('POST', f'payments/{payment_id}/capture', {
            'amount':   amount_paise,
            'currency': currency,
        })

    # ── Refunds ───────────────────────────────────────────────────────────

    def create_refund(self, payment_id: str, amount_paise: int,
                      notes: dict = None) -> dict:
        payload = {
            'amount': amount_paise,
            'notes':  notes or {},
        }
        refund = self._request('POST', f'payments/{payment_id}/refund', payload)
        logger.info(f'Refund created: {refund.get("id")} '
                    f'payment={payment_id} amount={amount_paise}')
        return refund

    def fetch_refund(self, payment_id: str, refund_id: str) -> dict:
        return self._request('GET', f'payments/{payment_id}/refunds/{refund_id}')

    # ── Signature verification ─────────────────────────────────────────────

    def verify_payment_signature(
        self,
        order_id:   str,
        payment_id: str,
        signature:  str,
    ) -> bool:
        """
        Verifies Razorpay payment signature.
        Must be called before marking a booking as paid.
        """
        message = f'{order_id}|{payment_id}'.encode()
        expected = hmac.new(
            self.key_secret.encode(),
            message,
            hashlib.sha256,
        ).hexdigest()
        result = hmac.compare_digest(expected, signature)
        if not result:
            logger.warning(
                f'Signature mismatch: order={order_id} payment={payment_id}')
        return result

    def verify_webhook_signature(
        self,
        payload_body: bytes,
        signature:    str,
    ) -> bool:
        """Verifies incoming webhook signature from Razorpay."""
        if not self.webhook_secret:
            logger.warning('webhook_secret not configured — skipping verification')
            return True
        expected = hmac.new(
            self.webhook_secret.encode(),
            payload_body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)


class RazorpayNotConfiguredError(Exception):
    pass

class RazorpayAPIError(Exception):
    pass