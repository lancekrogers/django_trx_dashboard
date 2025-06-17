#!/usr/bin/env python
"""Quick database check"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from wallets.models import Wallet
from portfolio.models import InvestigationCase
from transactions.models import Transaction

User = get_user_model()

print("=== Database Status ===")
print(f"Users: {User.objects.count()}")
print(f"Wallets: {Wallet.objects.count()}")
print(f"Cases: {InvestigationCase.objects.count()}")
print(f"Transactions: {Transaction.objects.count()}")

print("\n=== Users ===")
for user in User.objects.all()[:5]:
    print(f"- {user.email} (superuser: {user.is_superuser})")

print("\n=== Admin Check ===")
admin = User.objects.filter(email='admin@example.com').first()
if admin:
    print(f"Admin exists: {admin.email}")
    print(f"Can login: {admin.check_password('admin123')}")
else:
    print("Admin user NOT FOUND")

print("\n=== Investigation Cases ===")
for case in InvestigationCase.objects.all()[:5]:
    print(f"- {case.name} (Status: {case.status})")
    print(f"  Wallets: {case.wallets.count()}")
    print(f"  Risk Score: {case.risk_score}")