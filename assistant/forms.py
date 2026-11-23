"""
Forms for Urban Air Quality Assistant:
Family profiles, preferences, saved locations, and user authentication.
"""

from django import forms
from django.contrib.auth.models import User
from .models import FamilyProfile, UserPreference, SavedLocation


class FamilyProfileForm(forms.ModelForm):
    class Meta:
        model = FamilyProfile
        fields = [
            'name',
            'age_group',
            'activity_preferences',
            'outdoor_habits',
            'has_respiratory_condition',
            'condition_details'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Leo (Son), Grandma Helen, or Self',
                'required': True
            }),
            'age_group': forms.Select(attrs={
                'class': 'form-select'
            }),
            'activity_preferences': forms.Select(attrs={
                'class': 'form-select'
            }),
            'outdoor_habits': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 7 AM school bus commute, cycling to work, evening park stroll'
            }),
            'has_respiratory_condition': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'id_has_respiratory_condition'
            }),
            'condition_details': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Mild asthma, seasonal dust allergy, heart sensitivity',
                'id': 'id_condition_details'
            })
        }
        labels = {
            'name': 'Member Name or Nickname',
            'age_group': 'Age Bracket',
            'activity_preferences': 'Primary Outdoor Activity / Routine',
            'outdoor_habits': 'Typical Timing & Habits',
            'has_respiratory_condition': 'Has respiratory or cardiovascular vulnerability?',
            'condition_details': 'Vulnerability / Medical Context (Optional)'
        }


class UserPreferenceForm(forms.ModelForm):
    class Meta:
        model = UserPreference
        fields = [
            'preferred_aqi_scale',
            'alert_threshold',
            'notify_vulnerable_only',
            'gemini_api_key_override'
        ]
        widgets = {
            'preferred_aqi_scale': forms.Select(attrs={'class': 'form-select'}),
            'alert_threshold': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 50,
                'max': 500,
                'step': 10
            }),
            'notify_vulnerable_only': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'gemini_api_key_override': forms.PasswordInput(render_value=True, attrs={
                'class': 'form-control',
                'placeholder': 'AIzaSy... (leave blank to use system key or offline mode)'
            }),
        }
        labels = {
            'preferred_aqi_scale': 'Default Air Quality Index Scale',
            'alert_threshold': 'Severe Smog Alert Threshold (US AQI)',
            'notify_vulnerable_only': 'Prioritize alerts specifically for vulnerable family members',
            'gemini_api_key_override': 'Custom Google Gemini API Key'
        }


class SavedLocationForm(forms.ModelForm):
    class Meta:
        model = SavedLocation
        fields = ['city_name', 'country', 'latitude', 'longitude', 'is_default']
        widgets = {
            'city_name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'required': True}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'required': True}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label='Confirm Password')

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('password_confirm')
        if p1 and p2 and p1 != p2:
            self.add_error('password_confirm', 'Passwords do not match.')
        return cleaned_data
