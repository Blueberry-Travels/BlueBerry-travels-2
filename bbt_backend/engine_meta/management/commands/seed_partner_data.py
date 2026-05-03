import uuid
from django.core.management.base import BaseCommand
from engine_meta.models import User
from engine_b2b.models import PartnerProfile, PartnerVehicle, PartnerEarning
from engine_b2c.models import Booking, BookingLineItem, Region
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Seed a sample partner with vehicles and bookings.'

    def handle(self, *args, **options):
        self.stdout.write('Seeding partner data...')

        # 1. Create Partner User
        email = 'partner@example.com'
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'name': 'Himachal Travels',
                'roles': ['partner'],
                'is_active': True
            }
        )
        if created:
            user.set_password('Partner@123')
            user.save()

        # 2. Create Partner Profile
        partner, _ = PartnerProfile.objects.get_or_create(
            user=user,
            defaults={
                'business_name': 'Himachal Travels & Co',
                'commission_rate': 0.15,
                'status': 'active'
            }
        )

        # 3. Create Vehicles
        PartnerVehicle.objects.get_or_create(
            partner=partner,
            registration_no='HP-01-A-1234',
            defaults={
                'vehicle_type': 'suv',
                'make': 'Toyota',
                'model': 'Innova Crysta',
                'capacity_persons': 7,
                'status': 'available'
            }
        )
        
        PartnerVehicle.objects.get_or_create(
            partner=partner,
            registration_no='HP-01-B-5678',
            defaults={
                'vehicle_type': 'tempo_traveller',
                'make': 'Force',
                'model': 'Traveller',
                'capacity_persons': 12,
                'status': 'available'
            }
        )

        # 4. Create Sample Bookings (Line Items)
        customer_user = User.objects.filter(roles__contains=['customer']).first()
        if not customer_user:
            customer_user = User.objects.create(
                email='guest@example.com', 
                name='Guest User', 
                roles=['customer']
            )

        region = Region.objects.first()
        if not region:
            region = Region.objects.create(name='Himachal', state='HP', zone='uttar')

        booking = Booking.objects.create(
            user_id=str(customer_user.id),
            user_email=customer_user.email,
            user_name=customer_user.name,
            region=region,
            total_amount=5000,
            trip_start_date=timezone.now().date(),
            trip_end_date=timezone.now().date() + timedelta(days=5),
            status='confirmed'
        )

        BookingLineItem.objects.create(
            booking=booking,
            partner_id=str(partner.id),
            activity_name='Manali to Leh Transfer',
            scheduled_date=timezone.now().date(),
            quantity=4,
            subtotal=4500,
            status='pending'
        )

        # 5. Create some Earnings
        PartnerEarning.objects.create(
            partner=partner,
            booking_item_id=str(uuid.uuid4()),
            amount_gross=10000,
            amount_net=8500,
            status='verified'
        )

        self.stdout.write(self.style.SUCCESS('Successfully seeded partner data.'))
        self.stdout.write(f'Login: {email} / Partner@123')
