# 🌫️ Urban Air Quality Assistant

> A production-quality environmental health and winter smog defense platform built to help families reduce exposure, plan safer daily activities, optimize low-emission routines, and implement high-impact indoor air hacks.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-29%20Passed-success.svg)]()

---

## 1. Problem Statement & Mission

Severe winter smog caused by thermal ground inversions, calm surface winds, vehicle exhaust, biomass burning, and dust accumulation poses extreme cardiovascular and respiratory risks to urban households—especially vulnerable children and elderly members.

**Urban Air Quality Assistant** solves this by providing:
- **Real-Time Environmental Clarity**: Transparently distinguishing physical pollutant concentrations ($\mu\text{g/m}^3$) from aggregate Air Quality Index (AQI) values.
- **Smart Diurnal Exposure Timing**: Identifying safe midday inversion-lift windows while flagging dangerous morning and night smog traps.
- **Personalized Household Defense**: Tailoring exposure guidance, school commute precautions, and outdoor exertion advice to family members based on age and respiratory vulnerabilities.
- **Actionable Indoor Air Hacks**: Science-based guidance on HEPA CADR sizing, damp mopping versus dry sweeping, indoor combustion elimination, and timed flush ventilation.
- **Gemini-Powered Environmental Intelligence**: Context-aware AI answering family queries backed by live sensor metrics and a resilient offline rule-based fallback.

---

## 2. Technology Stack

- **Backend**: Python 3.11+, Django 5.2
- **Database**: SQLite (ORM-managed, zero complex configuration)
- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3, Bootstrap Icons
- **Visualizations**: Chart.js 4.4 (AQI progression lines, WHO multi-pollutant comparison bars, diurnal inversion trends)
- **Air Quality Data**: Open-Meteo Air Quality API & Geocoding API (Live CAMS/Copernicus atmospheric models, 7-day historical archive, 24-hour predictions)
- **AI Integration**: Google Gemini API (`google-generativeai`) with context injection and rule-based expert engine fallback
- **Caching**: Django In-Memory Cache (`LocMemCache`, 30-minute TTL) with rate-limit protection

---

## 3. Core Modules & Pages

The application delivers 9 fully interactive, dedicated pages:

| # | Page / Feature | Route | Key Capabilities |
|---|----------------|-------|------------------|
| 1 | **Home / Dashboard** | `/` | Real-time US AQI hero meter, 6 key pollutant concentrations ($\text{PM}_{2.5}$, $\text{PM}_{10}$, $\text{NO}_2$, $\text{O}_3$, $\text{CO}$, $\text{SO}_2$), 24-hour forecast chart, active emergency banners, and family safety callouts. |
| 2 | **Air Quality Details** | `/air-quality-details/` | Deep chemical breakdown, WHO 24h limit ratio chart, documented US EPA mathematical conversion formula ($I = \frac{I_{hi} - I_{lo}}{C_{hi} - C_{lo}}(C - C_{lo}) + I_{lo}$), and European AQI comparison. |
| 3 | **Personalized Family Profiles** | `/family-profiles/` | Member CRUD (infants, children, adults, seniors), activity preferences, outdoor habit timing, respiratory vulnerability tracking, and live individualized smog advice. |
| 4 | **Smart Daily Routine Planner** | `/routine-planner/` | Meteorological diurnal analysis, safe midday windows vs. inversion smog peaks, low-emission commute comparisons (Metro vs. EV vs. Cycling), and hour-by-hour family action schedules. |
| 5 | **Indoor Air Assistant** | `/indoor-air/` | Real-time ventilation advisory, True HEPA (H13/H14) CADR sizing, unit placement rules, wet mopping protocols, indoor combustion elimination, and room-by-room checklists. |
| 6 | **AI Chat Assistant** | `/ai-assistant/` | Interactive conversational assistant with live environmental context injection, prompt pill suggestions, and non-diagnostic medical disclaimers. |
| 7 | **Pollution Alerts** | `/alerts/` | Threshold-based warnings, severe smog emergency alerts, family precautions, and public health action matrices. |
| 8 | **Historical Trends** | `/historical-trends/` | Real 7-day past hourly measurements, multi-pollutant overlays, statistical metrics (mean AQI, peak spike, cleanest dip, and WHO exceedance rates). |
| 9 | **Settings & Preferences** | `/settings/` | Toggle default AQI standard (US EPA vs. European EAQI), adjust alert thresholds, manage saved cities, and configure custom Gemini API keys. |

---

## 4. Architectural & Safety Principles

### A. Concentration ($\mu\text{g/m}^3$) vs. AQI
Concentration measures physical mass in the air, whereas AQI is a standardized index calculated to communicate aggregate health risk. The application never confuses these two values and clearly marks units across all cards and charts.

### B. Prediction Transparency & No Safety Guarantee
Lower pollution periods (e.g. afternoon dips) reduce exposure relative to morning peaks, but the system **never claims an activity is 100% safe**. Predictions are explicitly labeled as meteorological models subject to atmospheric wind shifts.

### C. Indoor Guidance vs. Fabricated Measurements
The application provides evidence-based indoor hacks (e.g., damp mopping to prevent particulate resuspension, window sealing during smog peaks) without fabricating artificial indoor sensor readings.

### D. Medical Disclaimer & Non-Diagnostic Boundary
All recommendations include clear non-diagnostic public health disclaimers emphasizing that environmental advice cannot replace a licensed physician.

---

## 5. Installation & Setup

### Prerequisites
- Python 3.10, 3.11, 3.12, 3.13, or 3.14
- `pip` package manager

### Step 1: Clone or Navigate to the Project
```bash
cd C:\Users\USER\.gemini\antigravity\scratch\urban_air_quality
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
copy .env.example .env
```
*(Optional)* Add your Google Gemini API key to `.env` if you want live generative AI queries:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```
> **Note**: If `GEMINI_API_KEY` is not provided, the application automatically runs in **Offline Expert Mode**, utilizing a comprehensive rule-based reasoning engine.

### Step 4: Run Database Migrations
```bash
python manage.py migrate
```

### Step 5: (Optional) Seed Sample Family & Location Demo Data
```bash
python manage.py setup_demo
```

### Step 6: Start the Development Server
```bash
python manage.py runserver
```
Visit the application in your browser at: **`http://127.0.0.1:8000/`**

---

## 6. Running Automated Tests

Run the complete test suite covering conversions, services, fallback engines, and web views:
```bash
python manage.py test
```

### Test Suite Summary:
- **29 Automated Tests**
- **100% Passing**
- Tests include:
  - US EPA piecewise linear interpolation calculations
  - Open-Meteo payload parser and fallback generation
  - Family profile CRUD and tailored vulnerability guidance
  - Diurnal routine planner and activity window selection
  - Indoor ventilation and HEPA purifier recommendation logic
  - Severe alert threshold evaluation
  - Gemini AI and expert rule-based fallback responses
  - All 9 web view endpoints and AJAX APIs

---

## 7. API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/search-locations/?q=<city>` | `GET` | Geocoding search returning matching global cities with coordinates. |
| `/api/set-location/` | `POST` | Sets active city and coordinates in user session. |
| `/api/ai-chat/` | `POST` | Sends question with live environmental context to Gemini or rule-based engine. |

---

## 8. License

This project is open-source under the MIT License.
