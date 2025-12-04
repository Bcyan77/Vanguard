from django.urls import path
from . import views

app_name = 'players'

urlpatterns = [
    path('', views.player_search, name='search'),
    path('<int:membership_type>/<str:membership_id>/', views.player_detail, name='detail'),
]
