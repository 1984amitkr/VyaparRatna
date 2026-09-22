import io
import math
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Set Streamlit Page Configuration
st.set_page_config(page_title="Sarvatobhadra Chakra Application", layout="wide")

# ==========================================
# CONSTANTS & ASTROLOGICAL DATA MAPPING
# ==========================================
NAKSHATRAS = [
    "Krittika", "Rohini", "Mrigasira", "Ardra", "Punarvasu", "Pushya", "Ashlesha",
    "Magha", "P. Phalguni", "U. Phalguni", "Hasta", "Chitra", "Swati", "Visakha",
    "Anuradha", "Jyeshta", "Moola", "P. Shada", "U. Shada", "Abhijit", "Sravana",
    "Dhanishta", "Satabisha", "P. Bhadrapada", "U. Bhadrapada", "Revati", "Aswini", "Bharani"
]

RASIS = [
    "Mesha", "Vrisabha", "Mithuna", "Karka", "Simha", "Kanya",
    "Tula", "Vriscika", "Dhanur", "Makara", "Kumbha", "Mina"
]

TITHI_GROUPS = ["Nanda (1,6,11)", "Bhadra (2,7,12)", "Jaya (3,8,13)", "Rikta (4,9,14)", "Poornima (5,10,15)"]
WEEKDAYS = ["Sun/Tue", "Mon/Wed", "Thu", "Fri", "Sat"]

VOWELS = ["A", "AA", "E", "EE", "U", "OO", "RE", "REE", "LRI", "LREE", "AE", "AEI", "O", "OU", "AM", "AHA"]

MALEFICS = ["Surya (Sun)", "Mangala (Mars)", "Sani (Saturn)", "Rahu", "Ketu"]
BENEFICS = ["Chandra (Moon)", "Budha (Mercury)", "Guru (Jupiter)", "Sukra (Venus)"]

# Outer Border Sequence of 28 Nakshatras for 9x9 SBC Matrix
OUTER_NAKSHATRA_POSITIONS = [
    # Top Row (East: Left to Right)
    (0, 1, "Krittika"), (0, 2, "Rohini"), (0, 3, "Mrigasira"), (0, 4, "Ardra"),
    (0, 5, "Punarvasu"), (0, 6, "Pushya"), (0, 7, "Ashlesha"),
    # Right Column (South: Top to Bottom)
    (1, 8, "Magha"), (2, 8, "P. Phalguni"), (3, 8, "U. Phalguni"), (4, 8, "Hasta"),
    (5, 8, "Chitra"), (6, 8, "Swati"), (7, 8, "Visakha"),
    # Bottom Row (West: Right to Left)
    (8, 7, "Anuradha"), (8, 6, "Jyeshta"), (8, 5, "Moola"), (8, 4, "P. Shada"),
    (8, 3, "U. Shada"), (8, 2, "Abhijit"), (8, 1, "Sravana"),
    # Left Column (North: Bottom to Top)
    (7, 0, "Dhanishta"), (6, 0, "Satabisha"), (5, 0, "P. Bhadrapada"), (4, 0, "U. Bhadrapada"),
    (3, 0, "Revati"), (2, 0, "Aswini"), (1, 0, "Bharani")
]

# Inner Grid Content Definition (Coordinates for Rasis, Tithis, Weekdays, Vowels)
INNER_GRID_LAYOUT = {
    (1, 1): "Vrisabha", (1, 2): "A", (1, 3): "Va", (1, 4): "Ka", (1, 5): "Ha", (1, 6): "Da", (1, 7): "Mithuna",
    (2, 1): "AA", (2, 2): "Nanda\n1,6,11", (2, 3): "Sun/Tue", (2, 4): "Ma", (2, 5): "Ta", (2, 6): "Bhadra\n2,7,12", (2, 7): "E",
    (3, 1): "LRI", (3, 2): "Mon/Wed", (3, 3): "Karka", (3, 4): "Pa", (3, 5): "Simha", (3, 6): "Thu", (3, 7): "EE",
    (4, 1): "La", (4, 2): "Ra", (4, 3): "Ta", (4, 4): "Poornima\nSat", (4, 5): "Na", (4, 6): "Ya", (4, 7): "Bha",
    (5, 1): "LREE", (5, 2): "Fri", (5, 3): "Mina", (5, 4): "Ja", (5, 5): "Kanya", (5, 6): "Fri", (5, 7): "OO",
    (6, 1): "AEI", (6, 2): "Rikta\n4,9,14", (6, 3): "Thu", (6, 4): "Kha", (6, 5): "Ga", (6, 6): "Jaya\n3,8,13", (6, 7): "OO (Big)",
    (7, 1): "Kumbha", (7, 2): "O", (7, 3): "Sa", (7, 4): "Da", (7, 5): "Cha", (7, 6): "OU", (7, 7): "Makara"
}

