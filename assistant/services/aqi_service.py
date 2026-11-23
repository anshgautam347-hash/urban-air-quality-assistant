"""
Air Quality Service: Open-Meteo integration, AQI calculation, and pollutant evaluation.
Clearly distinguishes between pollutant concentrations (ug/m3) and AQI index values.
"""

import logging
import requests
from django.core.cache import cache
from datetime import datetime

logger = logging.getLogger(__name__)

# US EPA Breakpoints for PM2.5 (ug/m3 -> AQI 0-500)
EPA_PM25_BREAKPOINTS = [
    (0.0, 12.0, 0, 50),
    (12.1, 35.4, 51, 100),
    (35.5, 55.4, 101, 150),
    (55.5, 150.4, 151, 200),
    (150.5, 250.4, 201, 300),
    (250.5, 350.4, 301, 400),
    (350.5, 500.4, 401, 500),
]

# US EPA Breakpoints for PM10 (ug/m3 -> AQI 0-500)
EPA_PM10_BREAKPOINTS = [
    (0, 54, 0, 50),
    (55, 154, 51, 100),
    (155, 254, 101, 150),
    (255, 354, 151, 200),
    (355, 424, 201, 300),
    (425, 504, 301, 400),
    (505, 604, 401, 500),
]


def calculate_us_aqi_from_pm25(pm25_val):
    """
    Calculate US EPA AQI from PM2.5 concentration (ug/m3)
    using standard piecewise linear interpolation formula:
    I = [(I_hi - I_lo) / (C_hi - C_lo)] * (C - C_lo) + I_lo
    """
    if pm25_val is None or pm25_val < 0:
        return 0
    c = round(float(pm25_val), 1)

    for c_low, c_high, i_low, i_high in EPA_PM25_BREAKPOINTS:
        if c_low <= c <= c_high:
            aqi = ((i_high - i_low) / (c_high - c_low)) * (c - c_low) + i_low
            return int(round(aqi))

    if c > 500.4:
        return 500
    return 0


def calculate_us_aqi_from_pm10(pm10_val):
    """
    Calculate US EPA AQI from PM10 concentration (ug/m3)
    """
    if pm10_val is None or pm10_val < 0:
        return 0
    c = int(round(float(pm10_val)))

    for c_low, c_high, i_low, i_high in EPA_PM10_BREAKPOINTS:
        if c_low <= c <= c_high:
            aqi = ((i_high - i_low) / (c_high - c_low)) * (c - c_low) + i_low
            return int(round(aqi))

    if c > 604:
        return 500
    return 0


