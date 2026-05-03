import uuid
from django.core.management.base import BaseCommand
from engine_b2c.models import Region, Activity, Package, MiscService

class Command(BaseCommand):
    help = 'Seed sample regions, activities, and packages for the frontend.'

    def handle(self, *args, **options):
        self.stdout.write('Seeding sample data...')

        # 1. Regions
        spiti, _ = Region.objects.get_or_create(
            name='Spiti Valley',
            defaults={
                'state': 'Himachal Pradesh',
                'zone': 'uttar',
                'description': 'A high-altitude cold desert with stunning landscapes and monasteries.',
                'image_url': 'https://images.unsplash.com/photo-1581793745862-99fde7f43f2a',
                'region_code': 'SPI'
            }
        )

        ladakh, _ = Region.objects.get_or_create(
            name='Ladakh',
            defaults={
                'state': 'Ladakh',
                'zone': 'uttar',
                'description': 'Land of high passes, crystal clear lakes, and ancient culture.',
                'image_url': 'https://images.unsplash.com/photo-1596395817113-761379d7482c',
                'region_code': 'LDK'
            }
        )

        # 2. Activities
        Activity.objects.get_or_create(
            name='Key Monastery Visit',
            region=spiti,
            defaults={
                'category': 'cultural',
                'short_desc': 'Visit the largest monastery in Spiti Valley.',
                'tone': 'yin',
                'effort_score': 0.2,
                'duration_hrs': 2,
                'reward_score': 0.9,
                'price_from': 500,
                'content_approved': True
            }
        )

        Activity.objects.get_or_create(
            name='Chandratal Lake Trek',
            region=spiti,
            defaults={
                'category': 'trekking',
                'short_desc': 'Trek to the magical Moon Lake.',
                'tone': 'yang',
                'effort_score': 0.8,
                'duration_hrs': 6,
                'reward_score': 0.95,
                'price_from': 2500,
                'content_approved': True
            }
        )

        # 3. Packages
        Package.objects.get_or_create(
            name='Spiti Winter Expedition',
            defaults={
                'short_desc': 'A 7-day journey into the heart of the Himalayas in winter.',
                'category': 'adventure_sports',
                'days_count': 7,
                'per_person_estimate': 35000,
                'description': 'Experience the raw beauty of Spiti in snow.',
                'is_active': True
            }
        )

        Package.objects.get_or_create(
            name='Ladakh Cultural Tour',
            defaults={
                'short_desc': 'Explore monasteries and villages of Ladakh.',
                'category': 'cultural',
                'days_count': 5,
                'per_person_estimate': 25000,
                'description': 'A deep dive into Tibetan-Buddhist culture.',
                'is_active': True
            }
        )

        # 4. Misc Services
        MiscService.objects.get_or_create(
            name='Photography Kit',
            defaults={
                'description': 'Rent a professional camera kit for your trip.',
                'category': 'hobbyist',
                'price': 1500,
                'is_active': True
            }
        )

        self.stdout.write(self.style.SUCCESS('Successfully seeded sample data.'))
