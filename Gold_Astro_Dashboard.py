import streamlit as st
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

# ==========================================
# 1. STREAMLIT PAGE CONFIGURATION
# (Must be the very first Streamlit command)
# ==========================================
st.set_page_config(
    page_title="SBC Gold Trading Dashboard",
    page_icon="🪙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. CORE SBC ASTROLOGICAL ENGINE DATA STRUCTURES
# ==========================================

class MotionType(Enum):
    NORMAL = "Front"
    FAST = "Left"
    RETROGRADE = "Right"

class Nature(Enum):
    BENEFIC = "Benefic"
    MALEFIC = "Malefic"

STANDARD_SPEEDS_ARCMIN = {
    "Surya (Sun)": 59.13,
    "Chandra (Moon)": 790.50,
    "Mangala (Mars)": 31.43,
    "Budha (Mercury)": 59.13,
    "Guru (Jupiter)": 4.98,
    "Sukra (Venus)": 59.13,
    "Sani (Saturn)": 2.00,
    "Rahu": -3.18,
    "Ketu": -3.18,
}

@dataclass
class Graha:
    name: str
    longitude: float
    daily_speed_arcmin: float
    is_retrograde: bool = False
    nature: Nature = Nature.MALEFIC

    def determine_motion(self) -> MotionType:
        if self.is_retrograde or self.name in ["Rahu", "Ketu"]:
            return MotionType.RETROGRADE
        avg_speed = STANDARD_SPEEDS_ARCMIN.get(self.name, 60.0)
        if self.daily_speed_arcmin > avg_speed * 1.2:
            return MotionType.FAST
        return MotionType.NORMAL

@dataclass
class MarketProfile:
    asset_name: str
    janma_nakshatra_idx: int
    janma_rasi_idx: int
    janma_tithi_idx: int
    name_consonant: str
    name_vowel: str

class SarvatobhadraChakra:
    NAKSHATRAS_28 = [
        "Aswini", "Bharani", "Krittika", "Rohini", "Mrigasira", "Ardra",
        "Punarvasu", "Pushya", "Ashlesha", "Magha", "P. Phalguni", "U. Phalguni",
        "Hasta", "Chitra", "Swati", "Visakha", "Anuradha", "Jyeshta",
        "Moola", "P. Shada", "U. Shada", "Abhijit", "Sravana", "Dhanishta",
        "Satabisha", "P. Bhadrapada", "U. Bhadrapada", "Revati"
    ]

    RASIS = [
        "Mesha (Aries)", "Vrisabha (Taurus)", "Mithuna (Gemini)", "Karka (Cancer)",
        "Simha (Leo)", "Kanya (Virgo)", "Tula (Libra)", "Vriscika (Scorpio)",
        "Dhanur (Sagittarius)", "Makara (Capricorn)", "Kumbha (Aquarius)", "Mina (Pisces)"
    ]

    def get_28_nakshatra_from_longitude(self, lon: float) -> Tuple[str, int, int]:
        lon = lon % 360.0
        abhijit_start = 276.666667
        abhijit_end = 280.888889

        if abhijit_start <= lon < abhijit_end:
            nak_name = "Abhijit"
            nak_idx = 21
            span = abhijit_end - abhijit_start
            pada = int(((lon - abhijit_start) / span) * 4) + 1
            return nak_name, nak_idx, min(pada, 4)

        if lon < abhijit_start:
            nak_float = lon / (360.0 / 27.0)
            nak_idx = int(nak_float)
            pada = int((nak_float - nak_idx) * 4) + 1
            return self.NAKSHATRAS_28[nak_idx], nak_idx, min(pada, 4)
        else:
            remaining_lon = lon - abhijit_end
            standard_span = 360.0 / 27.0
            sravana_offset_idx = int(remaining_lon / standard_span)
            nak_idx = 22 + sravana_offset_idx
            pada = int(((remaining_lon - (sravana_offset_idx * standard_span)) / standard_span) * 4) + 1
            return self.NAKSHATRAS_28[min(nak_idx, 27)], min(nak_idx, 27), min(pada, 4)

    def calculate_vedha_targets(self, graha: Graha) -> Dict[str, Optional[int]]:
        _, nak_idx, _ = self.get_28_nakshatra_from_longitude(graha.longitude)
        motion = graha.determine_motion()

        if motion == MotionType.NORMAL:
            target_nak_idx = (nak_idx + 14) % 28
        elif motion == MotionType.RETROGRADE:
            target_nak_idx = (nak_idx + 7) % 28
        else:  # FAST (Left)
            target_nak_idx = (nak_idx - 7) % 28

        return {
            "motion_used": motion.value,
            "source_nak_idx": nak_idx,
            "target_nak_idx": target_nak_idx,
            "target_rasi_idx": int((target_nak_idx / 28.0) * 12),
        }

    def evaluate_panchaka_affliction(self, transiting_grahas: List[Graha], market: MarketProfile) -> Dict:
        afflictions = {
            "Nakshatra": False,
            "Rasi": False,
            "Tithi": False,
            "Consonant": False,
            "Vowel": False,
        }

        malefic_score = 0.0
        benefic_score = 0.0

        for graha in transiting_grahas:
            vedha = self.calculate_vedha_targets(graha)
            target_nak = vedha["target_nak_idx"]
            weight = 2.0 if graha.is_retrograde else 1.0

            if target_nak == market.janma_nakshatra_idx:
                afflictions["Nakshatra"] = True
                if graha.nature == Nature.MALEFIC:
                    malefic_score += 1.0 * weight
                else:
                    benefic_score += 1.0 * weight

            if vedha["target_rasi_idx"] == market.janma_rasi_idx:
                afflictions["Rasi"] = True
                if graha.nature == Nature.MALEFIC:
                    malefic_score += 0.75 * weight
                else:
                    benefic_score += 0.75 * weight

        afflicted_count = sum(1 for v in afflictions.values() if v)
        net_score = malefic_score - benefic_score

        if net_score > 0:
            market_signal = "BEARISH / VOLATILE"
            signal_color = "red"
        elif net_score < 0:
            market_signal = "BULLISH / POSITIVE"
            signal_color = "green"
        else:
            market_signal = "NEUTRAL / SIDEWAYS"
            signal_color = "orange"

        return {
            "afflicted_components": afflictions,
            "afflicted_count": afflicted_count,
            "malefic_score": malefic_score,
            "benefic_score": benefic_score,
            "net_score": net_score,
            "market_signal": market_signal,
            "signal_color": signal_color
        }

# ==========================================
# 3. STREAMLIT UI IMPLEMENTATION
# ==========================================

def main():
    try:
        sbc = SarvatobhadraChakra()

        st.title("🪙 Sarvatobhadra Chakra (SBC) - Gold Trading Engine")
        st.caption("Precision 28-Nakshatra & Panchaka Affliction Analytics for Commodity Markets")

        st.sidebar.header("🎯 Target Asset Profile")
        asset_name = st.sidebar.text_input("Asset / Commodity Name", value="Gold (Suvarna)")
        
        janma_nak = st.sidebar.selectbox(
            "Asset Janma Nakshatra",
            options=sbc.NAKSHATRAS_28,
            index=15 # Visakha by default
        )
        janma_nak_idx = sbc.NAKSHATRAS_28.index(janma_nak)

        janma_rasi = st.sidebar.selectbox(
            "Asset Janma Rasi",
            options=sbc.RASIS,
            index=6 # Tula by default
        )
        janma_rasi_idx = sbc.RASIS.index(janma_rasi)

        market_profile = MarketProfile(
            asset_name=asset_name,
            janma_nakshatra_idx=janma_nak_idx,
            janma_rasi_idx=janma_rasi_idx,
            janma_tithi_idx=1,
            name_consonant="S",
            name_vowel="U"
        )

        st.subheader("🪐 Transiting Planetary Configurations")
        st.write("Configure the current positions and motions of transit planets:")

        col1, col2, col3 = st.columns(3)

        # Saturn Config
        with col1:
            st.markdown("### 🪐 Saturn (Sani)")
            sat_lon = st.number_input("Saturn Longitude (°)", 0.0, 360.0, 320.5, step=1.0)
            sat_spd = st.number_input("Saturn Speed (arcmin/day)", -10.0, 15.0, 1.5)
            sat_retro = st.checkbox("Saturn Retrograde", value=True)

        # Mars Config
        with col2:
            st.markdown("### 🔴 Mars (Mangala)")
            mars_lon = st.number_input("Mars Longitude (°)", 0.0, 360.0, 145.2, step=1.0)
            mars_spd = st.number_input("Mars Speed (arcmin/day)", -20.0, 60.0, 45.0)
            mars_retro = st.checkbox("Mars Retrograde", value=False)

        # Jupiter Config
        with col3:
            st.markdown("### 🟡 Jupiter (Guru)")
            jup_lon = st.number_input("Jupiter Longitude (°)", 0.0, 360.0, 85.0, step=1.0)
            jup_spd = st.number_input("Jupiter Speed (arcmin/day)", -10.0, 20.0, 6.0)
            jup_retro = st.checkbox("Jupiter Retrograde", value=False)

        # Aggregate transits
        transits = [
            Graha("Sani (Saturn)", sat_lon, sat_spd, is_retrograde=sat_retro, nature=Nature.MALEFIC),
            Graha("Mangala (Mars)", mars_lon, mars_spd, is_retrograde=mars_retro, nature=Nature.MALEFIC),
            Graha("Guru (Jupiter)", jup_lon, jup_spd, is_retrograde=jup_retro, nature=Nature.BENEFIC),
        ]

        st.divider()

        # Run Analysis
        result = sbc.evaluate_panchaka_affliction(transits, market_profile)

        # Display Summary Dashboard Metrics
        st.subheader("📈 Market Analysis & Signal Output")
        
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("Target Asset", asset_name)
        m_col2.metric("Afflicted Components", f"{result['afflicted_count']} / 5")
        m_col3.metric("Net Aspect Score", f"{result['net_score']:.2f}")
        
        signal = result['market_signal']
        if result['signal_color'] == "red":
            m_col4.error(f"Signal: {signal}")
        elif result['signal_color'] == "green":
            m_col4.success(f"Signal: {signal}")
        else:
            m_col4.warning(f"Signal: {signal}")

        st.subheader("📋 Planetary Vedha & Target Breakdown")
        breakdown_data = []
        for g in transits:
            nak_name, nak_idx, pada = sbc.get_28_nakshatra_from_longitude(g.longitude)
            vedha = sbc.calculate_vedha_targets(g)
            target_nak_name = sbc.NAKSHATRAS_28[vedha["target_nak_idx"]]
            
            breakdown_data.append({
                "Planet": g.name,
                "Nature": g.nature.value,
                "Longitude": f"{g.longitude:.2f}°",
                "Nakshatra": f"{nak_name} (Pada {pada})",
                "Motion": vedha["motion_used"],
                "Vedha Target Nakshatra": target_nak_name,
                "Retro Multiplier": "200%" if g.is_retrograde else "100%"
            })

        st.dataframe(breakdown_data, use_container_width=True)

    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
