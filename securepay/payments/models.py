from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class UserProfile(AbstractUser):
    class Role(models.TextChoices):
        INITIATOR = 'INITIATOR', _('Initiator')
        APPROVER = 'APPROVER', _('Approver')
        ADMIN = 'ADMIN', _('Admin')

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.INITIATOR,
    )

    def is_initiator(self):
        return self.role == self.Role.INITIATOR

    def is_approver(self):
        return self.role == self.Role.APPROVER

    def is_admin(self):
        return self.role == self.Role.ADMIN

class PaymentRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending Approval')
        APPROVED = 'APPROVED', _('Ready for Execution')
        REJECTED = 'REJECTED', _('Rejected')
        EXECUTED = 'EXECUTED', _('Executed')
    
    initiator = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='initiated_payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    beneficiary_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment #{self.id} - {self.amount} to {self.beneficiary_name}"

class PaymentApproval(models.Model):
    class Status(models.TextChoices):
        APPROVED = 'APPROVED', _('Approved')
        REJECTED = 'REJECTED', _('Rejected')

    payment = models.ForeignKey(PaymentRequest, on_delete=models.CASCADE, related_name='approvals')
    approver = models.ForeignKey(UserProfile, on_delete=models.PROTECT, related_name='approvals')
    status = models.CharField(max_length=20, choices=Status.choices)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('payment', 'approver')

class AuditLog(models.Model):
    action = models.CharField(max_length=255)
    user = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True)
    payment = models.ForeignKey(PaymentRequest, on_delete=models.CASCADE, null=True, blank=True)
    payload = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.timestamp} - {self.action} by {self.user}"
