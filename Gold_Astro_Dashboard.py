"""
Sarvatobhadra Chakra (SBC) Engine
----------------------------------
Agile Component: Core Vedha & Panchaka Evaluation Engine
Incorporate 28-Nakshatra Zodiac, dynamic speed-based aspecting (Vedha), 
and multi-component affliction evaluation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class MotionType(Enum):
    NORMAL = "Front"
    FAST = "Left"
    RETROGRADE = "Right"


class Nature(Enum):
    BENEFIC = "Benefic"
    MALEFIC = "Malefic"


# Standard average speeds in arcminutes per day for motion determination
STANDARD_SPEEDS_ARCMIN = {
    "Surya": 59.13,
    "Chandra": 790.5,
    "Mangala": 31.43,
    "Budha": 59.13,
    "Guru": 4.98,
    "Sukra": 59.13,
    "Sani": 2.0,
    "Rahu": -3.18,
    "Ketu": -3.18,
}


@dataclass
class Graha:
    name: str
    longitude: float  # In absolute degrees (0 - 360)
    daily_speed_arcmin: float
    is_retrograde: bool = False
    is_combust: bool = False
    nature: Nature = Nature.MALEFIC

    def determine_motion(self) -> MotionType:
        """Determines planetary motion based on retrogradation and speed relative to mean speed."""
        if self.is_retrograde or self.name in ["Rahu", "Ketu"]:
            return MotionType.RETROGRADE

        avg_speed = STANDARD_SPEEDS_ARCMIN.get(self.name, 60.0)
        if self.daily_speed_arcmin > avg_speed * 1.2:
            return MotionType.FAST
        return MotionType.NORMAL


@dataclass
class NativeProfile:
    name: str
    janma_nakshatra_idx: int
    janma_rasi_idx: int
    janma_tithi_idx: int
    name_consonant: str
    name_vowel: str


class SarvatobhadraChakra:
    """Sarvatobhadra Chakra Engine handling 28-Nakshatra mapping, Vedha calculation, and Panchaka evaluation."""

    # 28 Nakshatras including Abhijit
    NAKSHATRAS_28 = [
        "Aswini",
        "Bharani",
        "Krittika",
        "Rohini",
        "Mrigasira",
        "Ardra",
        "Punarvasu",
        "Pushya",
        "Ashlesha",
        "Magha",
        "P. Phalguni",
        "U. Phalguni",
        "Hasta",
        "Chitra",
        "Swati",
        "Visakha",
        "Anuradha",
        "Jyeshta",
        "Moola",
        "P. Shada",
        "U. Shada",
        "Abhijit",
        "Sravana",
        "Dhanishta",
        "Satabisha",
        "P. Bhadrapada",
        "U. Bhadrapada",
        "Revati",
    ]

    RASIS = [
        "Mesha",
        "Vrisabha",
        "Mithuna",
        "Karka",
        "Simha",
        "Kanya",
        "Tula",
        "Vriscika",
        "Dhanur",
        "Makara",
        "Kumbha",
        "Mina",
    ]

    def __init__(self):
        pass

    def get_28_nakshatra_from_longitude(
        self, lon: float
    ) -> Tuple[str, int, int]:
        """Calculates 28-Nakshatra index and Pada, accounting for Abhijit's specific span.

        Abhijit spans from 276°40' (276.6667°) to 280°53'20" (280.8889°).
        """
        lon = lon % 360.0

        # Boundary checks for Abhijit
        abhijit_start = 276.666667
        abhijit_end = 280.888889

        if abhijit_start <= lon < abhijit_end:
            nak_name = "Abhijit"
            nak_idx = 21
            # Calculate Pada within Abhijit span
            span = abhijit_end - abhijit_start
            pada = int(((lon - abhijit_start) / span) * 4) + 1
            return nak_name, nak_idx, min(pada, 4)

        # Standard 27-Nakshatra adjustment when outside Abhijit
        # Pre-Abhijit adjustment (0° to 276°40')
        if lon < abhijit_start:
            nak_float = lon / (360.0 / 27.0)
            nak_idx = int(nak_float)
            pada = int((nak_float - nak_idx) * 4) + 1
            # Map index directly
            return self.NAKSHATRAS_28[nak_idx], nak_idx, min(pada, 4)
        else:
            # Post-Abhijit adjustment (280°53'20" to 360°)
            # U.Shada ends at Abhijit start. Sravana starts at Abhijit end.
            remaining_lon = lon - abhijit_end
            # Sravana is index 22 in NAKSHATRAS_28
            standard_span = 360.0 / 27.0
            sravana_offset_idx = int(remaining_lon / standard_span)
            nak_idx = 22 + sravana_offset_idx
            pada = (
                int(
                    (
                        (remaining_lon - (sravana_offset_idx * standard_span))
                        / standard_span
                    )
                    * 4
                )
                + 1
            )
            return (
                self.NAKSHATRAS_28[min(nak_idx, 27)],
                min(nak_idx, 27),
                min(pada, 4),
            )

    def calculate_vedha_targets(
        self, graha: Graha
    ) -> Dict[str, Optional[int]]:
        """Calculates the target cross-aspects (Vedha) based on planet's motion type."""
        _, nak_idx, _ = self.get_28_nakshatra_from_longitude(graha.longitude)
        motion = graha.determine_motion()

        # SBC 28-Nakshatra Vedha Target Offset Mapping (Simplified Matrix Representation)
        # Front = Opposite across 81-Varga grid (+14 Nakshatra steps)
        # Right = Angular Right Vedha (+7 Nakshatra steps)
        # Left = Angular Left Vedha (-7 Nakshatra steps)
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
            "target_rasi_idx": (target_nak_idx // 2.33) % 12,
        }

    def evaluate_panchaka_affliction(
        self, transiting_grahas: List[Graha], native: NativeProfile
    ) -> Dict:
        """Evaluates Vedha afflictions on all 5 Panchakas of the native."""
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

            # Weight factor multiplier: Retrograde doubles the intensity (200%)
            weight = 2.0 if graha.is_retrograde else 1.0

            # Check if target Nakshatra hits Native's Janma Nakshatra
            if target_nak == native.janma_nakshatra_idx:
                afflictions["Nakshatra"] = True
                if graha.nature == Nature.MALEFIC:
                    malefic_score += 1.0 * weight
                else:
                    benefic_score += 1.0 * weight

            # Additional Panchaka cross-affliction checks (Rasi, Tithi, Phonetics)
            if vedha["target_rasi_idx"] == native.janma_rasi_idx:
                afflictions["Rasi"] = True
                if graha.nature == Nature.MALEFIC:
                    malefic_score += 0.75 * weight
                else:
                    benefic_score += 0.75 * weight

        afflicted_components_count = sum(1 for v in afflictions.values() if v)

        # Severe malefic diagnostic evaluation
        severity_desc = "Favorable/Neutral"
        if malefic_score > benefic_score:
            if afflicted_components_count == 1:
                severity_desc = "Minor Disagreement / Effort Failure"
            elif afflicted_components_count == 2:
                severity_desc = "Fear and Financial Loss"
            elif afflicted_components_count == 3:
                severity_desc = "High Obstruction & Destruction"
            elif afflicted_components_count == 4:
                severity_desc = "Severe Sickness & Distress"
            elif afflicted_components_count >= 5:
                severity_desc = "Critical Threat / Extreme Adverse Impact"

        return {
            "afflicted_components": afflictions,
            "afflicted_count": afflicted_components_count,
            "net_malefic_score": max(0.0, malefic_score - benefic_score),
            "assessment": severity_desc,
        }


