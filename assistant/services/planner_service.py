"""
Routine Planner Service:
Analyzes hourly air quality forecasts, identifies optimal low-pollution windows,
suggests low-emission commuting modes, and creates family-personalized daily routines.
Always explicitly marks forecasts as model predictions and includes exposure disclaimers.
"""

from datetime import datetime


def generate_family_daily_routine(aqi_data, family_profiles=None):
    """
    Analyzes hourly forecast and synthesizes a tailored daily routine for the family.
    """
    forecast_items = aqi_data.get('forecast_items', [])
    current_aqi = aqi_data.get('us_aqi', 100)
    city_name = aqi_data.get('city_name', 'your city')

    # Find the lowest and highest pollution hours in the next 24h
    best_window = None
    worst_window = None
    min_aqi = 9999
    max_aqi = -1

    for item in forecast_items[:24]:
        val = item.get('aqi', 100)
        if val < min_aqi:
            min_aqi = val
            best_window = item
        if val > max_aqi:
            max_aqi = val
            worst_window = item

    # If forecast is empty, create safe defaults
    if not best_window:
        best_window = {'time': '02:00 PM', 'aqi': current_aqi, 'pm25': aqi_data.get('pm25', 40)}
        min_aqi = current_aqi
    if not worst_window:
        worst_window = {'time': '08:00 AM', 'aqi': current_aqi + 30, 'pm25': aqi_data.get('pm25', 60)}
        max_aqi = current_aqi + 30

    # Low-emission commute suggestions
    commute_guidance = [
        {
            'mode': 'Metro / Electric Rapid Transit',
            'rating': 'Recommended Choice',
            'badge': 'bg-success',
            'emission_impact': 'Zero direct tailpipe emissions',
            'exposure_risk': 'Low (air-conditioned, filtered underground stations)',
            'guidance': 'Avoid street-level traffic exhaust. Wear an N95 while walking to the station entrance.'
        },
        {
            'mode': 'Electric Bus / Shared Transit',
            'rating': 'Good Alternative',
            'badge': 'bg-info',
            'emission_impact': 'Reduces per-passenger emissions by 75%',
            'exposure_risk': 'Moderate (waiting at outdoor bus stops)',
            'guidance': 'Keep windows closed inside the bus. Step away from idling diesel trucks at intersections.'
        },
        {
            'mode': 'Carpool / Electric Vehicle',
            'rating': 'Acceptable with precautions',
            'badge': 'bg-secondary',
            'emission_impact': 'Reduces vehicle count on roads',
            'exposure_risk': 'Moderate (roadway congestion)',
            'guidance': 'Switch car ventilation strictly to Air Recirculation mode to keep out particulate matter.'
        },
        {
            'mode': 'Cycling / Walking',
            'rating': 'Not Recommended during Smog' if current_aqi > 150 else 'Feasible with N95 mask',
            'badge': 'bg-danger' if current_aqi > 150 else 'bg-warning',
            'emission_impact': 'Zero emissions',
            'exposure_risk': 'High during heavy smog (elevated respiration rate)',
            'guidance': 'Physical exertion while cycling increases lung intake of fine particulate matter by 3x to 5x.'
        }
    ]

    # Generate time slots
    slots = [
        {
            'time_range': '06:30 AM – 09:00 AM',
            'title': 'Morning Smog Peak & Waking',
            'status': 'High Exposure Risk',
            'status_class': 'badge-unhealthy',
            'general_action': 'Keep all windows tightly closed. Run bedroom air purifier on medium/high.',
            'child_action': 'No outdoor morning sports. Conduct indoor stretching or reading.',
            'elderly_action': 'Postpone morning walk completely. Sip warm water and remain in purified rooms.',
            'commute_action': 'Wear N95 masks for work/school departures; travel via metro or car on recirculation.'
        },
        {
            'time_range': '09:00 AM – 12:30 PM',
            'title': 'Mid-Morning Indoor Work & Study',
            'status': 'Moderate Smog Inversion',
            'status_class': 'badge-moderate',
            'general_action': 'Indoor humidity maintained between 40%–50%. Avoid vacuuming or dry dusting.',
            'child_action': 'School recess should be conducted in indoor classrooms.',
            'elderly_action': 'Indoor gentle yoga or seated mobility exercises.',
            'commute_action': 'Avoid non-essential street movement during morning traffic dispersal.'
        },
        {
            'time_range': '01:00 PM – 04:00 PM',
            'title': f'Optimal Activity Window (Projected AQI: ~{min_aqi})',
            'status': 'Relatively Lower Pollution',
            'status_class': 'badge-good',
            'general_action': 'Atmospheric boundary layer expands under solar heating, temporarily diluting smog. Safest period for essential outdoor errands.',
            'child_action': 'Supervised brief outdoor play (20-30 mins) if AQI < 150. Otherwise indoor play.',
            'elderly_action': 'A short 15-minute garden or balcony stroll is feasible if feeling comfortable.',
            'commute_action': 'Best time to run shopping errands or schedule meetings outside the house.'
        },
        {
            'time_range': '05:00 PM – 08:30 PM',
            'title': 'Evening Rush & Smog Re-accumulation',
            'status': 'High Exposure Risk',
            'status_class': 'badge-unhealthy',
            'general_action': 'Cooling air traps vehicular exhaust near the ground. Close doors and windows before sunset.',
            'child_action': 'Transition children indoors before dusk. Ensure hands and faces are washed after returning.',
            'elderly_action': 'Stay indoors; avoid evening outdoor strolls.',
            'commute_action': 'Wear N95 respirators. Avoid open-air two-wheelers in dense traffic bottlenecks.'
        },
        {
            'time_range': '08:30 PM – 10:30 PM',
            'title': 'Dinner & Indoor Air Cleansing',
            'status': 'Smog Peak',
            'status_class': 'badge-very-unhealthy' if max_aqi > 200 else 'badge-unhealthy',
            'general_action': 'Operate kitchen exhaust fan on maximum during cooking. Damp-mop high-traffic living areas.',
            'child_action': 'Wind-down quiet play in purified family room.',
            'elderly_action': 'Check blood pressure or respiratory comfort if asthma or COPD history exists.',
            'commute_action': 'All family members safely home.'
        },
        {
            'time_range': '10:30 PM – 06:30 AM',
            'title': 'Overnight Rest & Continuous Filtration',
            'status': 'Overnight Ground Inversion',
            'status_class': 'badge-moderate',
            'general_action': 'Air purifiers switched to Sleep/Quiet mode next to beds. Keep bedroom doors ajar for CO2 balance if purifiers are running.',
            'child_action': 'Deep sleep in purified room.',
            'elderly_action': 'Rescue inhaler and glass of water bedside.',
            'commute_action': 'Rest period.'
        }
    ]

    # Family-specific personalization notes
    personalized_notes = []
    if family_profiles:
        for member in family_profiles:
            age = member.get_age_group_display()
            cond = member.condition_details if member.has_respiratory_condition else "No known respiratory vulnerabilities"
            note = {
                'member_name': member.name,
                'age_group': age,
                'vulnerability': cond,
                'custom_guidance': get_member_specific_guidance(member, current_aqi, min_aqi)
            }
            personalized_notes.append(note)

    disclaimer = (
        "⚠️ Important Safety Clarification: Lower pollution periods (such as midday windows) offer "
        "comparatively lower exposure, but are NOT guaranteed to be 100% risk-free. All hourly values "
        "are meteorological model predictions subject to sudden atmospheric wind and inversion changes."
    )

    return {
        'city_name': city_name,
        'current_aqi': current_aqi,
        'min_aqi': min_aqi,
        'max_aqi': max_aqi,
        'best_window': best_window,
        'worst_window': worst_window,
        'commute_guidance': commute_guidance,
        'routine_slots': slots,
        'personalized_notes': personalized_notes,
        'disclaimer': disclaimer,
        'generated_at': datetime.utcnow().strftime('%b %d, %Y %I:%M %p UTC')
    }


