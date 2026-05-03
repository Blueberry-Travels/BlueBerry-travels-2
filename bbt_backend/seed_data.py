import os
import django
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blueberry_backend.settings')
django.setup()

from engine_b2c.models import Region, Activity

def seed():
    print("Seeding data...")
    
    # 1. Create Regions
    regions_to_create = [
        {'name': 'Uttar',    'state': 'Himachal Pradesh', 'zone': 'uttar'},
        {'name': 'Pashchim', 'state': 'Maharashtra',     'zone': 'pashchim'},
        {'name': 'Madhyam',  'state': 'Madhya Pradesh',  'zone': 'madhyam'},
        {'name': 'Poorabh',  'state': 'Sikkim',          'zone': 'poorab'},
        {'name': 'Dakshin',  'state': 'Kerala',          'zone': 'dakshin'},
    ]
    
    region_map = {}
    for r_data in regions_to_create:
        region, created = Region.objects.get_or_create(
            name=r_data['name'],
            defaults={'state': r_data['state'], 'zone': r_data['zone'], 'is_active': True}
        )
        region_map[r_data['name']] = region
        print(f"Region: {region.name} ({'Created' if created else 'Exists'})")

    # 2. Create Activities
    activities_to_create = [
        {
            'region': region_map['Uttar'],
            'name': 'Hampta Pass Trek',
            'short_desc': 'A stunning trek from Manali to Spiti Valley.',
            'category': 'trekking',
            'price_from': 8500,
            'tone': 'yang'
        },
        {
            'region': region_map['Uttar'],
            'name': 'Yoga in Rishikesh',
            'short_desc': 'Soulful meditation and yoga by the Ganges.',
            'category': 'meditation',
            'price_from': 3200,
            'tone': 'yin'
        },
        {
            'region': region_map['Dakshin'],
            'name': 'Munnar Tea Garden Walk',
            'short_desc': 'A peaceful walk through lush tea estates.',
            'category': 'chill',
            'price_from': 1200,
            'tone': 'yin'
        }
    ]

    for a_data in activities_to_create:
        act, created = Activity.objects.get_or_create(
            name=a_data['name'],
            region=a_data['region'],
            defaults={
                'short_desc': a_data['short_desc'],
                'category': a_data['category'],
                'price_from': a_data['price_from'],
                'tone': a_data['tone'],
                'is_active': True,
                'content_approved': True
            }
        )
        print(f"Activity: {act.name} ({'Created' if created else 'Exists'})")

if __name__ == '__main__':
    seed()
