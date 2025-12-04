from django.urls import path
from . import api_views

urlpatterns = [
    # Current user profile
    path('accounts/profile/', api_views.CurrentUserProfileAPIView.as_view(), name='api_current_user_profile'),
]
