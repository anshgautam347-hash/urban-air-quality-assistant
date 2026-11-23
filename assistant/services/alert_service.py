"""
Pollution Alert Service:
Evaluates current and forecasted AQI against critical health thresholds and user/family profiles
to generate actionable warning banners, personalized precautions, and severity notices.
"""


def evaluate_pollution_alerts(aqi_data, family_profiles=None, user_threshold=150):
    """
    Evaluates pollution alerts for dashboard banners and notifications.
    """
    current_aqi = int(aqi_data.get('us_aqi', 100))
    pm25 = float(aqi_data.get('pm25', 35.0))
    city = aqi_data.get('city_name', 'your location')
    forecast_items = aqi_data.get('forecast_items', [])

    alerts = []
    is_severe = False
    banner_color = 'info'

    # Check for Severe / Emergency Pollution
    if current_aqi >= 300:
        is_severe = True
        banner_color = 'danger'
        alerts.append({
            'type': 'EMERGENCY_SMOG_ALERT',
            'severity': 'Hazardous (Emergency Level)',
            'title': f'🚨 Emergency Smog Inversion in {city} (AQI: {current_aqi})',
            'badge': 'Hazardous Alert',
            'badge_class': 'bg-dark text-white',
            'color_class': 'border-danger bg-danger-subtle text-danger-emphasis',
            'message': f'Measured AQI is {current_aqi} with PM2.5 at {pm25} µg/m³. Atmospheric conditions represent an emergency health warning for all residents.',
            'primary_action': 'Remain indoors in closed rooms. Turn air purifiers to Turbo. Outdoor exposure should be eliminated completely.',
            'target_group': 'All family members'
        })
    elif current_aqi >= 200:
        is_severe = True
        banner_color = 'danger'
        alerts.append({
            'type': 'VERY_UNHEALTHY_ALERT',
            'severity': 'Very Unhealthy',
            'title': f'⚠️ Severe Smog Advisory for {city} (AQI: {current_aqi})',
            'badge': 'Very Unhealthy',
            'badge_class': 'bg-purple text-white',
            'color_class': 'border-danger bg-danger-subtle text-danger-emphasis',
            'message': f'Air quality has reached very unhealthy levels (AQI: {current_aqi}). Risk of respiratory distress and cardiovascular strain is significantly heightened.',
            'primary_action': 'Cancel all outdoor workouts and sports. Seal windows. Wear certified N95 respirators for mandatory travel.',
            'target_group': 'General public & high-risk members'
        })
    elif current_aqi >= user_threshold or current_aqi >= 150:
        is_severe = True
        banner_color = 'warning'
        alerts.append({
            'type': 'UNHEALTHY_THRESHOLD_ALERT',
            'severity': 'Unhealthy',
            'title': f'⚠️ Unhealthy Air Quality Threshold Exceeded (AQI: {current_aqi})',
            'badge': 'Threshold Exceeded',
            'badge_class': 'bg-warning text-dark',
            'color_class': 'border-warning bg-warning-subtle text-warning-emphasis',
            'message': f'AQI ({current_aqi}) exceeds recommended threshold ({user_threshold}). Particulate concentration PM2.5 is {pm25} µg/m³.',
            'primary_action': 'Sensitive groups should avoid prolonged outdoor exposure. Shift high-intensity cardio exercises indoors.',
            'target_group': 'Children, seniors & individuals with lung/heart disease'
        })
    elif current_aqi > 100:
        alerts.append({
            'type': 'MODERATE_SENSITIVE_ALERT',
            'severity': 'Sensitive Group Warning',
            'title': f'ℹ️ Moderate Pollution with Sensitive Group Impact ({city})',
            'badge': 'Sensitive Groups',
            'badge_class': 'bg-info text-white',
            'color_class': 'border-info bg-info-subtle text-info-emphasis',
            'message': f'Current AQI is {current_aqi}. While acceptable for most adults, sensitive individuals may experience throat tickle or eye irritation.',
            'primary_action': 'Keep children with asthma hydrated and monitor for wheezing. Ventilate homes during afternoon hours only.',
            'target_group': 'Sensitive individuals'
        })

    # Family-Specific Customized Precautions
    family_precautions = []
    if family_profiles:
        for member in family_profiles:
            precautions = []
            if member.age_group in ('child', 'infant'):
                if current_aqi > 150:
                    precautions.append("Keep indoors; replace outdoor games with indoor physical activities.")
                    precautions.append("Equip with well-fitting child N95/KF94 mask if transit is necessary.")
                elif current_aqi > 100:
                    precautions.append("Limit outdoor playtime to 30 mins during afternoon dip.")
            if member.age_group == 'senior':
                if current_aqi > 150:
                    precautions.append("Strictly avoid morning/evening park walks.")
                    precautions.append("Ensure rapid access to prescribed respiratory inhalers.")
                elif current_aqi > 100:
                    precautions.append("Switch from brisk morning walking to afternoon indoor mobility.")
            if member.has_respiratory_condition:
                if current_aqi > 100:
                    precautions.append(f"Condition notice ({member.condition_details}): Prevent flare-ups with continuous HEPA filtration.")
                    precautions.append("Avoid proximity to kitchen frying fumes or incense.")

            if precautions:
                family_precautions.append({
                    'name': member.name,
                    'age_group': member.get_age_group_display(),
                    'precautions': precautions
                })

    # Hourly Forecast Spikes (e.g. evening inversion)
    upcoming_spike = None
    for item in forecast_items[:12]:
        if item.get('aqi', 0) > max(150, current_aqi + 30):
            upcoming_spike = item
            break

    if upcoming_spike:
        alerts.append({
            'type': 'FORECAST_SPIKE_WARNING',
            'severity': 'Upcoming Smog Surge',
            'title': f'📈 Projected Smog Surge at {upcoming_spike.get("time")}',
            'badge': 'Upcoming Surge',
            'badge_class': 'bg-secondary text-white',
            'color_class': 'border-secondary bg-secondary-subtle text-secondary-emphasis',
            'message': f'Forecast models predict AQI rising to ~{upcoming_spike.get("aqi")} around {upcoming_spike.get("time")}.',
            'primary_action': 'Complete outdoor tasks before this surge and ensure air purifiers are powered on in advance.',
            'target_group': 'All family members'
        })

    return {
        'alerts': alerts,
        'is_severe': is_severe,
        'banner_color': banner_color,
        'family_precautions': family_precautions,
        'has_alerts': len(alerts) > 0
    }
