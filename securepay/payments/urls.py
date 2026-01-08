from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("payments/new/", views.payment_create, name="payment_create"),
    path("payments/mine/", views.my_payments, name="my_payments"),
    path("payments/pending/", views.pending_payments, name="pending_payments"),
    path("payments/<int:pk>/detail/", views.payment_detail, name="payment_detail"),
    path("payments/<int:pk>/approve/", views.payment_approve, name="payment_approve"),
    path("payments/<int:pk>/reject/", views.payment_reject, name="payment_reject"),
    path("payments/<int:pk>/execute/", views.payment_execute, name="payment_execute"),
]
