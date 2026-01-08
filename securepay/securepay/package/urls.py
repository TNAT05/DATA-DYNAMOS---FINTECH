# securepay/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),  # login/logout
    path("", RedirectView.as_view(pattern_name="payments:home", permanent=False)),
    path("", include(("payments.urls", "payments"), namespace="payments")),
]
