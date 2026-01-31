"""
Management command to create the initial Super Admin user.
"""
from django.core.management.base import BaseCommand
from accounts.models import User


class Command(BaseCommand):
    help = 'Creates the initial Super Admin user for AIMS EXAM'
    
    def handle(self, *args, **options):
        email = 'ariet5656@gmail.com'
        password = 'Admin_Ariet_5652'
        
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f'Super Admin {email} already exists.'))
            return
        
        user = User.objects.create_superuser(
            email=email,
            password=password,
            first_name='Ariet',
            last_name='Admin',
            role='super_admin',
        )
        
        self.stdout.write(self.style.SUCCESS(f'Super Admin created successfully!'))
        self.stdout.write(f'Email: {email}')
        self.stdout.write(f'Password: {password}')