# ==========================================
# HELPER FUNCTIONS & CALCULATION LOGIC
# ==========================================

def calculate_sapta_nadi(nakshatra):
    """Maps a Nakshatra to its Sapta Nadi, Nadi Lord, and Nadi Quality."""
    nadi_mapping = {
        "Prachand Pawan": (["Krittika", "Visakha", "Anuradha", "Bharani"], "Sani", "Dangerous, high travel, fast changes"),
        "Dehan": (["Rohini", "Swati", "Jyeshta", "Aswini"], "Surya", "Mental tension, quarrelsome, anger"),
        "Sobhya": (["Mrigasira", "Chitra", "Moola", "Revati"], "Mangala", "Happy results, prosperity, unexpected gains"),
        "Neer": (["Ardra", "Hasta", "P. Shada", "U. Bhadrapada"], "Guru", "Uncertainty, hard work required"),
        "Jal": (["Punarvasu", "U. Phalguni", "U. Shada", "P. Bhadrapada"], "Sukra", "Specific benefic events, lasting impacts"),
        "Amrit": (["Pushya", "P. Phalguni", "Abhijit", "Satabisha"], "Budha", "Everlasting benefic results throughout life"),
        "Pawan": (["Ashlesha", "Magha", "Sravana", "Dhanishta"], "Chandra", "Quick travel, rapid minor results")
    }
    for nadi, (naks, lord, quality) in nadi_mapping.items():
        if nakshatra in naks:
            return nadi, lord, quality
    return "Unknown", "Unknown", "N/A"

def calculate_navatara(janma_nak, target_nak):
    """Calculates Navatara series classification relative to Janma Nakshatra."""
    if janma_nak not in NAKSHATRAS or target_nak not in NAKSHATRAS:
        return "N/A", "Unknown"
    
    # Exclude Abhijit for Navatara calculation per standard SBC rule
    std_naks = [n for n in NAKSHATRAS if n != "Abhijit"]
    if janma_nak == "Abhijit" or target_nak == "Abhijit":
        return "Neutral", "Abhijit Special Point"
        
    j_idx = std_naks.index(janma_nak)
    t_idx = std_naks.index(target_nak)
    
    diff = (t_idx - j_idx) % 27 + 1
    tara_num = ((diff - 1) % 9) + 1
    
    taras = {
        1: ("Janma (Danger/Stress)", "Malefic"),
        2: ("Sampat (Wealth/Prosperity)", "Benefic"),
        3: ("Vipat (Loss/Accident)", "Malefic"),
        4: ("Kshema (Prosperity/Wellbeing)", "Benefic"),
        5: ("Pratwara (Obstacles/Delays)", "Malefic"),
        6: ("Sadhaka (Success/Achievement)", "Benefic"),
        7: ("Naidhana (Severe Obstacles/Death)", "Malefic"),
        8: ("Mitra (Friendship/Gain)", "Benefic"),
        9: ("Param Mitra (Intimate Friend/High Gain)", "Benefic")
    }
    return taras[tara_num]

def evaluate_vedha_impact(afflicted_components, transiting_planets):
    """Evaluates Vedha results based on principles in text."""
    count = len(afflicted_components)
    malefic_count = sum(1 for p in transiting_planets if p in MALEFICS)
    benefic_count = sum(1 for p in transiting_planets if p in BENEFICS)
    
    summary = []
    if malefic_count > 0:
        if count == 1:
            summary.append("Failure in efforts, disputes, and minor friction.")
        elif count == 2:
            summary.append("Fear, anxiety, and financial loss.")
        elif count == 3:
            summary.append("Severe obstacles, destruction of objectives, and defeat.")
        elif count >= 4:
            summary.append("Critical affliction: Severe illness, health danger, or complete failure.")
    
    if benefic_count > 0:
        summary.append("Benefic Vedha active: Provides protection, unexpected gains, and success in endeavors.")
        
    if not summary:
        summary.append("No active Vedha afflictions detected on key natal sensitive points.")
        
    return " ".join(summary)

