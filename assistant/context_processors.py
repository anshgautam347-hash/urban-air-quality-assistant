"""
Context Processor for Urban Air Quality Assistant:
Injects active location, family count, scale preference, and global helper states into templates.
"""

from django.conf import settings
from .models import FamilyProfile, UserPreference


def app_context(request):
    # Ensure session key exists for guest tracking
    if not request.session.session_key:
        request.session.save()
    session_key = request.session.session_key

    # Active Location from session or defaults
    city_name = request.session.get('active_city', settings.DEFAULT_CITY_NAME)
    latitude = request.session.get('active_lat', settings.DEFAULT_LATITUDE)
    longitude = request.session.get('active_lon', settings.DEFAULT_LONGITUDE)

    # User Preferences
    pref = None
    if request.user.is_authenticated:
        pref = UserPreference.objects.filter(user=request.user).first()
    if not pref:
        pref = UserPreference.objects.filter(session_key=session_key).first()

    active_scale = pref.preferred_aqi_scale if pref else settings.DEFAULT_AQI_SCALE
    alert_threshold = pref.alert_threshold if pref else 150

    # Family profiles count
    if request.user.is_authenticated:
        profiles_qs = FamilyProfile.objects.filter(user=request.user)
    else:
        profiles_qs = FamilyProfile.objects.filter(session_key=session_key)

    total_family = profiles_qs.count()
    vulnerable_family = profiles_qs.filter(has_respiratory_condition=True).count()

    has_gemini = bool(getattr(settings, 'GEMINI_API_KEY', '') or (pref and pref.gemini_api_key_override))

    return {
        'APP_NAME': 'Urban Air Quality Assistant',
        'current_location': {
            'city_name': city_name,
            'latitude': latitude,
            'longitude': longitude,
        },
        'active_scale': active_scale,
        'alert_threshold': alert_threshold,
        'family_count': total_family,
        'vulnerable_count': vulnerable_family,
        'has_gemini_configured': has_gemini,
    }
