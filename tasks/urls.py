from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, CommentViewSet, TaskAttachmentViewSet, TaskHistoryViewSet

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'attachments', TaskAttachmentViewSet, basename='attachment')
router.register(r'history', TaskHistoryViewSet, basename='history')

urlpatterns = [
    path('', include(router.urls)),
]