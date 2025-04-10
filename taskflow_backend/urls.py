from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='admin/', permanent=False)),  # Redirect root to admin
    path('admin/', admin.site.urls),
    path('api/v1/', include('api.urls')),
    path('api/v1/auth/', include('accounts.urls')),  # Add this line
    path('api/calendar/', include('calendar_events.api.urls')),
    path('roles/', include('roles.urls')),
    path('api/v1/messaging/', include('messaging.urls')),
]