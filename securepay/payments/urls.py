from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.home, name='home'),
    path('create/', views.create_payment, name='create_payment'),
    path('my-payments/', views.my_payments, name='my_payments'),
    path('pending/', views.pending_approvals, name='pending_approvals'),
    path('payment/<int:pk>/', views.payment_detail, name='payment_detail'),
    path('payment/<int:pk>/approve/', views.approve_payment, name='approve_payment'),
    path('payment/<int:pk>/reject/', views.reject_payment, name='reject_payment'),
    path('payment/<int:pk>/execute/', views.execute_payment, name='execute_payment'),
    path('register/', views.register, name='register'),
]