def get_us_aqi_category(aqi_val):
    """
    Returns US AQI severity categorization, color codes, health summary and vulnerable alerts.
    """
    try:
        val = int(aqi_val or 0)
    except (ValueError, TypeError):
        val = 0

    if val <= 50:
        return {
            'level': 'Good',
            'severity': 'low',
            'color': '#10b981',       # Emerald green
            'bg_class': 'bg-success',
            'badge_class': 'badge-good',
            'text_color': 'text-success',
            'description': 'Air quality is satisfactory and poses little or no risk.',
            'health_impact': 'Air pollution poses little or no risk to all groups.',
            'outdoor_advice': 'Ideal for all outdoor activities, workouts and child play.',
            'ventilation_advice': 'Open windows freely to air out indoor spaces.',
            'alert_level': 'info',
            'is_severe': False
        }
    elif val <= 100:
        return {
            'level': 'Moderate',
            'severity': 'moderate',
            'color': '#f59e0b',       # Amber
            'bg_class': 'bg-warning',
            'badge_class': 'badge-moderate',
            'text_color': 'text-warning',
            'description': 'Air quality is acceptable; some pollutants may pose a moderate concern for sensitive individuals.',
            'health_impact': 'Unusually sensitive people should consider reducing prolonged or heavy outdoor exertion.',
            'outdoor_advice': 'General public can enjoy outdoors; sensitive children and adults should monitor symptoms.',
            'ventilation_advice': 'Ventilation is generally fine during afternoon hours.',
            'alert_level': 'warning',
            'is_severe': False
        }
    elif val <= 150:
        return {
            'level': 'Unhealthy for Sensitive Groups',
            'severity': 'unhealthy_sensitive',
            'color': '#f97316',       # Orange
            'bg_class': 'bg-orange',
            'badge_class': 'badge-sensitive',
            'text_color': 'text-orange',
            'description': 'Members of sensitive groups may experience health effects. General public is less likely to be affected.',
            'health_impact': 'Children, the elderly and people with respiratory or heart conditions are at greater risk.',
            'outdoor_advice': 'Children and seniors should reduce strenuous outdoor activities; shift workouts indoors.',
            'ventilation_advice': 'Keep windows closed during morning/evening smog peaks. Run indoor air purifiers.',
            'alert_level': 'warning',
            'is_severe': True
        }
    elif val <= 200:
        return {
            'level': 'Unhealthy',
            'severity': 'unhealthy',
            'color': '#ef4444',       # Red
            'bg_class': 'bg-danger',
            'badge_class': 'badge-unhealthy',
            'text_color': 'text-danger',
            'description': 'Everyone may begin to experience health effects; members of sensitive groups may experience more serious health effects.',
            'health_impact': 'Irritation in eyes, throat, and airway. Increased respiratory symptoms in vulnerable persons.',
            'outdoor_advice': 'Avoid prolonged outdoor exertion. Wear well-fitted N95 masks when stepping out.',
            'ventilation_advice': 'Keep windows firmly closed. Keep HEPA purifiers running on medium/high speed.',
            'alert_level': 'danger',
            'is_severe': True
        }
    elif val <= 300:
        return {
            'level': 'Very Unhealthy',
            'severity': 'very_unhealthy',
            'color': '#8b5cf6',       # Purple
            'bg_class': 'bg-purple',
            'badge_class': 'badge-very-unhealthy',
            'text_color': 'text-purple',
            'description': 'Health alert: the risk of health effects is increased for everyone.',
            'health_impact': 'Significant aggravation of heart and lung conditions; widespread respiratory discomfort.',
            'outdoor_advice': 'Avoid all outdoor physical activity. Keep children and seniors strictly indoors.',
            'ventilation_advice': 'Strictly seal windows and doors. Wet mop floors; operate air purifiers continuously.',
            'alert_level': 'danger',
            'is_severe': True
        }
    else:
        return {
            'level': 'Hazardous',
            'severity': 'hazardous',
            'color': '#831843',       # Maroon / Dark Burgundy
            'bg_class': 'bg-dark',
            'badge_class': 'badge-hazardous',
            'text_color': 'text-danger',
            'description': 'Health warning of emergency conditions: everyone is more likely to be severely affected.',
            'health_impact': 'Severe risk of respiratory and cardiovascular events. Extreme smog emergency.',
            'outdoor_advice': 'Remain indoors in clean rooms. Eliminate all outdoor exposure. N95/FFP2 mandatory if transit unavoidable.',
            'ventilation_advice': 'Zero natural ventilation. Turn purifier to turbo. Damp mop surfaces to trap indoor dust.',
            'alert_level': 'danger',
            'is_severe': True
        }


def get_european_aqi_category(eaqi_val):
    """
    Returns European Air Quality Index (EAQI) category (1 to 5+ scale)
    """
    try:
        val = int(eaqi_val or 1)
    except (ValueError, TypeError):
        val = 1

    mapping = {
        1: {'level': 'Very Good', 'color': '#10b981'},
        2: {'level': 'Good', 'color': '#34d399'},
        3: {'level': 'Medium', 'color': '#f59e0b'},
        4: {'level': 'Poor', 'color': '#ef4444'},
        5: {'level': 'Very Poor', 'color': '#8b5cf6'},
        6: {'level': 'Extremely Poor', 'color': '#831843'}
    }
    return mapping.get(val, {'level': 'Unknown', 'color': '#6b7280'})


