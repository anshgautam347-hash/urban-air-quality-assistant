"""
Automated Test Suite for Urban Air Quality Assistant:
Covers AQI calculation, categories, Open-Meteo data processing, family profiles,
routine planner, indoor recommendations, alert evaluation, AI fallback, and web routes.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from assistant.models import FamilyProfile, UserPreference, SavedLocation, AIChatHistory
from assistant.services import aqi_service, gemini_service, planner_service, indoor_service, alert_service


class AQICalculationTests(TestCase):
    def test_pm25_to_us_aqi_good(self):
        # 0 - 12 ug/m3 -> AQI 0 - 50
        aqi = aqi_service.calculate_us_aqi_from_pm25(9.0)
        self.assertGreaterEqual(aqi, 0)
        self.assertLessEqual(aqi, 50)

    def test_pm25_to_us_aqi_moderate(self):
        # 12.1 - 35.4 ug/m3 -> AQI 51 - 100
        aqi = aqi_service.calculate_us_aqi_from_pm25(25.0)
        self.assertGreaterEqual(aqi, 51)
        self.assertLessEqual(aqi, 100)

    def test_pm25_to_us_aqi_unhealthy_sensitive(self):
        # 35.5 - 55.4 ug/m3 -> AQI 101 - 150
        aqi = aqi_service.calculate_us_aqi_from_pm25(45.0)
        self.assertGreaterEqual(aqi, 101)
        self.assertLessEqual(aqi, 150)

    def test_pm25_to_us_aqi_unhealthy(self):
        # 55.5 - 150.4 ug/m3 -> AQI 151 - 200
        aqi = aqi_service.calculate_us_aqi_from_pm25(90.0)
        self.assertGreaterEqual(aqi, 151)
        self.assertLessEqual(aqi, 200)

    def test_pm25_to_us_aqi_hazardous(self):
        # > 350 ug/m3 -> AQI > 300
        aqi = aqi_service.calculate_us_aqi_from_pm25(400.0)
        self.assertGreaterEqual(aqi, 401)

    def test_pm10_to_us_aqi(self):
        aqi = aqi_service.calculate_us_aqi_from_pm10(100)
        self.assertGreaterEqual(aqi, 51)
        self.assertLessEqual(aqi, 100)

    def test_us_aqi_category_mapping(self):
        cat_good = aqi_service.get_us_aqi_category(35)
        self.assertEqual(cat_good['level'], 'Good')
        self.assertFalse(cat_good['is_severe'])

        cat_unhealthy = aqi_service.get_us_aqi_category(165)
        self.assertEqual(cat_unhealthy['level'], 'Unhealthy')
        self.assertTrue(cat_unhealthy['is_severe'])

        cat_hazardous = aqi_service.get_us_aqi_category(420)
        self.assertEqual(cat_hazardous['level'], 'Hazardous')
        self.assertTrue(cat_hazardous['is_severe'])

    def test_european_aqi_category(self):
        e1 = aqi_service.get_european_aqi_category(1)
        self.assertEqual(e1['level'], 'Very Good')
        e5 = aqi_service.get_european_aqi_category(5)
        self.assertEqual(e5['level'], 'Very Poor')


class AirQualityServiceDataTests(TestCase):
    def test_fallback_air_data_generation(self):
        data = aqi_service.generate_fallback_air_data(28.6139, 77.2090)
        self.assertIn('current', data)
        self.assertIn('hourly', data)
        self.assertGreater(data['current']['us_aqi'], 50)
        self.assertGreater(len(data['hourly']['time']), 50)

    def test_process_air_quality_payload(self):
        mock_raw = aqi_service.generate_fallback_air_data(28.6139, 77.2090)
        processed = aqi_service.process_air_quality_payload(
            mock_raw, "New Delhi", 28.6139, 77.2090, "Test Source", False, "US_AQI"
        )
        self.assertEqual(processed['city_name'], "New Delhi")
        self.assertIn('pollutants', processed)
        self.assertEqual(len(processed['pollutants']), 6)
        self.assertIn('forecast_items', processed)
        self.assertIn('historical_times', processed)


class FamilyProfileAndRoutineTests(TestCase):
    def setUp(self):
        self.profile_child = FamilyProfile.objects.create(
            session_key='test-session-123',
            name='Maya',
            age_group='child',
            activity_preferences='outdoor_sports',
            has_respiratory_condition=True,
            condition_details='Mild asthma'
        )
        self.profile_senior = FamilyProfile.objects.create(
            session_key='test-session-123',
            name='Arthur',
            age_group='senior',
            activity_preferences='walking',
            has_respiratory_condition=False
        )

    def test_member_guidance_for_child_with_asthma(self):
        guidance = planner_service.get_member_specific_guidance(self.profile_child, current_aqi=180, min_aqi=130)
        self.assertIn('indoors', guidance.lower())

    def test_daily_routine_generation(self):
        mock_raw = aqi_service.generate_fallback_air_data(28.6139, 77.2090)
        aqi_data = aqi_service.process_air_quality_payload(mock_raw, "Delhi", 28.61, 77.20, "Test", False)
        profiles = [self.profile_child, self.profile_senior]

        routine = planner_service.generate_family_daily_routine(aqi_data, profiles)
        self.assertIn('routine_slots', routine)
        self.assertIn('commute_guidance', routine)
        self.assertIn('personalized_notes', routine)
        self.assertEqual(len(routine['personalized_notes']), 2)
        self.assertIn('Safety Clarification', routine['disclaimer'])


class IndoorAndAlertServiceTests(TestCase):
    def test_indoor_air_strategy_high_smog(self):
        strategy = indoor_service.get_indoor_air_strategy(outdoor_aqi=240, pm25_val=120.0)
        self.assertEqual(strategy['ventilation_class'], 'danger')
        self.assertIn('purifier_guide', strategy)
        self.assertIn('indoor_hacks', strategy)
        self.assertIn('room_checklist', strategy)
        self.assertIn('sensor_notice', strategy)

    def test_indoor_air_strategy_clean(self):
        strategy = indoor_service.get_indoor_air_strategy(outdoor_aqi=40, pm25_val=9.0)
        self.assertEqual(strategy['ventilation_class'], 'success')

    def test_evaluate_pollution_alerts_hazardous(self):
        mock_aqi_data = {'us_aqi': 320, 'pm25': 260.0, 'city_name': 'Delhi', 'forecast_items': []}
        alerts_res = alert_service.evaluate_pollution_alerts(mock_aqi_data, user_threshold=150)
        self.assertTrue(alerts_res['is_severe'])
        self.assertGreater(len(alerts_res['alerts']), 0)
        self.assertIn('Emergency', alerts_res['alerts'][0]['title'])


class GeminiAIFallbackTests(TestCase):
    def test_rule_based_fallback_child_safety(self):
        aqi_context = {
            'city_name': 'Delhi',
            'us_aqi': 190,
            'category': {'level': 'Unhealthy'},
            'pm25': 110
        }
        res = gemini_service.generate_rule_based_response(
            "Is it safe to take my child outside right now?",
            aqi_context
        )
        self.assertTrue(res['success'])
        self.assertFalse(res['is_ai'])
        self.assertIn('indoors', res['reply'].lower())
        self.assertIn('Health & Safety Notice', res['reply'])

    def test_rule_based_fallback_indoor_exposure(self):
        aqi_context = {
            'city_name': 'Beijing',
            'us_aqi': 160,
            'category': {'level': 'Unhealthy'},
            'pm25': 85
        }
        res = gemini_service.generate_rule_based_response(
            "How can I reduce pollution exposure at home with indoor hacks?",
            aqi_context
        )
        self.assertTrue(res['success'])
        self.assertIn('HEPA', res['reply'])
        self.assertIn('Wet Mopping', res['reply'])


class WebRoutesAndViewsTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_dashboard_route(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Air Quality Index')
        self.assertContains(response, 'PM2.5')

    def test_air_quality_details_route(self):
        response = self.client.get(reverse('air_quality_details'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Concentration vs. AQI')

    def test_family_profiles_route(self):
        response = self.client.get(reverse('family_profiles'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Personalized Family Profiles')

    def test_routine_planner_route(self):
        response = self.client.get(reverse('routine_planner'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Smart Daily Routine Planner')

    def test_indoor_air_route(self):
        response = self.client.get(reverse('indoor_air'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Indoor Air Quality Assistant')

    def test_ai_chat_route(self):
        response = self.client.get(reverse('ai_chat'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gemini AI Air Quality Assistant')

    def test_alerts_route(self):
        response = self.client.get(reverse('alerts'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Smart Pollution Alerts')

    def test_historical_trends_route(self):
        response = self.client.get(reverse('historical_trends'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Historical Air Quality')

    def test_settings_route(self):
        response = self.client.get(reverse('settings'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Settings & Preferences')

    def test_ai_chat_api(self):
        response = self.client.post(
            reverse('api_ai_chat'),
            data={'message': 'What are the best low-emission commuting alternatives?'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('reply', data)

    def test_search_locations_api(self):
        response = self.client.get(reverse('api_search_locations') + '?q=London')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('results', data)

    def test_set_active_location_api(self):
        response = self.client.post(
            reverse('api_set_location'),
            data={'city_name': 'London', 'latitude': 51.5074, 'longitude': -0.1278},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session['active_city'], 'London')
