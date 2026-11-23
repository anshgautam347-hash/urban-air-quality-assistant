"""
Indoor Air Quality Service:
Provides evidence-based indoor hacks, air purifier guidance, ventilation rules,
and habit modifications to keep indoor air clean during severe winter smog episodes.
Clearly clarifies that recommendations are guidance protocols, not fabricated indoor sensor readings.
"""


def get_indoor_air_strategy(outdoor_aqi, pm25_val):
    """
    Returns structured, room-by-room and habit-by-habit indoor air management protocols
    calibrated to the current outdoor smog severity.
    """
    outdoor_aqi = int(outdoor_aqi or 100)
    pm25 = float(pm25_val or 35.0)

    # 1. Ventilation Protocol
    if outdoor_aqi > 200:
        ventilation_status = "STRICT LOCKDOWN (Windows Sealed)"
        ventilation_class = "danger"
        ventilation_protocol = (
            "Keep all doors, windows, and balcony vents tightly sealed. Heavy winter smog will "
            "rapidly overwhelm indoor purifiers if outdoor air is allowed in. If stuffiness or high CO2 "
            "develops, open windows only for 5 minutes during the afternoon (1:30 PM - 2:30 PM) while "
            "running purifiers on Turbo, then immediately re-seal."
        )
    elif outdoor_aqi > 100:
        ventilation_status = "RESTRICTED / TARGETED VENTILATION"
        ventilation_class = "warning"
        ventilation_protocol = (
            "Keep windows shut during early morning hours (6:00 AM - 10:00 AM) and after dusk when "
            "traffic smog settles. Ventilate for 15-20 minutes only during peak afternoon sunlight "
            "(1:00 PM - 3:30 PM) when atmospheric inversion breaks."
        )
    else:
        ventilation_status = "OPEN VENTILATION RECOMMENDED"
        ventilation_class = "success"
        ventilation_protocol = (
            "Outdoor air quality is clean. Open opposing windows to create cross-ventilation, "
            "flushing out indoor CO2, VOCs, and moisture."
        )

    # 2. Air Purifier & HEPA Recommendations
    purifier_guide = [
        {
            'topic': 'True HEPA (H13 / H14) Filter Standard',
            'icon': 'bi-filter-circle',
            'detail': 'Ensure your purifier uses certified True HEPA filters that capture 99.97% of particles down to 0.3 microns. Avoid relying on simple pre-filters or nylon mesh alone.'
        },
        {
            'topic': 'CADR & Room Sizing',
            'icon': 'bi-aspect-ratio',
            'detail': 'Check the Clean Air Delivery Rate (CADR). To effectively scrub winter smog, your purifier should provide at least 4 to 5 Air Changes per Hour (ACH) for your room volume.'
        },
        {
            'topic': 'Optimal Unit Positioning',
            'icon': 'bi-geo-alt',
            'detail': 'Place purifiers at least 1.5 to 2 feet away from walls, curtains, and furniture. Position them near where you breathe (e.g. bedside or near desk) rather than hidden in corners.'
        },
        {
            'topic': 'Filter Maintenance & Longevity',
            'icon': 'bi-arrow-repeat',
            'detail': 'In severe smog climates, vacuum the pre-filter mesh every 2 weeks. Inspect the main HEPA filter every 3–4 months; replace when grayed or air output drops significantly.'
        }
    ]

    # 3. Critical Indoor Smog Hacks
    indoor_hacks = [
        {
            'title': 'Damp Mopping vs. Dry Sweeping',
            'category': 'Cleaning Hack',
            'badge': 'Essential',
            'icon': 'bi-droplet-half',
            'color': 'primary',
            'why': 'Dry brooms and vacuum cleaners without sealed HEPA exhaust merely resuspend settled fine PM2.5 particles back into the air you breathe for hours.',
            'action': 'Always use damp microfiber mops and wet wiping cloths to trap dust particles physically.'
        },
        {
            'title': 'Zero Indoor Combustion Rule',
            'category': 'Airway Protection',
            'badge': 'High Priority',
            'icon': 'bi-fire',
            'color': 'danger',
            'why': 'Burning incense sticks, religious dhoop, scented paraffin candles, or mosquito coils releases dense plumes of PM2.5, benzene, and PAHs.',
            'action': 'Completely eliminate indoor burning during winter smog season. Use liquid vaporizers or essential oil diffusers without smoke.'
        },
        {
            'title': 'Kitchen Range Hood Discipline',
            'category': 'Cooking Strategy',
            'badge': 'Daily Habit',
            'icon': 'bi-stove',
            'color': 'warning',
            'why': 'High-temperature shallow frying, deep frying, and searing oil create intense particulate surges exceeding 300 µg/m³ in unvented kitchens.',
            'action': 'Turn on exhaust hood 1 minute before turning on the burner. Cook with lids covered, and keep the exhaust running for 5 minutes after cooking completes.'
        },
        {
            'title': 'Shoe & Outerwear Air-Lock',
            'category': 'Entryway Protocol',
            'badge': 'Dust Barrier',
            'icon': 'bi-door-closed',
            'color': 'info',
            'why': 'Shoes track in toxic roadside soot, tire dust particles, and heavy metals from outdoor streets directly onto your carpets and tiles.',
            'action': 'Remove all outdoor footwear at the entry threshold. Place heavy rubber-backed walk-off mats both outside and inside the doorway.'
        },
        {
            'title': 'Indoor Humidity Balancing (40% - 50%)',
            'category': 'Comfort & Defense',
            'badge': 'Respiratory Shield',
            'icon': 'bi-moisture',
            'color': 'success',
            'why': 'Dry winter air dries out nasal mucous membranes and ciliated epithelial cells, destroying the respiratory tract’s primary defense against smog.',
            'action': 'Use an ultrasonic or evaporative humidifier with filtered water to maintain 40%–50% relative humidity.'
        },
        {
            'title': 'Indoor Plants: What They Do & Do Not Do',
            'category': 'Science Fact',
            'badge': 'Myth Buster',
            'icon': 'bi-flower1',
            'color': 'secondary',
            'why': 'Houseplants (Snake plants, Areca palms) enhance mood and micro-humidity, but laboratory tests show they cannot replace HEPA purifiers for PM2.5 particulate filtration.',
            'action': 'Enjoy plants for aesthetic well-being, but rely strictly on mechanical HEPA purifiers for hazardous winter particulate removal.'
        }
    ]

    # Room-by-room checklist
    room_checklist = [
        {
            'room': 'Master Bedroom & Children’s Room',
            'priority': 'Clean Sanctuary (Tier 1)',
            'recommendations': [
                'Prioritize air purifier placement here where you spend 7-8 hours resting.',
                'Keep bedroom door closed while running purifier.',
                'Wash bedding weekly in hot water to eliminate dust mites.'
            ]
        },
        {
            'room': 'Living & Dining Area',
            'priority': 'Family Gathering Hub (Tier 2)',
            'recommendations': [
                'Deploy larger capacity purifier with high CADR.',
                'Damp mop tiles twice daily during smog spikes.',
                'Seal gaps under external balcony doors using brush weatherstrips.'
            ]
        },
        {
            'room': 'Kitchen',
            'priority': 'Source Control Zone',
            'recommendations': [
                'Always run exhaust fan venting directly outside.',
                'Prefer boiling, steaming, or baking over high-heat open wok frying.',
                'Isolate kitchen from living rooms with door closed while cooking.'
            ]
        }
    ]

    sensor_notice = (
        "Note on Indoor Measurements: The recommendations above are evidence-based environmental guidance "
        "calibrated against outdoor ambient air data. This application does not connect to unauthenticated "
        "indoor sensors and does NOT invent artificial indoor sensor readings."
    )

    return {
        'outdoor_aqi': outdoor_aqi,
        'pm25': pm25,
        'ventilation_status': ventilation_status,
        'ventilation_class': ventilation_class,
        'ventilation_protocol': ventilation_protocol,
        'purifier_guide': purifier_guide,
        'indoor_hacks': indoor_hacks,
        'room_checklist': room_checklist,
        'sensor_notice': sensor_notice
    }