def search_locations(query):
    """
    Geocodes city name via Open-Meteo Geocoding API with caching and error handling.
    """
    if not query or len(query.strip()) < 2:
        return []

    cache_key = f"geo_{query.strip().lower()}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        'name': query.strip(),
        'count': 6,
        'language': 'en',
        'format': 'json'
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        results = []
        for item in data.get('results', []):
            name = item.get('name')
            admin1 = item.get('admin1', '')
            country = item.get('country', '')
            display_parts = [name]
            if admin1 and admin1 != name:
                display_parts.append(admin1)
            if country:
                display_parts.append(country)

            results.append({
                'id': item.get('id'),
                'name': name,
                'display_name': ', '.join(display_parts),
                'country': country,
                'country_code': item.get('country_code', ''),
                'latitude': round(float(item.get('latitude')), 4),
                'longitude': round(float(item.get('longitude')), 4),
                'timezone': item.get('timezone', 'UTC'),
                'population': item.get('population', 0),
            })
        cache.set(cache_key, results, timeout=86400)  # Cache geocoding for 24h
        return results
    except Exception as e:
        logger.warning(f"Geocoding API error for query '{query}': {e}")
        # Provide fallback curated cities if network fails
        curated = [
            {'name': 'New Delhi', 'display_name': 'New Delhi, Delhi, India', 'country': 'India', 'latitude': 28.6139, 'longitude': 77.2090},
            {'name': 'Beijing', 'display_name': 'Beijing, China', 'country': 'China', 'latitude': 39.9042, 'longitude': 116.4074},
            {'name': 'London', 'display_name': 'London, England, United Kingdom', 'country': 'United Kingdom', 'latitude': 51.5074, 'longitude': -0.1278},
            {'name': 'New York', 'display_name': 'New York, NY, United States', 'country': 'United States', 'latitude': 40.7128, 'longitude': -74.0060},
            {'name': 'Lahore', 'display_name': 'Lahore, Punjab, Pakistan', 'country': 'Pakistan', 'latitude': 31.5204, 'longitude': 74.3587},
            {'name': 'Paris', 'display_name': 'Paris, France', 'country': 'France', 'latitude': 48.8566, 'longitude': 2.3522},
        ]
        q_lower = query.lower()
        matched = [c for c in curated if q_lower in c['name'].lower() or q_lower in c['display_name'].lower()]
        return matched if matched else curated[:3]


def get_air_quality_data(latitude, longitude, city_name="Current Location", scale="US_AQI"):
    """
    Fetches real-time & hourly air quality from Open-Meteo Air Quality API.
    Includes caching (30m), graceful error handling, and robust data synthesis.
    """
    cache_key = f"air_quality_{round(latitude, 3)}_{round(longitude, 3)}"
    cached = cache.get(cache_key)
    if cached is not None:
        # Update scale-specific views if needed and return
        cached['requested_scale'] = scale
        return cached

    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        'latitude': latitude,
        'longitude': longitude,
        'current': 'us_aqi,european_aqi,pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone',
        'hourly': 'pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone,us_aqi,european_aqi',
        'past_days': 7,
        'forecast_days': 2,
        'timezone': 'auto'
    }

    raw_data = None
    source = "Open-Meteo Air Quality API (Live Measurement & CAMS/Copernicus Ensemble)"
    is_live = True

    try:
        response = requests.get(url, params=params, timeout=8)
        response.raise_for_status()
        raw_data = response.json()
    except Exception as e:
        logger.error(f"Error fetching air quality data from Open-Meteo for ({latitude}, {longitude}): {e}")
        is_live = False
        source = "Simulated Winter Smog Dataset (API Offline Fallback)"
        raw_data = generate_fallback_air_data(latitude, longitude)

    processed = process_air_quality_payload(raw_data, city_name, latitude, longitude, source, is_live, scale)
    if is_live:
        cache.set(cache_key, processed, timeout=1800)  # 30 minutes

    return processed


