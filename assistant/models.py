"""
Models for Urban Air Quality Assistant:
Supports both authenticated users and guest sessions seamlessly.
Stores family profiles, preferences, saved locations, chat records, and air quality snapshots.
"""

from django.db import models
from django.contrib.auth.models import User


class FamilyProfile(models.Model):
    AGE_CHOICES = [
        ('infant', 'Infant / Toddler (0–4 yrs)'),
        ('child', 'Child / Teen (5–17 yrs)'),
        ('adult', 'Adult (18–64 yrs)'),
        ('senior', 'Senior / Elderly (65+ yrs)'),
    ]

    ACTIVITY_CHOICES = [
        ('school_commute', 'School / Daily Transit'),
        ('outdoor_sports', 'Outdoor Sports & Play'),
        ('walking', 'Morning / Evening Walking'),
        ('cycling', 'Cycling / Active Commute'),
        ('running', 'Running / High Cardio Exertion'),
        ('indoor_fitness', 'Indoor Fitness / Gym'),
        ('general', 'General Household / Casual'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='family_profiles')
    session_key = models.CharField(max_length=40, db_index=True, blank=True, help_text="Session key for guest access")
    name = models.CharField(max_length=100, help_text="Member nickname or display name")
    age_group = models.CharField(max_length=20, choices=AGE_CHOICES, default='adult')
    activity_preferences = models.CharField(max_length=30, choices=ACTIVITY_CHOICES, default='general')
    outdoor_habits = models.CharField(max_length=250, blank=True, default='Daily routine activities', help_text="Typical outdoor habits (e.g., 7 AM morning walk, cycling to office)")
    has_respiratory_condition = models.BooleanField(default=False, help_text="Indicate asthma, bronchitis, allergy or cardiac vulnerability")
    condition_details = models.CharField(max_length=200, blank=True, help_text="Details (e.g. Mild asthma, dust allergy)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.name} ({self.get_age_group_display()})"


class SavedLocation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='saved_locations')
    session_key = models.CharField(max_length=40, db_index=True, blank=True)
    city_name = models.CharField(max_length=150)
    country = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_default', 'city_name']

    def __str__(self):
        return f"{self.city_name}, {self.country} ({self.latitude}, {self.longitude})"


class UserPreference(models.Model):
    SCALE_CHOICES = [
        ('US_AQI', 'US EPA AQI (0–500 standard)'),
        ('EUROPEAN_AQI', 'European Air Quality Index (EAQI 1–5+ scale)'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='preferences')
    session_key = models.CharField(max_length=40, db_index=True, blank=True)
    preferred_aqi_scale = models.CharField(max_length=20, choices=SCALE_CHOICES, default='US_AQI')
    alert_threshold = models.IntegerField(default=150, help_text="AQI threshold triggering severe pollution alerts")
    notify_vulnerable_only = models.BooleanField(default=False)
    gemini_api_key_override = models.CharField(max_length=200, blank=True, help_text="Optional user-provided Gemini API key")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Preferences for {self.user.username if self.user else self.session_key}"


class AirQualitySnapshot(models.Model):
    city_name = models.CharField(max_length=150)
    latitude = models.FloatField()
    longitude = models.FloatField()
    us_aqi = models.IntegerField()
    european_aqi = models.IntegerField(null=True, blank=True)
    pm25 = models.FloatField(help_text="ug/m3")
    pm10 = models.FloatField(help_text="ug/m3")
    no2 = models.FloatField(null=True, blank=True)
    o3 = models.FloatField(null=True, blank=True)
    co = models.FloatField(null=True, blank=True)
    so2 = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.city_name} - AQI {self.us_aqi} at {self.timestamp}"


class AIChatHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='chat_history')
    session_key = models.CharField(max_length=40, db_index=True, blank=True)
    user_message = models.TextField()
    ai_response = models.TextField()
    model_source = models.CharField(max_length=100, default='Google Gemini')
    is_ai = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Chat ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
