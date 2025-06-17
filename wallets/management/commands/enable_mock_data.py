from django.core.management.base import BaseCommand
from wallets.models import User, UserSettings


class Command(BaseCommand):
    help = 'Enable mock data for a user'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='User email')

    def handle(self, *args, **options):
        email = options['email']
        
        try:
            user = User.objects.get(email=email)
            settings, created = UserSettings.objects.get_or_create(
                user=user,
                defaults={'mock_data_enabled': True}
            )
            
            if not created:
                settings.mock_data_enabled = True
                settings.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully enabled mock data for {email}')
            )
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with email {email} not found')
            )