def process_air_quality_payload(data, city_name, latitude, longitude, source, is_live, scale="US_AQI"):
    """
    Parses Open-Meteo payload into structured, display-ready data structures with unit documentation.
    """
    current_raw = data.get('current', {})
    hourly_raw = data.get('hourly', {})

    # Extract Current Pollutant Concentrations (ug/m3 or mg/m3)
    pm25 = current_raw.get('pm2_5')
    pm10 = current_raw.get('pm10')
    no2 = current_raw.get('nitrogen_dioxide')
    o3 = current_raw.get('ozone')
    co = current_raw.get('carbon_monoxide')
    so2 = current_raw.get('sulphur_dioxide')

    # AQI index readings
    us_aqi = current_raw.get('us_aqi')
    european_aqi = current_raw.get('european_aqi')

    # If US AQI is missing from API, compute mathematically from PM2.5 / PM10
    if us_aqi is None and pm25 is not None:
        us_aqi = calculate_us_aqi_from_pm25(pm25)

    us_aqi = us_aqi if us_aqi is not None else 85
    category_info = get_us_aqi_category(us_aqi)

    # European AQI category
    european_info = get_european_aqi_category(european_aqi)

    # Format timestamp
    time_str = current_raw.get('time', datetime.utcnow().strftime('%Y-%m-%dT%H:00'))
    try:
        parsed_time = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        formatted_time = parsed_time.strftime('%b %d, %Y %I:%M %p')
    except Exception:
        formatted_time = time_str

    # Process Hourly Data for Forecast (Next 24h) and Historical (Past 7 days)
    hourly_times = hourly_raw.get('time', [])
    hourly_pm25 = hourly_raw.get('pm2_5', [])
    hourly_pm10 = hourly_raw.get('pm10', [])
    hourly_no2 = hourly_raw.get('nitrogen_dioxide', [])
    hourly_o3 = hourly_raw.get('ozone', [])
    hourly_co = hourly_raw.get('carbon_monoxide', [])
    hourly_so2 = hourly_raw.get('sulphur_dioxide', [])
    hourly_us_aqi = hourly_raw.get('us_aqi', [])

    # If hourly_us_aqi is missing values, compute from PM2.5
    computed_hourly_aqi = []
    for idx, aqi in enumerate(hourly_us_aqi):
        if aqi is not None:
            computed_hourly_aqi.append(int(aqi))
        elif idx < len(hourly_pm25) and hourly_pm25[idx] is not None:
            computed_hourly_aqi.append(calculate_us_aqi_from_pm25(hourly_pm25[idx]))
        else:
            computed_hourly_aqi.append(50)

    # Find the current hour index
    current_iso_hour = time_str[:13] if time_str else ""
    current_index = 0
    for idx, t in enumerate(hourly_times):
        if t.startswith(current_iso_hour):
            current_index = idx
            break
    if current_index == 0 and len(hourly_times) > 24:
        # Default to the 7-day past marker (approx 7*24 = 168)
        current_index = max(0, len(hourly_times) - 48)

    # Extract 24-Hour Forecast (from current index forward)
    forecast_times = []
    forecast_aqi = []
    forecast_pm25 = []
    forecast_pm10 = []
    forecast_items = []

    f_end = min(len(hourly_times), current_index + 24)
    for i in range(current_index, f_end):
        t_raw = hourly_times[i]
        try:
            dt = datetime.fromisoformat(t_raw.replace('Z', '+00:00'))
            label = dt.strftime('%I %p')
            full_label = dt.strftime('%a %I %p')
        except Exception:
            label = t_raw[-5:]
            full_label = t_raw

        aqi_val = computed_hourly_aqi[i] if i < len(computed_hourly_aqi) else 50
        pm25_val = round(hourly_pm25[i], 1) if (i < len(hourly_pm25) and hourly_pm25[i] is not None) else 25.0
        pm10_val = round(hourly_pm10[i], 1) if (i < len(hourly_pm10) and hourly_pm10[i] is not None) else 45.0

        forecast_times.append(label)
        forecast_aqi.append(aqi_val)
        forecast_pm25.append(pm25_val)
        forecast_pm10.append(pm10_val)

        forecast_items.append({
            'time': label,
            'full_time': full_label,
            'raw_time': t_raw,
            'aqi': aqi_val,
            'pm25': pm25_val,
            'pm10': pm10_val,
            'category': get_us_aqi_category(aqi_val),
        })

    # Extract Historical Trend (Past 7 Days, daily averaged or 6-hour sampled)
    historical_times = []
    historical_aqi = []
    historical_pm25 = []
    historical_pm10 = []
    historical_no2 = []

    # Take step of 6 hours for clean 7-day line chart
    hist_end = min(current_index, len(hourly_times))
    hist_start = max(0, current_index - (7 * 24))

    for i in range(hist_start, hist_end, 4):  # Every 4 hours for good granularity
        t_raw = hourly_times[i]
        try:
            dt = datetime.fromisoformat(t_raw.replace('Z', '+00:00'))
            label = dt.strftime('%b %d %H:%M')
        except Exception:
            label = t_raw

        aqi_val = computed_hourly_aqi[i] if i < len(computed_hourly_aqi) else 60
        pm25_val = round(hourly_pm25[i], 1) if (i < len(hourly_pm25) and hourly_pm25[i] is not None) else 30.0
        pm10_val = round(hourly_pm10[i], 1) if (i < len(hourly_pm10) and hourly_pm10[i] is not None) else 55.0
        no2_val = round(hourly_no2[i], 1) if (i < len(hourly_no2) and hourly_no2[i] is not None) else 20.0

        historical_times.append(label)
        historical_aqi.append(aqi_val)
        historical_pm25.append(pm25_val)
        historical_pm10.append(pm10_val)
        historical_no2.append(no2_val)

    # Detailed pollutant metrics with reference limits and health guidance
    pollutants = [
        {
            'name': 'PM2.5',
            'full_name': 'Fine Particulate Matter (<= 2.5 um)',
            'value': round(pm25, 1) if pm25 is not None else 0.0,
            'unit': 'ug/m3',
            'who_limit': 15.0,  # 24h WHO guideline
            'ratio_to_who': round((pm25 or 0) / 15.0, 1) if pm25 else 0.0,
            'source': 'Vehicle exhaust, biomass burning, winter smog inversion, secondary sulfates/nitrates',
            'health_effect': 'Penetrates deep into alveolar air sacs and blood circulation, worsening asthma and heart disease.',
            'status': 'Elevated' if (pm25 or 0) > 35 else 'Normal' if (pm25 or 0) <= 15 else 'Moderate',
            'status_class': 'text-danger' if (pm25 or 0) > 35 else 'text-success' if (pm25 or 0) <= 15 else 'text-warning'
        },
        {
            'name': 'PM10',
            'full_name': 'Inhalable Particulate Matter (<= 10 um)',
            'value': round(pm10, 1) if pm10 is not None else 0.0,
            'unit': 'ug/m3',
            'who_limit': 45.0,  # 24h WHO guideline
            'ratio_to_who': round((pm10 or 0) / 45.0, 1) if pm10 else 0.0,
            'source': 'Road dust, construction, unpaved surfaces, windblown soil, agricultural residue',
            'health_effect': 'Deposits in upper respiratory tract, inducing throat irritation, coughing and wheezing.',
            'status': 'Elevated' if (pm10 or 0) > 100 else 'Normal' if (pm10 or 0) <= 45 else 'Moderate',
            'status_class': 'text-danger' if (pm10 or 0) > 100 else 'text-success' if (pm10 or 0) <= 45 else 'text-warning'
        },
        {
            'name': 'NO2',
            'full_name': 'Nitrogen Dioxide',
            'value': round(no2, 1) if no2 is not None else 0.0,
            'unit': 'ug/m3',
            'who_limit': 25.0,
            'ratio_to_who': round((no2 or 0) / 25.0, 1) if no2 else 0.0,
            'source': 'Diesel vehicle emissions, power plants, gas stoves without range hoods',
            'health_effect': 'Airway inflammation, exacerbation of pediatric asthma, reduced lung function.',
            'status': 'Elevated' if (no2 or 0) > 50 else 'Normal' if (no2 or 0) <= 25 else 'Moderate',
            'status_class': 'text-danger' if (no2 or 0) > 50 else 'text-success' if (no2 or 0) <= 25 else 'text-warning'
        },
        {
            'name': 'O3',
            'full_name': 'Ground-Level Ozone',
            'value': round(o3, 1) if o3 is not None else 0.0,
            'unit': 'ug/m3',
            'who_limit': 100.0,
            'ratio_to_who': round((o3 or 0) / 100.0, 1) if o3 else 0.0,
            'source': 'Photochemical reactions between NOx and VOCs under intense sunlight',
            'health_effect': 'Chest tightness, airway spasms during outdoor exercise, diminished lung capacity.',
            'status': 'Elevated' if (o3 or 0) > 120 else 'Normal' if (o3 or 0) <= 70 else 'Moderate',
            'status_class': 'text-danger' if (o3 or 0) > 120 else 'text-success' if (o3 or 0) <= 70 else 'text-warning'
        },
        {
            'name': 'CO',
            'full_name': 'Carbon Monoxide',
            'value': round(co, 1) if co is not None else 0.0,
            'unit': 'ug/m3',
            'who_limit': 4000.0,
            'ratio_to_who': round((co or 0) / 4000.0, 2) if co else 0.0,
            'source': 'Incomplete combustion in vehicles, faulty heaters, tobacco smoke, biomass',
            'health_effect': 'Binds to hemoglobin forming carboxyhemoglobin, impairing oxygen delivery to brain and heart.',
            'status': 'Elevated' if (co or 0) > 4000 else 'Normal',
            'status_class': 'text-danger' if (co or 0) > 4000 else 'text-success'
        },
        {
            'name': 'SO2',
            'full_name': 'Sulphur Dioxide',
            'value': round(so2, 1) if so2 is not None else 0.0,
            'unit': 'ug/m3',
            'who_limit': 40.0,
            'ratio_to_who': round((so2 or 0) / 40.0, 1) if so2 else 0.0,
            'source': 'Coal combustion, industrial smelters, high-sulfur diesel fuel',
            'health_effect': 'Bronchoconstriction, severe eye and throat irritation, exacerbates chronic bronchitis.',
            'status': 'Elevated' if (so2 or 0) > 40 else 'Normal',
            'status_class': 'text-danger' if (so2 or 0) > 40 else 'text-success'
        }
    ]

    return {
        'city_name': city_name,
        'latitude': latitude,
        'longitude': longitude,
        'timestamp': formatted_time,
        'raw_time': time_str,
        'data_source': source,
        'is_live': is_live,
        'requested_scale': scale,

        # Primary Indicators
        'us_aqi': int(us_aqi),
        'european_aqi': european_aqi,
        'european_category': european_info,
        'category': category_info,

        # Pollutant concentrations
        'pm25': round(pm25, 1) if pm25 is not None else 0.0,
        'pm10': round(pm10, 1) if pm10 is not None else 0.0,
        'no2': round(no2, 1) if no2 is not None else 0.0,
        'o3': round(o3, 1) if o3 is not None else 0.0,
        'co': round(co, 1) if co is not None else 0.0,
        'so2': round(so2, 1) if so2 is not None else 0.0,
        'pollutants': pollutants,

        # Forecast Charts Data
        'forecast_times': forecast_times,
        'forecast_aqi': forecast_aqi,
        'forecast_pm25': forecast_pm25,
        'forecast_pm10': forecast_pm10,
        'forecast_items': forecast_items,

        # Historical Charts Data
        'historical_times': historical_times,
        'historical_aqi': historical_aqi,
        'historical_pm25': historical_pm25,
        'historical_pm10': historical_pm10,
        'historical_no2': historical_no2,
    }


