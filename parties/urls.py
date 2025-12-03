from django.urls import path
from . import views

app_name = 'parties'

urlpatterns = [
    path('', views.party_list, name='party_list'),
    path('create/', views.party_create, name='party_create'),
    path('<str:pk>/', views.party_detail, name='party_detail'),
    path('<str:pk>/edit/', views.party_edit, name='party_edit'),
    path('<str:pk>/delete/', views.party_delete, name='party_delete'),
    path('<str:pk>/apply/', views.party_apply, name='party_apply'),
    path('<str:pk>/leave/', views.party_leave, name='party_leave'),
    path('<str:pk>/applications/', views.party_applications, name='party_applications'),
    path('application/<int:application_id>/accept/', views.application_accept, name='application_accept'),
    path('application/<int:application_id>/reject/', views.application_reject, name='application_reject'),
]
