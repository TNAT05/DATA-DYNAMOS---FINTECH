from django.core.exceptions import ValidationError
from django.db import transaction
from .models import PaymentRequest, PaymentApproval, AuditLog, UserProfile
from .policies import get_required_approvals, requires_admin_approval

class WorkflowError(ValidationError):
    pass

class PaymentWorkflow:
    def __init__(self, payment: PaymentRequest, user: UserProfile):
        self.payment = payment
        self.user = user

    def _log(self, action, payload=None):
        AuditLog.objects.create(
            action=action,
            user=self.user,
            payment=self.payment,
            payload=payload or {}
        )

    def approve(self):
        # Invariant 1: Maker-Checker (Initiator cannot approve)
        if self.payment.initiator == self.user:
            raise WorkflowError("Initiator cannot approve their own request.")

        # Invariant 2: User cannot approve twice
        if self.payment.approvals.filter(approver=self.user).exists():
            raise WorkflowError("You have already approved this request.")

        # State check
        if self.payment.status != PaymentRequest.Status.PENDING:
            raise WorkflowError("Payment is not in PENDING state.")

        # Role check
        if not (self.user.is_approver() or self.user.is_admin()):
            raise WorkflowError("Unauthorized to approve.")

        with transaction.atomic():
            # Create Approval
            PaymentApproval.objects.create(
                payment=self.payment,
                approver=self.user,
                status=PaymentApproval.Status.APPROVED
            )
            self._log("APPROVED")

            # Check if ready for next state
            self._check_transition()

    def reject(self):
        # Simplified: Any approver/admin can reject
        if not (self.user.is_approver() or self.user.is_admin()):
            raise WorkflowError("Unauthorized to reject.")
        
        with transaction.atomic():
            self.payment.status = PaymentRequest.Status.REJECTED
            self.payment.save()
            
            PaymentApproval.objects.create(
                payment=self.payment,
                approver=self.user,
                status=PaymentApproval.Status.REJECTED
            )
            self._log("REJECTED")

    def execute(self):
         # Role check
        if not self.user.is_admin():
            raise WorkflowError("Only Admins can execute payments.")

        # State check
        if self.payment.status != PaymentRequest.Status.APPROVED:
            raise WorkflowError("Payment must be APPROVED before execution.")

        with transaction.atomic():
            self.payment.status = PaymentRequest.Status.EXECUTED
            self.payment.save()
            self._log("EXECUTED")

    def _check_transition(self):
        approvals = self.payment.approvals.filter(status=PaymentApproval.Status.APPROVED)
        approval_count = approvals.count()
        
        required_count = get_required_approvals(self.payment)
        needs_admin = requires_admin_approval(self.payment)
        
        # Check if Admin has approved (if required)
        has_admin_approval = approvals.filter(approver__role=UserProfile.Role.ADMIN).exists()

        if approval_count >= required_count:
            if needs_admin and not has_admin_approval:
                # Still waiting for admin
                return
            
            # Transition to APPROVED (Ready for Execution)
            self.payment.status = PaymentRequest.Status.APPROVED
            self.payment.save()
            self._log("TRANSITION_TO_APPROVED", {
                "approvals": approval_count,
                "required": required_count,
                "needs_admin": needs_admin
            })