# ==========================================
# CHART DRAWING ROUTINE (MATPLOTLIB)
# ==========================================

def generate_sbc_chart(janma_nak, transits):
    """Generates the 9x9 Sarvatobhadra Chakra visual representation."""
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_xlim(0, 9)
    ax.set_ylim(0, 9)
    ax.axis('off')

    # Base Grid Construction
    for i in range(10):
        ax.plot([0, 9], [i, i], color='black', lw=1.5)
        ax.plot([i, i], [0, 9], color='black', lw=1.5)

    # Fill Outer Ring (28 Nakshatras)
    for row, col, name in OUTER_NAKSHATRA_POSITIONS:
        # Check if Janma Nakshatra
        bg_color = '#FFD700' if name == janma_nak else '#F0F8FF'
        rect = patches.Rectangle((col, 8 - row), 1, 1, facecolor=bg_color, edgecolor='black', lw=1)
        ax.add_patch(rect)
        
        # Display Transits
        planet_str = ""
        for p_name, p_nak in transits.items():
            if p_nak == name:
                planet_str += f"\n[{p_name[:3]}]"
                
        ax.text(col + 0.5, 8 - row + 0.5, f"{name}{planet_str}", 
                ha='center', va='center', fontsize=7, fontweight='bold')

    # Fill Inner Ring Details
    for (row, col), label in INNER_GRID_LAYOUT.items():
        rect = patches.Rectangle((col, 8 - row), 1, 1, facecolor='#FAFAFA', edgecolor='black', lw=0.5)
        ax.add_patch(rect)
        ax.text(col + 0.5, 8 - row + 0.5, label, ha='center', va='center', fontsize=7, color='#333333')

    # Center Corner Accent (Varga 81 Center)
    rect_center = patches.Rectangle((4, 4), 1, 1, facecolor='#E6F2FF', edgecolor='black', lw=1.5)
    ax.add_patch(rect_center)
    ax.text(4.5, 4.5, "CENTER\n(Poornima/Sat)", ha='center', va='center', fontsize=8, fontweight='bold', color='#003366')

    plt.tight_layout()
    return fig

# ==========================================
# PDF GENERATION ROUTINE (REPORTLAB)
# ==========================================

