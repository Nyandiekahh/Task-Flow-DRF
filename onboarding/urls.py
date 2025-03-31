# onboarding/urls.py

from django.urls import path
from .views import (
    OnboardingDataView, 
    CompleteOnboardingView, 
    OrganizationSetupView,
    OnboardingStatusView
)

urlpatterns = [
    path('data/', OnboardingDataView.as_view(), name='onboarding-data'),
    path('complete/', CompleteOnboardingView.as_view(), name='complete-onboarding'),
    path('organization-setup/', OrganizationSetupView.as_view(), name='organization-setup'),
    path('status/', OnboardingStatusView.as_view(), name='onboarding-status'),
]