from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile, PaymentRequest, PaymentApproval, AuditLog

@admin.register(UserProfile)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('role',)}),
    )

@admin.register(PaymentRequest)
class PaymentRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'initiator', 'amount', 'beneficiary_name', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('beneficiary_name', 'initiator__username')

@admin.register(PaymentApproval)
class PaymentApprovalAdmin(admin.ModelAdmin):
    list_display = ('payment', 'approver', 'status', 'timestamp')

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'action', 'user', 'payment')
    readonly_fields = ('timestamp', 'action', 'user', 'payment', 'payload', 'ip_address')
