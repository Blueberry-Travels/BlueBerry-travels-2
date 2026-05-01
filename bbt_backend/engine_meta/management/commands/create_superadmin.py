from django.core.management.base import BaseCommand
from django.db import transaction
from engine_meta.models import User


class Command(BaseCommand):
    help = 'Creates the Blueberry super-admin account'

    def add_arguments(self, parser):
        parser.add_argument('--email',    required=True)
        parser.add_argument('--name',     required=True)
        parser.add_argument('--mobile',   required=True)
        parser.add_argument('--password', required=True)

    def handle(self, *args, **options):
        if User.objects.filter(email=options['email']).exists():
            self.stdout.write(self.style.ERROR('User already exists.'))
            return
        try:
            with transaction.atomic():
                user = User.objects.create_superuser(
                    email=options['email'], password=options['password'],
                    name=options['name'], mobile=options['mobile'],
                    roles=['super_admin'],
                )
                user.is_staff = True
                user.is_superuser = True
                user.save(update_fields=['is_staff', 'is_superuser', 'roles'])
                self.stdout.write(self.style.SUCCESS(
                    f'\n✓ Super-admin created: {options["email"]}'
                ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed: {e}'))