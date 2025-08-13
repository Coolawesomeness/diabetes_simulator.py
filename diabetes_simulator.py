import streamlit as st
import matplotlib.pyplot as plt
from random import uniform
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import math

selected_tab = st.sidebar.radio("Select a tab", ["🏠 Home", "📈 CGM Simulation", "📤 CGM Upload"])
if selected_tab == "🏠 Home":
    
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

    # Define glucose impact values for additional medications
    bp_medications = {med: 0.10 for med in bp_options}
    chol_medications = {med: 0.05 for med in chol_options}
    steroid_medications = {k: v[0] for k, v in steroid_options.items()}
    antidepressant_medications = {k: v[0] for k, v in antidepressant_options.items()}
    antipsychotic_medications = {k: v[0] for k, v in antipsychotic_options.items()}
    # --- Insulin Sensitivity Factor Calculator ---
    st.subheader("💉 Insulin Sensitivity Calculator (Outpatient Use Only)")
    st.markdown("""
    The Insulin Sensitivity Factor (ISF) tells you how much 1 unit of insulin will lower your blood glucose.
    
    - **Rapid-acting insulin (e.g., Humalog, Novolog)**: use the **1800 Rule** → ISF = 1800 ÷ Total Daily Dose (TDD)
    - **Short-acting (Regular insulin)**: use the **1500 Rule** → ISF = 1500 ÷ TDD
    """)
    
    insulin_type = st.selectbox("Select Insulin Type", ["Rapid-acting", "Short-acting (Regular)", "Intermediate-acting", "Long-acting"])
    tdd = st.number_input("Enter Total Daily Insulin Dose (TDD) in units", min_value=1.0, step=1.0)
    
    if insulin_type == "Rapid-acting":
        isf = round(1800 / tdd, 1)
        st.markdown("💡 Rapid-acting insulin works quickly (within 15 mins), peaks in 1-2 hrs, lasts 3-5 hrs.")
    elif insulin_type == "Short-acting (Regular)":
        isf = round(1500 / tdd, 1)
        st.markdown("💡 Regular insulin begins working in 30 minutes, peaks in 2-3 hrs, and lasts 5-8 hrs.")
    else:
        isf = None
        st.markdown("⚠️ ISF is typically used with rapid or short-acting insulin only.")
    
    if isf:
        st.success(f"Estimated ISF: 1 unit lowers glucose by ~{isf} mg/dL")
        current_bg = st.number_input("Enter Current Blood Glucose (mg/dL)", min_value=0.0, step=1.0)
        target_bg = st.number_input("Enter Target Blood Glucose (mg/dL)", min_value=0.0, value=110.0, step=1.0)
        if current_bg > target_bg:
            correction_dose = round((current_bg - target_bg) / isf, 1)
            st.info(f"Suggested Correction Dose: {correction_dose} units of {insulin_type} insulin")
            st.markdown("✅ Safe correction is usually 1–3 units unless otherwise instructed by a healthcare provider.")
    # ------------------ SLEEP AND HORMONAL SURVEY ------------------#
    st.subheader("🛌 Sleep and Hormonal Factors")
    
    sleep_hours = st.slider("Average Sleep Duration (hours/night)", 3, 12, 7)
    is_menstruating = st.checkbox("Is the patient currently menstruating?", value=False)
    is_pregnant = st.checkbox("Is the patient currently pregnant?", value=False)
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
    
        # Base glucose depending on diagnosis
        base_glucose = 110 if diagnosis == "Non-diabetic" else (125 if diagnosis == "Pre-diabetic" else 160)
    
        # Medication effect
        med_effect = 0
        for med in selected_meds:
            base_effect = (
                medication_types.get(med, (0, 0))[0]
                if diagnosis == "Diabetic"
                else prediabetic_meds.get(med, (0, 0))[0]
            )
            if med in meds_with_dose:
                med_effect += base_effect * (med_doses.get(med, 0) / 1000)
            else:
                med_effect += base_effect
    
        if diagnosis == "Pre-diabetic":
            med_effect *= 0.7
        elif diagnosis == "Non-diabetic":
            med_effect *= 0.3
    
        if len(selected_meds) > 1:
            med_effect *= 0.8  # Diminishing return on med stacking
    
        # BP and cholesterol med effects
        base_glucose += 5 * len([med for med in bp_meds if med != "None"])
        base_glucose += 7 * len([med for med in chol_meds if med != "None"])
    
        # Antidepressant, antipsychotic, and steroid effects
        base_glucose += 12 * len([med for med in steroid_meds if med != "None"])
        base_glucose += 10 * len([med for med in antidepressant_meds if med != "None"])
        base_glucose += 15 * len([med for med in antipsychotic_meds if med != "None"])
    
        # Diet and exercise adjustments
        diet_factor = max(0.5, 1 - 0.01 * diet_score)
        adjusted_glucose = base_glucose - (med_effect * 15) - (exercise * 0.2) + (weight * 0.05)
        adjusted_glucose *= diet_factor
    
        # --- INSULIN EFFECT ---
        insulin_effect = 0
        correction_dose = 0
        
        if insulin_type in ["Rapid-acting", "Short-acting"] and tdd > 0:
            isf = (1800 if insulin_type == "Rapid-acting" else 1500) / tdd
    
            if current_bg and target_bg:
                try:
                    correction_dose = max((current_glucose - target_glucose) / isf, 0)
                    insulin_effect = correction_dose * isf
                    adjusted_glucose -= insulin_effect
                except ZeroDivisionError:
                    pass
        # ----------------------
    
        avg_glucose = adjusted_glucose
    
        # Simulated glucose levels over a week
        glucose_levels = [avg_glucose + uniform(-10, 10) for _ in range(7)]
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    
        # Metrics
        estimated_hba1c = round((sum(glucose_levels) / 7 + 46.7) / 28.7, 2)
        fasting_glucose = round(avg_glucose - 10, 1)
        post_meal_glucose = round(avg_glucose + 25, 1)
    
        if estimated_hba1c < 5.7:
            diagnosis_label = "Normal"
        elif estimated_hba1c < 6.5:
            diagnosis_label = "Pre-diabetic"
        else:
            diagnosis_label = "Diabetic"
    
        # Display results
        st.subheader("📊 Simulation Results")
        st.metric("Average Glucose (mg/dL)", f"{round(sum(glucose_levels)/7, 1)}")
        st.metric("Fasting Glucose (mg/dL)", f"{fasting_glucose}")
        st.metric("2-hour Post-Meal Glucose (mg/dL)", f"{post_meal_glucose}")
        st.metric("Estimated HbA1c (%)", f"{estimated_hba1c}", diagnosis_label)
    
        fig, ax = plt.subplots()
        ax.plot(days, glucose_levels, marker="o", color="blue")
        ax.set_title("Simulated Blood Glucose Over 7 Days")
        ax.set_ylabel("Glucose (mg/dL)")
        st.pyplot(fig)
    

