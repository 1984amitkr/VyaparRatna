import streamlit as st
import datetime
import swisseph as swe

# -------------------------------------------------------------------
# 1. CONSTANTS & SBC GRID CONFIGURATION
# -------------------------------------------------------------------
NAKSHATRAS_28 = [
    "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha",
    "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Svati", "Vishakha",
    "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Abhijit", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati", "Ashwini", "Bharani"
]

AVERAGE_DAILY_SPEEDS = {
    "Sun": 0.9856, "Moon": 13.1764, "Mars": 0.524, "Mercury": 1.383,
    "Jupiter": 0.0831, "Venus": 1.200, "Saturn": 0.0335, "Rahu": -0.0529, "Ketu": -0.0529
}

# 9x9 Perimeter Layout
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
# 2. HELPER FUNCTIONS: CALCULATION & VEDHA LOGIC
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

    # Directions based on edge location
    if r == 0:   (dr_f, dc_f), (dr_l, dc_l), (dr_r, dc_r) = (1, 0), (1, 1), (1, -1)
    elif r == 8: (dr_f, dc_f), (dr_l, dc_l), (dr_r, dc_r) = (-1, 0), (-1, -1), (-1, 1)
    elif c == 8: (dr_f, dc_f), (dr_l, dc_l), (dr_r, dc_r) = (0, -1), (1, -1), (-1, -1)
    else:        (dr_f, dc_f), (dr_l, dc_l), (dr_r, dc_r) = (0, 1), (-1, 1), (1, 1)

    front_ray = trace_ray(r, c, dr_f, dc_f)
    left_ray  = trace_ray(r, c, dr_l, dc_l)
    right_ray = trace_ray(r, c, dr_r, dc_r)

    # Motion rule shift
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
        "Right Target": GRID_TO_NAKSHATRA.get(right_ray[-1], "Inner Box") if right_ray else None
    }

def get_ephemeris_data(dt: datetime.datetime):
    # Set Lahiri Ayanamsa
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    julian_day = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0)

    planet_data = []
    for p_name, p_id in PLANET_IDS.items():
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
        res, _ = swe.calc_ut(julian_day, p_id, flags)
        lon = res[0]
        speed = res[3]

        if p_name == "Ketu":
            lon = (lon + 180) % 360
            speed = -speed

        # 28 Nakshatras mapped linearly (approx equal division including Abhijit span)
        nak_idx = int(lon // (360 / 28))
        nak_name = NAKSHATRAS_28[nak_idx % 28]

        vedha = calculate_vedha(p_name, nak_name, speed)

        planet_data.append({
            "Planet": p_name,
            "Longitude": f"{lon:.2f}°",
            "Speed (°/day)": round(speed, 4),
            "Nakshatra": nak_name,
            "Motion": vedha["Motion"],
            "Primary Vedha": vedha["Primary Vedha"],
            "Front Target": vedha["Front Target"],
            "Left Target": vedha["Left Target"],
            "Right Target": vedha["Right Target"]
        })

    return planet_data

# -------------------------------------------------------------------
# 3. STREAMLIT UI
# -------------------------------------------------------------------
st.set_page_config(page_title="Sarvatobhadra Chakra Vedha Engine", layout="wide")

st.title("🔮 Sarvatobhadra Chakra (SBC) Engine")
st.subheader("Real-Time Planetary Motion & Vedha Calculator")

# Sidebar - Date & Time Selection
st.sidebar.header("Date & Time Picker")
selected_date = st.sidebar.date_input("Select Date", datetime.date.today())
selected_time = st.sidebar.time_input("Select Time (UTC/Local)", datetime.time(12, 0))

combined_datetime = datetime.datetime.combine(selected_date, selected_time)

# Main Calculations
data = get_ephemeris_data(combined_datetime)

st.markdown(f"**Calculated Positions for:** `{combined_datetime.strftime('%Y-%m-%d %H:%M:%S')}`")

# Render Interactive Data Table
st.dataframe(
    data,
    column_config={
        "Planet": "Planet",
        "Nakshatra": "Host Nakshatra",
        "Motion": st.column_config.TextColumn("Motion State", help="Vakra, Atichara, Manda, or Sama"),
        "Primary Vedha": st.column_config.TextColumn("Active Primary Vedha", help="Shifted by planetary speed/motion"),
    },
    use_container_width=True
)

st.divider()

# Detailed Planetary Inspection Cards
st.subheader("Planetary Vedha Detail Breakdown")
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