def generate_fallback_air_data(latitude, longitude):
    """
    Generates realistic, physically consistent air quality data for fallback/offline scenarios.
    Reflects typical severe winter smog diurnal inversion patterns (high morning/evening, moderate mid-day).
    """
    now = datetime.utcnow()
    times = []
    pm25_series = []
    pm10_series = []
    no2_series = []
    o3_series = []
    co_series = []
    so2_series = []
    us_aqi_series = []
    eaqi_series = []

    # Generate 9 days of hourly data (7 past + 2 forecast = 216 hours)
    start_hour = - (7 * 24)
    end_hour = 2 * 24

    for offset in range(start_hour, end_hour):
        h = (now.hour + offset) % 24
        # Winter temperature inversion peaks around 6 AM - 9 AM and 8 PM - 11 PM
        # Mid-day boundary layer mixing creates lower smog 1 PM - 4 PM
        if 6 <= h <= 9 or 20 <= h <= 23:
            diurnal_factor = 1.45
        elif 13 <= h <= 16:
            diurnal_factor = 0.65
        else:
            diurnal_factor = 1.0

        base_pm25 = 115.0 * diurnal_factor
        base_pm10 = 195.0 * diurnal_factor
        base_no2 = 48.0 * diurnal_factor
        base_o3 = 25.0 * (1.8 if 12 <= h <= 15 else 0.5)
        base_co = 1400.0 * diurnal_factor
        base_so2 = 18.0

        aqi = calculate_us_aqi_from_pm25(base_pm25)

        # Approximate ISO timestamp
        dt_hour = datetime(now.year, now.month, now.day, h, 0)
        times.append(dt_hour.isoformat())
        pm25_series.append(round(base_pm25, 1))
        pm10_series.append(round(base_pm10, 1))
        no2_series.append(round(base_no2, 1))
        o3_series.append(round(base_o3, 1))
        co_series.append(round(base_co, 1))
        so2_series.append(round(base_so2, 1))
        us_aqi_series.append(aqi)
        eaqi_series.append(5 if base_pm25 > 75 else 4)

    current_pm25 = 142.0
    current_pm10 = 230.0
    current_aqi = calculate_us_aqi_from_pm25(current_pm25)

    return {
        'current': {
            'time': now.strftime('%Y-%m-%dT%H:00'),
            'us_aqi': current_aqi,
            'european_aqi': 5,
            'pm2_5': current_pm25,
            'pm10': current_pm10,
            'nitrogen_dioxide': 54.0,
            'ozone': 28.0,
            'carbon_monoxide': 1650.0,
            'sulphur_dioxide': 19.5,
        },
        'hourly': {
            'time': times,
            'pm2_5': pm25_series,
            'pm10': pm10_series,
            'nitrogen_dioxide': no2_series,
            'ozone': o3_series,
            'carbon_monoxide': co_series,
            'sulphur_dioxide': so2_series,
            'us_aqi': us_aqi_series,
            'european_aqi': eaqi_series,
        }
    }
