import streamlit as st
import pandas as pd
import datetime
import numpy as np

# Import Swiss Ephemeris
try:
    import swisseph as swe
    SWE_AVAILABLE = True
except ImportError:
    SWE_AVAILABLE = False

# Set Streamlit Page Config
st.set_page_config(
    page_title="Vyapar Ratna - Gold Astro Engine V2",
    page_icon="🪙",
    layout="wide"
)

# --- ASTRONOMICAL CONSTANTS & UTILITIES ---
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

# Vyapar Ratna V2 Rulebook with Machine Learning Optimized Weights
RULES_CONFIG = {
    "BULLISH": [
        {"id": "mars_retro", "name": "Mars Retrograde (मंगल वक्री)", "weight": 3.0, "layer": "Trend"},
        {"id": "saturn_retro_bull", "name": "Jupiter Retrograde (गुरु वक्री)", "weight": 2.5, "layer": "Trend"},
        {"id": "rahu_mars_conj", "name": "Rahu + Mars Conjunction (राहु-मंगल युति)", "weight": 2.0, "layer": "Trend"},
        {"id": "sun_pushya", "name": "Sun in Pushya (सूर्य पुष्य में)", "weight": 2.0, "layer": "Swing"},
        {"id": "mars_taurus", "name": "Mars in Taurus (मंगल वृषभ में)", "weight": 1.5, "layer": "Trend"},
        {"id": "jupiter_leo", "name": "Jupiter in Leo (गुरु सिंह में)", "weight": 1.0, "layer": "Trend"},
        {"id": "mars_leo", "name": "Mars in Leo (मंगल सिंह में)", "weight": 1.0, "layer": "Swing"},
        {"id": "mars_virgo", "name": "Mars in Virgo (मंगल कन्या में)", "weight": 1.0, "layer": "Swing"},
        {"id": "mars_capricorn", "name": "Mars in Capricorn (मंगल मकर में)", "weight": 1.0, "layer": "Trend"},
        {"id": "mercury_leo", "name": "Mercury in Leo (बुध सिंह में)", "weight": 1.0, "layer": "Swing"},
        {"id": "venus_leo", "name": "Venus in Leo (शुक्र सिंह में)", "weight": 1.0, "layer": "Swing"},
        {"id": "sun_libra", "name": "Sun in Libra (सूर्य तुला में)", "weight": 1.0, "layer": "Swing"},
        {"id": "rahu_cancer", "name": "Rahu in Cancer (राहु कर्क में बलवान)", "weight": 0.5, "layer": "Trend"},
        {"id": "sun_bharani", "name": "Sun in Bharani (सूर्य भरणी में)", "weight": 0.5, "layer": "Swing"},
        {"id": "sun_krittika", "name": "Sun in Krittika (सूर्य कृत्तिका में)", "weight": 0.5, "layer": "Swing"},
        {"id": "sun_punarvasu", "name": "Sun in Punarvasu (सूर्य पुनर्वसु में)", "weight": 0.5, "layer": "Swing"},
        {"id": "venus_rohini", "name": "Venus in Rohini (शुक्र रोहिणी में)", "weight": 0.5, "layer": "Swing"},
        {"id": "saturn_krittika", "name": "Saturn in Krittika (शनि कृत्तिका में)", "weight": 0.5, "layer": "Trend"},
        {"id": "moon_monday", "name": "Moon Sighting Monday (सोमवार चन्द्र-दर्शन)", "weight": 0.5, "layer": "Timing"},
        {"id": "moon_friday", "name": "Moon Sighting Friday (शुक्रवार चन्द्र-दर्शन)", "weight": 0.5, "layer": "Timing"},
    ],
    "BEARISH": [
        {"id": "saturn_retro", "name": "Saturn Retrograde (शनि वक्री)", "weight": -3.0, "layer": "Trend"},
        {"id": "rahu_gemini", "name": "Rahu in Gemini (राहु मिथुन में)", "weight": -2.0, "layer": "Trend"},
        {"id": "sun_anuradha", "name": "Sun in Anuradha (सूर्य अनुराधा में)", "weight": -2.0, "layer": "Swing"},
        {"id": "saturn_gemini", "name": "Saturn in Gemini (शनि मिथुन में)", "weight": -2.0, "layer": "Trend"},
        {"id": "mercury_gemini", "name": "Mercury in Gemini (बुध मिथुन में)", "weight": -1.0, "layer": "Swing"},
        {"id": "jupiter_capricorn", "name": "Jupiter in Capricorn (गुरु मकर में)", "weight": -1.0, "layer": "Trend"},
        {"id": "jupiter_aries", "name": "Jupiter in Aries (गुरु मेष में)", "weight": -1.0, "layer": "Trend"},
        {"id": "jupiter_sagittarius", "name": "Jupiter in Sagittarius (गुरु धनु में)", "weight": -1.0, "layer": "Trend"},
        {"id": "mercury_pushya", "name": "Mercury in Pushya (बुध पुष्य में)", "weight": -1.0, "layer": "Swing"},
        {"id": "jupiter_bharani", "name": "Jupiter in Bharani (गुरु भरणी में)", "weight": -1.0, "layer": "Trend"},
        {"id": "venus_jyeshtha", "name": "Venus in Jyeshtha (शुक्र ज्येष्ठा में)", "weight": -1.0, "layer": "Swing"},
        {"id": "moon_saturday", "name": "Moon Sighting Saturday (शनिवार चन्द्र-दर्शन)", "weight": -0.5, "layer": "Timing"},
    ]
}

