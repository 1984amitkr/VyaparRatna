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

SBC_GRID_POSITIONS = {
    "Krittika": (0, 1), "Rohini": (0, 2), "Mrigashira": (0, 3), "Ardra": (0, 4), 
    "Punarvasu": (0, 5), "Pushya": (0, 6), "Ashlesha": (0, 7),
    "Magha": (1, 8), "Purva Phalguni": (2, 8), "Uttara Phalguni": (3, 8), "Hasta": (4, 8), 
    "Chitra": (5, 8), "Svati": (6, 8), "Vishakha": (7, 8),
    "Anuradha": (8, 7), "Jyeshtha": (8, 6), "Mula": (8, 5), "Purva Ashadha": (8, 4), 
    "Uttara Ashadha": (8, 3), "Abhijit": (8, 2), "Shravana": (8, 1),
    "Dhanishta": (7, 0), "Shatabhisha": (6, 0), "Purva Bhadrapada": (5, 0), "Uttara Bhadrapada": (4, 0), 
    "Revati": (3, 0), "Ashwini": (2, 0), "Bharani": (1, 0)
}

GRID_TO_NAKSHATRA = {v: k for k, v in SBC_GRID_POSITIONS.items()}

# VARNADIPANCHAK MAPPING (INNER 7x7 GRID LAYOUT)
VARNADIPANCHAK_GRID = {
    # Layer 1 (Outer Inner Border - Svara/Vowels & Tithi)
    (1, 1): "अ / Nanda",   (1, 2): "आ / Bhadra",  (1, 3): "इ / Jaya",    (1, 4): "ई / Rikta",   (1, 5): "उ / Purna",   (1, 6): "ऊ / Nanda",   (1, 7): "ऋ / Bhadra",
    (2, 1): "अः / Purna",  (3, 1): "अं / Rikta",  (4, 1): "औ / Jaya",    (5, 1): "ओ / Bhadra",  (6, 1): "ऐ / Nanda",   (7, 1): "ए / Purna",
    (2, 7): "ॠ / Jaya",    (3, 7): "ऌ / Rikta",   (4, 7): "ॡ / Purna",   (5, 7): "ए / Nanda",   (6, 7): "ऐ / Bhadra",  (7, 7): "ओ / Jaya",
    (7, 2): "अः / Rikta",  (7, 3): "अं / Purna",  (7, 4): "औ / Nanda",   (7, 5): "ओ / Bhadra",  (7, 6): "ऐ / Jaya",

    # Layer 2 (Rashi & Varna Outer)
    (2, 2): "Mesha (Aries)",    (2, 3): "Vrishaba (Taurus)", (2, 4): "Mithuna (Gemini)", (2, 5): "Karka (Cancer)",   (2, 6): "Simha (Leo)",
    (3, 2): "Meena (Pisces)",                                                                                         (3, 6): "Kanya (Virgo)",
    (4, 2): "Kumbha (Aqua)",                                                                                          (4, 6): "Tula (Libra)",
    (5, 2): "Makara (Capri)",                                                                                         (5, 6): "Vrishchika (Scorpio)",
    (6, 2): "Dhanu (Sagit)",    (6, 3): "क, ख, ग, घ",        (6, 4): "च, छ, ज, झ",       (6, 5): "ट, ठ, ड, ढ",    (6, 6): "त, थ, द, ध",

    # Layer 3 (Inner Varna & Svara Core)
    (3, 3): "प, फ, ब, भ", (3, 4): "म, य, र, ल", (3, 5): "व, श, ष, स",
    (4, 3): "ह, क्ष",      (4, 4): "☸ CENTER",   (4, 5): "अ, आ, इ, ई",
    (5, 3): "उ, ऊ, ऋ, ॠ", (5, 4): "ऌ, ॡ, ए, ऐ", (5, 5): "ओ, औ, अं, अः"
}

