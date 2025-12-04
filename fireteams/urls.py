from django.urls import path
from . import views

app_name = 'fireteams'

urlpatterns = [
    # Fireteam CRUD
    path('', views.fireteam_list, name='fireteam_list'),
    path('create/', views.fireteam_create, name='fireteam_create'),
    path('<str:pk>/', views.fireteam_detail, name='fireteam_detail'),
    path('<str:pk>/edit/', views.fireteam_edit, name='fireteam_edit'),
    path('<str:pk>/delete/', views.fireteam_delete, name='fireteam_delete'),
    path('<str:pk>/apply/', views.fireteam_apply, name='fireteam_apply'),
    path('<str:pk>/leave/', views.fireteam_leave, name='fireteam_leave'),
    path('<str:pk>/applications/', views.fireteam_applications, name='fireteam_applications'),

    # Application actions
    path('application/<int:application_id>/accept/', views.application_accept, name='application_accept'),
    path('application/<int:application_id>/reject/', views.application_reject, name='application_reject'),

    # API endpoints for 3-tier cascading selection
    path('api/specific-activities/', views.SpecificActivitiesAPIView.as_view(), name='api_get_specific_activities'),
    path('api/activity-modes/', views.ActivityModesAPIView.as_view(), name='api_get_activity_modes'),
]
