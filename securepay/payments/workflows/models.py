from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class UserRole(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    INITIATOR = "INITIATOR", "Initiator"
    APPROVER = "APPROVER", "Approver"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.INITIATOR)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "Pending Approval"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    EXECUTED = "EXECUTED", "Executed"


class PaymentRequest(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_payments")
    beneficiary_name = models.CharField(max_length=255)
    beneficiary_ref = models.CharField(max_length=255)  # e.g. account ID or UPI handle
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=10, default="INR")
    purpose = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)

    required_approvals = models.PositiveIntegerField(default=1)
    required_admin_approval = models.BooleanField(default=False)
    is_high_risk = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id} - {self.beneficiary_name} - {self.amount} {self.currency}"


class PaymentApproval(models.Model):
    payment = models.ForeignKey(PaymentRequest, on_delete=models.CASCADE, related_name="approvals")
    approver = models.ForeignKey(User, on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("payment", "approver")

    def __str__(self):
        return f"{self.payment.id} approved by {self.approver.username}"


class AuditLog(models.Model):
    payment = models.ForeignKey(PaymentRequest, on_delete=models.CASCADE, related_name="logs", null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} on {self.payment_id} by {self.user}"

