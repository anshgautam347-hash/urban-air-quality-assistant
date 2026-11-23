"""
Gemini AI Assistant Service:
Provides conversational AI guidance based on real AQI context and family profile vulnerability.
Includes an intelligent rule-based expert engine as a graceful fallback when GEMINI_API_KEY is not set or network fails.
Always includes clear non-diagnostic medical disclaimers.
"""

import os
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Medical & safety disclaimer mandated by guidelines
MEDICAL_DISCLAIMER = (
    "\n\n*Health & Safety Notice: This guidance is based on environmental air quality metrics and public health standards. "
    "It is not medical advice and does not diagnose conditions. Consult a licensed physician for individualized medical care.*"
)


def ask_gemini_assistant(user_question, aqi_context, family_profiles=None):
    """
    Sends a query to Gemini API with full local environmental context and family profiles.
    Falls back gracefully to the rule-based expert system if GEMINI_API_KEY is absent or if API call fails.
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', '') or os.environ.get('GEMINI_API_KEY', '')

    # If no key configured, immediately use the expert rule-based reasoning engine
    if not api_key or api_key.strip() == '' or 'your_gemini_key' in api_key.lower():
        return generate_rule_based_response(user_question, aqi_context, family_profiles, fallback_reason="No API key provided (Operating in Offline Rule-Based Mode)")

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)

        # Build comprehensive system and situational prompt
        system_instruction = build_system_prompt(aqi_context, family_profiles)

        # Try gemini-1.5-flash or gemini-2.5-flash / gemini-pro
        model_names = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
        last_error = None

        for m_name in model_names:
            try:
                model = genai.GenerativeModel(m_name)
                full_prompt = f"{system_instruction}\n\nUSER QUESTION: {user_question}"
                response = model.generate_content(full_prompt)
                if response and response.text:
                    reply = response.text.strip()
                    if not reply.endswith(MEDICAL_DISCLAIMER):
                        reply += MEDICAL_DISCLAIMER
                    return {
                        'reply': reply,
                        'source': f'Google Gemini ({m_name})',
                        'is_ai': True,
                        'success': True
                    }
            except Exception as e:
                last_error = e
                continue

        logger.warning(f"Gemini API calls failed with: {last_error}")
        return generate_rule_based_response(
            user_question,
            aqi_context,
            family_profiles,
            fallback_reason=f"Gemini API temporary connection error: {str(last_error)}"
        )

    except Exception as e:
        logger.error(f"Error initializing Gemini: {e}")
        return generate_rule_based_response(
            user_question,
            aqi_context,
            family_profiles,
            fallback_reason=f"AI Service exception: {str(e)}"
        )


def build_system_prompt(aqi_context, family_profiles=None):
    """
    Constructs a rich contextual prompt incorporating measured air quality and family details.
    """
    city = aqi_context.get('city_name', 'Unknown')
    aqi = aqi_context.get('us_aqi', 100)
    severity = aqi_context.get('category', {}).get('level', 'Moderate')
    pm25 = aqi_context.get('pm25', 0)
    pm10 = aqi_context.get('pm10', 0)
    no2 = aqi_context.get('no2', 0)
    data_source = aqi_context.get('data_source', 'Open-Meteo')
    timestamp = aqi_context.get('timestamp', 'Recent')

    family_summary = "None specified (general household)."
    if family_profiles:
        profile_lines = []
        for p in family_profiles:
            cond = f" [Respiratory sensitivity: {p.condition_details}]" if p.has_respiratory_condition else ""
            profile_lines.append(f"- {p.name} ({p.get_age_group_display()}): Activities: {p.get_activity_preferences_display()}{cond}")
        family_summary = "\n".join(profile_lines)

    prompt = f"""
You are the AI Urban Air Quality Assistant, an expert environmental health and winter smog specialist.
You help families beat severe winter smog with personalized low-emission routines, indoor air hacks, and exposure reduction.

LOCAL ENVIRONMENTAL DATA:
- Location: {city}
- Current Measured US AQI: {aqi} ({severity})
- PM2.5: {pm25} ug/m3 (WHO 24h limit is 15 ug/m3)
- PM10: {pm10} ug/m3 (WHO 24h limit is 45 ug/m3)
- NO2: {no2} ug/m3
- Data Timestamp: {timestamp} (Source: {data_source})

REGISTERED FAMILY MEMBERS:
{family_summary}

