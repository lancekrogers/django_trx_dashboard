#!/usr/bin/env python
"""Reset all users and create a fresh superuser"""

import os
import sys
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from wallets.models import User

# Delete all existing users
print("Deleting all existing users...")
User.objects.all().delete()
print("All users deleted!")

# Create new superuser
print("\nNow run one of these commands to create a new superuser:")
print("1. python manage.py createsuperuser")
print("2. python manage.py generate_mock_data --superusers 1 --users 2")
