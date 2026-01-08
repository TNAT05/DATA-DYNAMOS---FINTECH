from decimal import Decimal
from .models import PaymentRequest

HIGH_VALUE_THRESHOLD = Decimal('50000.00')

def is_high_value(payment: PaymentRequest) -> bool:
    return payment.amount > HIGH_VALUE_THRESHOLD

def is_new_beneficiary(payment: PaymentRequest) -> bool:
    # Check if we have any previously EXECUTED payments to this beneficiary
    # Note: We only trust EXECUTED payments as 'known' beneficiaries
    previous_payments = PaymentRequest.objects.filter(
        beneficiary_name__iexact=payment.beneficiary_name,
        status=PaymentRequest.Status.EXECUTED
    ).exclude(id=payment.id).exists()
    return not previous_payments

def get_required_approvals(payment: PaymentRequest) -> int:
    required = 1
    if is_high_value(payment):
        required += 1 # Needs 2 approvals
    return required

def requires_admin_approval(payment: PaymentRequest) -> bool:
    # New beneficiaries always require admin set of eyes
    return is_new_beneficiary(payment)