# CGM Simulation Tab
if selected_tab == "📈 CGM Simulation":
    st.header("📈 CGM Data Simulation")
    st.markdown("Simulate continuous glucose monitor (CGM) data based on your inputs.")

    st.subheader("CGM Settings")
    num_days = st.slider("Number of Days to Simulate", 1, 14, 7)
    readings_per_day = st.slider("Readings per Day", 24, 288, 96)

    total_readings = num_days * readings_per_day
    time_interval = 24 * 60 // readings_per_day  # minutes between readings

    st.subheader("Simulation Parameters")
    baseline_glucose = st.slider("Baseline Glucose (mg/dL)", 70, 180, 110)
    glucose_variability = st.slider("Glucose Variability", 0, 50, 15)
    meal_effect = st.slider("Meal Effect Amplitude (mg/dL)", 0, 100, 40)
    exercise_effect = st.slider("Exercise Drop Amplitude (mg/dL)", 0, 80, 25)

    if st.button("Run CGM Simulation"):
        cgm_data = []
        timestamps = []

        for day in range(num_days):
            for reading in range(readings_per_day):
                minutes_since_start = day * 1440 + reading * time_interval
                time = datetime.now() + timedelta(minutes=minutes_since_start)
                meal_bump = meal_effect * np.sin(2 * np.pi * reading / (readings_per_day // 3))
                exercise_dip = -exercise_effect * np.cos(2 * np.pi * reading / (readings_per_day // 4))
                random_noise = np.random.normal(0, glucose_variability)
                value = baseline_glucose + meal_bump + exercise_dip + random_noise
                cgm_data.append(round(value, 1))
                timestamps.append(time.strftime("%Y-%m-%d %I:%M %p"))

        df_cgm = pd.DataFrame({"Timestamp": timestamps, "Glucose (mg/dL)": cgm_data})

        st.subheader("📊 Simulated CGM Data")
        st.line_chart(df_cgm.set_index("Timestamp"))

        st.subheader("Summary Metrics")
        avg_glucose = np.mean(cgm_data)
        time_in_range = sum(70 <= val <= 180 for val in cgm_data) / len(cgm_data) * 100
        estimated_hba1c = round((avg_glucose + 46.7) / 28.7, 2)

        st.metric("Average Glucose", f"{round(avg_glucose, 1)} mg/dL")
        st.metric("Time in Range (70-180 mg/dL)", f"{round(time_in_range, 1)}%")
        st.metric("Estimated HbA1c", f"{estimated_hba1c}%")

        # Summary Metrics
avg_glucose = np.mean(cgm_data)
time_in_range = sum(70 <= val <= 180 for val in cgm_data) / len(cgm_data) * 100
estimated_hba1c = round((avg_glucose + 46.7) / 28.7, 2)

st.metric("Average Glucose", f"{round(avg_glucose, 1)} mg/dL")
st.metric("Time in Range (70-180 mg/dL)", f"{round(time_in_range, 1)}%")
st.metric("Estimated HbA1c", f"{estimated_hba1c}%")

# Recommendations based on average glucose
st.subheader("📋 Recommendations")
if avg_glucose < 70:
    st.warning("Your average glucose level is below the normal range. Consider consulting your healthcare provider.")
elif 70 <= avg_glucose <= 180:
    st.success("Great job! Your average glucose level is within the normal range. Keep up the good work!")
else:
    st.error("Your average glucose level is above the normal range. Consider reviewing your diet and medication with your healthcare provider.")
# Placeholder tabs for future expansion
elif selected_tab == "📤 CGM Upload":
    st.header("📤 Upload CGM Data")
    st.markdown("Upload a CSV file with CGM readings to analyze your glucose trends.")

    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

    if uploaded_file is not None:
        try:
            df_uploaded = pd.read_csv(uploaded_file)

            # Try standardizing columns
            df_uploaded.columns = [col.strip().lower() for col in df_uploaded.columns]
            if "timestamp" in df_uploaded.columns and ("glucose" in df_uploaded.columns or "glucose (mg/dl)" in df_uploaded.columns):
                glucose_col = "glucose" if "glucose" in df_uploaded.columns else "glucose (mg/dl)"
                df_uploaded["Timestamp"] = pd.to_datetime(df_uploaded["timestamp"])
                df_uploaded["Glucose (mg/dL)"] = pd.to_numeric(df_uploaded[glucose_col], errors="coerce")
                df_uploaded = df_uploaded.dropna(subset=["Glucose (mg/dL)"])

                st.subheader("📊 Uploaded CGM Data")
                st.line_chart(df_uploaded.set_index("Timestamp")["Glucose (mg/dL)"])

                st.subheader("Summary Metrics")
                avg_glucose = df_uploaded["Glucose (mg/dL)"].mean()
                time_in_range = df_uploaded["Glucose (mg/dL)"].between(70, 180).mean() * 100
                estimated_hba1c = round((avg_glucose + 46.7) / 28.7, 2)

                st.metric("Average Glucose", f"{avg_glucose:.1f} mg/dL")
                st.metric("Time in Range (70-180 mg/dL)", f"{time_in_range:.1f}%")
                st.metric("Estimated HbA1c", f"{estimated_hba1c}%")
            else:
                st.error("Make sure your CSV includes 'Timestamp' and 'Glucose (mg/dL)' columns.")

        except Exception as e:
            st.error(f"Error reading file: {e}")






