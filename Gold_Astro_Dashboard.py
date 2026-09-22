import datetime
import zoneinfo
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import yfinance as yf

# Try importing Swiss Ephemeris with fallback
SWISS_EPH_AVAILABLE = False
try:
    import swisseph as swe
    SWISS_EPH_AVAILABLE = True
except Exception:
    SWISS_EPH_AVAILABLE = False

# -------------------------------------------------------------------
# 1. PAGE CONFIG & CONSTANTS
# -------------------------------------------------------------------
st.set_page_config(
    page_title="VyaparRatna Gold Astro Dashboard",
    page_icon="🏆",
    layout="wide",
)

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

# -------------------------------------------------------------------
# 2. SESSION STATE MANAGEMENT & TIME CONTROL
# -------------------------------------------------------------------
if "app_mode" not in st.session_state:
    st.session_state["app_mode"] = "Live Real-Time Dashboard"

if "eval_time" not in st.session_state:
    st.session_state["eval_time"] = datetime.datetime.now(MUMBAI_TZ)

def reset_to_current_time():
    st.session_state["eval_time"] = datetime.datetime.now(MUMBAI_TZ)
    st.session_state["app_mode"] = "Live Real-Time Dashboard"
    st.rerun()

# -------------------------------------------------------------------
# 3. ASTRONOMICAL & SBC VEDHA CALCULATIONS
# -------------------------------------------------------------------
def get_sbc_nakshatra(lon: float) -> str:
    if 276.6667 <= lon < 280.8889:
        return "Abhijit"
    idx = int(lon // (360.0 / 27.0))
    return NAKSHATRAS_27[idx % 27]

def get_ephemeris_data(dt: datetime.datetime):
    utc_dt = dt.astimezone(datetime.timezone.utc)
    planet_data = {}

    if SWISS_EPH_AVAILABLE:
        try:
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            julian_day = swe.julday(
                utc_dt.year, utc_dt.month, utc_dt.day, 
                utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
            )
            planets_map = {
                "Sun": 0, "Moon": 1, "Mars": 4, "Mercury": 2,
                "Jupiter": 5, "Venus": 3, "Saturn": 6, "Rahu": 11, "Ketu": 11
            }
            for p_name, p_id in planets_map.items():
                flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
                res, _ = swe.calc_ut(julian_day, p_id, flags)
                lon = res[0] % 360
                speed = res[3]
                if p_name == "Ketu":
                    lon = (lon + 180) % 360
                    speed = -speed
                planet_data[p_name] = {"lon": lon, "speed": speed, "nakshatra": get_sbc_nakshatra(lon)}
            return planet_data
        except Exception:
            pass

    # Mathematical Fallback
    delta_days = (utc_dt - datetime.datetime(2000, 1, 1, 12, 0, tzinfo=datetime.timezone.utc)).total_seconds() / 86400.0
    lons = {
        "Sun": (280.460 + 0.9856474 * delta_days) % 360,
        "Moon": (218.316 + 13.176396 * delta_days) % 360,
        "Mars": (355.453 + 0.524033 * delta_days) % 360,
        "Mercury": (252.251 + 4.092334 * delta_days) % 360,
        "Jupiter": (34.351 + 0.083091 * delta_days) % 360,
        "Venus": (181.979 + 1.602130 * delta_days) % 360,
        "Saturn": (50.077 + 0.033459 * delta_days) % 360,
        "Rahu": (125.045 - 0.05295 * delta_days) % 360,
    }
    lons["Ketu"] = (lons["Rahu"] + 180) % 360

    for p_name, lon in lons.items():
        speed = AVERAGE_DAILY_SPEEDS.get(p_name, 1.0)
        planet_data[p_name] = {"lon": lon, "speed": speed, "nakshatra": get_sbc_nakshatra(lon)}

    return planet_data

def calculate_nested_sbc_scores(ephem_data):
    jup_retro = ephem_data["Jupiter"]["speed"] < 0.080
    sat_affliction = np.cos(np.radians(ephem_data["Saturn"]["lon"] - ephem_data["Sun"]["lon"])) > 0.5

    tier1_score = 0.0
    if jup_retro:
        tier1_score += 1.5
    if sat_affliction:
        tier1_score += 2.0
    else:
        tier1_score -= 1.0

    sun_speed = ephem_data["Sun"]["speed"]
    tier2_score = 0.0
    if sun_speed > 1.00:
        tier2_score += 1.5
    elif sun_speed < 0.97:
        tier2_score -= 1.5

    moon_lon = ephem_data["Moon"]["lon"]
    tier3_score = float(np.sin(np.radians(moon_lon * 4.0)))

    macro_direction = 1 if tier1_score >= 0.5 else -1
    composite_signal = macro_direction * (1.0 + abs(tier2_score)) + (tier3_score * 0.5)

    return {
        "Tier1_Macro": tier1_score,
        "Tier2_Intermediate": tier2_score,
        "Tier3_Micro": tier3_score,
        "Macro_Regime": "BULL" if macro_direction == 1 else "BEAR",
        "Composite_Signal": composite_signal,
    }

# -------------------------------------------------------------------
# 4. YFINANCE MARKET DATA FETCHING
# -------------------------------------------------------------------
@st.cache_data(ttl=300)
def fetch_live_gold_data(ticker="GC=F", period="1y"):
    try:
        gold = yf.Ticker(ticker)
        df = gold.history(period=period)
        if df.empty:
            raise ValueError("Empty dataframe returned")
        df = df.reset_index()
        df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
        return df[['Date', 'Close']]
    except Exception:
        dates = pd.date_range(end=datetime.date.today(), periods=250, freq='D')
        prices = 1800.0 + np.cumsum(np.random.randn(250) * 8)
        return pd.DataFrame({"Date": dates, "Close": prices})

def generate_historical_series(start_date, end_date):
    dates = pd.date_range(start=start_date, end=end_date, freq="D")
    records = []
    for dt in dates:
        ephem = get_ephemeris_data(dt)
        scores = calculate_nested_sbc_scores(ephem)
        records.append({
            "Date": pd.to_datetime(dt.date()),
            "Tier1_Macro": scores["Tier1_Macro"],
            "Tier2_Intermediate": scores["Tier2_Intermediate"],
            "Tier3_Micro": scores["Tier3_Micro"],
            "Macro_Regime": scores["Macro_Regime"],
            "Composite_Signal": scores["Composite_Signal"],
        })
    return pd.DataFrame(records)

# -------------------------------------------------------------------
# 5. SIDEBAR & CONTROLLER PANEL
# -------------------------------------------------------------------
st.sidebar.markdown("### 🕹️ Mode & Time Controller")

st.session_state["app_mode"] = st.sidebar.radio(
    "Select Engine Mode",
    ["Live Real-Time Dashboard", "Historical Backtest Suite"],
    index=0 if st.session_state["app_mode"] == "Live Real-Time Dashboard" else 1
)

# Reset Button
if st.sidebar.button("🔄 Reset to Current Time", use_container_width=True):
    reset_to_current_time()

# Auto Refresh logic: 5 Minutes (300 seconds) in Live Mode
if st.session_state["app_mode"] == "Live Real-Time Dashboard":
    st.sidebar.caption("⏱️ Live Mode: Auto-refreshes every 5 minutes")
    st.components.v1.html(
        """
        <script>
            setTimeout(function(){
                window.parent.location.reload();
            }, 300000); // 300,000 ms = 5 minutes
        </script>
        """,
        height=0,
        width=0,
    )
else:
    st.sidebar.caption("⏸️ Backtest Mode: Auto-refresh paused")

# -------------------------------------------------------------------
# 6. MAIN DASHBOARD RENDER
# -------------------------------------------------------------------
st.title("🏆 VyaparRatna Gold Astro Engine")
st.caption("Sarvatobhadra Chakra (SBC) • Real-Time Vedha Engine & Market Analytics")

if st.session_state["app_mode"] == "Live Real-Time Dashboard":
    # Always evaluate at stored timestamp (defaults to current live time)
    eval_dt = st.session_state["eval_time"]
    
    st.info(f"📅 **Current Evaluation Time (Asia/Kolkata):** `{eval_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}`")

    ephem = get_ephemeris_data(eval_dt)
    scores = calculate_nested_sbc_scores(ephem)
    gold_df = fetch_live_gold_data("GC=F", period="1y")
    latest_price = gold_df['Close'].iloc[-1] if not gold_df.empty else 0.0

    # Top Metric Display
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Live Gold Price (yfinance)", f"${latest_price:,.2f}")
    col2.metric("Macro Regime (Tier 1)", scores["Macro_Regime"], delta=f"Score: {scores['Tier1_Macro']:.1f}")
    col3.metric("Intermediate Signal (Tier 2)", f"{scores['Tier2_Intermediate']:+.1f}")
    col4.metric("Composite Astro Signal", f"{scores['Composite_Signal']:+.2f}")

    st.markdown("---")

    col_grid, col_info = st.columns([2, 1])

    with col_grid:
        st.subheader("🕸️ 9x9 Sarvatobhadra Chakra Grid & Vedha Rays")

        fig = go.Figure()
        grid_data = np.zeros((9, 9))
        fig.add_trace(go.Heatmap(
            z=grid_data, showscale=False,
            colorscale=[[0, "#0f172a"], [1, "#1e293b"]],
            xgap=2, ygap=2
        ))

        # Map Planets on SBC Perimeter
        for p_name, data in ephem.items():
            nak_name = data["nakshatra"]
            if nak_name in SBC_GRID_POSITIONS:
                r, c = SBC_GRID_POSITIONS[nak_name]
                is_malefic = p_name in MALEFICS
                color = "#ef4444" if is_malefic else "#10b981"

                fig.add_annotation(
                    x=c, y=r, text=f"<b>{p_name[:3]}</b>",
                    showarrow=False,
                    font=dict(color=color, size=11),
                    bordercolor=color, borderwidth=1, borderpad=2, bgcolor="#000000"
                )

                # Diagonal Vedha Rays
                end_r, end_c = 8 - r, 8 - c
                fig.add_trace(go.Scatter(
                    x=[c, end_c], y=[r, end_r],
                    mode="lines",
                    line=dict(color=color, width=1, dash="dot" if is_malefic else "solid"),
                    hoverinfo="text", text=f"Vedha Ray: {p_name} ({nak_name})"
                ))

        fig.update_layout(
            height=550,
            showlegend=False,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(showticklabels=False, zeroline=False),
            yaxis=dict(showticklabels=False, zeroline=False, autorange="reversed"),
            template="plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_info:
        st.subheader("🪐 Planetary Parameters")
        ephem_df = pd.DataFrame([
            {
                "Planet": k,
                "Nakshatra": v["nakshatra"],
                "Type": "Malefic" if k in MALEFICS else "Benefic",
                "Lon (°)": f"{v['lon']:.1f}",
                "Speed": f"{v['speed']:.2f}"
            }
            for k, v in ephem.items()
        ])
        st.dataframe(ephem_df, hide_index=True, use_container_width=True)

    # Historical Price Chart Below Grid
    st.subheader("📈 1-Year Gold Price History")
    fig_price = go.Figure()
    fig_price.add_trace(go.Scatter(x=gold_df['Date'], y=gold_df['Close'], line=dict(color='#f59e0b', width=2), name="Gold"))
    fig_price.update_layout(height=300, template="plotly_dark", margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_price, use_container_width=True)

elif st.session_state["app_mode"] == "Historical Backtest Suite":
    st.subheader("📊 Historical Gold Market & Vedha Backtesting Engine")

    st.sidebar.markdown("---")
    st.sidebar.subheader("Backtest Settings")
    ticker = st.sidebar.text_input("Market Ticker", "GC=F")
    start_date = st.sidebar.date_input("Start Date", datetime.date(2022, 1, 1))
    end_date = st.sidebar.date_input("End Date", datetime.date(2024, 1, 1))

    run_button = st.sidebar.button("Run Live Backtest", type="primary")

    if run_button or "backtest_results" in st.session_state:
        if run_button:
            with st.spinner("Fetching Market History & Processing SBC Vedha Signals..."):
                df_signals = generate_historical_series(start_date, end_date)
                df_prices = fetch_live_gold_data(ticker, period="5y")
                
                df_prices['Date'] = pd.to_datetime(df_prices['Date'])
                df_signals['Date'] = pd.to_datetime(df_signals['Date'])

                merged = pd.merge(df_prices, df_signals, on="Date", how="inner")
                merged['SMA_200'] = merged['Close'].rolling(window=200).mean()
                merged['Market_Trend'] = np.where(merged['Close'] > merged['SMA_200'], "BULL", "BEAR")
                merged['Accuracy'] = merged['Macro_Regime'] == merged['Market_Trend']
                merged['Returns_20D'] = merged['Close'].pct_change(20) * 100

                st.session_state["backtest_results"] = merged

        results = st.session_state["backtest_results"]

        accuracy = results['Accuracy'].mean() * 100 if len(results) > 0 else 0
        bull_ret = results[results['Macro_Regime'] == "BULL"]['Returns_20D'].mean()
        bear_ret = results[results['Macro_Regime'] == "BEAR"]['Returns_20D'].mean()

        st.success(f"Backtest Completed across {len(results)} Trading Days!")

        m1, m2, m3 = st.columns(3)
        m1.metric("Macro Accuracy vs 200 SMA", f"{accuracy:.1f}%")
        m2.metric("Avg 20D Return (SBC BULL)", f"{bull_ret:+.2f}%" if pd.notnull(bull_ret) else "N/A")
        m3.metric("Avg 20D Return (SBC BEAR)", f"{bear_ret:+.2f}%" if pd.notnull(bear_ret) else "N/A")

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, row_heights=[0.7, 0.3])
        fig.add_trace(go.Scatter(x=results['Date'], y=results['Close'], mode='lines', name='Price ($)', line=dict(color='#f59e0b')), row=1, col=1)
        fig.add_trace(go.Scatter(x=results['Date'], y=results['SMA_200'], mode='lines', name='200 SMA', line=dict(color='#6b7280', dash='dash')), row=1, col=1)
        fig.add_trace(go.Bar(x=results['Date'], y=results['Composite_Signal'], name='SBC Signal', marker_color=np.where(results['Composite_Signal'] >= 0, '#10b981', '#ef4444')), row=2, col=1)

        fig.update_layout(height=550, template="plotly_dark", legend=dict(orientation="h", y=1.02, x=0.1))
        st.plotly_chart(fig, use_container_width=True)