# -------------------------------------------------------------------
# 2. ACCURATE NAKSHATRA MAPPING
# -------------------------------------------------------------------
def get_sbc_nakshatra(lon: float) -> str:
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

    # Standard Fallback Positions
    fallback_naks = {
        "Sun": "Purva Phalguni", "Moon": "Rohini", "Mars": "Chitra", 
        "Mercury": "Magha", "Jupiter": "Rohini", "Venus": "Purva Phalguni", 
        "Saturn": "Shatabhisha", "Rahu": "Purva Bhadrapada", "Ketu": "Purva Phalguni"
    }

    for p_name, nak_name in fallback_naks.items():
        speed = AVERAGE_DAILY_SPEEDS.get(p_name, 1.0)
        vedha = calculate_vedha(p_name, nak_name, speed)
        planet_data.append({
            "Planet": p_name, "Longitude": 0.0, "Speed (°/day)": speed,
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
def render_sbc_grid_visual_with_svg(planet_data, selected_planets):
    CELL_SIZE = 100
    GRID_DIM = 900
    
    planet_positions = {}
    vedha_targets = set()
    svg_lines = []

    for p in planet_data:
        nak = p["Nakshatra"]
        planet_positions.setdefault(nak, []).append(p["Planet"])

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

        stroke_color = "#ff4b4b" if p_name in MALEFICS else "#00c853"

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

                stroke_width = "4" if is_primary else "1.5"
                opacity = "0.95" if is_primary else "0.40"
                dash_array = "none" if is_primary else "6,4"

                svg_lines.append(
                    f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                    f'stroke="{stroke_color}" stroke-width="{stroke_width}" '
                    f'stroke-linecap="round" stroke-dasharray="{dash_array}" opacity="{opacity}" />'
                )

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ margin: 0; background-color: #0e1117; color: white; }}
        .sbc-container {{ position: relative; width: 100%; max-width: 650px; margin: 0 auto; aspect-ratio: 1 / 1; }}
        .sbc-table-svg {{ width: 100%; height: 100%; border-collapse: collapse; text-align: center; font-family: sans-serif; table-layout: fixed; }}
        .sbc-cell-svg {{ border: 1px solid #333; vertical-align: middle; padding: 2px; font-size: 10px; box-sizing: border-box; word-wrap: break-word; }}
        .sbc-outer-svg {{ background-color: #181d24; color: #e0e0e0; font-weight: bold; }}
        .sbc-inner-varna {{ background-color: #0d131a; color: #8a9ba8; font-size: 9px; font-weight: 500; }}
        .sbc-center-cell {{ background-color: #161020; color: #d0a0ff; font-weight: bold; }}
        .sbc-badge {{ display: inline-block; padding: 1px 3px; margin: 1px; border-radius: 3px; font-size: 9px; font-weight: bold; }}
        .bg-malefic {{ background-color: #ff4b4b; color: white; }}
        .bg-benefic {{ background-color: #00c853; color: white; }}
        .is-target {{ border: 2px solid #ffaa00 !important; background-color: #2a2000 !important; }}
    </style>
    </head>
    <body>
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
                is_tgt = nak_name in vedha_targets
                cell_cls = "sbc-cell-svg sbc-outer-svg" + (" is-target" if is_tgt else "")
                planets = planet_positions.get(nak_name, [])
                
                badges = "".join([f"<span class='sbc-badge {'bg-malefic' if p in MALEFICS else 'bg-benefic'}'>{p}</span>" for p in planets])

                html += f"""
                <td class='{cell_cls}'>
                    <div style='font-size: 10px; margin-top: 2px;'>{nak_name}</div>
                    <div style='margin-top:2px;'>{badges}</div>
                </td>
                """
            else:
                varna_val = VARNADIPANCHAK_GRID.get((r, c), "")
                is_center = (r == 4 and c == 4)
                inner_cls = "sbc-cell-svg sbc-center-cell" if is_center else "sbc-cell-svg sbc-inner-varna"
                html += f"<td class='{inner_cls}'>{varna_val}</td>"
        html += "</tr>"

    html += "</table></div></body></html>"
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
st.caption(f"Sarvatobhadra Chakra Analysis • Mumbai Reference Location ({MUMBAI_LAT}° N, {MUMBAI_LON}° E)")

# -------------------------------------------------------------------
# 7. SIDEBAR CONTROLS (REFRESH + HISTORICAL VIEW)
# -------------------------------------------------------------------
st.sidebar.header("🕹️ Mode & Time Controller")

if st.session_state.mode == "LIVE":
    st.sidebar.success("🔴 LIVE MODE (Auto-Refreshing every 5 mins)")
else:
    st.sidebar.warning("⏳ HISTORICAL MODE (Auto-Refresh Paused)")

if st.sidebar.button("🔄 Reset to Current Mumbai Time"):
    st.session_state.mode = "LIVE"
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("📅 Date & Time Input")

now_mumbai = datetime.datetime.now(MUMBAI_TZ)

if st.session_state.mode == "LIVE":
    active_date = now_mumbai.date()
    active_time = now_mumbai.time()
else:
    active_date = st.session_state.get("hist_date", now_mumbai.date())
    active_time = st.session_state.get("hist_time", now_mumbai.time())

selected_date = st.sidebar.date_input("Select Date", active_date)
selected_time = st.sidebar.time_input("Select Time (IST)", active_time)

combined_input = datetime.datetime.combine(selected_date, selected_time, tzinfo=MUMBAI_TZ)
time_diff = abs((combined_input - now_mumbai).total_seconds())

if time_diff > 60:
    st.session_state.mode = "HISTORICAL"
    st.session_state.hist_date = selected_date
    st.session_state.hist_time = selected_time

effective_datetime = combined_input if st.session_state.mode == "HISTORICAL" else now_mumbai

# -------------------------------------------------------------------
# 8. AUTO-REFRESH SCRIPT FOR LIVE MODE
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
    f"| **Location:** Mumbai, India "
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
st.caption("🔴 Red = Malefic Planet | 🟢 Green = Benefic Planet | 🟠 Yellow Highlight = Active Vedha Target | 🔤 Inner 7x7 Grid = Varnadipanchak")

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

sbc_html = render_sbc_grid_visual_with_svg(data, selected_planets)
st.components.v1.html(sbc_html, height=670, scrolling=False)

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
