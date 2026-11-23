"""
Views for Urban Air Quality Assistant:
Covers all 9 required pages, interactive AJAX APIs, family management, and authentication.
"""

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.conf import settings

from .models import FamilyProfile, SavedLocation, UserPreference, AirQualitySnapshot, AIChatHistory
from .forms import FamilyProfileForm, UserPreferenceForm, SavedLocationForm, UserRegisterForm
from .services import aqi_service, gemini_service, planner_service, indoor_service, alert_service


def _get_session_key(request):
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


def _get_active_location_and_scale(request):
    session_key = _get_session_key(request)
    city = request.session.get('active_city', settings.DEFAULT_CITY_NAME)
    lat = float(request.session.get('active_lat', settings.DEFAULT_LATITUDE))
    lon = float(request.session.get('active_lon', settings.DEFAULT_LONGITUDE))

    pref = None
    if request.user.is_authenticated:
        pref = UserPreference.objects.filter(user=request.user).first()
    if not pref:
        pref = UserPreference.objects.filter(session_key=session_key).first()

    scale = pref.preferred_aqi_scale if pref else settings.DEFAULT_AQI_SCALE
    threshold = pref.alert_threshold if pref else 150

    return city, lat, lon, scale, threshold


def _get_family_profiles(request):
    session_key = _get_session_key(request)
    if request.user.is_authenticated:
        return FamilyProfile.objects.filter(user=request.user)
    return FamilyProfile.objects.filter(session_key=session_key)


# 1. Home / Dashboard Page
def dashboard_view(request):
    city, lat, lon, scale, threshold = _get_active_location_and_scale(request)
    aqi_data = aqi_service.get_air_quality_data(lat, lon, city, scale)
    family_profiles = _get_family_profiles(request)

    # Evaluate alerts
    alert_info = alert_service.evaluate_pollution_alerts(aqi_data, family_profiles, threshold)

    # Quick preview for daily routine window
    routine_preview = planner_service.generate_family_daily_routine(aqi_data, family_profiles)

    # Indoor quick status
    indoor_preview = indoor_service.get_indoor_air_strategy(aqi_data['us_aqi'], aqi_data['pm25'])

    context = {
        'page_title': 'Smart Dashboard',
        'aqi_data': aqi_data,
        'alert_info': alert_info,
        'routine_preview': routine_preview,
        'indoor_preview': indoor_preview,
        'family_profiles': family_profiles,
        'forecast_json': json.dumps({
            'labels': aqi_data['forecast_times'],
            'aqi': aqi_data['forecast_aqi'],
            'pm25': aqi_data['forecast_pm25'],
            'pm10': aqi_data['forecast_pm10']
        })
    }
    return render(request, 'dashboard.html', context)


# 2. Air Quality Details Page
def air_quality_details_view(request):
    city, lat, lon, scale, threshold = _get_active_location_and_scale(request)
    aqi_data = aqi_service.get_air_quality_data(lat, lon, city, scale)

    pollutant_chart_data = {
        'labels': [p['name'] for p in aqi_data['pollutants']],
        'values': [p['value'] for p in aqi_data['pollutants']],
        'ratios': [p['ratio_to_who'] for p in aqi_data['pollutants']],
    }

    context = {
        'page_title': 'Air Quality Details & Scale Breakdown',
        'aqi_data': aqi_data,
        'pollutant_chart_json': json.dumps(pollutant_chart_data),
    }
    return render(request, 'air_quality_details.html', context)


# 3. Family Profiles Page
def family_profiles_view(request):
    session_key = _get_session_key(request)
    city, lat, lon, scale, threshold = _get_active_location_and_scale(request)
    aqi_data = aqi_service.get_air_quality_data(lat, lon, city, scale)
    profiles = _get_family_profiles(request)

    if request.method == 'POST':
        form = FamilyProfileForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            if request.user.is_authenticated:
                profile.user = request.user
            profile.session_key = session_key
            profile.save()
            messages.success(request, f'Family profile for "{profile.name}" added successfully.')
            return redirect('family_profiles')
    else:
        form = FamilyProfileForm()

    # Calculate personalized risk badges for each family member
    analyzed_profiles = []
    for p in profiles:
        guidance = planner_service.get_member_specific_guidance(p, aqi_data['us_aqi'], aqi_data['us_aqi'])
        analyzed_profiles.append({
            'profile': p,
            'guidance': guidance,
            'is_high_risk': p.has_respiratory_condition or (p.age_group in ('infant', 'senior', 'child') and aqi_data['us_aqi'] > 100)
        })

    context = {
        'page_title': 'Personalized Family Profiles',
        'form': form,
        'analyzed_profiles': analyzed_profiles,
        'aqi_data': aqi_data,
    }
    return render(request, 'family_profiles.html', context)


