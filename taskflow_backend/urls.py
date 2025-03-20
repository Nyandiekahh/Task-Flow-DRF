# taskflow_backend/urls.py

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='admin/', permanent=False)),  # Redirect root to admin
    path('admin/', admin.site.urls),
    path('api/v1/', include('api.urls')),
]