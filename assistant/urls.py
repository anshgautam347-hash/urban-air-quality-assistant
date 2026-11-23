"""
URL configuration for Urban Air Quality Assistant application.
"""

from django.urls import path
from . import views

urlpatterns = [
    # 1. Dashboard
    path('', views.dashboard_view, name='dashboard'),

    # 2. Air Quality Details
    path('air-quality-details/', views.air_quality_details_view, name='air_quality_details'),

    # 3. Family Profiles
    path('family-profiles/', views.family_profiles_view, name='family_profiles'),
    path('family-profiles/<int:profile_id>/delete/', views.delete_family_profile_view, name='delete_family_profile'),

    # 4. Daily Routine Planner
    path('routine-planner/', views.routine_planner_view, name='routine_planner'),

    # 5. Indoor Air Quality Assistant
    path('indoor-air/', views.indoor_air_view, name='indoor_air'),

    # 6. Gemini AI Assistant
    path('ai-assistant/', views.ai_chat_view, name='ai_chat'),

    # 7. Pollution Alerts
    path('alerts/', views.alerts_view, name='alerts'),

    # 8. Historical Trends
    path('historical-trends/', views.historical_trends_view, name='historical_trends'),

    # 9. Settings
    path('settings/', views.settings_view, name='settings'),

    # AJAX & JSON APIs
    path('api/search-locations/', views.search_locations_api, name='api_search_locations'),
    path('api/set-location/', views.set_active_location_api, name='api_set_location'),
    path('api/ai-chat/', views.ai_chat_api, name='api_ai_chat'),

    # Authentication
    path('login/', views.auth_login_view, name='login'),
    path('register/', views.auth_register_view, name='register'),
    path('logout/', views.auth_logout_view, name='logout'),
]
