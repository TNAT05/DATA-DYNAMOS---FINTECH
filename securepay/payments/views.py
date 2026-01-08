from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Sum
from .models import PaymentRequest, PaymentApproval, UserProfile
from .forms import PaymentRequestForm
from .workflow import PaymentWorkflow, WorkflowError
from .policies import get_required_approvals, requires_admin_approval

def is_initiator(user):
    return user.is_authenticated and user.role == UserProfile.Role.INITIATOR

def is_approver_or_admin(user):
    return user.is_authenticated and (user.role == UserProfile.Role.APPROVER or user.role == UserProfile.Role.ADMIN)

def home(request):
    if not request.user.is_authenticated:
        return render(request, 'payments/home.html')

    # Dashboard Stats Logic
    context = {}
    if request.user.role == UserProfile.Role.INITIATOR:
        payments = PaymentRequest.objects.filter(initiator=request.user)
        context['total_initiated'] = payments.count()
        context['total_value'] = payments.aggregate(Sum('amount'))['amount__sum'] or 0
        context['pending_count'] = payments.filter(status='PENDING').count()
        context['approved_count'] = payments.filter(status='APPROVED').count()
        
    elif request.user.role in [UserProfile.Role.APPROVER, UserProfile.Role.ADMIN]:
        # Global stats for approvers/admins
        all_payments = PaymentRequest.objects.all()
        context['total_initiated'] = all_payments.count()
        context['total_value'] = all_payments.aggregate(Sum('amount'))['amount__sum'] or 0
        context['pending_global'] = all_payments.filter(status='PENDING').count()
        
        # My pending actions
        context['my_pending_actions'] = PaymentRequest.objects.filter(
            status=PaymentRequest.Status.PENDING
        ).exclude(
            initiator=request.user
        ).exclude(
            approvals__approver=request.user
        ).count()

    # Graph Data (Last 6 Months)
    from django.db.models.functions import TruncMonth
    import datetime

    today = datetime.date.today()
    six_months_ago = today - datetime.timedelta(days=180)
    
    # Base query based on role
    chart_query = PaymentRequest.objects.all()
    if request.user.role == UserProfile.Role.INITIATOR:
        chart_query = chart_query.filter(initiator=request.user)
        
    monthly_data = chart_query.filter(created_at__gte=six_months_ago)\
        .annotate(month=TruncMonth('created_at'))\
        .values('month')\
        .annotate(total=Sum('amount'))\
        .order_by('month')

    # Format for Chart.js
    chart_labels = []
    chart_data = []
    
    # Fill in sparse data
    for entry in monthly_data:
        chart_labels.append(entry['month'].strftime('%b'))
        chart_data.append(int(entry['total']))
        
    # Default State (if no data)
    if not chart_data:
        # Show last 6 months empty
        for i in range(5, -1, -1):
            d = today - datetime.timedelta(days=i*30)
            chart_labels.append(d.strftime('%b'))
            chart_data.append(0)

    context['chart_labels'] = chart_labels
    context['chart_data'] = chart_data

    return render(request, 'payments/home.html', context)

@login_required
def create_payment(request):
    if not is_initiator(request.user):
        messages.error(request, "Only initiators can create payments.")
        return redirect('payments:home')

    if request.method == 'POST':
        form = PaymentRequestForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.initiator = request.user
            payment.save()
            messages.success(request, f"Payment request #{payment.id} created successfully.")
            return redirect('payments:payment_detail', pk=payment.id)
    else:
        form = PaymentRequestForm()
    
    return render(request, 'payments/payment_create.html', {'form': form})

@login_required
def my_payments(request):
    payments = PaymentRequest.objects.filter(initiator=request.user).order_by('-created_at')
    return render(request, 'payments/my_payments.html', {'payments': payments})

@login_required
def pending_approvals(request):
    if not is_approver_or_admin(request.user):
        messages.error(request, "Access denied.")
        return redirect('payments:home')
    
    # Logic to show what THIS user can act on
    pending_payments = PaymentRequest.objects.filter(
        status=PaymentRequest.Status.PENDING
    ).exclude(
        initiator=request.user
    ).exclude(
        approvals__approver=request.user
    ).order_by('-created_at')

    # For Admins, also show APPROVED payments ready for EXECUTION
    ready_for_execution = []
    if request.user.role == UserProfile.Role.ADMIN:
        ready_for_execution = PaymentRequest.objects.filter(
            status=PaymentRequest.Status.APPROVED
        ).order_by('-created_at')

    return render(request, 'payments/pending_payments.html', {
        'pending_payments': pending_payments,
        'ready_for_execution': ready_for_execution
    })

@login_required
def payment_detail(request, pk):
    payment = get_object_or_404(PaymentRequest, pk=pk)
    
    if payment.initiator != request.user and not is_approver_or_admin(request.user):
        messages.error(request, "Access denied.")
        return redirect('payments:home')

    current_approvals = payment.approvals.count()
    required_approvals = get_required_approvals(payment)
    needs_admin = requires_admin_approval(payment)
    
    user_has_approved = payment.approvals.filter(approver=request.user).exists()
    can_approve = (
        payment.status == PaymentRequest.Status.PENDING and
        is_approver_or_admin(request.user) and
        payment.initiator != request.user and
        not user_has_approved
    )
    
    can_execute = (
        payment.status == PaymentRequest.Status.APPROVED and
        request.user.role == UserProfile.Role.ADMIN
    )

    return render(request, 'payments/payment_detail.html', {
        'payment': payment,
        'approvals': payment.approvals.all(),
        'audit_logs': payment.auditlog_set.all().order_by('-timestamp'),
        'required_approvals': required_approvals,
        'needs_admin': needs_admin,
        'can_approve': can_approve,
        'can_execute': can_execute,
    })

@login_required
def approve_payment(request, pk):
    payment = get_object_or_404(PaymentRequest, pk=pk)
    workflow = PaymentWorkflow(payment, request.user)
    
    try:
        workflow.approve()
        messages.success(request, "Payment approved.")
    except WorkflowError as e:
        messages.error(request, str(e))
        
    return redirect('payments:payment_detail', pk=pk)

@login_required
def reject_payment(request, pk):
    payment = get_object_or_404(PaymentRequest, pk=pk)
    workflow = PaymentWorkflow(payment, request.user)
    
    try:
        workflow.reject()
        messages.success(request, "Payment rejected.")
    except WorkflowError as e:
        messages.error(request, str(e))
        
    return redirect('payments:payment_detail', pk=pk)

@login_required
def execute_payment(request, pk):
    payment = get_object_or_404(PaymentRequest, pk=pk)
    workflow = PaymentWorkflow(payment, request.user)
    
    try:
        workflow.execute()
        messages.success(request, "Payment executed.")
    except WorkflowError as e:
        messages.error(request, str(e))
        
    return redirect('payments:payment_detail', pk=pk)

def register(request):
    from .forms import UserRegistrationForm
    from django.contrib.auth import login
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.username}! Your account has been created.")
            return redirect('payments:home')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})