def get_member_specific_guidance(member, current_aqi, min_aqi):
    """
    Computes precise tailored guidance for individual family profile members.
    """
    is_vulnerable = member.has_respiratory_condition
    age = member.age_group

    if age == 'infant':
        return "Infant airways are delicate. Eliminate all outdoor stroller walks when AQI > 100. Keep nursery purified 24/7."
    elif age == 'child':
        if current_aqi > 150:
            return "Keep strictly indoors today. Replace soccer/recess with indoor LEGO, puzzles, or creative art."
        elif current_aqi > 100:
            return f"Allow a maximum of 25 minutes outdoor play during the {min_aqi} AQI afternoon dip, followed by nasal hydration."
        else:
            return "Good for outdoor school sports and play. Encourage active recreation today."
    elif age == 'senior':
        if is_vulnerable or current_aqi > 150:
            return f"High cardiac/respiratory alert due to smog. Restrict movement to indoors. Inhaler/meds should be at hand."
        else:
            return "Afternoon walk feasible between 1:30 PM and 3:30 PM. Keep walking pace moderate."
    else:  # Adult
        if is_vulnerable:
            return "Work from home if feasible. If commuting, N95 respirator is essential."
        elif current_aqi > 150:
            return "Move daily workout indoors (gym, treadmill, HIIT). Avoid outdoor jogging along motorways."
        else:
            return "Outdoor exercise permissible. Prefer green parks over roadside running."
