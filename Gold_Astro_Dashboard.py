import streamlit as st
import pandas as pd
import datetime
import numpy as np
import plotly.graph_objects as go

# Import Swiss Ephemeris for accurate topocentric calculations
try:
    import swisseph as swe
    HAS_SWISSEPH = True
except ImportError:
    HAS_SWISSEPH = False

# Set Streamlit Page Config
st.set_page_config(
    page_title="Vyapar Ratna - Gold Astro Engine V3.5 (Mumbai Ephemeris)",
    page_icon="🪙",
    layout="wide"
)

# --- MUMBAI LOCATION CONSTANTS ---
MUMBAI_LAT = 18.9220
MUMBAI_LON = 72.8347
MUMBAI_ELEV = 14.0  # meters above sea level

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

VEDHA_PAIRS = {
    0: 13, 1: 12, 2: 11, 3: 10, 4: 9, 5: 8, 6: 7,
    7: 6, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1, 13: 0,
    14: 26, 15: 25, 16: 24, 17: 23, 18: 22, 19: 21, 20: 20,
    21: 19, 22: 18, 23: 17, 24: 16, 25: 15, 26: 14
}

PLANET_WEIGHTS = {
    "Sun": 1.5, "Moon": 0.8, "Mercury": 1.0, "Venus": 1.2,
    "Mars": 2.5, "Jupiter": 2.0, "Saturn": -2.5, "Rahu": -1.8, "Ketu": -1.2
}

