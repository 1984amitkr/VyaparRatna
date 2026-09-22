import streamlit as st
import datetime
import zoneinfo
import swisseph as swe

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

PLANET_IDS = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE, "Ketu": swe.MEAN_NODE
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
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    
    julian_day = swe.julday(
        utc_dt.year, utc_dt.month, utc_dt.day, 
        utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
    )

    planet_data = []
    for p_name, p_id in PLANET_IDS.items():
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
            "Planet": p_name,
            "Longitude": lon,
            "Longitude_str": f"{lon:.2f}°",
            "Speed (°/day)": round(speed, 4),
            "Nakshatra": nak_name,
            "Motion": vedha["Motion"],
            "Primary Vedha": vedha["Primary Vedha"],
            "Front Target": vedha["Front Target"],
            "Left Target": vedha["Left Target"],
            "Right Target": vedha["Right Target"],
            "All Targets": vedha["All_Targets"]
        })

    return planet_data

# -------------------------------------------------------------------
# 4. GOLD TRADING ANALYSIS ENGINE
# -------------------------------------------------------------------
def analyze_gold_market(planet_data):
    p_map = {p["Planet"]: p for p in planet_data}
    
    sun = p_map["Sun"]
    jupiter = p_map["Jupiter"]

    bullish_factors = []
    bearish_factors = []
    score = 0

    if "Atichara" in sun["Motion"]:
        score += 2
        bullish_factors.append("Sun is in Atichara (Fast Direct) — Upward gold momentum.")
    elif "Manda" in sun["Motion"]:
        score -= 1
        bearish_factors.append("Sun is Manda (Slow) — Stagnant/slight downward bias.")

    if "Vakra" in jupiter["Motion"]:
        score += 1.5
        bullish_factors.append("Jupiter Retrograde (Vakra) — Increases physical gold safe-haven demand.")
    elif "Atichara" in jupiter["Motion"]:
        score += 1
        bullish_factors.append("Jupiter in Atichara — Positive financial expansion.")

    sun_nak = sun["Nakshatra"]
    afflicting_malefics = []
    for p in planet_data:
        if p["Planet"] in MALEFICS and p["Planet"] != "Sun":
            if sun_nak in p["All Targets"]:
                afflicting_malefics.append(f"{p['Planet']} ({p['Motion']})")

    if afflicting_malefics:
        score -= 2 * len(afflicting_malefics)
        bearish_factors.append(f"Asubha Vedha on Sun's Nakshatra ({sun_nak}) by: {', '.join(afflicting_malefics)}.")

    jup_nak = jupiter["Nakshatra"]
    jup_afflictions = [p["Planet"] for p in planet_data if p["Planet"] in MALEFICS and jup_nak in p["All Targets"]]
    if jup_afflictions:
        score -= 1.5 * len(jup_afflictions)
        bearish_factors.append(f"Jupiter's Nakshatra ({jup_nak}) under Vedha from {', '.join(jup_afflictions)}.")

    if score >= 2:
        signal = "BULLISH 📈"
        bias = "Buy on Dips / Positive Sentiment"
    elif score <= -2:
        signal = "BEARISH 📉"
        bias = "Sell on Rallies / Downward Pressure"
    else:
        signal = "NEUTRAL / VOLATILE ⚠️"
        bias = "Range-Bound / Exercise Caution"

    return {
        "Signal": signal,
        "Bias": bias,
        "Score": score,
        "Bullish Factors": bullish_factors,
        "Bearish Factors": bearish_factors
    }

