from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from wallets.models import Wallet
from portfolio.models import InvestigationCase
from transactions.models import Transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Check the current state of demo data'

    def handle(self, *args, **options):
        self.stdout.write("=== Data Status ===")
        self.stdout.write(f"Users: {User.objects.count()}")
        self.stdout.write(f"Superusers: {User.objects.filter(is_superuser=True).count()}")
        self.stdout.write(f"Wallets: {Wallet.objects.count()}")
        self.stdout.write(f"Investigation Cases: {InvestigationCase.objects.count()}")
        self.stdout.write(f"Transactions: {Transaction.objects.count()}")
        
        # Check for admin user
        admin_exists = User.objects.filter(email='admin@example.com').exists()
        self.stdout.write(f"\nAdmin user (admin@example.com): {'EXISTS' if admin_exists else 'NOT FOUND'}")
        
        # List first few users
        self.stdout.write("\nFirst 5 users:")
        for user in User.objects.all()[:5]:
            self.stdout.write(f"  - {user.email} (superuser: {user.is_superuser})")