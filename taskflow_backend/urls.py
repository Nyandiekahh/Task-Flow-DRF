# taskflow_backend/urls.py

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='admin/', permanent=False)),  # Redirect root to admin
    path('admin/', admin.site.urls),
    path('api/v1/', include('api.urls')),
    path('api/calendar/', include('calendar_events.api.urls')),  # Add this new line
    path('roles/', include('roles.urls')),  # Add this new line
]