STRICT INSTRUCTIONS:
1. Ground all recommendations on the ACTUAL MEASURED DATA above. Do not invent fake readings or claim absolute zero risk.
2. If AQI > 150 (Unhealthy), advise against outdoor workouts/play for children and elderly, recommending N95 respirators for unavoidable commutes.
3. For indoor air: discuss ventilation timing (avoiding morning/evening smog peaks, sealing leaky frames), air purifiers with true HEPA (CADR matching room volume), wet mopping over sweeping, and eliminating indoor combustion (incense, mosquito coils, unvented frying).
4. Commuting: recommend low-emission alternatives (electric public transit, metro, carpooling, off-peak travel).
5. Never diagnose medical illnesses or prescribe medications. Provide a concise, empathetic, practical answer.
"""
    return prompt


def generate_rule_based_response(user_question, aqi_context, family_profiles=None, fallback_reason=None):
    """
    Intelligent expert rule-based reasoning engine.
    Ensures the user gets high-quality, personalized answers even when offline or without an API key.
    """
    q_lower = user_question.lower()
    city = aqi_context.get('city_name', 'your city')
    aqi = int(aqi_context.get('us_aqi', 120))
    severity = aqi_context.get('category', {}).get('level', 'Moderate')
    pm25 = aqi_context.get('pm25', 45)

    has_children = any(p.age_group in ('child', 'infant') for p in family_profiles) if family_profiles else False
    has_elderly = any(p.age_group == 'senior' for p in family_profiles) if family_profiles else False
    has_vulnerable = any(p.has_respiratory_condition for p in family_profiles) if family_profiles else False

    # Topic matching:
    # 1. Taking children outside / child outdoor activity
    if any(k in q_lower for k in ['child', 'kid', 'baby', 'toddler', 'school', 'play', 'outside']):
        if aqi > 150:
            content = (
                f"### 🛑 Outdoor Advisory for Children ({city} AQI: {aqi} — {severity})\n\n"
                f"**Recommendation: Keep children indoors today.**\n\n"
                f"**Why:** Children breathe 50% more air per pound of body weight than adults, and their lung alveoli are still developing. "
                f"With PM2.5 currently at **{pm25} µg/m³**, outdoor exertion forces ultrafine particulate matter deep into their lungs.\n\n"
                f"**Action Steps:**\n"
                f"1. **Indoor Play Alternatives:** Set up indoor obstacle courses, puzzles, board games, or yoga routines.\n"
                f"2. **School Commute:** If going to school is mandatory, equip your child with a well-fitted child-sized N95/KF94 mask. Ensure a tight seal over nose and chin.\n"
                f"3. **Recess Guidance:** Ask teachers or school coordinators to conduct recess and physical education inside the gymnasium or classroom."
            )
        elif aqi > 100:
            content = (
                f"### ⚠️ Cautionary Window for Children ({city} AQI: {aqi} — {severity})\n\n"
                f"**Recommendation: Limit outdoor playtime to 20–30 minutes, ideally between 1:00 PM and 3:30 PM.**\n\n"
                f"**Why:** Winter temperature inversions usually weaken in the early afternoon, making mid-day slightly less polluted than early mornings or evenings.\n\n"
                f"**Action Steps:**\n"
                f"1. Replace high-intensity running with lower-exertion activities (casual walking or scooter play).\n"
                f"2. Have your child hydrate before and after stepping out to soothe mucous membranes.\n"
                f"3. Children with asthma or allergies should stay strictly indoors."
            )
        else:
            content = (
                f"### ✅ Favorable Time for Children ({city} AQI: {aqi} — {severity})\n\n"
                f"**Recommendation: Safe for regular outdoor play and activities.**\n\n"
                f"With the AQI at **{aqi}**, outdoor air is relatively clean. Encourage outdoor physical exercise today while conditions are favorable."
            )

    # 2. Elderly parents / Seniors / Vulnerable members
    elif any(k in q_lower for k in ['elder', 'senior', 'parent', 'grandparent', 'asthma', 'copd', 'heart']):
        if aqi > 150:
            content = (
                f"### 🛡️ Vulnerable & Senior Health Protection ({city} AQI: {aqi} — {severity})\n\n"
                f"**Recommendation: Strict indoor stay for seniors and members with respiratory or cardiac conditions.**\n\n"
                f"**Critical Precautions:**\n"
                f"1. **Cancel Morning & Evening Walks:** Avoid stepping out between 6:00 AM – 9:00 AM and after 7:00 PM when winter smog is trapped near ground level.\n"
                f"2. **Clean Room Environment:** Designate the bedroom as a 'clean room' with a closed door and a running HEPA air purifier.\n"
                f"3. **Medication Readiness:** Keep prescribed rescue inhalers, spacers, and peak flow meters readily accessible.\n"
                f"4. **Indoor Movement:** Practice gentle indoor stretching, corridor pacing, or chair exercises rather than brisk outdoor walking."
            )
        else:
            content = (
                f"### 🚶 Senior Guidance ({city} AQI: {aqi} — {severity})\n\n"
                f"**Recommendation: Moderate outdoor walks are acceptable, preferably in the afternoon.**\n\n"
                f"Current AQI is **{aqi}**. Seniors should avoid strenuous exertion and pick routes away from busy traffic corridors."
            )

    # 3. Indoor air quality / home exposure / purifiers
    elif any(k in q_lower for k in ['indoor', 'home', 'purifier', 'hepa', 'ventilation', 'window', 'mop', 'clean']):
        content = (
            f"### 🏡 Indoor Air Quality Strategy for Severe Smog (Outdoor AQI: {aqi})\n\n"
            f"When outdoor pollution is severe, indoor air can quickly accumulate fine particles unless active measures are taken:\n\n"
            f"1. **Smart Ventilation Timing:**\n"
            f"   - Keep windows closed during morning (6 AM – 10 AM) and night smog peaks.\n"
            f"   - If air feels stale, conduct a brief 10-minute 'flush ventilation' between 1:30 PM and 3:00 PM, then immediately close windows and set purifiers to Turbo.\n\n"
            f"2. **Air Purifier Deployment:**\n"
            f"   - Use True HEPA (H13/H14) purifiers. Position the unit at least 1–2 feet away from walls in the center of living areas or near beds.\n"
            f"   - Match the Clean Air Delivery Rate (CADR) to your room size.\n\n"
            f"3. **Eliminate Indoor Particulate Sources:**\n"
            f"   - **Wet Mopping:** Never use dry brooms or dusters which resuspend fine dust. Use damp microfiber cloths and wet mopping.\n"
            f"   - **No Combustion:** Ban indoor incense, scented candles, and mosquito coils. A single incense stick can emit PM2.5 equivalent to several cigarettes.\n\n"
            f"4. **Kitchen Protection:** Always switch on the exhaust hood before turning on gas burners and keep it running for 5 minutes after cooking."
        )

    # 4. Commuting / low-emission travel
    elif any(k in q_lower for k in ['commute', 'travel', 'car', 'bike', 'metro', 'train', 'emission', 'work']):
        content = (
            f"### 🚆 Low-Emission & Low-Exposure Commute Plan ({city} AQI: {aqi})\n\n"
            f"Protecting your lungs while lowering emissions during winter smog season:\n\n"
            f"1. **Transit Mode Selection:**\n"
            f"   - **Top Choice:** Underground Metro / Electric Rail. Stations have filtered air exchange and zero roadside vehicle tailpipe exposure.\n"
            f"   - **Bus / Carpooling:** Electric or CNG buses over personal single-occupant cars to reduce localized emissions.\n"
            f"   - **Cycling / Walking:** Not recommended during severe smog (AQI > 150) because rapid breathing accelerates particulate inhalation by 300%.\n\n"
            f"2. **In-Vehicle Air Settings:**\n"
            f"   - If driving, set car ventilation strictly to **Recirculation Mode** to block exhaust fumes from entering the cabin.\n"
            f"   - Upgrade cabin air filters to activated carbon + PM2.5 filters.\n\n"
            f"3. **Personal PPE:** Wear a certified N95 or FFP2 respirator throughout your outdoor commute."
        )

    # 5. Daily routine / clean air plan
    elif any(k in q_lower for k in ['routine', 'daily', 'schedule', 'plan', 'morning']):
        content = (
            f"### 📅 Personalized Clean-Air Daily Routine for {city} (AQI: {aqi})\n\n"
            f"Based on diurnal temperature inversion and winter pollution trends:\n\n"
            f"- **06:30 – 08:30 (Morning Smog Inversion Peak):**\n"
            f"  - Windows strictly closed. Run air purifier in bedroom.\n"
            f"  - No outdoor jogging or balcony workouts. Light indoor stretching.\n\n"
            f"- **08:30 – 09:30 (Work / School Commute):**\n"
            f"  - N95 respirators for all commuting family members.\n"
            f"  - Metro or car with recirculation on.\n\n"
            f"- **13:00 – 15:30 (Lowest Smog Window):**\n"
            f"  - Safest window for necessary errands, brief outdoor walks, or rapid home airing.\n"
            f"  - Sunlight breaks inversion layer and aids atmospheric dispersion.\n\n"
            f"- **18:00 – 21:00 (Evening Traffic & Smog Surge):**\n"
            f"  - Return indoors promptly. Seal windows.\n"
            f"  - Cook with range hood on high.\n\n"
            f"- **21:00 – Night (Rest & Air Purification):**\n"
            f"  - Damp mop bedroom floors.\n"
            f"  - Run purifier on whisper/quiet mode throughout sleep."
        )

    # Default / General Question
    else:
        content = (
            f"### 🌫️ Winter Smog Advisory for {city} (Measured AQI: {aqi} — {severity})\n\n"
            f"Thank you for your question. Here are key evidence-based guidelines for your household today:\n\n"
            f"- **Current Exposure Risk:** With PM2.5 at **{pm25} µg/m³**, atmospheric pollution is elevated due to winter calm winds and temperature inversions.\n"
            f"- **Activity Strategy:** Shift high-cardio exercises indoors. If venturing out, schedule outdoor tasks between 1:00 PM and 3:30 PM.\n"
            f"- **Family Safeguards:** {'Ensure vulnerable family members stay indoors in purified rooms.' if (has_children or has_elderly or has_vulnerable) else 'Keep outdoor exposure brief and wear an N95 mask if in traffic.'}\n"
            f"- **Indoor Hacks:** Keep windows closed during morning/evening smog peaks, use wet mopping to capture dust, and operate a True HEPA air purifier."
        )

    # Append disclaimer
    content += MEDICAL_DISCLAIMER

    return {
        'reply': content,
        'source': 'Expert Rule-Based Engine (Fallback Mode)',
        'fallback_reason': fallback_reason,
        'is_ai': False,
        'success': True
    }
