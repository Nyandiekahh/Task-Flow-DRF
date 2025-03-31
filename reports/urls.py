# reports/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    ReportConfigurationViewSet,
    ProjectStatusReportView,
    TeamProductivityReportView,
    TaskCompletionReportView,
    TimeTrackingReportView,
    OverdueTasksReportView
)

router = DefaultRouter()
router.register(r'configurations', ReportConfigurationViewSet, basename='report-config')

urlpatterns = [
    path('project-status/', ProjectStatusReportView.as_view(), name='project-status-report'),
    path('team-productivity/', TeamProductivityReportView.as_view(), name='team-productivity-report'),
    path('task-completion/', TaskCompletionReportView.as_view(), name='task-completion-report'),
    path('time-tracking/', TimeTrackingReportView.as_view(), name='time-tracking-report'),
    path('overdue-tasks/', OverdueTasksReportView.as_view(), name='overdue-tasks-report'),
]

urlpatterns += router.urls