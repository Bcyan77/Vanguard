from django.urls import path
from . import api_views

urlpatterns = [
    # Player search and detail
    path('players/search/', api_views.PlayerSearchAPIView.as_view(), name='api_player_search'),
    path('players/<int:membership_type>/<str:membership_id>/', api_views.PlayerDetailAPIView.as_view(), name='api_player_detail'),

    # Statistics API (public - no authentication required)
    path('statistics/descriptive/', api_views.StatisticsDescriptiveAPIView.as_view(), name='api_statistics_descriptive'),
    path('statistics/class-comparison/', api_views.StatisticsClassComparisonAPIView.as_view(), name='api_statistics_class_comparison'),
    path('statistics/correlation/', api_views.StatisticsCorrelationAPIView.as_view(), name='api_statistics_correlation'),
    path('statistics/distribution/', api_views.StatisticsDistributionAPIView.as_view(), name='api_statistics_distribution'),
    path('statistics/hypothesis-tests/', api_views.StatisticsHypothesisTestsAPIView.as_view(), name='api_statistics_hypothesis_tests'),
    path('statistics/filtered-count/', api_views.StatisticsFilteredCountAPIView.as_view(), name='api_statistics_filtered_count'),

    # Gamification API
    path('statistics/leaderboard/', api_views.LeaderboardAPIView.as_view(), name='api_leaderboard'),
    path('gamification/badges/', api_views.BadgesAPIView.as_view(), name='api_badges'),
]
