import streamlit as st
import matplotlib.pyplot as plt
from random import uniform
import math

# ------------------ PAGE CONFIG ------------------ #
st.set_page_config(
    page_title="Diabetes Digital Twin by Siddharth Tirumalai",
    page_icon="📈",
    layout="centered"
)

# ------------------ TITLE & DISCLAIMER ------------------ #
st.title("📈 Diabetes Digital Simulator")
st.markdown("""
**Created by: Siddharth Tirumalai**  
Simulate blood glucose and HbA1c changes based on medications, diet, and lifestyle factors.
""")

st.warning("""
This simulation provides estimated trends in glucose and HbA1c based on user input. 
It assumes you are only taking medications related to blood sugar, blood pressure, or cholesterol.
If you are on other drugs (e.g., corticosteroids, antidepressants, antipsychotics), results may vary significantly.
Always consult your healthcare provider before making medical decisions based on this simulation.
""")

# ------------------ USER INFO ------------------ #
age = st.slider("Patient Age (years)", 10, 100, 45)
weight = st.slider("Weight (lbs)", 60, 200, 117)
exercise = st.slider("Daily Exercise (min)", 0, 120, 30)
insulin_sensitivity = st.slider("Insulin Sensitivity (1 = normal)", 0.5, 2.0, 1.0)

# ------------------ DIAGNOSIS ------------------ #
diagnosis = st.radio("Select Glucose Status:", ["Non-diabetic", "Pre-diabetic", "Diabetic"])

# ------------------ MEDICATION OPTIONS ------------------ #
medication_types = {
    "Insulin": (1.00, 200),
    "Sulfonylureas": (0.70, 20),
    "Metformin": (0.50, 2000),
    "GLP-1 Receptor Agonists": (0.60, 5),
    "SGLT2 Inhibitors": (0.40, 25),
    "Thiazolidinediones (TZDs)": (0.45, 45),
    "DPP-4 Inhibitors": (0.30, 100),
    "Meglitinides": (0.55, 16),
    "Alpha-glucosidase Inhibitors": (0.35, 100),
    "Amylin Analogs": (0.25, 120)
}

prediabetic_meds = {
    "Metformin": (0.40, 2000),
    "Lifestyle Coaching": (0.30, 1),
    "Weight Loss Agents": (0.20, 200),
    "GLP-1 Receptor Agonists": (0.45, 5),
    "Alpha-glucosidase Inhibitors": (0.25, 100),
    "Thiazolidinediones (TZDs)": (0.35, 45),
    "Acarbose": (0.30, 100),
    "Intermittent Fasting Protocols": (0.25, 1)
}

if diagnosis == "Diabetic":
    selected_meds = st.multiselect("Select Anti-Diabetic Medications:", list(medication_types.keys()))
elif diagnosis == "Pre-diabetic":
    selected_meds = st.multiselect("Select Pre-Diabetic Medications:", list(prediabetic_meds.keys()))
else:
    selected_meds = []

med_doses = {}
for med in selected_meds:
    max_dose = medication_types[med][1] if diagnosis == "Diabetic" else prediabetic_meds[med][1]
    med_doses[med] = st.slider(f"Dose for {med} (mg/day)", 0, max_dose, min(max_dose, 500))

# ------------------ OTHER MEDICATIONS ------------------ #
bp_options = {
    "Beta Blockers": 200,
    "ACE Inhibitors": 40,
    "Angiotensin II Receptor Blockers (ARBs)": 320,
    "Calcium Channel Blockers": 240,
    "Diuretics": 100,
    "Alpha Blockers": 20,
    "Vasodilators": 40,
    "Central Agonists": 0  # placeholder
}
chol_options = {
    "Statins": 80,
    "Fibrates": 200,
    "Niacin": 2000,
    "Bile Acid Sequestrants": 15000,
    "Cholesterol Absorption Inhibitors": 10,
    "PCSK9 Inhibitors": 420,
    "Omega-3 Fatty Acids": 4000
}

bp_meds = st.multiselect("Select Blood Pressure Medications:", ["None"] + list(bp_options.keys()))
chol_meds = st.multiselect("Select Cholesterol Medications:", ["None"] + list(chol_options.keys()))

bp_doses = {}
for med in bp_meds:
    if med != "None":
        bp_doses[med] = st.slider(f"Dose for Blood Pressure Med: {med} (mg/day)", 0, bp_options[med], min(bp_options[med], 50))

chol_doses = {}
for med in chol_meds:
    if med != "None":
        chol_doses[med] = st.slider(f"Dose for Cholesterol Med: {med} (mg/day)", 0, chol_options[med], min(chol_options[med], 50))
