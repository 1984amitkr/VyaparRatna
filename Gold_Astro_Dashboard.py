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

AVERAGE_DAILY_SPEEDS = {
    "Sun": 0.9856, "Moon": 13.1764, "Mars": 0.524, "Mercury": 1.383,
    "Jupiter": 0.0831, "Venus": 1.200, "Saturn": 0.0335, "Rahu": -0.0529, "Ketu": -0.0529
}

MALEFICS = ["Sun", "Mars", "Saturn", "Rahu", "Ketu"]
BENEFICS = ["Jupiter", "Venus", "Mercury", "Moon"]

# SBC Outer Ring Mapping (28 Nakshatras including Abhijit)
# Standard orientation based on provided image layout
SBC_GRID_POSITIONS = {
    # Top Row (North): Left to Right
    "Dhanishta": (0, 1), "Shatabhisha": (0, 2), "Purva Bhadrapada": (0, 3), 
    "Uttara Bhadrapada": (0, 4), "Revati": (0, 5), "Ashwini": (0, 6), "Bharani": (0, 7),

    # Right Column (East): Top to Bottom
    "Krittika": (1, 8), "Rohini": (2, 8), "Mrigashira": (3, 8), "Ardra": (4, 8), 
    "Punarvasu": (5, 8), "Pushya": (6, 8), "Ashlesha": (7, 8),

    # Bottom Row (South): Right to Left
    "Magha": (8, 7), "Purva Phalguni": (8, 6), "Uttara Phalguni": (8, 5), 
    "Hasta": (8, 4), "Chitra": (8, 3), "Svati": (8, 2), "Vishakha": (8, 1),

    # Left Column (West): Bottom to Top
    "Anuradha": (7, 0), "Jyeshtha": (6, 0), "Mula": (5, 0), "Purva Ashadha": (4, 0), 
    "Uttara Ashadha": (3, 0), "Abhijit": (2, 0), "Shravana": (1, 0)
}

GRID_TO_NAKSHATRA = {v: k for k, v in SBC_GRID_POSITIONS.items()}

# Display Name Shortening Map for Nakshatras
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

# -------------------------------------------------------------------
# EXACT SARVATOBHADRA CHAKRA INNER GRID (7x7 INNER MATRIX)
# Matched precisely to the reference image structure
# -------------------------------------------------------------------
VARNADIPANCHAK_GRID = {
    # 4 Outer Corner Vowels
    (0, 0): "ई ī",
    (0, 8): "अ a",
    (8, 8): "आ ā",
    (8, 0): "इ i",

    # Ring 1: Swara / Vowel Band
    (1, 1): "ऋ ṛ",  (1, 2): "ग ga", (1, 3): "स sa", (1, 4): "द da", (1, 5): "च ca", (1, 6): "ल la", (1, 7): "उ u",
    (2, 7): "अ a",  (3, 7): "व va", (4, 7): "क ka", (5, 7): "ह ha", (6, 7): "ड ḍa", (7, 7): "ऊ ū",
    (7, 6): "म ma", (7, 5): "ट ṭa", (7, 4): "प pa", (7, 3): "र ra", (7, 2): "त ta", (7, 1): "ऋ ṛ",
    (6, 1): "न na", (5, 1): "य ya", (4, 1): "भ bha", (3, 1): "ज ja", (2, 1): "ख kha",

    # Ring 2: Consonants & Vowels
    (2, 2): "ऐ ai", (2, 6): "ऌ ḷ",
    (6, 6): "ॡ ḹ", (6, 2): "ए e",

    # Ring 3: 12 Rashis (Zodiac Signs)
    (2, 3): "Aq", (2, 4): "Pi", (2, 5): "Ar",
    (3, 5): "Ta", (4, 5): "Ge", (5, 5): "Ca",
    (5, 4): "Le", (5, 3): "Vi", (5, 2): "Li",
    (4, 2): "Sc", (3, 2): "Sg", (3, 3): "Cp",

    # Inner Core: Tithis & Center
    (3, 4): "अः aḥ<br><span style='font-size:8px; color:#aaa;'>Rikta<br>Fri</span>",
    (4, 4): "Purna<br><span style='font-size:8px; color:#aaa;'>Sat</span>",
    (4, 3): "Jaya<br><span style='font-size:8px; color:#aaa;'>Thu</span>",
    (4, 5): "Nanda<br><span style='font-size:8px; color:#aaa;'>Sun Tue</span>",
    (5, 3): "Li", # Handled via layout grid
    (4, 4): "Purna<br><span style='font-size:8px; color:#aaa;'>Sat</span>",
    (5, 4): "Bhadra<br><span style='font-size:8px; color:#aaa;'>Mon Wed</span>",
    (4, 3): "Jaya<br><span style='font-size:8px; color:#aaa;'>Thu</span>",
    (4, 2): "Sc",
    (3, 3): "Cp",
    (4, 3): "Jaya<br><span style='font-size:8px; color:#aaa;'>Thu</span>",
    (3, 4): "अः aḥ",
    (4, 4): "Purna<br><span style='font-size:8px; color:#aaa;'>Sat</span>",
}

