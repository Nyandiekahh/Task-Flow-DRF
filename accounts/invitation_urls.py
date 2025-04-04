# accounts/invitation_urls.py
from django.urls import path
from .invitation_views import InvitationCreateView

urlpatterns = [
    path('', InvitationCreateView.as_view(), name='invitation-create'),
]