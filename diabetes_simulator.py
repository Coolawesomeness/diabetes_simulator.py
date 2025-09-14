import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from random import uniform

# ------------------ APP LAYOUT ------------------ #
st.set_page_config(page_title="Diabetes Digital Twin", layout="wide")

# Sidebar Navigation
tabs = ["🏠 Home", "📊 CGM Simulation", "📂 CGM Upload", "📝 Action Plan"]
selected_tab = st.sidebar.radio("Navigate", tabs)

# ========================================================= #
# ====================== HOME TAB ========================= #
# ========================================================= #
if selected_tab == "🏠 Home":
    st.title("📈 Diabetes Digital Simulator")
    st.markdown("""
    **Created by: Siddharth Tirumalai**  
    Simulate blood glucose and HbA1c changes based on medications, diet, and lifestyle factors.
    """)

    st.warning("""
    ⚠️ This simulation provides **estimated trends** in glucose and HbA1c based on your input. 
    Results may not reflect your actual health status. Always consult your healthcare provider.
    """)

    # ------------------ USER INFO ------------------ #
    age = st.slider("Patient Age (years)", 10, 100, 45)
    weight = st.slider("Weight (lbs)", 60, 300, 117)
    exercise = st.slider("Daily Exercise (min)", 0, 120, 30)

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

    chol_options = {
        "Statins": 80,
        "Fibrates": 200,
        "Niacin": 2000,
        "Bile Acid Sequestrants": 15000,
        "Cholesterol Absorption Inhibitors": 10,
        "PCSK9 Inhibitors": 420,
        "Omega-3 Fatty Acids": 4000
    }

    steroid_options = {
        "Prednisone": (0.20, 60),
        "Hydrocortisone": (0.15, 100),
        "Dexamethasone": (0.25, 20),
        "Methylprednisolone": (0.18, 80)
    }

    antidepressant_options = {
        "SSRIs": (0.10, 100),
        "SNRIs": (0.12, 200),
        "Tricyclics": (0.15, 150),
        "MAO Inhibitors": (0.10, 60)
    }

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

    med_doses = {}
    meds_with_dose = list(medication_types.keys()) + list(prediabetic_meds.keys())
    for med in selected_meds:
        max_dose = medication_types[med][1] if diagnosis == "Diabetic" else prediabetic_meds[med][1]
        med_doses[med] = st.slider(f"Dose for {med} (mg/day)", 0, max_dose, min(max_dose, 500))

    # ------------------ OTHER MEDICATIONS ------------------ #
    bp_meds = st.multiselect("Select Blood Pressure Medications:", ["None"] + list(bp_options.keys()))
    chol_meds = st.multiselect("Select Cholesterol Medications:", ["None"] + list(chol_options.keys()))
    steroid_meds = st.multiselect("Select Steroid Medications:", ["None"] + list(steroid_options.keys()))
    antidepressant_meds = st.multiselect("Select Antidepressant Medications:", ["None"] + list(antidepressant_options.keys()))
    antipsychotic_meds = st.multiselect("Select Antipsychotic Medications:", ["None"] + list(antipsychotic_options.keys()))

    # ------------------ INSULIN SENSITIVITY FACTOR ------------------ #
    st.subheader("💉 Insulin Sensitivity Calculator (Outpatient Use Only)")
    insulin_type = st.selectbox("Select Insulin Type", ["Rapid-acting", "Short-acting (Regular)", "Intermediate-acting", "Long-acting"])
    tdd = st.number_input("Enter Total Daily Insulin Dose (TDD) in units", min_value=1.0, step=1.0)
    
    if insulin_type == "Rapid-acting":
        isf = round(1800 / tdd, 1)
    elif insulin_type == "Short-acting (Regular)":
        isf = round(1500 / tdd, 1)
    else:
        isf = None

    if isf:
        st.success(f"Estimated ISF: 1 unit lowers glucose by ~{isf} mg/dL")

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
        base_glucose = 110 if diagnosis == "Non-diabetic" else (125 if diagnosis == "Pre-diabetic" else 160)
        adjusted_glucose = base_glucose - (exercise * 0.2) + (weight * 0.05)
        adjusted_glucose *= max(0.5, 1 - 0.01 * diet_score)

        glucose_levels = [adjusted_glucose + uniform(-10, 10) for _ in range(7)]
        estimated_hba1c = round((sum(glucose_levels) / 7 + 46.7) / 28.7, 2)

        st.metric("Average Glucose (mg/dL)", f"{round(sum(glucose_levels)/7, 1)}")
        st.metric("Estimated HbA1c (%)", f"{estimated_hba1c}")

        # Explanations
        with st.expander("ℹ️ What do these results mean?"):
            st.markdown("""
            - **Fasting Glucose**: <100 normal | 100–125 pre-diabetes | ≥126 diabetes  
            - **Post-Meal Glucose**: Goal <180 mg/dL  
            - **HbA1c**: <5.7% normal | 5.7–6.4% pre-diabetes | ≥6.5% diabetes
            """)

        # Feedback
        st.subheader("📋 Lifestyle Feedback")
        if exercise < 30:
            st.warning("Try to exercise at least 30 mins daily.")
        if diet_score < 10:
            st.error("Low diet score — add more vegetables and fruits.")
        if sleep_hours < 7:
            st.warning("Less than 7 hrs of sleep may worsen insulin resistance.")

        fig, ax = plt.subplots()
        ax.plot(["Mon","Tue","Wed","Thu","Fri","Sat","Sun"], glucose_levels, marker="o")
        st.pyplot(fig)

