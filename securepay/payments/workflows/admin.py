from django.contrib import admin
from .models import UserProfile, PaymentRequest, PaymentApproval, AuditLog


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role")


@admin.register(PaymentRequest)
class PaymentRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "beneficiary_name", "amount", "currency", "status", "is_high_risk")
    list_filter = ("status", "is_high_risk")
    search_fields = ("beneficiary_name", "beneficiary_ref")


@admin.register(PaymentApproval)
class PaymentApprovalAdmin(admin.ModelAdmin):
    list_display = ("payment", "approver", "is_admin", "created_at")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("payment", "user", "action", "created_at")
    list_filter = ("action",)
