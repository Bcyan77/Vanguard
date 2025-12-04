from django.urls import path
from . import api_views

urlpatterns = [
    # Fireteams CRUD
    path('fireteams/', api_views.FireteamListCreateAPIView.as_view(), name='api_fireteam_list'),
    path('fireteams/<str:pk>/', api_views.FireteamDetailAPIView.as_view(), name='api_fireteam_detail'),

    # Fireteam membership actions
    path('fireteams/<str:pk>/apply/', api_views.FireteamApplyAPIView.as_view(), name='api_fireteam_apply'),
    path('fireteams/<str:pk>/leave/', api_views.FireteamLeaveAPIView.as_view(), name='api_fireteam_leave'),

    # Fireteam applications management
    path('fireteams/<str:pk>/applications/', api_views.FireteamApplicationsAPIView.as_view(), name='api_fireteam_applications'),
    path('fireteams/<str:pk>/applications/<int:application_id>/accept/', api_views.FireteamApplicationAcceptAPIView.as_view(), name='api_fireteam_application_accept'),
    path('fireteams/<str:pk>/applications/<int:application_id>/reject/', api_views.FireteamApplicationRejectAPIView.as_view(), name='api_fireteam_application_reject'),

    # Activity data (Tier 1, 2, 3)
    path('activities/types/', api_views.ActivityTypesAPIView.as_view(), name='api_activity_types'),
    path('activities/specific/', api_views.SpecificActivitiesAPIView.as_view(), name='api_specific_activities'),
    path('activities/modes/', api_views.ActivityModesAPIView.as_view(), name='api_activity_modes'),
]
