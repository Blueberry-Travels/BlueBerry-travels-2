"""
python manage.py seed_api_configs

Creates ThirdPartyAPIConfig records for all known external APIs.
Safe to run multiple times — uses get_or_create.
Admin then pastes credentials via Django admin panel.
"""
from django.core.management.base import BaseCommand


CONFIGS = [
    {
        'api_key':       'razorpay',
        'display_name':  'Razorpay',
        'is_coming_soon': False,
        'credentials':   {'key_id': '', 'key_secret': '', 'webhook_secret': ''},
        'docs_url':      'https://razorpay.com/docs/api/',
        'internal_notes':'Payment gateway. INR domestic + EUR international.',
    },
    {
        'api_key':       'redbus',
        'display_name':  'RedBus',
        'is_coming_soon': False,
        'credentials':   {'api_key': '', 'source_id': '', 'base_url': 'https://api.redbus.in'},
        'docs_url':      'https://api.redbus.in/docs',
        'internal_notes':'Bus ticketing. NueGo and Laxmi Travels appear as operators automatically.',
    },
    {
        'api_key':       'abhibus',
        'display_name':  'AbhiBus',
        'is_coming_soon': False,
        'credentials':   {'api_key': '', 'partner_id': '', 'base_url': 'https://api.abhibus.com'},
        'docs_url':      'https://www.abhibus.com/api-partner',
        'internal_notes':'Bus ticketing fallback alongside RedBus. Identical flow, different credentials.',
    },
    {
        'api_key':       'irctc',
        'display_name':  'IRCTC (Train Booking)',
        'is_coming_soon': True,
        'coming_soon_note': (
            'IRCTC TSP (Tourism Service Provider) agent registration required. '
            'Apply at https://www.irctc.co.in/nget/train-search — B2B / TSP section. '
            'Once approved, paste agent_id and api_key here and untick Coming Soon.'
        ),
        'credentials':   {'agent_id': '', 'api_key': '', 'base_url': ''},
        'docs_url':      'https://www.irctc.co.in/nget/train-search',
        'internal_notes':'Train booking. Requires mandatory passenger Aadhaar/PAN/Passport at booking.',
    },
    {
        'api_key':       'bookingcom',
        'display_name':  'Booking.com',
        'is_coming_soon': False,
        'credentials':   {'affiliate_id': '', 'api_key': ''},
        'docs_url':      'https://developers.booking.com/api/index.html',
        'internal_notes':'Hotel fallback when no platform hotels exist in region. Label all results "Powered by Booking.com".',
    },
    {
        'api_key':       'uidai',
        'display_name':  'UIDAI Aadhaar OTP',
        'is_coming_soon': False,
        'credentials':   {'client_id': '', 'client_secret': '', 'base_url': 'https://developer.uidai.gov.in'},
        'docs_url':      'https://developer.uidai.gov.in/',
        'internal_notes':'Aadhaar OTP KYC for Indian users. Currently using stub — replace with live credentials.',
    },
    {
        'api_key':       'mrz',
        'display_name':  'MRZ Passport Scanner',
        'is_coming_soon': False,
        'credentials':   {'provider': 'python-mrz-library', 'api_key': ''},
        'docs_url':      'https://pypi.org/project/mrz/',
        'internal_notes':'Passport MRZ parsing for foreign nationals. Uses python-mrz library locally — no external API needed unless switching to cloud OCR.',
    },
    {
        'api_key':       'whatsapp',
        'display_name':  'WhatsApp Business API',
        'is_coming_soon': True,
        'coming_soon_note': (
            'Requires Meta Business Manager approval and WhatsApp Business API access. '
            'Apply at https://business.facebook.com/ — once approved paste '
            'phone_number_id, access_token, app_secret, and verify_token.'
        ),
        'credentials':   {
            'phone_number_id': '',
            'access_token':    '',
            'app_secret':      '',
            'verify_token':    'blueberry_verify',
            'base_url':        'https://graph.facebook.com/v18.0',
        },
        'docs_url':      'https://developers.facebook.com/docs/whatsapp/cloud-api',
        'internal_notes':'Primary notification channel. Fallback: email.',
    },
    {
        'api_key':       'osrm',
        'display_name':  'OSRM Routing (self-hosted)',
        'is_active':     True,
        'is_coming_soon': False,
        'credentials':   {'base_url': 'http://router.project-osrm.org'},
        'docs_url':      'https://project-osrm.org/docs/v5.24.0/api/',
        'internal_notes':'Self-hosted routing. Set base_url to local OSRM instance when deployed. Falls back to Haversine on failure.',
    },
    {
        'api_key':       'bms',
        'display_name':  'BookMyShow (Events)',
        'is_coming_soon': True,
        'coming_soon_note': (
            'Apply at https://corporate.bookmyshow.com/affiliates — '
            'Partner/Affiliate program. Once approved, paste api_key and '
            'affiliate_id here and untick Coming Soon. '
            'Deep link redirect is live in the meantime.'
        ),
        'credentials':   {'api_key': '', 'affiliate_id': '', 'base_url': 'https://api.bookmyshow.com'},
        'docs_url':      'https://corporate.bookmyshow.com/affiliates',
        'internal_notes':'Event ticketing. Deep link redirect active until partner API approved.',
    },
]


class Command(BaseCommand):
    help = 'Seed ThirdPartyAPIConfig records for all known external APIs.'

    def handle(self, *args, **options):
        from engine_meta.models import ThirdPartyAPIConfig

        created_count = 0
        updated_count = 0

        for cfg in CONFIGS:
            obj, created = ThirdPartyAPIConfig.objects.get_or_create(
                api_key=cfg['api_key'],
                defaults={
                    'display_name':    cfg['display_name'],
                    'is_active':       cfg.get('is_active', False),
                    'is_coming_soon':  cfg.get('is_coming_soon', False),
                    'coming_soon_note':cfg.get('coming_soon_note', ''),
                    'credentials':     cfg.get('credentials', {}),
                    'docs_url':        cfg.get('docs_url', ''),
                    'internal_notes':  cfg.get('internal_notes', ''),
                    'status':          'coming_soon' if cfg.get('is_coming_soon') else 'unconfigured',
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f'  Created: {obj.display_name}')
            else:
                updated_count += 1
                self.stdout.write(f'  Exists:  {obj.display_name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone. Created {created_count}, already existed {updated_count}.'
            )
        )