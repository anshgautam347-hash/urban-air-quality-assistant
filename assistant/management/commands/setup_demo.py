"""
Management command to populate realistic demo family profiles and saved locations.
Usage: python manage.py setup_demo
"""

from django.core.management.base import BaseCommand
from assistant.models import FamilyProfile, SavedLocation, UserPreference


class Command(BaseCommand):
    help = 'Seeds representative family profiles and saved smog locations for quick demonstration.'

    def handle(self, *args, **options):
        # 1. Family Profiles
        profiles_data = [
            {
                'session_key': '',
                'name': 'Leo (Child)',
                'age_group': 'child',
                'activity_preferences': 'outdoor_sports',
                'outdoor_habits': 'School bus at 7:30 AM, outdoor soccer practice at 4:30 PM',
                'has_respiratory_condition': True,
                'condition_details': 'Mild asthma and seasonal dust allergy'
            },
            {
                'session_key': '',
                'name': 'Grandma Elena',
                'age_group': 'senior',
                'activity_preferences': 'walking',
                'outdoor_habits': 'Morning community park walk at 6:45 AM',
                'has_respiratory_condition': True,
                'condition_details': 'Cardiovascular sensitivity / High BP'
            },
            {
                'session_key': '',
                'name': 'Sarah (Parent)',
                'age_group': 'adult',
                'activity_preferences': 'cycling',
                'outdoor_habits': 'Daily 12km cycling commute to tech campus at 8:30 AM',
                'has_respiratory_condition': False,
                'condition_details': ''
            }
        ]

        count_added = 0
        for p in profiles_data:
            if not FamilyProfile.objects.filter(name=p['name']).exists():
                FamilyProfile.objects.create(**p)
                count_added += 1

        # 2. Saved Locations
        locations_data = [
            {'city_name': 'New Delhi', 'country': 'India', 'latitude': 28.6139, 'longitude': 77.2090, 'is_default': True},
            {'city_name': 'Beijing', 'country': 'China', 'latitude': 39.9042, 'longitude': 116.4074, 'is_default': False},
            {'city_name': 'Lahore', 'country': 'Pakistan', 'latitude': 31.5204, 'longitude': 74.3587, 'is_default': False},
            {'city_name': 'London', 'country': 'United Kingdom', 'latitude': 51.5074, 'longitude': -0.1278, 'is_default': False},
        ]

        for loc in locations_data:
            if not SavedLocation.objects.filter(city_name=loc['city_name']).exists():
                SavedLocation.objects.create(session_key='', **loc)

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {count_added} demo family profiles and default locations.'))
