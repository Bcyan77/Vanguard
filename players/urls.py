from django.urls import path
from . import views

app_name = 'players'

urlpatterns = [
    path('', views.player_search, name='search'),
    path('statistics/', views.player_statistics, name='statistics'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('refresh-stats/', views.refresh_stats, name='refresh_stats'),
    path('<int:membership_type>/<str:membership_id>/', views.player_detail, name='detail'),
]
