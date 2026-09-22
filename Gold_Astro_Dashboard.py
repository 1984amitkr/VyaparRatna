import streamlit as st
import datetime
import zoneinfo
import pandas as pd

# Try importing Swiss Ephemeris with fallback
SWISS_EPH_AVAILABLE = False
try:
    import swisseph as swe
    SWISS_EPH_AVAILABLE = True
except Exception:
    SWISS_EPH_AVAILABLE = False

# -------------------------------------------------------------------
# 1. CONSTANTS & CONFIGURATION
# -------------------------------------------------------------------
MUMBAI_TZ = zoneinfo.ZoneInfo("Asia/Kolkata")
MUMBAI_LAT = 19.0760
MUMBAI_LON = 72.8777

NAKSHATRAS_27 = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Svati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

TITHIS = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shasthi",
    "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi",
    "Trayodashi", "Chaturdashi", "Purnima / Amavasya"
]

YOGAS = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda",
    "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva",
    "Vyaghat", "Harshan", "Vajra", "Siddhi", "Vyatipat", "Variyan",
    "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha", "Shukla",
    "Brahma", "Indra", "Vaidhriti"
]

KARANAS = [
    "Bava", "Balava", "Kaulava", "Taitila", "Garaja", "Vanija", "Vishti (Bhadra)",
    "Shakuni", "Chatushpada", "Naga", "Kintughna"
]

AVERAGE_DAILY_SPEEDS = {
    "Sun": 0.9856, "Moon": 13.1764, "Mars": 0.524, "Mercury": 1.383,
    "Jupiter": 0.0831, "Venus": 1.200, "Saturn": 0.0335, "Rahu": -0.0529, "Ketu": -0.0529
}

MALEFICS = ["Sun", "Mars", "Saturn", "Rahu", "Ketu"]
BENEFICS = ["Jupiter", "Venus", "Mercury", "Moon"]

SBC_GRID_POSITIONS = {
    "Dhanishta": (0, 1), "Shatabhisha": (0, 2), "Purva Bhadrapada": (0, 3), 
    "Uttara Bhadrapada": (0, 4), "Revati": (0, 5), "Ashwini": (0, 6), "Bharani": (0, 7),
    "Krittika": (1, 8), "Rohini": (2, 8), "Mrigashira": (3, 8), "Ardra": (4, 8), 
    "Punarvasu": (5, 8), "Pushya": (6, 8), "Ashlesha": (7, 8),
    "Magha": (8, 7), "Purva Phalguni": (8, 6), "Uttara Phalguni": (8, 5), 
    "Hasta": (8, 4), "Chitra": (8, 3), "Svati": (8, 2), "Vishakha": (8, 1),
    "Anuradha": (7, 0), "Jyeshtha": (6, 0), "Mula": (5, 0), "Purva Ashadha": (4, 0), 
    "Uttara Ashadha": (3, 0), "Abhijit": (2, 0), "Shravana": (1, 0)
}

GRID_TO_NAKSHATRA = {v: k for k, v in SBC_GRID_POSITIONS.items()}

NAK_SHORT_NAMES = {
    "Dhanishta": "Dhan", "Shatabhisha": "Shat", "Purva Bhadrapada": "P.Bha", 
    "Uttara Bhadrapada": "U.Bha", "Revati": "Reva", "Ashwini": "Asvi", "Bharani": "Bhar",
    "Krittika": "Krit", "Rohini": "Rohi", "Mrigashira": "Mrig", "Ardra": "Ardr", 
    "Punarvasu": "Puna", "Pushya": "Push", "Ashlesha": "Ashl",
    "Magha": "Magh", "Purva Phalguni": "P.Pha", "Uttara Phalguni": "U.Pha", 
    "Hasta": "Hast", "Chitra": "Chit", "Svati": "Swat", "Vishakha": "Vish",
    "Anuradha": "Anu", "Jyeshtha": "Jyes", "Mula": "Mula", "Purva Ashadha": "P.Sha", 
    "Uttara Ashadha": "U.Sha", "Abhijit": "Abhi", "Shravana": "Srav"
}

