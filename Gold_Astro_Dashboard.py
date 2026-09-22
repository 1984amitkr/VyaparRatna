import datetime
import zoneinfo
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import yfinance as yf

# Streamlit Page Configuration
st.set_page_config(
    page_title="Sarvatobhadra Chakra Engine & Gold Tracker",
    page_icon="🔮",
    layout="wide",
)

# -------------------------------------------------------------------
# 1. ASTRONOMICAL & SBC VEDHA CALCULATIONS
# -------------------------------------------------------------------

NAKSHATRAS = [
    "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha",
    "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
    "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha",
    "Abhijit", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadra",
    "Uttara Bhadra", "Revati", "Ashwini", "Bharani"
]

MALEFICS = ["Sun", "Mars", "Saturn", "Rahu", "Ketu"]

def get_ephemeris_data(dt: datetime.datetime):
    """Computes geocentric sidereal planetary positions for SBC."""
    utc_dt = dt.astimezone(datetime.timezone.utc)
    delta_days = (
        utc_dt - datetime.datetime(2000, 1, 1, 12, 0, tzinfo=datetime.timezone.utc)
    ).total_seconds() / 86400.0

    sun_lon = (280.460 + 0.9856474 * delta_days) % 360
    moon_lon = (218.316 + 13.176396 * delta_days) % 360
    mars_lon = (355.453 + 0.524033 * delta_days) % 360
    mercury_lon = (252.251 + 4.092334 * delta_days) % 360
    jupiter_lon = (34.351 + 0.083091 * delta_days) % 360
    venus_lon = (181.979 + 1.602130 * delta_days) % 360
    saturn_lon = (50.077 + 0.033459 * delta_days) % 360
    rahu_lon = (125.045 - 0.05295 * delta_days) % 360
    ketu_lon = (rahu_lon + 180) % 360

    sun_speed = 0.9856 + 0.0334 * np.sin(np.radians(sun_lon - 282.93))
    jup_speed = 0.083091 + 0.005 * np.sin(np.radians(jupiter_lon))

    return {
        "Sun": {"lon": sun_lon, "speed": sun_speed},
        "Moon": {"lon": moon_lon, "speed": 13.176},
        "Mars": {"lon": mars_lon, "speed": 0.524},
        "Mercury": {"lon": mercury_lon, "speed": 4.092},
        "Jupiter": {"lon": jupiter_lon, "speed": jup_speed},
        "Venus": {"lon": venus_lon, "speed": 1.602},
        "Saturn": {"lon": saturn_lon, "speed": 0.033},
        "Rahu": {"lon": rahu_lon, "speed": -0.052},
        "Ketu": {"lon": ketu_lon, "speed": -0.052},
    }

def get_grid_coordinates(longitude):
    """Maps longitude (0-360) to perimeter cell coordinates on a 9x9 SBC grid."""
    nak_idx = int((longitude / 360.0) * 28) % 28
    
    # 28 Nakshatras placed along the outer 9x9 border (32 perimeter slots)
    perimeter_coords = [
        (0,0), (0,1), (0,2), (0,3), (0,4), (0,5), (0,6), (0,7), (0,8),
        (1,8), (2,8), (3,8), (4,8), (5,8), (6,8), (7,8),
        (8,8), (8,7), (8,6), (8,5), (8,4), (8,3), (8,2), (8,1), (8,0),
        (7,0), (6,0), (5,0), (4,0), (3,0), (2,0), (1,0)
    ]
    coord_idx = int((nak_idx / 28.0) * len(perimeter_coords))
    return perimeter_coords[coord_idx]

def calculate_nested_sbc_scores(ephem_data):
    """Evaluates Tier 1 (Macro), Tier 2 (Intermediate), and Tier 3 (Micro) scores."""
    jup_retro = ephem_data["Jupiter"]["speed"] < 0.080
    sat_affliction = (
        np.cos(np.radians(ephem_data["Saturn"]["lon"] - ephem_data["Sun"]["lon"])) > 0.5
    )

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
# 2. LIVE MARKET DATA (YFINANCE)
# -------------------------------------------------------------------

@st.cache_data(ttl=3600)
def fetch_live_gold_data(ticker="GC=F", period="2y"):
    """Fetches real-time & historical Gold data from Yahoo Finance."""
    try:
        gold = yf.Ticker(ticker)
        df = gold.history(period=period)
        if df.empty:
            raise ValueError("Empty dataframe returned.")
        df = df.reset_index()
        df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
        return df[['Date', 'Close']]
    except Exception as e:
        st.warning(f"Failed to fetch live yfinance data ({e}). Generating fallback market data.")
        dates = pd.date_range(end=datetime.date.today(), periods=500, freq='D')
        prices = 1800.0 + np.cumsum(np.random.randn(500) * 10)
        return pd.DataFrame({"Date": dates, "Close": prices})

def generate_historical_series(start_date, end_date):
    """Generates daily historical SBC scores across the date range."""
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
# 3. STREAMLIT USER INTERFACE & VEDHA GRID
# -------------------------------------------------------------------