# ========================================================= #
# ================== CGM SIMULATION TAB ================== #
# ========================================================= #
elif selected_tab == "📊 CGM Simulation":
    st.title("📊 Simulate CGM Data")
    days = st.slider("Days of CGM Data", 1, 30, 7)
    mean_glucose = st.slider("Average Glucose (mg/dL)", 80, 200, 120)
    variability = st.slider("Glucose Variability (SD)", 5, 50, 15)

    time = pd.date_range(start="2023-01-01", periods=days*288, freq="5min")
    glucose = np.random.normal(mean_glucose, variability, len(time))
    df = pd.DataFrame({"Time": time, "Glucose": glucose})

    st.line_chart(df.set_index("Time"))

    st.download_button("📥 Download Simulated CGM CSV", df.to_csv(index=False), "simulated_cgm.csv", "text/csv")

# ========================================================= #
# =================== CGM UPLOAD TAB ====================== #
# ========================================================= #
elif selected_tab == "📂 CGM Upload":
    st.title("📂 Upload Your CGM Data")
    uploaded_file = st.file_uploader("Upload CGM CSV", type=["csv"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write(df.head())
        st.line_chart(df.set_index(df.columns[0]))

# ========================================================= #
# ================== ACTION PLAN TAB ====================== #
# ========================================================= #
elif selected_tab == "📝 Action Plan":
    st.title("📝 Personalized Action Plan")

    # ----------------- MEAL LOGGING ----------------- #
    st.header("🍽️ Meal Logger & Calorie Check")

    if "meals" not in st.session_state:
        st.session_state["meals"] = []

    with st.form("meal_form", clear_on_submit=True):
        meal_name = st.text_input("Meal Name")
        meal_calories = st.number_input("Calories", min_value=0, step=10)
        submitted = st.form_submit_button("➕ Add Meal")
        if submitted and meal_name and meal_calories > 0:
            st.session_state["meals"].append({"meal": meal_name, "calories": meal_calories})

    if st.session_state["meals"]:
        df_meals = pd.DataFrame(st.session_state["meals"])
        st.table(df_meals)

        total_calories = sum(m["calories"] for m in st.session_state["meals"])
        st.metric("Total Calories Consumed", f"{total_calories} kcal")

        if "daily_calories" in st.session_state:
            daily_target = st.session_state["daily_calories"]
            if total_calories < daily_target * 0.9:
                st.success(f"✅ You’re under your target ({daily_target} kcal). Keep fueling your body!")
            elif total_calories <= daily_target * 1.1:
                st.info(f"⚖️ You’re right on track! ({total_calories}/{daily_target} kcal)")
            else:
                st.error(f"⚠️ You’ve exceeded your daily target ({daily_target} kcal). Consider lighter meals later.")

    st.divider()

    # ----------------- EXERCISE RECOMMENDER ----------------- #
    st.header("🏃 Exercise Recommendations")

    if "exercise" in st.session_state and st.session_state.exercise < 30:
        st.warning("You’re getting less than 30 mins of exercise daily. Try one of these:")

        exercises = {
            "🚶 Walking": 20,
            "🚴 Cycling": 15,
            "🧘 Yoga": 20,
            "🏋️ Strength Training": 25,
            "🕺 Dance": 15
        }

        for ex, mins in exercises.items():
            col1, col2 = st.columns([2,1])
            with col1:
                st.markdown(f"**{ex}** — {mins} mins")
            with col2:
                if st.button(f"▶️ Start {ex}", key=ex):
                    st.session_state["exercise_timer"] = {"exercise": ex, "remaining": mins}

    if "exercise_timer" in st.session_state:
        ex_info = st.session_state["exercise_timer"]
        st.subheader(f"⏱️ {ex_info['exercise']} Timer")
        if ex_info["remaining"] > 0:
            st.info(f"{ex_info['remaining']} minutes remaining")
            # Decrease timer on refresh
            st.session_state["exercise_timer"]["remaining"] -= 1
            st.experimental_rerun()
        else:
            st.success(f"✅ {ex_info['exercise']} complete! Great job!")
            del st.session_state["exercise_timer"]

    else:
        st.success("✅ You’re meeting your daily exercise goal!")