VARNADIPANCHAK_GRID = {
    (0, 0): "ई ī", (0, 8): "अ a", (8, 8): "आ ā", (8, 0): "इ i",
    (1, 1): "ऋ ṛ",  (1, 2): "ग ga", (1, 3): "स sa", (1, 4): "द da", (1, 5): "च ca", (1, 6): "ल la", (1, 7): "उ u",
    (2, 7): "अ a",  (3, 7): "व va", (4, 7): "क ka", (5, 7): "ह ha", (6, 7): "ड ḍa", (7, 7): "ऊ ū",
    (7, 6): "म ma", (7, 5): "ट ṭa", (7, 4): "प pa", (7, 3): "र ra", (7, 2): "त ta", (7, 1): "ऋ ṛ",
    (6, 1): "न na", (5, 1): "य ya", (4, 1): "भ bha", (3, 1): "ज ja", (2, 1): "ख kha",
    (2, 2): "ऐ ai", (2, 3): "Aq", (2, 4): "Pi", (2, 5): "Ar", (2, 6): "ऌ ḷ",
    (3, 2): "Cp",   (3, 3): "अः aḥ<br><span style='font-size:8px; color:#e0caaa;'>Rikta<br>Fri</span>", (3, 4): "ओ o", (3, 5): "Ta", (3, 6): "व va",
    (4, 2): "Sg",   (4, 3): "Jaya<br><span style='font-size:8px; color:#e0caaa;'>Thu</span>", (4, 4): "Purna<br><span style='font-size:8px; color:#e0caaa;'>Sat</span>", (4, 5): "Nanda<br><span style='font-size:8px; color:#e0caaa;'>Sun Tue</span>", (4, 6): "Ge",
    (5, 2): "Sc",   (5, 3): "अं aṃ", (5, 4): "Bhadra<br><span style='font-size:8px; color:#e0caaa;'>Mon Wed</span>", (5, 5): "औ au", (5, 6): "Ca",
    (6, 2): "Li",   (6, 3): "Vi", (6, 4): "Le", (6, 5): "ॡ ḹ", (6, 6): "ए e"
}

