from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.core.exceptions import PermissionDenied

from .forms import PaymentCreateForm
from .models import (
    PaymentRequest,
    PaymentApproval,
    PaymentStatus,
    UserRole,
    AuditLog,
)
from .policies import evaluate_policies
from .workflow import can_user_approve, apply_approval_and_maybe_finalize


def get_role(user):
    return getattr(user.profile, "role", UserRole.INITIATOR)


@login_required
def home(request):
    role = get_role(request.user)
    return render(request, "payments/home.html", {"role": role})


@login_required
def payment_create(request):
    role = get_role(request.user)
    if role not in [UserRole.INITIATOR, UserRole.ADMIN]:
        raise PermissionDenied("Only initiators or admins can create payments.")

    if request.method == "POST":
        form = PaymentCreateForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.created_by = request.user
            payment.status = PaymentStatus.PENDING

            payment.save()
            evaluate_policies(payment)
            payment.save(update_fields=["required_approvals", "required_admin_approval", "is_high_risk"])

            AuditLog.objects.create(
                payment=payment,
                user=request.user,
                action="PAYMENT_CREATED",
                details=f"High risk: {payment.is_high_risk}, Required approvals: {payment.required_approvals}, "
                        f"Admin required: {payment.required_admin_approval}",
            )

            messages.success(request, f"Payment request {payment.id} created.")
            return redirect("payments:my_payments")
    else:
        form = PaymentCreateForm()

    return render(request, "payments/payment_create.html", {"form": form})


@login_required
def my_payments(request):
    payments = PaymentRequest.objects.filter(created_by=request.user).order_by("-created_at")
    return render(request, "payments/my_payments.html", {"payments": payments})


@login_required
def pending_payments(request):
    # Approver/admin view
    role = get_role(request.user)
    if role not in [UserRole.APPROVER, UserRole.ADMIN]:
        raise PermissionDenied("Only approvers or admins can view pending payments.")

    payments = PaymentRequest.objects.filter(status=PaymentStatus.PENDING).exclude(
        created_by=request.user
    ).order_by("-created_at")

    return render(request, "payments/pending_payments.html", {"payments": payments, "role": role})


@login_required
def payment_detail(request, pk):
    payment = get_object_or_404(PaymentRequest, pk=pk)
    logs = payment.logs.all()
    approvals = payment.approvals.select_related("approver")
    return render(request, "payments/payment_detail.html", {
        "payment": payment,
        "logs": logs,
        "approvals": approvals,
    })


@login_required
@transaction.atomic
def payment_approve(request, pk):
    payment = get_object_or_404(PaymentRequest, pk=pk)
    if payment.status != PaymentStatus.PENDING:
        messages.error(request, "Payment is not pending.")
        return redirect("payments:payment_detail", pk=pk)

    if not can_user_approve(request.user, payment):
        raise PermissionDenied("You cannot approve this payment.")

    role = get_role(request.user)
    is_admin = role == UserRole.ADMIN

    approval, created = PaymentApproval.objects.get_or_create(
        payment=payment,
        approver=request.user,
        defaults={"is_admin": is_admin},
    )
    if not created:
        messages.info(request, "You have already approved this payment.")
    else:
        AuditLog.objects.create(
            payment=payment,
            user=request.user,
            action="PAYMENT_APPROVED",
            details=f"Admin: {is_admin}",
        )
        apply_approval_and_maybe_finalize(request.user, payment)

    return redirect("payments:payment_detail", pk=pk)


@login_required
@transaction.atomic
def payment_reject(request, pk):
    payment = get_object_or_404(PaymentRequest, pk=pk)
    if payment.status != PaymentStatus.PENDING:
        messages.error(request, "Payment is not pending.")
        return redirect("payments:payment_detail", pk=pk)

    role = get_role(request.user)
    if role not in [UserRole.APPROVER, UserRole.ADMIN]:
        raise PermissionDenied("You cannot reject this payment.")

    if payment.created_by == request.user:
        messages.error(request, "You cannot reject your own payment.")
        return redirect("payments:payment_detail", pk=pk)

    payment.status = PaymentStatus.REJECTED
    payment.save(update_fields=["status"])
    AuditLog.objects.create(
        payment=payment,
        user=request.user,
        action="PAYMENT_REJECTED",
        details="Rejected by approver.",
    )
    return redirect("payments:payment_detail", pk=pk)


@login_required
def payment_execute(request, pk):
    payment = get_object_or_404(PaymentRequest, pk=pk)
    role = get_role(request.user)
    if role != UserRole.ADMIN:
        raise PermissionDenied("Only admin can execute payments.")

    if payment.status != PaymentStatus.APPROVED:
        messages.error(request, "Payment must be approved before execution.")
        return redirect("payments:payment_detail", pk=pk)

    payment.status = PaymentStatus.EXECUTED
    payment.save(update_fields=["status"])

    AuditLog.objects.create(
        payment=payment,
        user=request.user,
        action="PAYMENT_EXECUTED",
        details="Simulated execution.",
    )
    messages.success(request, "Payment executed (simulated).")
    return redirect("payments:payment_detail", pk=pk)
