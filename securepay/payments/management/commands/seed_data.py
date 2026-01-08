from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from payments.models import UserProfile, PaymentRequest, AuditLog
from decimal import Decimal

class Command(BaseCommand):
    help = 'Seeds database with initial users and data'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Define the strict user list
        users = [
            {'username': 'sandeep', 'password': 'password123', 'role': UserProfile.Role.INITIATOR, 'email': 'sandeep@securepay.com'},
            {'username': 'approver', 'password': 'password123', 'role': UserProfile.Role.APPROVER, 'email': 'approver@securepay.com'},
            {'username': 'admin', 'password': 'password123', 'role': UserProfile.Role.ADMIN, 'email': 'admin@securepay.com'},
        ]

        # Clean up old/confusing users
        User.objects.filter(username__in=['initiator', 'approver1', 'approver2']).delete()

        for u in users:
            # Delete to ensure fresh password
            User.objects.filter(username=u['username']).delete()
            
            user = User.objects.create_user(
                username=u['username'],
                password=u['password'],
                email=u['email'],
                role=u['role']
            )
            self.stdout.write(self.style.SUCCESS(f'Created/Reset user: {u["username"]} ({u["role"]})'))

        # Create a sample payment
        initiator = User.objects.get(username='sandeep')
        if not PaymentRequest.objects.exists():
            PaymentRequest.objects.create(
                initiator=initiator,
                amount=Decimal('5000.00'),
                beneficiary_name='TechCorp Inc.',
                description='Server costs',
                status=PaymentRequest.Status.PENDING
            )
            self.stdout.write(self.style.SUCCESS('Created sample payment'))

        self.stdout.write(self.style.SUCCESS('Seeding complete'))