# -------------------------------------------------------------------
# 2. NAKSHATRA, PADA & PANCHANG CALCULATIONS
# -------------------------------------------------------------------
def get_sbc_nakshatra(lon: float) -> str:
    lon = lon % 360
    if 276.6667 <= lon < 280.8889:
        return "Abhijit"
    idx = int(lon // (360.0 / 27.0))
    return NAKSHATRAS_27[idx % 27]

def get_pada(lon: float) -> int:
    lon = lon % 360
    pada_span = 360.0 / 108.0  # Each pada is 3°20' (3.3333 degrees)
    return int((lon % (360.0 / 27.0)) // pada_span) + 1

def calculate_panchang(sun_lon: float, moon_lon: float, dt: datetime.datetime):
    vara = dt.strftime("%A")
    diff = (moon_lon - sun_lon) % 360
    
    # Tithi
    tithi_idx = int(diff // 12)
    paksha = "Shukla" if tithi_idx < 15 else "Krishna"
    tithi_name = TITHIS[tithi_idx % 15]
    tithi_str = f"{paksha} {tithi_name} (Tithi {tithi_idx + 1})"
    
    # Nakshatra & Pada
    nak_idx = int(moon_lon // (360.0 / 27.0))
    nakshatra_str = NAKSHATRAS_27[nak_idx % 27]
    pada_num = get_pada(moon_lon)
    
    # Yoga
    sum_lon = (sun_lon + moon_lon) % 360
    yoga_idx = int(sum_lon // (360.0 / 27.0))
    yoga_str = YOGAS[yoga_idx % 27]
    
    # Karana
    karana_idx = int(diff // 6)
    if karana_idx == 0:
        karana_str = KARANAS[10] # Kintughna
    elif karana_idx >= 57:
        karana_str = KARANAS[7 + (karana_idx - 57)] # Shakuni, Chatushpada, Naga
    else:
        karana_str = KARANAS[(karana_idx - 1) % 7]
        
    return {
        "Vara": vara,
        "Tithi": tithi_str,
        "Nakshatra": f"{nakshatra_str} (Pada {pada_num})",
        "Yoga": yoga_str,
        "Karana": karana_str
    }

# -------------------------------------------------------------------
# 3. VEDHA & MOTION CALCULATION LOGIC
# -------------------------------------------------------------------
def get_motion_status(planet: str, speed: float) -> str:
    if planet in ["Rahu", "Ketu"]:
        return "Normal"
    avg_speed = AVERAGE_DAILY_SPEEDS.get(planet, 1.0)
    if speed < 0:
        return "Vakra (Retrograde)"
    elif speed > 1.15 * avg_speed:
        return "Atichara (Fast Direct)"
    elif speed < 0.5 * avg_speed:
        return "Manda (Slow/Stationary)"
    else:
        return "Sama (Normal)"

def trace_ray(r: int, c: int, dr: int, dc: int):
    path = []
    curr_r, curr_c = r + dr, c + dc
    while 0 <= curr_r <= 8 and 0 <= curr_c <= 8:
        path.append((curr_r, curr_c))
        curr_r += dr
        curr_c += dc
    return path

def calculate_vedha(planet: str, nakshatra: str, speed: float):
    motion = get_motion_status(planet, speed)
    r, c = SBC_GRID_POSITIONS[nakshatra]

    if r == 0:   (dr_f, dc_f), (dr_l, dc_l), (dr_r, dc_r) = (1, 0), (1, 1), (1, -1)
    elif r == 8: (dr_f, dc_f), (dr_l, dc_l), (dr_r, dc_r) = (-1, 0), (-1, -1), (-1, 1)
    elif c == 8: (dr_f, dc_f), (dr_l, dc_l), (dr_r, dc_r) = (0, -1), (1, -1), (-1, -1)
    else:        (dr_f, dc_f), (dr_l, dc_l), (dr_r, dc_r) = (0, 1), (-1, 1), (1, 1)

    front_ray = trace_ray(r, c, dr_f, dc_f)
    left_ray  = trace_ray(r, c, dr_l, dc_l)
    right_ray = trace_ray(r, c, dr_r, dc_r)

    primary_vedha = "Front (Sammukha)"
    if "Vakra" in motion:
        primary_vedha = "Left Diagonal (Vama)"
    elif "Atichara" in motion:
        primary_vedha = "Right Diagonal (Dakshina)"

    return {
        "Motion": motion,
        "Primary Vedha": primary_vedha,
        "Front Target": GRID_TO_NAKSHATRA.get(front_ray[-1], "Inner Box") if front_ray else None,
        "Left Target": GRID_TO_NAKSHATRA.get(left_ray[-1], "Inner Box") if left_ray else None,
        "Right Target": GRID_TO_NAKSHATRA.get(right_ray[-1], "Inner Box") if right_ray else None,
        "All_Targets": list(filter(None, [
            GRID_TO_NAKSHATRA.get(front_ray[-1], None) if front_ray else None,
            GRID_TO_NAKSHATRA.get(left_ray[-1], None) if left_ray else None,
            GRID_TO_NAKSHATRA.get(right_ray[-1], None) if right_ray else None,
        ]))
    }

def get_ephemeris_data(dt: datetime.datetime):
    utc_dt = dt.astimezone(datetime.timezone.utc)
    planet_data = []

    planets_map = {
        "Sun": 0, "Moon": 1, "Mars": 4, "Mercury": 2,
        "Jupiter": 5, "Venus": 3, "Saturn": 6, "Rahu": 11, "Ketu": 11
    }

    if SWISS_EPH_AVAILABLE:
        try:
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            julian_day = swe.julday(
                utc_dt.year, utc_dt.month, utc_dt.day, 
                utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
            )

            for p_name, p_id in planets_map.items():
                flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
                res, _ = swe.calc_ut(julian_day, p_id, flags)
                lon = res[0] % 360
                speed = res[3]

                if p_name == "Ketu":
                    lon = (lon + 180) % 360
                    speed = -speed

                nak_name = get_sbc_nakshatra(lon)
                pada_num = get_pada(lon)
                vedha = calculate_vedha(p_name, nak_name, speed)

                planet_data.append({
                    "Planet": p_name, "Longitude": lon, "Speed (°/day)": round(speed, 4),
                    "Nakshatra": nak_name, "Pada": pada_num, "Motion": vedha["Motion"],
                    "Primary Vedha": vedha["Primary Vedha"],
                    "Front Target": vedha["Front Target"], "Left Target": vedha["Left Target"],
                    "Right Target": vedha["Right Target"], "All Targets": vedha["All_Targets"]
                })
            return planet_data
        except Exception:
            pass

    # Fallback Dynamic Approximation
    epoch = datetime.datetime(2000, 1, 1, 12, 0, tzinfo=datetime.timezone.utc)
    delta_days = (utc_dt - epoch).total_seconds() / 86400.0

    mean_longitudes = {
        "Sun": (280.460 + 0.9856474 * delta_days) % 360,
        "Moon": (218.316 + 13.176396 * delta_days) % 360,
        "Mars": (355.453 + 0.524033 * delta_days) % 360,
        "Mercury": (252.251 + 4.092334 * delta_days) % 360,
        "Jupiter": (34.351 + 0.083091 * delta_days) % 360,
        "Venus": (181.979 + 1.602130 * delta_days) % 360,
        "Saturn": (50.077 + 0.033459 * delta_days) % 360,
        "Rahu": (125.045 - 0.05295 * delta_days) % 360,
        "Ketu": (305.045 - 0.05295 * delta_days) % 360,
    }

    for p_name, lon in mean_longitudes.items():
        speed = AVERAGE_DAILY_SPEEDS.get(p_name, 1.0)
        nak_name = get_sbc_nakshatra(lon)
        pada_num = get_pada(lon)
        vedha = calculate_vedha(p_name, nak_name, speed)
        planet_data.append({
            "Planet": p_name, "Longitude": lon, "Speed (°/day)": speed,
            "Nakshatra": nak_name, "Pada": pada_num, "Motion": "Sama (Normal)",
            "Primary Vedha": vedha["Primary Vedha"],
            "Front Target": vedha["Front Target"], "Left Target": vedha["Left Target"],
            "Right Target": vedha["Right Target"], "All Targets": vedha["All_Targets"]
        })

    return planet_data

# -------------------------------------------------------------------
# 4. GOLD TRADING ANALYSIS & PREDICTIVE 12-HOUR SCANNER
# -------------------------------------------------------------------
def analyze_gold_market(planet_data):
    p_map = {p["Planet"]: p for p in planet_data}
    sun = p_map["Sun"]
    jupiter = p_map["Jupiter"]

    bullish_factors, bearish_factors, score = [], [], 0

    if "Atichara" in sun["Motion"]:
        score += 2
        bullish_factors.append("Sun in Atichara (Fast Direct) — Upward gold momentum.")
    elif "Manda" in sun["Motion"]:
        score -= 1
        bearish_factors.append("Sun Manda (Slow) — Stagnant/slight downward bias.")

    if "Vakra" in jupiter["Motion"]:
        score += 1.5
        bullish_factors.append("Jupiter Retrograde (Vakra) — Increases safe-haven demand.")

    sun_nak = sun["Nakshatra"]
    afflicting = [p["Planet"] for p in planet_data if p["Planet"] in MALEFICS and p["Planet"] != "Sun" and sun_nak in p["All Targets"]]
    if afflicting:
        score -= 2 * len(afflicting)
        bearish_factors.append(f"Asubha Vedha on Sun ({sun_nak}) by: {', '.join(afflicting)}.")

    if score >= 2:
        signal, bias = "BULLISH 📈", "Buy on Dips"
    elif score <= -2:
        signal, bias = "BEARISH 📉", "Sell on Rallies"
    else:
        signal, bias = "NEUTRAL ⚠️", "Range-Bound"

    return {"Signal": signal, "Bias": bias, "Score": score, "Bullish Factors": bullish_factors, "Bearish Factors": bearish_factors}

def predict_upcoming_changes(base_dt: datetime.datetime, hours_ahead: int = 12):
    """Scans the next N hours in 15-minute steps for Nakshatra, Pada, and Vedha changes."""
    initial_data = get_ephemeris_data(base_dt)
    prev_state = {p["Planet"]: p for p in initial_data}

    changes = []
    step_minutes = 15
    total_steps = int((hours_ahead * 60) / step_minutes)

    for step in range(1, total_steps + 1):
        future_dt = base_dt + datetime.timedelta(minutes=step * step_minutes)
        future_data = get_ephemeris_data(future_dt)
        future_map = {p["Planet"]: p for p in future_data}

        for planet_name in prev_state:
            curr_p = prev_state[planet_name]
            fut_p = future_map[planet_name]

            # 1. Nakshatra Change
            if curr_p["Nakshatra"] != fut_p["Nakshatra"]:
                impact = "High Volatility Shift" if planet_name in ["Moon", "Sun", "Jupiter"] else "Moderate Shift"
                if planet_name in MALEFICS:
                    gold_impact = "🔴 Malefic star shift; watch for sudden price rejection or risk-off sentiment."
                else:
                    gold_impact = "🟢 Benefic star shift; potential positive support/momentum for gold."

                changes.append({
                    "Date & Time (IST)": future_dt.strftime("%d %b %Y, %I:%M %p"),
                    "Planet / Point": planet_name,
                    "Event Type": "Nakshatra Shift",
                    "Details": f"Moved from {curr_p['Nakshatra']} to {fut_p['Nakshatra']}",
                    "Impact on Gold": gold_impact
                })
                prev_state[planet_name]["Nakshatra"] = fut_p["Nakshatra"]

            # 2. Pada Change
            elif curr_p["Pada"] != fut_p["Pada"]:
                changes.append({
                    "Date & Time (IST)": future_dt.strftime("%d %b %Y, %I:%M %p"),
                    "Planet / Point": planet_name,
                    "Event Type": "Pada Transition",
                    "Details": f"{fut_p['Nakshatra']} — Entered Pada {fut_p['Pada']} (from Pada {curr_p['Pada']})",
                    "Impact on Gold": f"⚡ Subtle micro-trend shift in intraday momentum for {planet_name}."
                })
                prev_state[planet_name]["Pada"] = fut_p["Pada"]

            # 3. Vedha Target Change
            if curr_p["Front Target"] != fut_p["Front Target"] or curr_p["Left Target"] != fut_p["Left Target"] or curr_p["Right Target"] != fut_p["Right Target"]:
                target_desc = f"New Vedha Targets -> Front: {fut_p['Front Target']}, Left: {fut_p['Left Target']}, Right: {fut_p['Right Target']}"
                
                if planet_name in MALEFICS and fut_p["Front Target"] == prev_state["Sun"]["Nakshatra"]:
                    vedha_impact = "🔴 WARNING: Direct Malefic Vedha targeted at Sun. Strong bearish signal for Gold."
                elif planet_name == "Jupiter":
                    vedha_impact = "🟢 Jupiter Vedha realignment; impacts institutional buying levels."
                else:
                    vedha_impact = "⚠️ Intraday SBC Ray adjustment; monitor key support/resistance."

                changes.append({
                    "Date & Time (IST)": future_dt.strftime("%d %b %Y, %I:%M %p"),
                    "Planet / Point": planet_name,
                    "Event Type": "Vedha Ray Change",
                    "Details": target_desc,
                    "Impact on Gold": vedha_impact
                })
                prev_state[planet_name]["Front Target"] = fut_p["Front Target"]
                prev_state[planet_name]["Left Target"] = fut_p["Left Target"]
                prev_state[planet_name]["Right Target"] = fut_p["Right Target"]

    return changes

# -------------------------------------------------------------------
# 5. COMPACT RESPONSIVE SVG + HTML GRID RENDERER
# -------------------------------------------------------------------
def render_sbc_grid_visual_with_svg(planet_data, selected_planets, current_dt):
    CELL_SIZE = 100
    GRID_DIM = 900
    
    planet_positions = {}
    vedha_targets = set()
    svg_lines = []

    for p in planet_data:
        nak = p["Nakshatra"]
        planet_positions.setdefault(nak, []).append(p)

    for p in planet_data:
        p_name = p["Planet"]
        if p_name not in selected_planets:
            continue

        src_nak = p["Nakshatra"]
        if src_nak not in SBC_GRID_POSITIONS:
            continue
            
        src_r, src_c = SBC_GRID_POSITIONS[src_nak]
        x1 = src_c * CELL_SIZE + 50
        y1 = src_r * CELL_SIZE + 50

        stroke_color = "#ff4d4d" if p_name in MALEFICS else "#2ecc71"

        targets = [
            ("Front Target", p.get("Front Target")),
            ("Left Target", p.get("Left Target")),
            ("Right Target", p.get("Right Target"))
        ]

        for vedha_type, target_nak in targets:
            if target_nak and target_nak in SBC_GRID_POSITIONS:
                vedha_targets.add(target_nak)
                tgt_r, tgt_c = SBC_GRID_POSITIONS[target_nak]
                x2 = tgt_c * CELL_SIZE + 50
                y2 = tgt_r * CELL_SIZE + 50

                is_primary = (
                    ("Front" in p["Primary Vedha"] and vedha_type == "Front Target") or
                    ("Left" in p["Primary Vedha"] and vedha_type == "Left Target") or
                    ("Right" in p["Primary Vedha"] and vedha_type == "Right Target")
                )

                stroke_width = "3.0" if is_primary else "1.5"
                opacity = "0.95" if is_primary else "0.45"
                dash_array = "none" if is_primary else "5,5"

                svg_lines.append(
                    f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                    f'stroke="{stroke_color}" stroke-width="{stroke_width}" '
                    f'stroke-linecap="round" stroke-dasharray="{dash_array}" opacity="{opacity}" />'
                )

    date_str = current_dt.strftime("%d %b %Y")

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ margin: 0; padding: 0; background-color: #0e1117; color: #ffffff; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
        .sbc-card {{ 
            position: relative; 
            width: 100%; 
            max-width: 580px; 
            margin: 0 auto; 
            background: #161a23; 
            border: 1px solid #30363d; 
            border-radius: 6px; 
            padding: 8px; 
            box-shadow: 0 4px 16px rgba(0,0,0,0.5); 
        }}
        .sbc-header {{ text-align: center; padding-bottom: 4px; color: #f0f6fc; }}
        .sbc-header h3 {{ margin: 0; font-size: 16px; font-weight: 700; letter-spacing: 0.5px; }}
        .sbc-header .date {{ font-size: 11px; color: #8b949e; font-weight: 500; }}
        
        .sbc-container {{ position: relative; width: 100%; aspect-ratio: 1 / 1; }}
        .sbc-table-svg {{ width: 100%; height: 100%; border-collapse: collapse; text-align: center; table-layout: fixed; }}
        .sbc-cell-svg {{ border: 1px solid #30363d; vertical-align: middle; padding: 0px; font-size: 10px; position: relative; }}
        
        /* Outer Ring Nakshatras */
        .sbc-outer-svg {{ background-color: #21262d; color: #ffffff; font-weight: 700; }}
        
        /* Inner Grid Styling */
        .sbc-inner-varna {{ background-color: #161a23; color: #c9d1d9; font-size: 10px; font-weight: 600; }}
        .sbc-rashi-cell {{ background-color: #1f3a5f; color: #ffffff; font-weight: 800; font-size: 11px; border: 1px solid #2f5485; }}
        .sbc-tithi-cell {{ background-color: #382c21; color: #ffe8c5; font-weight: 700; font-size: 9px; line-height: 1.0; border: 1px solid #5a4838; }}
        
        /* Planet Badges */
        .sbc-badge {{ display: inline-flex; align-items: center; justify-content: center; min-width: 16px; height: 16px; border-radius: 50%; font-size: 8px; font-weight: 800; margin: 0.5px; padding: 0 1px; }}
        .bg-malefic {{ background-color: #da3633; color: white; border: 1px solid #f85149; }}
        .bg-benefic {{ background-color: #238636; color: white; border: 1px solid #2ea043; }}
        
        .is-target {{ border: 2px solid #d29922 !important; background-color: #3c2d1d !important; }}
        
        /* Compact Footer Legend */
        .legend {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; margin-top: 6px; font-size: 10px; color: #8b949e; font-weight: 500; }}
        .legend-item {{ display: flex; align-items: center; gap: 4px; }}
        .legend-dot {{ width: 8px; height: 8px; border-radius: 50%; display: inline-block; }}
    </style>
    </head>
    <body>
    <div class="sbc-card">
        <div class="sbc-header">
            <h3>Sarvatobhadra Chakra</h3>
            <div class="date">{date_str}</div>
        </div>

        <div style="position: relative;">
            <div style="text-align: center; font-size: 9px; font-weight: 700; color: #8b949e; margin-bottom: 2px; letter-spacing: 1px;">NORTH</div>

            <div class="sbc-container">
                <svg viewBox="0 0 {GRID_DIM} {GRID_DIM}" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 10;">
                    {''.join(svg_lines)}
                </svg>

                <table class="sbc-table-svg">
    """

    for r in range(9):
        html += "<tr>"
        for c in range(9):
            nak_name = GRID_TO_NAKSHATRA.get((r, c), None)
            if nak_name:
                short_nak = NAK_SHORT_NAMES.get(nak_name, nak_name[:4])
                is_tgt = nak_name in vedha_targets
                cell_cls = "sbc-cell-svg sbc-outer-svg" + (" is-target" if is_tgt else "")
                planets = planet_positions.get(nak_name, [])
                
                badges = ""
                for p_info in planets:
                    p = p_info["Planet"]
                    p_disp = p[:2] if p not in ["Rahu", "Ketu"] else ("Ra" if p == "Rahu" else "Ke")
                    if "Vakra" in p_info["Motion"]:
                        p_disp += "R"
                    bg_cls = 'bg-malefic' if p in MALEFICS else 'bg-benefic'
                    badges += f"<div class='sbc-badge {bg_cls}'>{p_disp}</div>"

                html += f"""
                <td class='{cell_cls}'>
                    <div style='font-size: 9px; color: #ffffff; font-weight: bold;'>{short_nak}</div>
                    <div style='margin-top:0px;'>{badges}</div>
                </td>
                """
            else:
                val = VARNADIPANCHAK_GRID.get((r, c), "")
                if val in ["Aq", "Pi", "Ar", "Ta", "Ge", "Ca", "Le", "Vi", "Li", "Sc", "Sg", "Cp"]:
                    inner_cls = "sbc-cell-svg sbc-rashi-cell"
                elif "Rikta" in val or "Purna" in val or "Jaya" in val or "Nanda" in val or "Bhadra" in val:
                    inner_cls = "sbc-cell-svg sbc-tithi-cell"
                else:
                    inner_cls = "sbc-cell-svg sbc-inner-varna"

                html += f"<td class='{inner_cls}'>{val}</td>"
        html += "</tr>"

    html += f"""
                </table>
            </div>

            <div style="display: flex; justify-content: space-between; font-size: 9px; font-weight: 700; color: #8b949e; margin-top: 2px; letter-spacing: 1px;">
                <span>WEST</span>
                <span>EAST</span>
            </div>
            <div style="text-align: center; font-size: 9px; font-weight: 700; color: #8b949e; margin-top: 0px; letter-spacing: 1px;">SOUTH</div>
        </div>

        <div class="legend">
            <div class="legend-item"><span style="border: 1px solid #d29922; background: #3c2d1d; width: 8px; height: 8px; display: inline-block; border-radius: 2px;"></span> Sensitive star</div>
            <div class="legend-item"><span style="border-top: 1.5px dashed #aaa; width: 12px; display: inline-block;"></span> Vedha ray</div>
            <div class="legend-item"><span class="legend-dot" style="background: #da3633;"></span> Malefic</div>
            <div class="legend-item"><span class="legend-dot" style="background: #238636;"></span> Benefic</div>
        </div>
    </div>
    </body>
    </html>
    """
    return html

# -------------------------------------------------------------------
# 6. STREAMLIT APP CONFIGURATION & STATE
# -------------------------------------------------------------------
st.set_page_config(page_title="VyaparRatna SBC Gold Engine", layout="wide")

# Custom CSS for high visual density and compact view
st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 2rem; max-width: 95%; }
    div[data-testid="stMetricValue"] { font-size: 1.3rem !important; }
    div[data-testid="stMetricLabel"] { font-size: 0.8rem !important; }
    hr { margin: 0.8rem 0 !important; }
    .panchang-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 8px 12px;
        margin-bottom: 8px;
    }
    .panchang-title { font-weight: bold; font-size: 0.85rem; color: #58a6ff; margin-bottom: 4px; }
    .panchang-val { font-size: 0.8rem; color: #c9d1d9; }
</style>
""", unsafe_allow_html=True)

all_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

if "mode" not in st.session_state:
    st.session_state.mode = "LIVE"

if "filter_multiselect" not in st.session_state:
    st.session_state["filter_multiselect"] = ["Sun", "Jupiter", "Saturn", "Mars", "Rahu", "Ketu"]

st.title("🏆 VyaparRatna SBC Gold Trading Engine")

# -------------------------------------------------------------------
# 7. SIDEBAR CONTROLS
# -------------------------------------------------------------------
st.sidebar.header("🕹️ Mode & Time Controller")

if st.sidebar.button("🔄 Reset to Current Time"):
    st.session_state.mode = "LIVE"
    if "hist_date" in st.session_state: del st.session_state["hist_date"]
    if "hist_time" in st.session_state: del st.session_state["hist_time"]
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("📅 Date & Time Input")

now_mumbai = datetime.datetime.now(MUMBAI_TZ)

if "hist_date" not in st.session_state:
    st.session_state.hist_date = now_mumbai.date()
if "hist_time" not in st.session_state:
    st.session_state.hist_time = now_mumbai.time()

selected_date = st.sidebar.date_input("Select Date", st.session_state.hist_date)
selected_time = st.sidebar.time_input("Select Time (IST)", st.session_state.hist_time)

if selected_date != st.session_state.hist_date or selected_time != st.session_state.hist_time:
    st.session_state.mode = "HISTORICAL"
    st.session_state.hist_date = selected_date
    st.session_state.hist_time = selected_time

if st.session_state.mode == "LIVE":
    st.sidebar.success("🔴 LIVE MODE (Auto-Refreshing)")
    effective_datetime = datetime.datetime.now(MUMBAI_TZ)
else:
    st.sidebar.warning("⏳ HISTORICAL MODE (Paused)")
    effective_datetime = datetime.datetime.combine(
        st.session_state.hist_date, 
        st.session_state.hist_time, 
        tzinfo=MUMBAI_TZ
    )

# -------------------------------------------------------------------
# 8. AUTO-REFRESH SCRIPT FOR LIVE MODE ONLY
# -------------------------------------------------------------------
if st.session_state.mode == "LIVE":
    st.components.v1.html(
        """
        <script>
            setTimeout(function(){
                window.parent.location.reload();
            }, 300000);
        </script>
        """,
        height=0
    )

# -------------------------------------------------------------------
# 9. DASHBOARD RENDER
# -------------------------------------------------------------------
data = get_ephemeris_data(effective_datetime)
gold = analyze_gold_market(data)

p_map = {p["Planet"]: p for p in data}
panchang = calculate_panchang(p_map["Sun"]["Longitude"], p_map["Moon"]["Longitude"], effective_datetime)

# --- TOP SECTION: PANCHANG & TIMESTAMP ---
st.markdown("### 🗓️ Panchang & Time Details")
p_col1, p_col2, p_col3, p_col4, p_col5 = st.columns(5)

with p_col1:
    st.markdown(f"<div class='panchang-card'><div class='panchang-title'>📅 Vara (Day)</div><div class='panchang-val'>{panchang['Vara']}</div></div>", unsafe_allow_html=True)
with p_col2:
    st.markdown(f"<div class='panchang-card'><div class='panchang-title'>🌙 Tithi</div><div class='panchang-val'>{panchang['Tithi']}</div></div>", unsafe_allow_html=True)
with p_col3:
    st.markdown(f"<div class='panchang-card'><div class='panchang-title'>⭐ Moon Nakshatra & Pada</div><div class='panchang-val'>{panchang['Nakshatra']}</div></div>", unsafe_allow_html=True)
with p_col4:
    st.markdown(f"<div class='panchang-card'><div class='panchang-title'>🧘 Yoga</div><div class='panchang-val'>{panchang['Yoga']}</div></div>", unsafe_allow_html=True)
with p_col5:
    st.markdown(f"<div class='panchang-card'><div class='panchang-title'>⚙️ Karana</div><div class='panchang-val'>{panchang['Karana']}</div></div>", unsafe_allow_html=True)

st.caption(f"⏱️ **Active Calculation Timestamp:** `{effective_datetime.strftime('%Y-%m-%d %H:%M:%S %Z')}` | **Location:** Mumbai ({MUMBAI_LAT}° N, {MUMBAI_LON}° E)")

st.markdown("---")

# --- SECOND SECTION: GOLD MARKET METRICS & FACTORS ---
st.markdown("### 📊 Gold Trading Analysis (Suvarna Vedha)")
g_col1, g_col2, g_col3 = st.columns(3)

with g_col1:
    st.metric("Gold Market Signal", gold["Signal"])
with g_col2:
    st.metric("Market Bias", gold["Bias"])
with g_col3:
    st.metric("Net SBC Score", f"{gold['Score']:+.1f}")

col_a, col_b = st.columns(2)
with col_a:
    st.success("🟢 **Bullish Factors**")
    if gold["Bullish Factors"]:
        for factor in gold["Bullish Factors"]:
            st.write(f"- {factor}")
    else:
        st.write("No strong bullish SBC factors present.")

with col_b:
    st.error("🔴 **Bearish / Risk Factors**")
    if gold["Bearish Factors"]:
        for factor in gold["Bearish Factors"]:
            st.write(f"- {factor}")
    else:
        st.write("No significant malefic Vedha afflicting Gold significators.")

st.markdown("---")

# --- THIRD SECTION: UPCOMING 12-HOUR PREDICTIVE TRANSITIONS ---
st.markdown("### 🔮 Upcoming Nakshatra, Pada & Vedha Changes (Next 12 Hours)")
st.caption(f"Calculated relative to active baseline timestamp: **{effective_datetime.strftime('%d %b %Y, %I:%M %p %Z')}**")

upcoming_events = predict_upcoming_changes(effective_datetime, hours_ahead=12)

if upcoming_events:
    df_upcoming = pd.DataFrame(upcoming_events)
    st.dataframe(
        df_upcoming,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Date & Time (IST)": st.column_config.TextColumn("Date & Time (IST)", width="medium"),
            "Planet / Point": st.column_config.TextColumn("Planet", width="small"),
            "Event Type": st.column_config.TextColumn("Event Type", width="small"),
            "Details": st.column_config.TextColumn("Details of Change", width="large"),
            "Impact on Gold": st.column_config.TextColumn("Impact on Gold Trading", width="large")
        }
    )
else:
    st.info("ℹ️ No major Nakshatra, Pada, or Vedha target changes detected in the upcoming 12 hours.")

st.markdown("---")

# --- FOURTH SECTION: VISUAL CHAKRA & CONTROLS ---
st.markdown("### 🕸️ Visual Sarvatobhadra Chakra & Active Vedha Paths")

btn_c1, btn_c2, btn_c3, btn_c4 = st.columns(4)
if btn_c1.button("Show All Planets", use_container_width=True):
    st.session_state["filter_multiselect"] = all_planets.copy()
if btn_c2.button("Malefics Only", use_container_width=True):
    st.session_state["filter_multiselect"] = MALEFICS.copy()
if btn_c3.button("Benefics Only", use_container_width=True):
    st.session_state["filter_multiselect"] = BENEFICS.copy()
if btn_c4.button("Gold Key Movers", use_container_width=True):
    st.session_state["filter_multiselect"] = ["Sun", "Jupiter", "Saturn", "Mars"]

selected_planets = st.multiselect(
    "Filter Vedha Rays by Planet:",
    options=all_planets,
    key="filter_multiselect"
)

sbc_html = render_sbc_grid_visual_with_svg(data, selected_planets, effective_datetime)
st.components.v1.html(sbc_html, height=680, scrolling=False)

st.markdown("---")

# --- FIFTH SECTION: PLANETARY TABLE DETAILS ---
st.markdown("### 🔍 Current Planetary Vedha Details")

table_data = []
for p in data:
    table_data.append({
        "Planet": p["Planet"],
        "Nakshatra": p["Nakshatra"],
        "Pada": p["Pada"],
        "Speed (°/d)": f"{p['Speed (°/day)']:.4f}",
        "Motion": p["Motion"],
        "Primary Aspect": p["Primary Vedha"],
        "🎯 Front Vedha": p["Front Target"] if p["Front Target"] else "-",
        "⬅️ Left Vedha": p["Left Target"] if p["Left Target"] else "-",
        "➡️ Right Vedha": p["Right Target"] if p["Right Target"] else "-"
    })

df_vedha = pd.DataFrame(table_data)

st.dataframe(
    df_vedha,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Planet": st.column_config.TextColumn("Planet", width="small"),
        "Nakshatra": st.column_config.TextColumn("Nakshatra", width="medium"),
        "Pada": st.column_config.NumberColumn("Pada", width="small"),
        "Speed (°/d)": st.column_config.TextColumn("Speed (°/d)", width="small"),
        "Motion": st.column_config.TextColumn("Motion", width="medium"),
        "Primary Aspect": st.column_config.TextColumn("Primary Aspect", width="medium"),
        "🎯 Front Vedha": st.column_config.TextColumn("🎯 Front Vedha", width="medium"),
        "⬅️ Left Vedha": st.column_config.TextColumn("⬅️ Left Vedha", width="medium"),
        "➡️ Right Vedha": st.column_config.TextColumn("➡️ Right Vedha", width="medium"),
    }
)
