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
weight = st.slider("Weight (lbs)", 60, 300, 117)
exercise = st.slider("Daily Exercise (min)", 0, 120, 30)
insulin_sensitivity = st.slider("Insulin Sensitivity (1 = normal)", 0.5, 2.0, 1.0)

# ------------------ DIAGNOSIS ------------------ #
diagnosis = st.radio("Select Glucose Status:", ["Non-diabetic", "Pre-diabetic", "Diabetic"])

# ------------------ MEDICATION OPTIONS ------------------ #
# Diabetic Medications: effectiveness decimal, max dose mg/day
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

# Pre-Diabetic Medications: effectiveness decimal, max dose mg/day
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

# Blood Pressure Medications: max dose mg/day
bp_options = {
    "Beta Blockers": 200,
    "ACE Inhibitors": 40,
    "Angiotensin II Receptor Blockers (ARBs)": 320,
    "Calcium Channel Blockers": 240,
    "Diuretics": 100,
    "Alpha Blockers": 20,
    "Vasodilators": 40,
    "Central Agonists": 100
}

# Cholesterol Medications: max dose mg/day
chol_options = {
    "Statins": 80,
    "Fibrates": 200,
    "Niacin": 2000,
    "Bile Acid Sequestrants": 15000,
    "Cholesterol Absorption Inhibitors": 10,
    "PCSK9 Inhibitors": 420,
    "Omega-3 Fatty Acids": 4000
}

# Steroid Medications: estimated effect on glucose (+) and max dose mg/day
steroid_options = {
    "Prednisone": (0.20, 60),
    "Hydrocortisone": (0.15, 100),
    "Dexamethasone": (0.25, 20),
    "Methylprednisolone": (0.18, 80)
}

# Antidepressant Medications: estimated effect on glucose (+) and max dose mg/day
antidepressant_options = {
    "SSRIs": (0.10, 100),
    "SNRIs": (0.12, 200),
    "Tricyclics": (0.15, 150),
    "MAO Inhibitors": (0.10, 60)
}

# Antipsychotic Medications: estimated effect on glucose (+) and max dose mg/day
antipsychotic_options = {
    "Olanzapine": (0.25, 20),
    "Risperidone": (0.18, 8),
    "Quetiapine": (0.20, 800),
    "Aripiprazole": (0.12, 30)
}

# ------------------ MEDICATION SELECTION ------------------ #
if diagnosis == "Diabetic":
    selected_meds = st.multiselect("Select Anti-Diabetic Medications:", list(medication_types.keys()))
elif diagnosis == "Pre-diabetic":
    selected_meds = st.multiselect("Select Pre-Diabetic Medications:", list(prediabetic_meds.keys()))
else:
    selected_meds = []

# Doses for diabetic/pre-diabetic meds
med_doses = {}
meds_with_dose = list(medication_types.keys()) + list(prediabetic_meds.keys())
for med in selected_meds:
    max_dose = medication_types[med][1] if diagnosis == "Diabetic" else prediabetic_meds[med][1]
    med_doses[med] = st.slider(f"Dose for {med} (mg/day)", 0, max_dose, min(max_dose, 500))

# ------------------ OTHER MEDICATIONS SELECTION ------------------ #
bp_meds = st.multiselect("Select Blood Pressure Medications:", ["None"] + list(bp_options.keys()))
chol_meds = st.multiselect("Select Cholesterol Medications:", ["None"] + list(chol_options.keys()))
steroid_meds = st.multiselect("Select Steroid Medications:", ["None"] + list(steroid_options.keys()))
antidepressant_meds = st.multiselect("Select Antidepressant Medications:", ["None"] + list(antidepressant_options.keys()))
antipsychotic_meds = st.multiselect("Select Antipsychotic Medications:", ["None"] + list(antipsychotic_options.keys()))

# Doses for blood pressure meds
bp_doses = {}
for med in bp_meds:
    if med != "None":
        bp_doses[med] = st.slider(f"Dose for Blood Pressure Med: {med} (mg/day)", 0, bp_options[med], min(bp_options[med], 50))

# Doses for cholesterol meds
chol_doses = {}
for med in chol_meds:
    if med != "None":
        chol_doses[med] = st.slider(f"Dose for Cholesterol Med: {med} (mg/day)", 0, chol_options[med], min(chol_options[med], 50))

# Doses for steroid meds
steroid_doses = {}
for med in steroid_meds:
    if med != "None":
        steroid_doses[med] = st.slider(f"Dose for Steroid Med: {med} (mg/day)", 0, steroid_options[med][1], min(steroid_options[med][1], 20))