@require_POST
def delete_family_profile_view(request, profile_id):
    session_key = _get_session_key(request)
    if request.user.is_authenticated:
        profile = get_object_or_404(FamilyProfile, id=profile_id, user=request.user)
    else:
        profile = get_object_or_404(FamilyProfile, id=profile_id, session_key=session_key)

    name = profile.name
    profile.delete()
    messages.info(request, f'Removed profile for {name}.')
    return redirect('family_profiles')


# 4. Daily Routine Planner Page
def routine_planner_view(request):
    city, lat, lon, scale, threshold = _get_active_location_and_scale(request)
    aqi_data = aqi_service.get_air_quality_data(lat, lon, city, scale)
    family_profiles = _get_family_profiles(request)

    routine_data = planner_service.generate_family_daily_routine(aqi_data, family_profiles)

    context = {
        'page_title': 'Smart Daily Routine Planner',
        'aqi_data': aqi_data,
        'routine': routine_data,
        'family_profiles': family_profiles,
        'hourly_chart_json': json.dumps({
            'labels': aqi_data['forecast_times'],
            'aqi': aqi_data['forecast_aqi'],
        })
    }
    return render(request, 'routine_planner.html', context)


# 5. Indoor Air Quality Assistant Page
def indoor_air_view(request):
    city, lat, lon, scale, threshold = _get_active_location_and_scale(request)
    aqi_data = aqi_service.get_air_quality_data(lat, lon, city, scale)

    indoor_strategy = indoor_service.get_indoor_air_strategy(aqi_data['us_aqi'], aqi_data['pm25'])

    context = {
        'page_title': 'Indoor Air Quality Assistant & Hacks',
        'aqi_data': aqi_data,
        'indoor': indoor_strategy,
    }
    return render(request, 'indoor_air.html', context)


# 6. Gemini-Powered AI Assistant Page
def ai_chat_view(request):
    session_key = _get_session_key(request)
    city, lat, lon, scale, threshold = _get_active_location_and_scale(request)
    aqi_data = aqi_service.get_air_quality_data(lat, lon, city, scale)
    family_profiles = _get_family_profiles(request)

    if request.user.is_authenticated:
        history = AIChatHistory.objects.filter(user=request.user).order_by('-created_at')[:15]
    else:
        history = AIChatHistory.objects.filter(session_key=session_key).order_by('-created_at')[:15]

    history = list(reversed(history))

    context = {
        'page_title': 'AI Urban Air Quality Assistant',
        'aqi_data': aqi_data,
        'family_profiles': family_profiles,
        'chat_history': history,
        'sample_prompts': [
            "Is it a good time to take my child outside?",
            "How can I reduce pollution exposure at home?",
            "What should my elderly parents avoid during severe smog?",
            "What are the best low-emission commuting alternatives?",
            "Create a daily clean-air routine for my family."
        ]
    }
    return render(request, 'ai_chat.html', context)


@require_POST
def ai_chat_api(request):
    """
    AJAX endpoint for conversational AI interaction.
    """
    session_key = _get_session_key(request)
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
    except Exception:
        user_message = request.POST.get('message', '').strip()

    if not user_message:
        return JsonResponse({'error': 'Message cannot be empty.'}, status=400)

    city, lat, lon, scale, threshold = _get_active_location_and_scale(request)
    aqi_data = aqi_service.get_air_quality_data(lat, lon, city, scale)
    family_profiles = _get_family_profiles(request)

    response = gemini_service.ask_gemini_assistant(user_message, aqi_data, family_profiles)

    # Save to history
    AIChatHistory.objects.create(
        user=request.user if request.user.is_authenticated else None,
        session_key=session_key,
        user_message=user_message,
        ai_response=response['reply'],
        model_source=response['source'],
        is_ai=response['is_ai']
    )

    return JsonResponse({
        'reply': response['reply'],
        'source': response['source'],
        'is_ai': response['is_ai'],
        'success': True
    })


# 7. Pollution Alerts Page
def alerts_view(request):
    city, lat, lon, scale, threshold = _get_active_location_and_scale(request)
    aqi_data = aqi_service.get_air_quality_data(lat, lon, city, scale)
    family_profiles = _get_family_profiles(request)

    alert_info = alert_service.evaluate_pollution_alerts(aqi_data, family_profiles, threshold)

    context = {
        'page_title': 'Smart Pollution Alerts & Severity Warnings',
        'aqi_data': aqi_data,
        'alert_info': alert_info,
        'threshold': threshold,
        'family_profiles': family_profiles,
    }
    return render(request, 'alerts.html', context)


