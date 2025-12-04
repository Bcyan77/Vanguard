from django.urls import path
from . import api_views

urlpatterns = [
    # Player search and detail
    path('players/search/', api_views.PlayerSearchAPIView.as_view(), name='api_player_search'),
    path('players/<int:membership_type>/<str:membership_id>/', api_views.PlayerDetailAPIView.as_view(), name='api_player_detail'),
]
