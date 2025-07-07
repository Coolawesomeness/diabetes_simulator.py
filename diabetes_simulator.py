import streamlit as st
import matplotlib.pyplot as plt
from random import uniform

# ------------------ PAGE CONFIG ------------------ #
st.set_page_config(
    page_title="Diabetes Digital Simulator by Siddharth Tirumalai",
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
med_dose = st.slider("Medication Dose (mg/day)", 0, 2000, 500)
weight = st.slider("Weight (lbs)", 30, 200, 70)
exercise = st.slider("Daily Exercise (min)", 0, 120, 30)
insulin_sensitivity = st.slider("Insulin Sensitivity (1 = normal)", 0.5, 2.0, 1.0)

# ------------------ DIAGNOSIS ------------------ #
diagnosis = st.radio("Select Glucose Status:", ["Non-diabetic", "Pre-diabetic", "Diabetic"])

# ------------------ MEDICATION OPTIONS ------------------ #
medication_types = {
    "Insulin": 1.00,
    "Sulfonylureas": 0.70,
    "Metformin": 0.50,
    "GLP-1 Receptor Agonists": 0.60,
    "SGLT2 Inhibitors": 0.40,
    "Thiazolidinediones (TZDs)": 0.45,
    "DPP-4 Inhibitors": 0.30,
    "Meglitinides": 0.55,
    "Alpha-glucosidase Inhibitors": 0.35,
    "Amylin Analogs": 0.25
}

prediabetic_meds = {
    "Metformin": 0.40,
    "Lifestyle Coaching": 0.30,
    "Weight Loss Agents": 0.20,
    "GLP-1 Receptor Agonists": 0.45,
    "Alpha-glucosidase Inhibitors": 0.25,
    "Thiazolidinediones (TZDs)": 0.35,
    "Acarbose": 0.30,
    "Intermittent Fasting Protocols": 0.25
}

# Show medication options depending on status
if diagnosis == "Diabetic":
    selected_meds = st.multiselect("Select Anti-Diabetic Medications:", list(medication_types.keys()))
elif diagnosis == "Pre-diabetic":
    selected_meds = st.multiselect("Select Pre-Diabetic Medications:", list(prediabetic_meds.keys()))
else:
    selected_meds = []

# Expanded medication classes for BP and cholesterol
bp_options = [
    "None", "Beta Blockers", "ACE Inhibitors", "Angiotensin II Receptor Blockers (ARBs)", "Calcium Channel Blockers",
    "Diuretics", "Alpha Blockers", "Vasodilators", "Central Agonists"
]
chol_options = [
    "None", "Statins", "Fibrates", "Niacin", "Bile Acid Sequestrants", "Cholesterol Absorption Inhibitors",
    "PCSK9 Inhibitors", "Omega-3 Fatty Acids"
]

bp_meds = st.multiselect("Select Blood Pressure Medications:", bp_options)
chol_meds = st.multiselect("Select Cholesterol Medications:", chol_options)

# ------------------ DIET SURVEY ------------------ #
st.subheader("🍽️ Diet Quality Survey")

veg_servings = st.slider("How many servings of vegetables per week?", 0, 70, 21)
fruit_servings = st.slider("How many servings of fruits per week?", 0, 70, 14)
sugary_snacks = st.slider("How many sugary snacks or drinks per week?", 0, 70, 14)
fast_food = st.slider("How many fast food meals per week?", 0, 14, 3)
cook_freq = st.slider("How often do you cook meals at home per week?", 0, 21, 5)

diet_score = 0
diet_score += (veg_servings / 7) * 3
diet_score += (fruit_servings / 7) * 2
diet_score -= sugary_snacks
diet_score -= fast_food
diet_score += (cook_freq / 7) * 2  # positive impact for cooking frequency

diet_score = max(0, diet_score)  # prevent negative diet score

# ------------------ SIMULATION ------------------ #
if st.button("⏱️ Run Simulation"):
    st.success("Simulation started!")

    # Base glucose estimate
    base_glucose = 110 if diagnosis == "Non-diabetic" else (125 if diagnosis == "Pre-diabetic" else 160)

    # Adjustments
    med_effect = 0
    for med in selected_meds:
        if diagnosis == "Diabetic":
            med_effect += medication_types.get(med, 0)
        elif diagnosis == "Pre-diabetic":
            med_effect += prediabetic_meds.get(med, 0)
        else:
            med_effect += 0  # Non-diabetic meds not expected to affect glucose significantly

    # Scale med effect to dose and condition
    if diagnosis == "Pre-diabetic":
        med_effect *= 0.7  # generally less sensitive to meds
    elif diagnosis == "Non-diabetic":
        med_effect *= 0.3  # very low effect expected

    med_effect *= med_dose / 1000

    # Diminishing returns for multiple meds
    if len(selected_meds) > 1:
        med_effect *= 0.8

    # Blood pressure & cholesterol meds (small raise in glucose)
    base_glucose += 5 * len([med for med in bp_meds if med != "None"])
    base_glucose += 7 * len([med for med in chol_meds if med != "None"])

    # Adjust for lifestyle
    diet_factor = max(0.5, 1 - 0.01 * diet_score)
    adjusted_sensitivity = insulin_sensitivity * diet_factor

    # Final glucose estimation
    med_effect *= med_dose / 1000
    avg_glucose = base_glucose - (med_effect * 15) - (exercise * 0.2) + (weight * 0.05)
    avg_glucose /= adjusted_sensitivity

    # Simulate over 7 days
    glucose_levels = [avg_glucose + uniform(-10, 10) for _ in range(7)]
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    # Estimate HbA1c
    estimated_hba1c = round((sum(glucose_levels) / 7 + 46.7) / 28.7, 2)
    if estimated_hba1c < 5.7:
        diagnosis_label = "Normal"
    elif estimated_hba1c < 6.5:
        diagnosis_label = "Pre-diabetic"
    else:
        diagnosis_label = "Diabetic"

    # ------------------ RESULTS ------------------ #
    st.subheader("📊 Simulation Results")
    st.metric("Average Glucose (mg/dL)", f"{round(sum(glucose_levels)/7,1)}")
    st.metric("Estimated HbA1c (%)", f"{estimated_hba1c}", diagnosis_label)

    fig, ax = plt.subplots()
    ax.plot(days, glucose_levels, marker='o', color='blue')
    ax.set_title("Simulated Blood Glucose Over 7 Days")
    ax.set_ylabel("Glucose (mg/dL)")
    st.pyplot(fig)