# Doses for antidepressant meds
antidepressant_doses = {}
for med in antidepressant_meds:
    if med != "None":
        antidepressant_doses[med] = st.slider(f"Dose for Antidepressant Med: {med} (mg/day)", 0, antidepressant_options[med][1], min(antidepressant_options[med][1], 50))

# Doses for antipsychotic meds
antipsychotic_doses = {}
for med in antipsychotic_meds:
    if med != "None":
        antipsychotic_doses[med] = st.slider(f"Dose for Antipsychotic Med: {med} (mg/day)", 0, antipsychotic_options[med][1], min(antipsychotic_options[med][1], 50))
# ------------------ DIET QUESTIONNAIRE ------------------ #
st.subheader("🍽️ Diet Quality Questionnaire")

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
diet_score += (cook_freq / 7) * 2

diet_score = max(0, diet_score)

# ------------------ SIMULATION ------------------ #
if st.button("⏱️ Run Simulation"):
    st.success("Simulation started!")

    # STEP 1: Determine base glucose based on diagnosis
    base_glucose = 110 if diagnosis == "Non-diabetic" else (125 if diagnosis == "Pre-diabetic" else 160)

    # STEP 2: Medication effects
    med_effect = 0
    all_meds = {
        **{med: medication_types.get(med, (0, 0))[0] for med in selected_meds},
        **{med: bp_medications.get(med, 0) for med in bp_meds if med != "None"},
        **{med: chol_medications.get(med, 0) for med in chol_meds if med != "None"},
        **{med: steroid_medications.get(med, 0) for med in steroid_meds if med != "None"},
        **{med: antidepressant_medications.get(med, 0) for med in antidepressant_meds if med != "None"},
        **{med: antipsychotic_medications.get(med, 0) for med in antipsychotic_meds if med != "None"},
    }

    for med, effect in all_meds.items():
        if med in med_doses:
            med_effect += effect * (med_doses.get(med, 0) / 1000)
        else:
            med_effect += effect

    # Adjust effect based on diagnosis
    if diagnosis == "Pre-diabetic":
        med_effect *= 0.7
    elif diagnosis == "Non-diabetic":
        med_effect *= 0.3

    # If many meds, reduce effectiveness due to interaction
    if len(all_meds) > 2:
        med_effect *= 0.85

    # STEP 3: Adjustments based on lifestyle & conditions
    diet_factor = max(0.4, 1 - 0.015 * diet_score)  # Higher diet_score = lower impact
    adjusted_sensitivity = insulin_sensitivity * diet_factor

    # Sleep effect
    if sleep_hours < 6:
        base_glucose += 15
    elif sleep_hours > 9:
        base_glucose -= 5

    # Menstrual cycle
    if is_menstruating:
        base_glucose += 10

    # Pregnancy effect
    if is_pregnant:
        base_glucose += 25

    # STEP 4: Final glucose computation
    avg_glucose = base_glucose - (med_effect * 15) - (exercise * 0.2) + (weight * 0.05)
    avg_glucose /= max(adjusted_sensitivity, 1)

    # Simulate daily variation
    glucose_levels = [avg_glucose + uniform(-12, 12) for _ in range(7)]
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    # Derived values
    estimated_hba1c = round((sum(glucose_levels) / 7 + 46.7) / 28.7, 2)
    fasting_glucose = round(avg_glucose - 10, 1)
    post_meal_glucose = round(avg_glucose + 25, 1)

    if estimated_hba1c < 5.7:
        diagnosis_label = "Normal"
    elif estimated_hba1c < 6.5:
        diagnosis_label = "Pre-diabetic"
    else:
        diagnosis_label = "Diabetic"

    # STEP 5: Output Results
    st.subheader("📊 Simulation Results")
    st.metric("Average Glucose (mg/dL)", f"{round(sum(glucose_levels)/7,1)}")
    st.metric("Fasting Glucose (mg/dL)", f"{fasting_glucose}")
    st.metric("2-hour Post-Meal Glucose (mg/dL)", f"{post_meal_glucose}")
    st.metric("Estimated HbA1c (%)", f"{estimated_hba1c}", diagnosis_label)

    fig, ax = plt.subplots()
    ax.plot(days, glucose_levels, marker='o', color='blue')
    ax.set_title("Simulated Blood Glucose Over 7 Days")
    ax.set_ylabel("Glucose (mg/dL)")
    st.pyplot(fig)