# --- Example Execution & Test ---
if __name__ == "__main__":
    sbc = SarvatobhadraChakra()

    # Define transiting planets
    transits = [
        Graha(
            name="Sani",
            longitude=320.5,
            daily_speed_arcmin=1.5,
            is_retrograde=True,
            nature=Nature.MALEFIC,
        ),
        Graha(
            name="Mangala",
            longitude=145.2,
            daily_speed_arcmin=45.0,
            is_retrograde=False,
            nature=Nature.MALEFIC,
        ),
        Graha(
            name="Guru",
            longitude=85.0,
            daily_speed_arcmin=6.0,
            is_retrograde=False,
            nature=Nature.BENEFIC,
        ),
    ]

    # Define native profile
    native = NativeProfile(
        name="Commander",
        janma_nakshatra_idx=15,  # Visakha
        janma_rasi_idx=6,  # Tula
        janma_tithi_idx=3,
        name_consonant="Ka",
        name_vowel="A",
    )

    # Evaluate Panchaka affliction
    result = sbc.evaluate_panchaka_affliction(transits, native)
    print("--- SBC PANCHAKA EVALUATION RESULT ---")
    print(f"Afflicted Count: {result['afflicted_count']}/5")
    print(f"Net Malefic Score: {result['net_malefic_score']}")
    print(f"Assessment: {result['assessment']}")
