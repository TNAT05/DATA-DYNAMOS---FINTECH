from django.db.models import Q
from .models import PaymentRequest, PaymentApproval, UserRole, PaymentStatus, AuditLog


def can_user_approve(user, payment: PaymentRequest) -> bool:
    # cannot approve own payment (maker-checker)
    if payment.created_by_id == user.id:
        return False

    role = getattr(user.profile, "role", UserRole.INITIATOR)
    if role not in [UserRole.APPROVER, UserRole.ADMIN]:
        return False

    # if admin is required and user is not admin, still allow them to be a normal approver
    # admin requirement will be checked at finalization
    return True


def apply_approval_and_maybe_finalize(user, payment: PaymentRequest):
    approvals = payment.approvals.all()
    total_approvals = approvals.count()
    admin_approvals = approvals.filter(is_admin=True).count()

    enough_normal = total_approvals >= payment.required_approvals
    enough_admin = (not payment.required_admin_approval) or (admin_approvals >= 1)

    if enough_normal and enough_admin and payment.status == PaymentStatus.PENDING:
        payment.status = PaymentStatus.APPROVED
        payment.save(update_fields=["status"])
        AuditLog.objects.create(
            payment=payment,
            user=user,
            action="PAYMENT_FINAL_APPROVED",
            details=f"Approvals: {total_approvals}, Admin approvals: {admin_approvals}",
        )