def get_ephemeris_positions(calc_date):
    """Calculate planetary positions in Vedic Sidereal (Lahiri Ayanamsha) coordinates."""
    if not SWE_AVAILABLE:
        st.error("pyswisseph is not installed. Please run: pip install pyswisseph")
        return {}

    # Set Lahiri Ayanamsha
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    
    # Julian Day calculation
    jd = swe.julday(calc_date.year, calc_date.month, calc_date.day, 12.0)
    
    planet_map = {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mercury": swe.MERCURY,
        "Venus": swe.VENUS,
        "Mars": swe.MARS,
        "Jupiter": swe.JUPITER,
        "Saturn": swe.SATURN,
        "Rahu": swe.MEAN_NODE
    }

    positions = {}
    for p_name, p_code in planet_map.items():
        # Calculation with Sidereal flag
        res, _ = swe.calc_ut(jd, p_code, swe.FLG_SIDEREAL | swe.FLG_SPEED)
        lon = res[0] % 360
        speed = res[3]
        
        sign_idx = int(lon // 30)
        sign_name = ZODIAC_SIGNS[sign_idx]
        
        nak_idx = int(lon // (360 / 27))
        nak_name = NAKSHATRAS[nak_idx]
        
        is_retrograde = speed < 0 if p_name not in ["Sun", "Moon", "Rahu"] else False
        if p_name == "Rahu":
            is_retrograde = True # Rahu is naturally retrograde

        positions[p_name] = {
            "longitude": lon,
            "sign": sign_name,
            "nakshatra": nak_name,
            "is_retrograde": is_retrograde,
            "speed": speed
        }

    return positions

def evaluate_gas_rules(positions, calc_date):
    """Evaluate all Vyapar Ratna conditions against calculated planetary data."""
    if not positions:
        return 0.0, [], []

    triggered_bullish = []
    triggered_bearish = []
    
    weekday = calc_date.strftime("%A")

    # Helper function to check sign and nakshatra
    def is_in_sign(p, sign): return positions[p]["sign"] == sign
    def is_in_nak(p, nak): return positions[p]["nakshatra"] == nak
    def is_retro(p): return positions[p]["is_retrograde"]

    # --- BULLISH RULES EVALUATION ---
    if is_retro("Mars"): triggered_bullish.append("mars_retro")
    if is_retro("Jupiter"): triggered_bullish.append("saturn_retro_bull")
    if is_in_sign("Mars", "Taurus"): triggered_bullish.append("mars_taurus")
    if is_in_sign("Mars", "Leo"): triggered_bullish.append("mars_leo")
    if is_in_sign("Mars", "Virgo"): triggered_bullish.append("mars_virgo")
    if is_in_sign("Mars", "Capricorn"): triggered_bullish.append("mars_capricorn")
    if is_in_sign("Mercury", "Leo"): triggered_bullish.append("mercury_leo")
    if is_in_sign("Jupiter", "Leo"): triggered_bullish.append("jupiter_leo")
    if is_in_sign("Venus", "Leo"): triggered_bullish.append("venus_leo")
    if is_in_sign("Sun", "Libra"): triggered_bullish.append("sun_libra")
    if is_in_sign("Rahu", "Cancer"): triggered_bullish.append("rahu_cancer")
    
    # Rahu + Mars Conjunction (within 12 degrees in same sign)
    if is_in_sign("Mars", positions["Rahu"]["sign"]) and abs(positions["Mars"]["longitude"] - positions["Rahu"]["longitude"]) < 12.0:
        triggered_bullish.append("rahu_mars_conj")

    if is_in_nak("Sun", "Bharani"): triggered_bullish.append("sun_bharani")
    if is_in_nak("Sun", "Krittika"): triggered_bullish.append("sun_krittika")
    if is_in_nak("Sun", "Punarvasu"): triggered_bullish.append("sun_punarvasu")
    if is_in_nak("Sun", "Pushya"): triggered_bullish.append("sun_pushya")
    if is_in_nak("Venus", "Rohini"): triggered_bullish.append("venus_rohini")
    if is_in_nak("Saturn", "Krittika"): triggered_bullish.append("saturn_krittika")
    
    if weekday == "Monday": triggered_bullish.append("moon_monday")
    if weekday == "Friday": triggered_bullish.append("moon_friday")

    # --- BEARISH RULES EVALUATION ---
    if is_retro("Saturn"): triggered_bearish.append("saturn_retro")
    if is_in_sign("Rahu", "Gemini"): triggered_bearish.append("rahu_gemini")
    if is_in_sign("Saturn", "Gemini"): triggered_bearish.append("saturn_gemini")
    if is_in_sign("Mercury", "Gemini"): triggered_bearish.append("mercury_gemini")
    if is_in_sign("Jupiter", "Capricorn"): triggered_bearish.append("jupiter_capricorn")
    if is_in_sign("Jupiter", "Aries"): triggered_bearish.append("jupiter_aries")
    if is_in_sign("Jupiter", "Sagittarius"): triggered_bearish.append("jupiter_sagittarius")

    if is_in_nak("Sun", "Anuradha"): triggered_bearish.append("sun_anuradha")
    if is_in_nak("Mercury", "Pushya"): triggered_bearish.append("mercury_pushya")
    if is_in_nak("Jupiter", "Bharani"): triggered_bearish.append("jupiter_bharani")
    if is_in_nak("Venus", "Jyeshtha"): triggered_bearish.append("venus_jyeshtha")

    if weekday == "Saturday": triggered_bearish.append("moon_saturday")

    # Score Summation
    total_score = 0.0
    active_bull_details = []
    active_bear_details = []

    for rule in RULES_CONFIG["BULLISH"]:
        if rule["id"] in triggered_bullish:
            total_score += rule["weight"]
            active_bull_details.append(rule)

    for rule in RULES_CONFIG["BEARISH"]:
        if rule["id"] in triggered_bearish:
            total_score += rule["weight"] # weights are negative
            active_bear_details.append(rule)

    return total_score, active_bull_details, active_bear_details

# --- STREAMLIT DASHBOARD UI ---
st.title("🪙 Vyapar Ratna Gold Astro Engine (GAS V2)")
st.caption("Quantitative Financial Astrology Engine | Multi-Layer Planetary Scoring & Price Filter Architecture")

st.sidebar.header("🗓️ Calculation Controls")
calc_date = st.sidebar.date_input("Select Evaluation Date", datetime.date.today())

positions = get_ephemeris_positions(calc_date)

if positions:
    score, active_bulls, active_bears = evaluate_gas_rules(positions, calc_date)

    # Regime Determination
    if score >= 6.0:
        regime = "STRONG BULLISH REGIME"
        color = "green"
        action = "LONG TRADES PERMITTED (Require Price + Volume Confirmation)"
    elif 3.0 <= score < 6.0:
        regime = "MODERATE BULLISH BIAS"
        color = "lightgreen"
        action = "CAUTIOUS LONG TRADES (Tight Trailing SL)"
    elif -2.5 < score < 3.0:
        regime = "NEUTRAL / NO-TRADE ZONE"
        color = "gray"
        action = "NO ASTRO BIAS — WAIT FOR CLEAR PLANETARY REGIME"
    elif -5.5 < score <= -2.5:
        regime = "MODERATE BEARISH BIAS"
        color = "orange"
        action = "CAUTIOUS SHORT TRADES (Tight Trailing SL)"
    else:
        regime = "STRONG BEARISH REGIME"
        color = "red"
        action = "SHORT TRADES PERMITTED (Require Price Breakdown Confirmation)"

    # Top Metric Banner
    col1, col2, col3 = st.columns([1, 2, 2])
    with col1:
        st.metric(label="Gold Astro Score (GAS V2)", value=f"{score:+.1f}")
    with col2:
        st.markdown(f"### Status: :{color}[{regime}]")
    with col3:
        st.info(f"**Execution Directive:**\n{action}")

    st.divider()

    # Active Rules Breakdown
    c_left, c_right = st.columns(2)

    with c_left:
        st.subheader("🟢 Active Bullish Conditions")
        if active_bulls:
            bull_df = pd.DataFrame(active_bulls)[["name", "layer", "weight"]]
            bull_df.columns = ["Condition", "Layer", "Weight"]
            st.dataframe(bull_df, use_container_width=True, hide_index=True)
        else:
            st.write("No active bullish conditions for this date.")

    with c_right:
        st.subheader("🔴 Active Bearish Conditions")
        if active_bears:
            bear_df = pd.DataFrame(active_bears)[["name", "layer", "weight"]]
            bear_df.columns = ["Condition", "Layer", "Weight"]
            st.dataframe(bear_df, use_container_width=True, hide_index=True)
        else:
            st.write("No active bearish conditions for this date.")

    st.divider()

    # Ephemeris State Table
    st.subheader("🪐 Live Sidereal Planetary Positions (Lahiri Ayanamsha)")
    eph_data = []
    for p, val in positions.items():
        eph_data.append({
            "Planet": p,
            "Sign": val["sign"],
            "Nakshatra": val["nakshatra"],
            "Longitude": f"{val['longitude']:.2f}°",
            "Motion": "RETROGRADE" if val["is_retrograde"] else "DIRECT"
        })
    st.table(pd.DataFrame(eph_data))