def generate_pdf_report(name, janma_nak, janma_rasi, tithi, vowel, nadi, lord, quality, taras_df, transits_df, summary_text):
    """Generates a downloadable PDF report summarizing SBC Analysis."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, leading=22, alignment=1, textColor=colors.HexColor('#1A365D'))
    h2_style = ParagraphStyle('Heading2', parent=styles['Heading2'], fontSize=12, leading=16, textColor=colors.HexColor('#2C5282'))
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=9, leading=12)

    story = []
    
    # Header
    story.append(Paragraph("<b>SARVATOBHADRA CHAKRA ASTROLOGICAL REPORT</b>", title_style))
    story.append(Spacer(1, 12))
    
    # Native Summary Table
    meta_data = [
        [Paragraph(f"<b>Native Name:</b> {name}", body_style), Paragraph(f"<b>Janma Nakshatra:</b> {janma_nak}", body_style)],
        [Paragraph(f"<b>Janma Rasi:</b> {janma_rasi}", body_style), Paragraph(f"<b>Janma Tithi:</b> {tithi}", body_style)],
        [Paragraph(f"<b>Name Vowel:</b> {vowel}", body_style), Paragraph(f"<b>Sapta Nadi:</b> {nadi} (Lord: {lord})", body_style)]
    ]
    meta_table = Table(meta_data, colWidths=[260, 260])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F7FAFC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # Sapta Nadi Details
    story.append(Paragraph("<b>1. Sapta Nadi Overview</b>", h2_style))
    story.append(Paragraph(f"<b>Nadi Nature & Effects:</b> {quality}", body_style))
    story.append(Spacer(1, 10))

    # Active Transits & Vedha
    story.append(Paragraph("<b>2. Current Planetary Transits</b>", h2_style))
    t_data = [["Planet", "Transiting Nakshatra", "Navatara Position", "Nature"]]
    for _, row in transits_df.iterrows():
        t_data.append([row['Planet'], row['Transiting Nakshatra'], row['Navatara Classification'], row['Nature']])
    
    t_table = Table(t_data, colWidths=[120, 140, 160, 100])
    t_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2B6CB0')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_table)
    story.append(Spacer(1, 14))

    # Vedha Assessment Summary
    story.append(Paragraph("<b>3. Vedha Impact & Predictive Summary</b>", h2_style))
    story.append(Paragraph(summary_text, body_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# ==========================================
# STREAMLIT USER INTERFACE
# ==========================================

def main():
    st.title("🔮 Sarvatobhadra Chakra (SBC) Web Application")
    st.markdown("Automated Vedha, Sapta Nadi, and Navatara Predictive Analysis Engine")
    st.divider()

    # Sidebar - Input Configuration
    st.sidebar.header("📋 Native Natal Details")
    native_name = st.sidebar.text_input("Native Name", value="Commander Ultra Maharaja")
    janma_nak = st.sidebar.selectbox("Janma Nakshatra (Moon Star)", NAKSHATRAS, index=0)
    janma_rasi = st.sidebar.selectbox("Janma Rasi (Moon Sign)", RASIS, index=0)
    janma_tithi = st.sidebar.selectbox("Janma Tithi", TITHI_GROUPS, index=0)
    janma_vowel = st.sidebar.selectbox("Name Initial Vowel", VOWELS, index=0)

    st.sidebar.header("🪐 Transiting Planetary Positions")
    transit_positions = {}
    
    # Default initial nakshatra positions for planets
    defaults = ["Krittika", "Rohini", "Mrigasira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "P. Phalguni"]
    all_planets = MALEFICS + BENEFICS
    
    for idx, planet in enumerate(all_planets):
        def_idx = idx % len(defaults)
        transit_positions[planet] = st.sidebar.selectbox(f"{planet}", NAKSHATRAS, index=def_idx, key=f"p_{idx}")

    # Calculations
    nadi, lord, quality = calculate_sapta_nadi(janma_nak)

    # Layout Columns
    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.subheader("🕸️ Sarvatobhadra Chakra Visualization")
        fig = generate_sbc_chart(janma_nak, transit_positions)
        st.pyplot(fig)

    with col2:
        st.subheader("📊 Native Panchaka & Nadi Analysis")
        st.info(f"**Janma Nakshatra:** {janma_nak} | **Rasi:** {janma_rasi}")
        
        # Sapta Nadi Display
        st.markdown(f"### Sapta Nadi: **{nadi}**")
        st.markdown(f"- **Nadi Lord:** {lord}")
        st.markdown(f"- **Characteristics:** {quality}")

        # Transits vs Navatara Table
        st.subheader("⚡ Transit Vedha & Navatara Status")
        transit_data = []
        afflicted_components = []
        
        for planet, nak in transit_positions.items():
            tara_name, nature = calculate_navatara(janma_nak, nak)
            p_type = "Malefic" if planet in MALEFICS else "Benefic"
            transit_data.append({
                "Planet": planet,
                "Transiting Nakshatra": nak,
                "Navatara Classification": tara_name,
                "Nature": p_type
            })
            if nak == janma_nak:
                afflicted_components.append(f"{planet} on Janma Nakshatra")

        transits_df = pd.DataFrame(transit_data)
        st.dataframe(transits_df, use_container_width=True)

    # Detailed Summary & PDF Generation
    st.divider()
    st.subheader("📑 Forecast Summary & Report Generation")
    
    summary_text = evaluate_vedha_impact(afflicted_components, transit_positions.keys())
    st.write(summary_text)

    # PDF Download Button
    pdf_buffer = generate_pdf_report(
        native_name, janma_nak, janma_rasi, janma_tithi, janma_vowel,
        nadi, lord, quality, None, transits_df, summary_text
    )
    
    st.download_button(
        label="📄 Download Detailed PDF Report",
        data=pdf_buffer,
        file_name=f"Sarvatobhadra_Chakra_Report_{native_name.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )

if __name__ == "__main__":
    main()
