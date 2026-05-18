from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import (
    RegisterView, LoginView, RoleRedirectView,
    HomeView, ProfileView
)
from .views_admin_dashboard import AdminAnalyticsView

app_name = 'accounts'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('analytics/', AdminAnalyticsView.as_view(), name='analytics'),
]
