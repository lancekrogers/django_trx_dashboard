#!/usr/bin/env python
"""
Standalone script to load demo data
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.core.management import call_command

User = get_user_model()

def load_demo_data():
    print("=== Loading Demo Data ===")
    
    # Check current state
    user_count = User.objects.count()
    print(f"Current users: {user_count}")
    
    # Only generate data if database is empty (fresh deployment)
    if user_count == 0:
        print("Empty database detected. Generating fresh demo data...")
        
        try:
            # Generate all demo data
            print("1. Generating users and wallets...")
            call_command('generate_mock_data', '--superusers', '1', '--users', '5', '--transactions', '100')
            print("✓ Users and wallets created")
            
            print("2. Generating investigation cases...")
            call_command('generate_investigation_data')
            print("✓ Investigation cases created")
            
            print("3. Generating portfolio cases...")
            call_command('generate_portfolio_cases')
            print("✓ Portfolio cases created")
            
            print("Demo data generated successfully!")
        except Exception as e:
            print(f"Error generating demo data: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"Database already has {user_count} users. Skipping data generation.")
    
    # Ensure admin user exists
    if not User.objects.filter(email='admin@example.com').exists():
        print("Creating admin user...")
        User.objects.create_superuser(
            username='admin@example.com',
            email='admin@example.com',
            password='admin123'
        )
        print("Admin user created: admin@example.com / admin123")
    else:
        print("Admin user already exists")
    
    # Final status
    print(f"\nFinal user count: {User.objects.count()}")
    print("First 5 users:")
    for user in User.objects.all()[:5]:
        print(f"  - {user.email}")

if __name__ == '__main__':
    load_demo_data()