from django import forms
from .models import PaymentRequest


class PaymentCreateForm(forms.ModelForm):
    class Meta:
        model = PaymentRequest
        fields = ["beneficiary_name", "beneficiary_ref", "amount", "currency", "purpose"]