# Accurate Inner 5x5 Grid explicit cell definitions to match screenshot
EXACT_INNER_GRID = {
    (2, 2): "ख kha", (2, 3): "ऐ ai", (2, 4): "Aq", (2, 5): "Pi", (2, 6): "Ar", (2, 7): "ऌ ḷ", (2, 8): "Rohi",
    (3, 2): "ज ja",  (3, 3): "Cp",   (3, 4): "अः aḥ<br><span style='font-size:8px; color:#888;'>Rikta<br>Fri</span>", (3, 5): "ओ o", (3, 6): "Ta",
    (4, 2): "भ bha", (4, 3): "Sg",   (4, 4): "Jaya<br><span style='font-size:8px; color:#888;'>Thu</span>", 
    (4, 5): "Purna<br><span style='font-size:8px; color:#888;'>Sat</span>", 
    (4, 6): "Nanda<br><span style='font-size:8px; color:#888;'>Sun Tue</span>", (4, 7): "Ge",
    (5, 2): "य ya",  (5, 3): "Sc",   (5, 4): "अं aṃ", (5, 5): "Bhadra<br><span style='font-size:8px; color:#888;'>Mon Wed</span>", 
    (5, 6): "औ au",  (5, 7): "Ca",
    (6, 2): "न na",  (6, 3): "ए e",  (6, 4): "Li", (6, 5): "Vi", (6, 6): "Le", (6, 7): "ॡ ḹ"
}

# Combine into master grid mapping
for k, v in EXACT_INNER_GRID.items():
    VARNADIPANCHAK_GRID[k] = v