# -------------------------------------------------------------------
# 5. RENDER VISUAL SARVATOBHADRA CHAKRA (9x9 GRID)
# -------------------------------------------------------------------
def render_sbc_grid_visual(planet_data):
    # Map planets to their current Nakshatras
    planet_positions = {}
    vedha_targets = set()

    for p in planet_data:
        nak = p["Nakshatra"]
        if nak not in planet_positions:
            planet_positions[nak] = []
        planet_positions[nak].append(p["Planet"])
        
        # Add Vedha target Nakshatras
        for target in p["All Targets"]:
            vedha_targets.add(target)

    # Generate 9x9 HTML Table
    html = """
    <style>
        .sbc-table { width: 100%; max-width: 750px; margin: 0 auto; border-collapse: collapse; text-align: center; font-family: sans-serif; }
        .sbc-cell { border: 1px solid #444; height: 65px; width: 11%; vertical-align: top; padding: 4px; font-size: 11px; position: relative; }
        .sbc-outer { background-color: #1e2530; color: #fff; font-weight: bold; }
        .sbc-inner { background-color: #0e1117; color: #666; }
        .sbc-planet { display: inline-block; padding: 2px 4px; margin: 1px; border-radius: 3px; font-size: 10px; font-weight: bold; }
        .p-malefic { background-color: #ff4b4b; color: white; }
        .p-benefic { background-color: #00c853; color: white; }
        .vedha-target { border: 2px solid #ffaa00 !important; background-color: #3d2b00 !important; }
        .corner-cell { background-color: #111; }
    </style>
    <table class="sbc-table">
    """

    for r in range(9):
        html += "<tr>"
        for c in range(9):
            nak_name = GRID_TO_NAKSHATRA.get((r, c), None)
            
            if nak_name:
                is_target = nak_name in vedha_targets
                cell_class = "sbc-cell sbc-outer" + (" vedha-target" if is_target else "")
                planets_here = planet_positions.get(nak_name, [])
                
                planet_badge = ""
                for p in planets_here:
                    badge_cls = "p-malefic" if p in MALEFICS else "p-benefic"
                    planet_badge += f"<span class='sbc-planet {badge_cls}'>{p}</span>"

                html += f"""
                <td class='{cell_class}'>
                    <div>{nak_name}</div>
                    <div style='margin-top:4px;'>{planet_badge}</div>
                </td>
                """
            else:
                if (r, c) in [(0,0), (0,8), (8,0), (8,8)]:
                    html += "<td class='sbc-cell corner-cell'></td>"
                else:
                    html += "<td class='sbc-cell sbc-inner'></td>"
        html += "</tr>"

    html += "</table>"
    return html

# -------------------------------------------------------------------
# 6. STREAMLIT APP CONFIGURATION & STATE
# -------------------------------------------------------------------
st.set_page_config(page_title="VyaparRatna SBC Gold Engine", layout="wide")

if "mode" not in st.session_state:
    st.session_state.mode = "LIVE"

st.title("🏆 VyaparRatna SBC Gold Trading Engine")
st.caption(f"Sarvatobhadra Chakra Analysis • Mumbai Reference Location ({MUMBAI_LAT}° N, {MUMBAI_LON}° E)")

# -------------------------------------------------------------------
# 7. SIDEBAR CONTROLS
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
# 8. CLIENT-SIDE AUTO-REFRESH (LIVE MODE ONLY)
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
    f"| **Refresh State:** {'🟢 Browser Auto-Refresh Active (300s)' if st.session_state.mode == 'LIVE' else '⏸️ Paused (Historical Analysis)'}"
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

# Visual SBC Grid (Replaces tabular dataframe)
st.divider()
st.subheader("🕸️ Visual Sarvatobhadra Chakra & Active Vedha Paths")
st.caption("🔴 Red = Malefic Planet | 🟢 Green = Benefic Planet | 🟠 Yellow Highlight = Active Vedha Target")

sbc_html = render_sbc_grid_visual(data)
st.markdown(sbc_html, unsafe_allow_html=True)

# Detailed Cards
st.divider()
st.subheader("🔍 Planetary Vedha Details")
cols = st.columns(3)
for idx, p in enumerate(data):
    with cols[idx % 3]:
        with st.container(border=True):
            st.markdown(f"### {p['Planet']}")
            st.write(f"**Nakshatra:** {p['Nakshatra']} | **Speed:** {p['Speed (°/day)']}°/d")
            st.write(f"**Motion:** `{p['Motion']}`")
            st.write(f"**Active Primary Aspect:** `{p['Primary Vedha']}`")
            st.markdown("---")
            st.write(f"🎯 **Front Vedha:** {p['Front Target']}")
            st.write(f"⬅️ **Left Vedha:** {p['Left Target']}")
            st.write(f"➡️ **Right Vedha:** {p['Right Target']}")