def calculate_mumbai_ephemeris(calc_date, calc_time):
    """Calculates topocentric Sidereal (Lahiri) longitudes for Mumbai, India."""
    
    # Combine date and time
    dt = datetime.datetime.combine(calc_date, calc_time)
    
    # Convert IST (UTC+5:30) to UTC
    utc_dt = dt - datetime.timedelta(hours=5, minutes=30)
    
    if HAS_SWISSEPH:
        # Swiss Ephemeris Setup
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        
        # Set Topocentric Location for Mumbai
        swe.set_topo(MUMBAI_LON, MUMBAI_LAT, MUMBAI_ELEV)
        
        # Calculate Julian Day in UT
        julian_day = swe.julday(
            utc_dt.year, utc_dt.month, utc_dt.day,
            utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
        )
        
        bodies_map = {
            "Sun": swe.SUN,
            "Moon": swe.MOON,
            "Mercury": swe.MERCURY,
            "Venus": swe.VENUS,
            "Mars": swe.MARS,
            "Jupiter": swe.JUPITER,
            "Saturn": swe.SATURN,
            "Rahu": swe.MEAN_NODE,
        }
        
        flags = swe.FLG_SIDEREAL | swe.FLG_SPEED | swe.FLG_TOPOCTR
        positions = {}
        
        for name, planet_id in bodies_map.items():
            res, _ = swe.calc_ut(julian_day, planet_id, flags)
            sid_lon = res[0] % 360
            speed = res[3]
            is_retro = speed < 0
            
            positions[name] = {
                "longitude": sid_lon,
                "speed": speed,
                "is_retrograde": is_retro
            }
            
        # Calculate Ketu (180 deg opposite Rahu)
        rahu_lon = positions["Rahu"]["longitude"]
        positions["Ketu"] = {
            "longitude": (rahu_lon + 180.0) % 360,
            "speed": positions["Rahu"]["speed"],
            "is_retrograde": True
        }
        
    else:
        # Fallback approximation adjusted for Mumbai offset
        d = (utc_dt - datetime.datetime(2000, 1, 1, 12, 0)).total_seconds() / 86400.0
        
        sun_lon = (280.460 + 0.9856474 * d) % 360
        moon_lon = (218.316 + 13.176396 * d) % 360
        mercury_lon = (252.251 + 4.092334 * d) % 360
        venus_lon = (181.979 + 1.602130 * d) % 360
        mars_lon = (355.433 + 0.524033 * d) % 360
        jupiter_lon = (34.351 + 0.083091 * d) % 360
        saturn_lon = (50.077 + 0.033459 * d) % 360
        rahu_lon = (125.044 - 0.0529539 * d) % 360
        ketu_lon = (rahu_lon + 180.0) % 360

        ayanamsha = 23.85 + (calc_date.year - 2000) * (50.29 / 3600.0)

        bodies = {
            "Sun": (sun_lon - ayanamsha) % 360,
            "Moon": (moon_lon - ayanamsha) % 360,
            "Mercury": (mercury_lon - ayanamsha) % 360,
            "Venus": (venus_lon - ayanamsha) % 360,
            "Mars": (mars_lon - ayanamsha) % 360,
            "Jupiter": (jupiter_lon - ayanamsha) % 360,
            "Saturn": (saturn_lon - ayanamsha) % 360,
            "Rahu": (rahu_lon - ayanamsha) % 360,
            "Ketu": (ketu_lon - ayanamsha) % 360,
        }

        synodic_retro = {
            "Mars": np.sin(np.radians((mars_lon - sun_lon) % 360)) < -0.85,
            "Jupiter": np.sin(np.radians((jupiter_lon - sun_lon) % 360)) < -0.90,
            "Saturn": np.sin(np.radians((saturn_lon - sun_lon) % 360)) < -0.90,
            "Mercury": np.sin(np.radians((mercury_lon - sun_lon) % 360)) < -0.75,
            "Venus": np.sin(np.radians((venus_lon - sun_lon) % 360)) < -0.80,
        }

        positions = {}
        for name, sid_lon in bodies.items():
            is_retro = synodic_retro.get(name, False)
            if name in ["Rahu", "Ketu"]:
                is_retro = True
            positions[name] = {
                "longitude": sid_lon,
                "speed": -0.1 if is_retro else 1.0,
                "is_retrograde": is_retro
            }

    # Enrich positions with Sign, Nakshatra, and Pada
    for name, data in positions.items():
        sid_lon = data["longitude"]
        sign_idx = int(sid_lon // 30)
        nak_exact = sid_lon / (360.0 / 27.0)
        nak_idx = int(nak_exact)
        rem_deg = (nak_exact - nak_idx) * (360.0 / 27.0)
        pada = int(rem_deg // (360.0 / 108.0)) + 1

        data["sign"] = ZODIAC_SIGNS[sign_idx]
        data["sign_idx"] = sign_idx
        data["nakshatra"] = NAKSHATRAS[nak_idx]
        data["nak_idx"] = nak_idx
        data["pada"] = pada

    return positions

def calculate_aspects(positions):
    aspects = []
    planets = list(positions.keys())
    
    for i in range(len(planets)):
        for j in range(i + 1, len(planets)):
            p1, p2 = planets[i], planets[j]
            lon1 = positions[p1]["longitude"]
            lon2 = positions[p2]["longitude"]
            
            diff = abs(lon1 - lon2)
            if diff > 180:
                diff = 360 - diff

            aspect_type = None
            weight = 0.0
            
            if diff <= 6.0:
                aspect_type = "Conjunction (0°)"
                weight = 2.0 if p1 in ["Jupiter", "Venus", "Sun"] or p2 in ["Jupiter", "Venus", "Sun"] else -1.5
            elif 174.0 <= diff <= 180.0:
                aspect_type = "Opposition (180°)"
                weight = -2.0
            elif 114.0 <= diff <= 126.0:
                aspect_type = "Trine (120°)"
                weight = 1.5
            elif 84.0 <= diff <= 96.0:
                aspect_type = "Square (90°)"
                weight = -1.2
            elif 54.0 <= diff <= 66.0:
                aspect_type = "Sextile (60°)"
                weight = 1.0

            sign_diff = (positions[p2]["sign_idx"] - positions[p1]["sign_idx"]) % 12
            if p1 == "Mars" and sign_diff in [3, 7]:
                aspect_type = f"Mars Special Drishti ({sign_diff + 1}th House)"
                weight = -1.8
            elif p1 == "Jupiter" and sign_diff in [4, 8]:
                aspect_type = f"Jupiter Special Drishti ({sign_diff + 1}th House)"
                weight = 2.5
            elif p1 == "Saturn" and sign_diff in [2, 9]:
                aspect_type = f"Saturn Special Drishti ({sign_diff + 1}th House)"
                weight = -2.2

            if aspect_type:
                aspects.append({
                    "P1": p1,
                    "P2": p2,
                    "Aspect": aspect_type,
                    "Angular Diff": f"{diff:.1f}°",
                    "Weight": weight
                })
                
    return aspects

def calculate_vedha(positions):
    vedha_events = []
    malefics = ["Saturn", "Mars", "Rahu", "Ketu", "Sun"]
    
    for p1, data1 in positions.items():
        nak1 = data1["nak_idx"]
        target_vedha_nak = VEDHA_PAIRS.get(nak1)
        
        for p2, data2 in positions.items():
            if p1 != p2 and data2["nak_idx"] == target_vedha_nak:
                is_malefic_vedha = p2 in malefics
                impact = -2.0 if is_malefic_vedha else 0.5
                
                vedha_events.append({
                    "Obstructing Planet": p2,
                    "Target Planet": p1,
                    "Target Nakshatra": NAKSHATRAS[nak1],
                    "Counter Nakshatra": NAKSHATRAS[target_vedha_nak],
                    "Nature": "Malefic Affliction" if is_malefic_vedha else "Benefic Mutual Vedha",
                    "Score Impact": impact
                })
                
    return vedha_events

def render_realtime_ephemeris_chart(positions):
    fig = go.Figure()

    for i, sign in enumerate(ZODIAC_SIGNS):
        angle = i * 30
        fig.add_trace(go.Scatterpolar(
            r=[0, 10],
            theta=[angle, angle],
            mode="lines",
            line=dict(color="rgba(150, 150, 150, 0.3)", width=1),
            showlegend=False,
            hoverinfo="none"
        ))
        fig.add_trace(go.Scatterpolar(
            r=[11],
            theta=[angle + 15],
            mode="text",
            text=[sign],
            textfont=dict(size=11, color="gold"),
            showlegend=False
        ))

    planet_colors = {
        "Sun": "#FFD700", "Moon": "#C0C0C0", "Mercury": "#32CD32",
        "Venus": "#FF69B4", "Mars": "#FF4500", "Jupiter": "#FFA500",
        "Saturn": "#4682B4", "Rahu": "#8A2BE2", "Ketu": "#4B0082"
    }

    for name, data in positions.items():
        lon = data["longitude"]
        retro_str = " (R)" if data["is_retrograde"] else ""
        label = f"{name}{retro_str}<br>{data['sign']}<br>{data['nakshatra']} P{data['pada']}"
        
        fig.add_trace(go.Scatterpolar(
            r=[8.5],
            theta=[lon],
            mode="markers+text",
            marker=dict(size=14, color=planet_colors.get(name, "#FFFFFF")),
            text=[name],
            textposition="top center",
            name=f"{name} ({lon:.2f}°)",
            hoverinfo="text",
            hovertext=label
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=False, range=[0, 12]),
            angularaxis=dict(
                tickmode="array",
                tickvals=list(range(0, 360, 30)),
                ticktext=ZODIAC_SIGNS,
                direction="counterclockwise",
                rotation=0
            ),
            bgcolor="rgba(15, 23, 42, 0.8)"
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=30, r=30, t=30, b=30),
        height=550,
        showlegend=True,
        legend=dict(orientation="h", y=-0.1)
    )

    return fig

# --- STREAMLIT DASHBOARD UI ---
st.title("🪙 Vyapar Ratna Gold Astro Engine V3.5")
st.caption("📍 Location Locked: **Mumbai, India** (18.9220° N, 72.8347° E) | IST Timezone (UTC+5:30)")

st.sidebar.header("🗓️ Mumbai Time Controls")
calc_date = st.sidebar.date_input("Evaluation Date", datetime.date.today())
calc_time = st.sidebar.time_input("Evaluation Time (IST)", datetime.time(9, 15))  # Default to MCX Market Open

# Engine Status Badge
if HAS_SWISSEPH:
    st.sidebar.success("Engine: High-Precision Swiss Ephemeris")
else:
    st.sidebar.warning("Engine: Approximation Engine (Install `pyswisseph` for Swiss Ephemeris)")

positions = calculate_mumbai_ephemeris(calc_date, calc_time)
aspects = calculate_aspects(positions)
vedhas = calculate_vedha(positions)

base_score = sum([PLANET_WEIGHTS.get(p, 0.0) * (-1.2 if data["is_retrograde"] and p in ["Saturn", "Rahu", "Ketu"] else 1.0) for p, data in positions.items()])
aspect_score = sum([a["Weight"] for a in aspects])
vedha_score = sum([v["Score Impact"] for v in vedhas])

total_score = base_score + aspect_score + vedha_score

if total_score >= 7.0:
    regime = "STRONG BULLISH REGIME"
    color = "green"
    action = "LONG TRADES PERMITTED — Align with Technical Breakouts"
elif 3.0 <= total_score < 7.0:
    regime = "MODERATE BULLISH BIAS"
    color = "lightgreen"
    action = "CAUTIOUS LONG TRADES — Trailing Stop Losses Mandatory"
elif -3.0 < total_score < 3.0:
    regime = "NEUTRAL / CONSOLIDATION ZONE"
    color = "gray"
    action = "NO CLEAR ASTRO EDGE — Range Bound Strategies Recommended"
elif -7.0 < total_score <= -3.0:
    regime = "MODERATE BEARISH BIAS"
    color = "orange"
    action = "CAUTIOUS SHORT TRADES — Tight Trailing SL"
else:
    regime = "STRONG BEARISH REGIME"
    color = "red"
    action = "SHORT TRADES PERMITTED — Align with Technical Breakdown"

m1, m2, m3, m4 = st.columns(4)
m1.metric("Composite Astro Score", f"{total_score:+.2f}")
m2.metric("Base Placement Score", f"{base_score:+.2f}")
m3.metric("Aspect Net Score", f"{aspect_score:+.2f}")
m4.metric("Vedha Net Impact", f"{vedha_score:+.2f}")

st.markdown(f"### Market Bias: :{color}[{regime}]")
st.info(f"**Execution Directive:** {action}")

st.divider()

st.subheader("🪐 Mumbai Topocentric 360° Ephemeris Wheel")
fig = render_realtime_ephemeris_chart(positions)
st.plotly_chart(fig, use_container_width=True)

st.divider()

tab1, tab2, tab3 = st.columns(3)

with tab1:
    st.subheader("📌 Positions & Pada (Mumbai IST)")
    pos_df = []
    for p, val in positions.items():
        pos_df.append({
            "Planet": p,
            "Sign": val["sign"],
            "Nakshatra": val["nakshatra"],
            "Pada": f"Pada {val['pada']}",
            "Motion": "RETROGRADE" if val["is_retrograde"] else "DIRECT"
        })
    st.dataframe(pd.DataFrame(pos_df), hide_index=True, use_container_width=True)

with tab2:
    st.subheader("⚡ Active Aspects & Drishti")
    if aspects:
        st.dataframe(pd.DataFrame(aspects)[["P1", "P2", "Aspect", "Weight"]], hide_index=True, use_container_width=True)
    else:
        st.write("No major planetary aspects active.")

with tab3:
    st.subheader("🛑 Active Vedha (Obstructions)")
    if vedhas:
        st.dataframe(pd.DataFrame(vedhas)[["Obstructing Planet", "Target Planet", "Target Nakshatra", "Score Impact"]], hide_index=True, use_container_width=True)
    else:
        st.write("No active planetary Vedha detected for this date/time.")