# -------------------------------------------------------------------
# 2. ACCURATE NAKSHATRA MAPPING
# -------------------------------------------------------------------
def get_sbc_nakshatra(lon: float) -> str:
    lon = lon % 360
    if 276.6667 <= lon < 280.8889:
        return "Abhijit"
    idx = int(lon // (360.0 / 27.0))
    return NAKSHATRAS_27[idx % 27]

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

    # Directions tailored to outer perimeter orientation
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
    # Ensure timezone awareness and correct UTC conversion
    utc_dt = dt.astimezone(datetime.timezone.utc)
    planet_data = []

    planets_map = {
        "Sun": 0, "Moon": 1, "Mars": 4, "Mercury": 2,
        "Jupiter": 5, "Venus": 3, "Saturn": 6, "Rahu": 11, "Ketu": 11
    }

    if SWISS_EPH_AVAILABLE:
        try:
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            # Precision Julian Day calculation from UTC
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
                vedha = calculate_vedha(p_name, nak_name, speed)

                planet_data.append({
                    "Planet": p_name, "Longitude": lon, "Speed (°/day)": round(speed, 4),
                    "Nakshatra": nak_name, "Motion": vedha["Motion"],
                    "Primary Vedha": vedha["Primary Vedha"],
                    "Front Target": vedha["Front Target"], "Left Target": vedha["Left Target"],
                    "Right Target": vedha["Right Target"], "All Targets": vedha["All_Targets"]
                })
            return planet_data
        except Exception:
            pass

    # Dynamic Analytical Approximation for Historical/Fallback Dates
    # Calculations based on elapsed days from Epoch 2000-01-01
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
        vedha = calculate_vedha(p_name, nak_name, speed)
        planet_data.append({
            "Planet": p_name, "Longitude": lon, "Speed (°/day)": speed,
            "Nakshatra": nak_name, "Motion": "Sama (Normal)",
            "Primary Vedha": vedha["Primary Vedha"],
            "Front Target": vedha["Front Target"], "Left Target": vedha["Left Target"],
            "Right Target": vedha["Right Target"], "All Targets": vedha["All_Targets"]
        })

    return planet_data

# -------------------------------------------------------------------
# 4. GOLD TRADING ANALYSIS ENGINE
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

# -------------------------------------------------------------------
# 5. SVG + HTML 9x9 GRID RENDERER WITH VARNADIPANCHAK
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

        stroke_color = "#e74c3c" if p_name in MALEFICS else "#2ecc71"

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

                stroke_width = "2.5" if is_primary else "1.2"
                opacity = "0.85" if is_primary else "0.35"
                dash_array = "none" if is_primary else "4,4"

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
        body {{ margin: 0; background-color: #1a1715; color: white; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
        .sbc-header {{ text-align: center; padding: 8px 0; background-color: #1a1715; color: #f0e6d2; }}
        .sbc-header h2 {{ margin: 0; font-size: 20px; font-weight: 600; letter-spacing: 0.5px; }}
        .sbc-header .date {{ font-size: 12px; color: #a09585; margin-top: 2px; }}
        .sbc-card {{ position: relative; width: 100%; max-width: 680px; margin: 0 auto; background: #1f1b18; border: 1px solid #332d28; border-radius: 6px; padding: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }}
        .sbc-container {{ position: relative; width: 100%; aspect-ratio: 1 / 1; }}
        .sbc-table-svg {{ width: 100%; height: 100%; border-collapse: collapse; text-align: center; table-layout: fixed; }}
        .sbc-cell-svg {{ border: 1px solid #342e29; vertical-align: middle; padding: 2px; font-size: 11px; box-sizing: border-box; position: relative; }}
        .sbc-outer-svg {{ background-color: #231e1a; color: #e0d5c5; font-weight: 600; }}
        .sbc-inner-varna {{ background-color: #181513; color: #d0c4b0; font-size: 11px; font-weight: 500; }}
        .sbc-rashi-cell {{ background-color: #1c2733; color: #ffffff; font-weight: bold; font-size: 13px; }}
        .sbc-tithi-cell {{ background-color: #2b241d; color: #f0e0c0; font-weight: 600; font-size: 10px; }}
        .sbc-badge {{ display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; border-radius: 50%; font-size: 10px; font-weight: bold; margin: 2px; box-shadow: 0 2px 4px rgba(0,0,0,0.4); }}
        .bg-malefic {{ background-color: #d9534f; color: white; border: 1px solid #ff706b; }}
        .bg-benefic {{ background-color: #2e7d32; color: white; border: 1px solid #4caf50; }}
        .is-target {{ border: 2px solid #e67e22 !important; background-color: #332211 !important; }}
        .dir-label {{ position: absolute; font-size: 10px; font-weight: bold; color: #8c8275; text-transform: uppercase; }}
        .legend {{ display: flex; justify-content: center; gap: 15px; margin-top: 10px; font-size: 11px; color: #b0a595; }}
        .legend-item {{ display: flex; align-items: center; gap: 5px; }}
        .legend-dot {{ width: 8px; height: 8px; border-radius: 50%; display: inline-block; }}
    </style>
    </head>
    <body>
    <div class="sbc-card">
        <div class="sbc-header">
            <h2>Sarvatobhadra Chakra</h2>
            <div class="date">{date_str}</div>
        </div>

        <div style="position: relative;">
            <!-- Direction Indicators -->
            <div style="text-align: center; font-size: 10px; font-weight: bold; color: #8c8275; margin-bottom: 3px;">NORTH</div>

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
                    <div style='font-size: 10px; color: #f0e6d2; font-weight: bold;'>{short_nak}</div>
                    <div style='margin-top:1px;'>{badges}</div>
                </td>
                """
            else:
                val = VARNADIPANCHAK_GRID.get((r, c), "")
                # Styling Rashi vs Tithi vs Varna cells
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

            <!-- Direction Labels around perimeter -->
            <div style="display: flex; justify-content: space-between; font-size: 10px; font-weight: bold; color: #8c8275; margin-top: 4px;">
                <span>WEST</span>
                <span>EAST</span>
            </div>
            <div style="text-align: center; font-size: 10px; font-weight: bold; color: #8c8275; margin-top: 2px;">SOUTH</div>
        </div>

        <div class="legend">
            <div class="legend-item"><span style="border: 1px solid #e67e22; width: 10px; height: 10px; display: inline-block;"></span> Sensitive star</div>
            <div class="legend-item"><span style="border-top: 1px dashed #888; width: 14px; display: inline-block;"></span> Planet's vedha ray</div>
            <div class="legend-item"><span class="legend-dot" style="background: #d9534f;"></span> Malefic vedha</div>
            <div class="legend-item"><span class="legend-dot" style="background: #2e7d32;"></span> Benefic vedha</div>
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

all_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

if "mode" not in st.session_state:
    st.session_state.mode = "LIVE"

if "selected_planets" not in st.session_state:
    st.session_state.selected_planets = ["Sun", "Jupiter", "Saturn", "Mars", "Rahu", "Ketu"]

st.title("🏆 VyaparRatna SBC Gold Trading Engine")
st.caption(f"Sarvatobhadra Chakra Analysis • Reference Location ({MUMBAI_LAT}° N, {MUMBAI_LON}° E)")

# -------------------------------------------------------------------
# 7. SIDEBAR CONTROLS (REFRESH + HISTORICAL VIEW)
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

# Persistent Historical Selection Management
if "hist_date" not in st.session_state:
    st.session_state.hist_date = now_mumbai.date()
if "hist_time" not in st.session_state:
    st.session_state.hist_time = now_mumbai.time()

selected_date = st.sidebar.date_input("Select Date", st.session_state.hist_date)
selected_time = st.sidebar.time_input("Select Time (IST)", st.session_state.hist_time)

# Detect user changes to date or time inputs
if selected_date != st.session_state.hist_date or selected_time != st.session_state.hist_time:
    st.session_state.mode = "HISTORICAL"
    st.session_state.hist_date = selected_date
    st.session_state.hist_time = selected_time

if st.session_state.mode == "LIVE":
    st.sidebar.success("🔴 LIVE MODE (Auto-Refreshing every 5 mins)")
    effective_datetime = datetime.datetime.now(MUMBAI_TZ)
else:
    st.sidebar.warning("⏳ HISTORICAL MODE (Auto-Refresh Paused)")
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

st.info(
    f"**Active Calculation Timestamp:** `{effective_datetime.strftime('%Y-%m-%d %H:%M:%S %Z')}` "
    f"| **Location:** Reference Location "
    f"| **Refresh State:** {'🟢 Auto-Refresh Active (300s)' if st.session_state.mode == 'LIVE' else '⏸️ Paused (Historical Analysis)'}"
)

# Metrics
st.divider()
st.subheader("📊 Gold Trading Analysis (Suvarna Vedha)")
g_col1, g_col2, g_col3 = st.columns([1, 1, 1])

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

# Visual SBC Grid with Filter Presets
st.divider()
st.subheader("🕸️ Visual Sarvatobhadra Chakra & Active Vedha Paths")
st.caption("🔴 Red = Malefic Planet | 🟢 Green = Benefic Planet | 🟠 Highlight = Active Target | Inner 7x7 Grid = Varnadipanchak & Rashis")

st.write("**Quick Presets:**")
btn_c1, btn_c2, btn_c3, btn_c4 = st.columns(4)

if btn_c1.button("Show All Planets"):
    st.session_state.selected_planets = all_planets.copy()
    st.rerun()

if btn_c2.button("Malefics Only"):
    st.session_state.selected_planets = MALEFICS.copy()
    st.rerun()

if btn_c3.button("Benefics Only"):
    st.session_state.selected_planets = BENEFICS.copy()
    st.rerun()

if btn_c4.button("Gold Key Movers"):
    st.session_state.selected_planets = ["Sun", "Jupiter", "Saturn", "Mars"]
    st.rerun()

selected_planets = st.multiselect(
    "Filter SVG Vedha Rays by Planet:",
    options=all_planets,
    default=st.session_state.selected_planets,
    key="planet_multiselect_filter"
)

sbc_html = render_sbc_grid_visual_with_svg(data, selected_planets, effective_datetime)
st.components.v1.html(sbc_html, height=760, scrolling=False)

# Compact Table for Planetary Vedha Details
st.divider()
st.subheader("🔍 Planetary Vedha Details")

table_data = []
for p in data:
    table_data.append({
        "Planet": p["Planet"],
        "Nakshatra": p["Nakshatra"],
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
        "Speed (°/d)": st.column_config.TextColumn("Speed (°/d)", width="small"),
        "Motion": st.column_config.TextColumn("Motion", width="medium"),
        "Primary Aspect": st.column_config.TextColumn("Primary Aspect", width="medium"),
        "🎯 Front Vedha": st.column_config.TextColumn("🎯 Front Vedha", width="medium"),
        "⬅️ Left Vedha": st.column_config.TextColumn("⬅️ Left Vedha", width="medium"),
        "➡️ Right Vedha": st.column_config.TextColumn("➡️ Right Vedha", width="medium"),
    }
)
