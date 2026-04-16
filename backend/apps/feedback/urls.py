from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('courses', views.CourseViewSet, basename='course')
router.register('sessions', views.ClassSessionViewSet, basename='session')

urlpatterns = [
    path('', include(router.urls)),
    path('submit/', views.submit_reaction, name='submit-reaction'),
    path('statistics/<int:session_id>/', views.session_statistics, name='session-statistics'),
    path('statistics/<int:session_id>/slots/', views.session_statistics_by_slots, name='session-statistics-slots'),
    path('history/', views.history_query, name='history-query'),
    path('export/<int:session_id>/', views.export_excel, name='export-excel'),
]