st.title("🔮 Sarvatobhadra Chakra Market Engine & Vedha Visualizer")
st.caption("Live Gold Prices (yfinance), Vedha Ray Pathways, & Multi-Tier Analytics")

st.sidebar.header("Control Panel")
app_mode = st.sidebar.radio(
    "Select Engine Mode",
    ["Live SBC Grid & Market Tracker", "Historical Backtest Suite"],
)

if app_mode == "Live SBC Grid & Market Tracker":
    st.subheader("Real-Time SBC Vedha Grid & Gold Price Tracker")

    # Timezone Selector
    tz_choice = st.sidebar.selectbox("Timezone", ["Asia/Kolkata", "UTC", "America/New_York"], index=0)
    try:
        tz_obj = zoneinfo.ZoneInfo(tz_choice)
    except Exception:
        tz_obj = datetime.timezone.utc

    current_time = datetime.datetime.now(tz_obj)
    ephem = get_ephemeris_data(current_time)
    scores = calculate_nested_sbc_scores(ephem)

    # Fetch Gold Market Data
    gold_df = fetch_live_gold_data("GC=F", period="1y")
    latest_price = gold_df['Close'].iloc[-1] if not gold_df.empty else 0.0

    # Display Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Live Gold Price (yfinance)", f"${latest_price:,.2f}")
    col2.metric("Macro Regime (Tier 1)", scores["Macro_Regime"], delta=f"Score: {scores['Tier1_Macro']:.1f}")
    col3.metric("Intermediate Signal (Tier 2)", f"{scores['Tier2_Intermediate']:+.1f}")
    col4.metric("Composite Astro Signal", f"{scores['Composite_Signal']:+.2f}")

    st.markdown("---")

    col_grid, col_info = st.columns([2, 1])

    with col_grid:
        st.subheader("Interactive 9x9 SBC Grid with Vedha Rays")

        fig = go.Figure()

        # Grid Matrix Background
        grid_data = np.zeros((9, 9))
        fig.add_trace(go.Heatmap(
            z=grid_data, showscale=False,
            colorscale=[[0, "#0f172a"], [1, "#1e293b"]],
            xgap=2, ygap=2
        ))

        # Map Planets to Perimeter and Draw Vedha Rays
        planet_positions = {}
        for p_name, data in ephem.items():
            r, c = get_grid_coordinates(data["lon"])
            planet_positions[p_name] = (r, c)
            
            is_malefic = p_name in MALEFICS
            color = "#ef4444" if is_malefic else "#10b981"
            
            # Place Planet Annotations
            fig.add_annotation(
                x=c, y=r, text=f"<b>{p_name[:3]}</b>",
                showarrow=False,
                font=dict(color=color, size=11),
                bordercolor=color, borderwidth=1, borderpad=2, bgcolor="#000000"
            )

            # Draw Vedha Rays (Diagonal Front & Side Rays across the Grid)
            # Diagonal Ray Across the Matrix
            end_r = 8 - r
            end_c = 8 - c
            fig.add_trace(go.Scatter(
                x=[c, end_c], y=[r, end_r],
                mode="lines",
                line=dict(color=color, width=1, dash="dot" if is_malefic else "solid"),
                hoverinfo="text", text=f"Vedha Ray: {p_name}"
            ))

            # Cross-Grid Front Ray
            fig.add_trace(go.Scatter(
                x=[c, c], y=[0, 8],
                mode="lines",
                line=dict(color=color, width=0.5, dash="dash"),
                showlegend=False
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
        st.subheader("Planetary Status")
        ephem_df = pd.DataFrame([
            {
                "Planet": k,
                "Type": "Malefic" if k in MALEFICS else "Benefic",
                "Lon (°)": f"{v['lon']:.1f}",
                "Speed": f"{v['speed']:.2f}"
            }
            for k, v in ephem.items()
        ])
        st.dataframe(ephem_df, hide_index=True, use_container_width=True)

    # Historical Price Chart Below Grid
    st.subheader("1-Year Gold Price Trend (Live yfinance)")
    fig_price = go.Figure()
    fig_price.add_trace(go.Scatter(x=gold_df['Date'], y=gold_df['Close'], line=dict(color='#f59e0b', width=2)))
    fig_price.update_layout(height=300, template="plotly_dark", margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_price, use_container_width=True)

elif app_mode == "Historical Backtest Suite":
    st.subheader("Live yfinance Historical Backtesting Engine")

    st.sidebar.markdown("---")
    st.sidebar.subheader("Backtest Settings")
    ticker = st.sidebar.text_input("Market Ticker", "GC=F")
    start_date = st.sidebar.date_input("Start Date", datetime.date(2022, 1, 1))
    end_date = st.sidebar.date_input("End Date", datetime.date(2024, 1, 1))

    run_button = st.sidebar.button("Run Live Backtest", type="primary")

    if run_button:
        with st.spinner("Fetching Live Market Data & Calculating Vedha Signals..."):
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

    if "backtest_results" in st.session_state:
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
