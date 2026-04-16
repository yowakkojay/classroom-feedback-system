from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('users', views.UserViewSet, basename='user')

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('github/', views.github_login, name='github-login'),
    path('github/bind/', views.github_bind, name='github-bind'),
    path('me/', views.me_view, name='me'),
    path('', include(router.urls)),
]