# 8. Historical Air Quality Page
def historical_trends_view(request):
    city, lat, lon, scale, threshold = _get_active_location_and_scale(request)
    aqi_data = aqi_service.get_air_quality_data(lat, lon, city, scale)

    # Compute historical statistics
    hist_aqi = aqi_data.get('historical_aqi', [])
    hist_pm25 = aqi_data.get('historical_pm25', [])

    avg_aqi = round(sum(hist_aqi) / len(hist_aqi), 1) if hist_aqi else 0
    max_aqi = max(hist_aqi) if hist_aqi else 0
    min_aqi = min(hist_aqi) if hist_aqi else 0

    avg_pm25 = round(sum(hist_pm25) / len(hist_pm25), 1) if hist_pm25 else 0
    peak_pm25 = max(hist_pm25) if hist_pm25 else 0
    who_exceedance_pct = round((sum(1 for v in hist_pm25 if v > 15.0) / len(hist_pm25) * 100), 1) if hist_pm25 else 0

    stats = {
        'avg_aqi': avg_aqi,
        'max_aqi': max_aqi,
        'min_aqi': min_aqi,
        'avg_pm25': avg_pm25,
        'peak_pm25': peak_pm25,
        'who_exceedance_pct': who_exceedance_pct,
    }

    context = {
        'page_title': 'Historical Air Quality & 7-Day Trends',
        'aqi_data': aqi_data,
        'stats': stats,
        'historical_chart_json': json.dumps({
            'labels': aqi_data['historical_times'],
            'aqi': aqi_data['historical_aqi'],
            'pm25': aqi_data['historical_pm25'],
            'pm10': aqi_data['historical_pm10'],
            'no2': aqi_data['historical_no2']
        })
    }
    return render(request, 'historical_trends.html', context)


# 9. Settings Page
def settings_view(request):
    session_key = _get_session_key(request)

    pref = None
    if request.user.is_authenticated:
        pref = UserPreference.objects.filter(user=request.user).first()
    if not pref:
        pref = UserPreference.objects.filter(session_key=session_key).first()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'save_preferences':
            form = UserPreferenceForm(request.POST, instance=pref)
            if form.is_valid():
                obj = form.save(commit=False)
                if request.user.is_authenticated:
                    obj.user = request.user
                obj.session_key = session_key
                obj.save()
                messages.success(request, 'Preferences saved successfully.')
                return redirect('settings')
        elif action == 'add_location':
            loc_form = SavedLocationForm(request.POST)
            if loc_form.is_valid():
                loc = loc_form.save(commit=False)
                if request.user.is_authenticated:
                    loc.user = request.user
                loc.session_key = session_key
                if loc.is_default:
                    # unset others
                    SavedLocation.objects.filter(session_key=session_key).update(is_default=False)
                loc.save()
                messages.success(request, f'Location "{loc.city_name}" saved.')
                return redirect('settings')
    else:
        form = UserPreferenceForm(instance=pref)
        loc_form = SavedLocationForm()

    if request.user.is_authenticated:
        saved_locations = SavedLocation.objects.filter(user=request.user)
    else:
        saved_locations = SavedLocation.objects.filter(session_key=session_key)

    context = {
        'page_title': 'Application Settings & Preferences',
        'form': form,
        'loc_form': loc_form,
        'saved_locations': saved_locations,
    }
    return render(request, 'settings.html', context)


# APIs and Location Handlers
@require_GET
def search_locations_api(request):
    q = request.GET.get('q', '').strip()
    results = aqi_service.search_locations(q)
    return JsonResponse({'results': results})


@require_POST
def set_active_location_api(request):
    try:
        data = json.loads(request.body)
        city = data.get('city_name')
        lat = float(data.get('latitude'))
        lon = float(data.get('longitude'))
    except Exception:
        city = request.POST.get('city_name')
        lat = float(request.POST.get('latitude', settings.DEFAULT_LATITUDE))
        lon = float(request.POST.get('longitude', settings.DEFAULT_LONGITUDE))

    if city and lat and lon:
        request.session['active_city'] = city
        request.session['active_lat'] = lat
        request.session['active_lon'] = lon
        request.session.modified = True
        return JsonResponse({'success': True, 'city': city, 'lat': lat, 'lon': lon})
    return JsonResponse({'error': 'Invalid parameters'}, status=400)


# Authentication Views
def auth_login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'auth/login.html', {'form': form, 'page_title': 'User Login'})


def auth_register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard')
    else:
        form = UserRegisterForm()
    return render(request, 'auth/register.html', {'form': form, 'page_title': 'Register Account'})


def auth_logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('dashboard')
