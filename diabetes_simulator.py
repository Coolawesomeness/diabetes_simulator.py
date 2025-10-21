
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from random import uniform
from datetime import datetime, timedelta
import streamlit.components.v1 as components

# Optional helper for auto-refresh used by timer. If not installed, the app still runs.
try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    def st_autorefresh(interval=0, key=None):
        # no-op fallback
        return None

# ------------------ PAGE CONFIG ------------------ #
st.set_page_config(page_title="Digital Diabetes Simulator", layout="wide")

# ------------------ SESSION STATE INIT ------------------ #
if "cgm_data" not in st.session_state:
    st.session_state.cgm_data = None
if "sim_results" not in st.session_state:
    st.session_state.sim_results = {}
if "meals" not in st.session_state:
    st.session_state.meals = []
if "exercise_timer" not in st.session_state:
    st.session_state.exercise_timer = None

# ------------------ SIDEBAR NAVIGATION ------------------ #
TABS = [
    "🏠 Home",
    "📊 CGM Simulation",
    "📂 CGM Upload",
    "📝 Action Plan",
    "🔬 How Diabetes Works (Interactive)"
]
selected_tab = st.sidebar.radio("Navigate", TABS)

# ===================== TAB: HOME ===================== #
if selected_tab == "🏠 Home":
    st.title("📈 Diabetes Digital Twin - Patient Intake")
    st.markdown("**Created by: Siddharth Tirumalai** — Simulate blood glucose and HbA1c changes based on medications, diet, sleep, and lifestyle.")

    st.info("ℹ️ Fill this intake to personalize simulations. Results are estimates — consult a clinician for medical decisions.")

    # ---------- Patient Info ----------
    st.header("🧑 Patient Information")
    col1, col2, col3 = st.columns(3)
    with col1:
        age = st.number_input("Age (years)", min_value=10, max_value=100, value=45)
    with col2:
        weight = st.number_input("Weight (lbs)", min_value=60, max_value=400, value=150)
    with col3:
        sex = st.selectbox("Sex", ["Male", "Female", "Other"])
    activity_level = st.selectbox("Activity Level", ["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Athlete"])
    exercise = st.slider("Daily Exercise (minutes)", 0, 120, 30, help="Minutes of moderate-to-vigorous activity per day")

    st.divider()

    # ---------- Diagnosis & Meds (FULL block) ----------
    st.header("🩺 Diagnosis & Medications")
    diagnosis = st.radio("Select Glucose Status:", ["Non-diabetic", "Pre-diabetic", "Diabetic"])

    # Diabetic Meds (effectiveness, max dose)
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

    # medication selection UI
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

    # other medication classes
    bp_meds = st.multiselect("Select Blood Pressure Medications:", ["None"] + list(bp_options.keys()))
    chol_meds = st.multiselect("Select Cholesterol Medications:", ["None"] + list(chol_options.keys()))
    steroid_meds = st.multiselect("Select Steroid Medications:", ["None"] + list(steroid_options.keys()))
    antidepressant_meds = st.multiselect("Select Antidepressant Medications:", ["None"] + list(antidepressant_options.keys()))
    antipsychotic_meds = st.multiselect("Select Antipsychotic Medications:", ["None"] + list(antipsychotic_options.keys()))

    bp_doses = {}
    for med in bp_meds:
        if med != "None":
            bp_doses[med] = st.slider(f"Dose for Blood Pressure Med: {med} (mg/day)", 0, bp_options[med], min(bp_options[med], 50))
    chol_doses = {}
    for med in chol_meds:
        if med != "None":
            chol_doses[med] = st.slider(f"Dose for Cholesterol Med: {med} (mg/day)", 0, chol_options[med], min(chol_options[med], 50))
    steroid_doses = {}
    for med in steroid_meds:
        if med != "None":
            steroid_doses[med] = st.slider(f"Dose for Steroid Med: {med} (mg/day)", 0, steroid_options[med][1], min(steroid_options[med][1], 20))
    antidepressant_doses = {}
    for med in antidepressant_meds:
        if med != "None":
            antidepressant_doses[med] = st.slider(f"Dose for Antidepressant Med: {med} (mg/day)", 0, antidepressant_options[med][1], min(antidepressant_options[med][1], 50))
    antipsychotic_doses = {}
    for med in antipsychotic_meds:
        if med != "None":
            antipsychotic_doses[med] = st.slider(f"Dose for Antipsychotic Med: {med} (mg/day)", 0, antipsychotic_options[med][1], min(antipsychotic_options[med][1], 50))

    st.divider()

    # ---------- Insulin Sensitivity ----------
    st.subheader("💉 Insulin Sensitivity Calculator (Outpatient Use Only)")
    st.markdown("""
        The **Insulin Sensitivity Factor (ISF)** tells how much 1 unit of rapid/short-acting insulin will lower blood glucose.
    """)
    insulin_type = st.selectbox("Select Insulin Type for ISF", ["Rapid-acting", "Short-acting (Regular)", "Intermediate-acting", "Long-acting"])
    tdd = st.number_input("Enter Total Daily Insulin Dose (TDD) in units", min_value=0.0, step=1.0)
    if insulin_type == "Rapid-acting" and tdd > 0:
        isf = round(1800 / tdd, 1)
    elif insulin_type == "Short-acting (Regular)" and tdd > 0:
        isf = round(1500 / tdd, 1)
    else:
        isf = None
    if isf:
        st.success(f"Estimated ISF: 1 unit lowers glucose by ~{isf} mg/dL")

    st.divider()

    # ---------- Sleep & Diet ----------
    st.header("🛌 Sleep & Diet")
    sleep_hours = st.slider("Average Sleep (hours/night)", 3, 12, 7, help="7–9 hours is generally recommended for adults.")
    is_menstruating = st.checkbox("Is the patient currently menstruating?", value=False)
    is_pregnant = st.checkbox("Is the patient currently pregnant?", value=False)

    st.subheader("🍽️ Diet Quality Questionnaire")
    col1, col2 = st.columns(2)
    with col1:
        veg_servings = st.slider("Vegetable servings per week", 0, 70, 21)
        fruit_servings = st.slider("Fruit servings per week", 0, 70, 14)
        cook_freq = st.slider("Home-cooked meals/week", 0, 21, 5)
    with col2:
        sugary_snacks = st.slider("Sugary snacks/drinks per week", 0, 70, 14)
        fast_food = st.slider("Fast food meals per week", 0, 14, 3)

    diet_score = max(0, (veg_servings / 7) * 3 + (fruit_servings / 7) * 2 - sugary_snacks - fast_food + (cook_freq / 7) * 2)
    # show progress (scaled)
    st.progress(min(diet_score / 20, 1.0))
    st.caption(f"Diet quality score: {diet_score:.1f} (higher is better)")

    st.divider()

    # ---------- Daily Calorie Target ----------
    st.header("🔥 Estimated Daily Calorie Target")
    # convert to kg for formulas
    weight_kg = weight * 0.45359237
    # Approximate height not provided — we will use a reasonable placeholder (170cm) for BMR; user can adjust later.
    height_cm = 170
    if sex == "Male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    activity_multiplier = {
        "Sedentary": 1.2,
        "Lightly Active": 1.375,
        "Moderately Active": 1.55,
        "Very Active": 1.725,
        "Athlete": 1.9
    }
    daily_calories = int(bmr * activity_multiplier.get(activity_level, 1.2))
    st.success(f"Estimated daily calories: {daily_calories} kcal")
    st.session_state["daily_calories"] = daily_calories

    st.divider()

    # ---------- Simulation (keeps existing logic) ----------
    if st.button("⏱️ Run Simulation"):
        st.success("Simulation started!")
        base_glucose = 110 if diagnosis == "Non-diabetic" else (125 if diagnosis == "Pre-diabetic" else 160)

        # Medication effect (simplified aggregation)
        med_effect = 0
        for med in selected_meds:
            base_eff = medication_types.get(med, (0, 0))[0] if diagnosis == "Diabetic" else prediabetic_meds.get(med, (0, 0))[0]
            if med in meds_with_dose:
                med_effect += base_eff * (med_doses.get(med, 0) / 1000)
            else:
                med_effect += base_eff
        if diagnosis == "Pre-diabetic":
            med_effect *= 0.7
        elif diagnosis == "Non-diabetic":
            med_effect *= 0.3
        if len(selected_meds) > 1:
            med_effect *= 0.8

        # base plus other meds effects
        base_glucose += 5 * len([m for m in bp_meds if m != "None"])
        base_glucose += 7 * len([m for m in chol_meds if m != "None"])
        base_glucose += 12 * len([m for m in steroid_meds if m != "None"])
        base_glucose += 10 * len([m for m in antidepressant_meds if m != "None"])
        base_glucose += 15 * len([m for m in antipsychotic_meds if m != "None"])

        diet_factor = max(0.5, 1 - 0.01 * diet_score)
        adjusted_glucose = base_glucose - (med_effect * 15) - (exercise * 0.2) + (weight * 0.05)
        adjusted_glucose *= diet_factor

        # generate a week
        avg_glucose = adjusted_glucose
        glucose_levels = [avg_glucose + uniform(-10, 10) for _ in range(7)]
        estimated_hba1c = round((sum(glucose_levels) / 7 + 46.7) / 28.7, 2)
        fasting_glucose = round(avg_glucose - 10, 1)
        post_meal_glucose = round(avg_glucose + 25, 1)

        st.subheader("📊 Simulation Results")
        st.metric("Average Glucose (mg/dL)", f"{round(np.mean(glucose_levels), 1)}")
        st.metric("Fasting Glucose (mg/dL)", f"{fasting_glucose}")
        st.metric("2-hour Post-Meal Glucose (mg/dL)", f"{post_meal_glucose}")
        st.metric("Estimated HbA1c (%)", f"{estimated_hba1c}")

        with st.expander("ℹ️ What do these results mean?"):
            st.markdown("""
                - **Fasting Glucose**: <100 mg/dL normal | 100–125 pre-diabetes | ≥126 diabetes  
                - **Post-Meal Glucose**: Goal typically <180 mg/dL (2 hours after meal)  
                - **HbA1c**: <5.7% normal | 5.7–6.4% pre-diabetes | ≥6.5% diabetes
            """)

       

        # store sim results
        st.session_state["sim_results"] = {
            "avg_glucose": np.mean(glucose_levels),
            "estimated_hba1c": estimated_hba1c,
            "diet_score": diet_score,
            "exercise": exercise
        }
        # plot
        fig, ax = plt.subplots()
        ax.plot(["Mon","Tue","Wed","Thu","Fri","Sat","Sun"], glucose_levels, marker="o")
        ax.set_ylabel("Glucose (mg/dL)")
        st.pyplot(fig)

# ===================== TAB: CGM SIMULATION ===================== #
elif selected_tab == "📊 CGM Simulation":
    st.title("📊 Simulate CGM Data")
    num_days = st.slider("Number of Days to Simulate", 1, 14, 7)
    readings_per_day = st.select_slider("Readings per Day", options=[24, 48, 96, 144, 288], value=96)
    baseline_glucose = st.slider("Baseline Glucose (mg/dL)", 70, 180, 110)
    glucose_variability = st.slider("Glucose Variability (SD)", 0, 50, 15)
    meal_effect = st.slider("Meal Effect Amplitude (mg/dL)", 0, 100, 40)
    exercise_effect = st.slider("Exercise Drop Amplitude (mg/dL)", 0, 80, 25)

    if st.button("Run CGM Simulation"):
        cgm_data = []
        timestamps = []
        interval_minutes = int(24*60 / readings_per_day)
        for day in range(num_days):
            for r in range(readings_per_day):
                minutes_since = day*1440 + r*interval_minutes
                t = datetime.now() + timedelta(minutes=minutes_since)
                meal_bump = meal_effect * np.sin(2*np.pi * r / (readings_per_day//3) if readings_per_day//3>0 else 0)
                exercise_dip = -exercise_effect * np.cos(2*np.pi * r / (readings_per_day//4) if readings_per_day//4>0 else 0)
                noise = np.random.normal(0, glucose_variability)
                val = baseline_glucose + meal_bump + exercise_dip + noise
                cgm_data.append(round(val,1))
                timestamps.append(t.strftime("%Y-%m-%d %H:%M"))
        df_cgm = pd.DataFrame({"Timestamp": timestamps, "Glucose (mg/dL)": cgm_data})
        st.session_state.cgm_data = df_cgm
        st.subheader("Simulated CGM (preview)")
        st.write(df_cgm.head(50))
        st.line_chart(df_cgm.set_index("Timestamp")["Glucose (mg/dL)"])
        avg_glucose = np.mean(cgm_data)
        time_in_range = sum((70 <= v <= 180) for v in cgm_data)/len(cgm_data)*100
        est_hba1c = round((avg_glucose + 46.7)/28.7, 2)
        st.metric("Average Glucose", f"{round(avg_glucose,1)} mg/dL")
        st.metric("Time in Range (70-180)", f"{round(time_in_range,1)}%")
        st.metric("Estimated HbA1c", f"{est_hba1c}%")
        st.download_button("📥 Download simulated CGM CSV", df_cgm.to_csv(index=False), "simulated_cgm.csv", "text/csv")

# ===================== TAB: CGM UPLOAD ===================== #
elif selected_tab == "📂 CGM Upload":
    st.title("📂 Upload Your CGM Data")
    uploaded_file = st.file_uploader("Upload CGM CSV", type=["csv"])
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            # store dataset for action plan
            st.session_state.cgm_data = df
            st.subheader("Preview uploaded CGM data")
            st.write(df.head(50))
            # try to plot: assume timestamp column first and glucose second
            try:
                st.line_chart(df.set_index(df.columns[0])[df.columns[1]])
            except Exception:
                st.line_chart(df.set_index(df.columns[0]))
            st.success("Upload successful — data available in Action Plan")
        except Exception as e:
            st.error(f"Could not read CSV: {e}")

# ===================== TAB: ACTION PLAN ===================== #
elif selected_tab == "📋 Action Plan":
    st.title("📋 Personalized Action Plan & Recommendations")
# Try to load glucose/simulation data if available
    df = st.session_state.cgm_data
    has_simulation = df is not None and isinstance(df, pd.DataFrame) and not df.empty
    # ---------------- EXERCISE RECOMMENDER & TIMER ---------------- #
    st.header("🏃 Personalized Exercise Recommender & Timer")
    
    if "exercise_timer" not in st.session_state:
            st.session_state.exercise_timer = None
    
        # Recommend based on glucose or home data
         base_exercise = st.session_state.get("exercise", 0)
         if has_simulation and avg_glucose and avg_glucose > 150:
            st.info("Recommendation: Add 15–20 minutes of aerobic activity (e.g., brisk walk).")
        elif base_exercise < 30:
            st.info("Increase exercise to at least 30 minutes per day for improved insulin sensitivity.")
    
        exercises = {
            "🚶 Brisk Walk": 20,
            "🚴 Cycling": 15,
            "🏋️ Strength Training": 20,
            "🧘 Yoga or Stretching": 15,
            "🏊 Swimming": 20
        }
    
        col_a, col_b = st.columns([2, 1])
        with col_a:
            ex_choice = st.selectbox("Choose Exercise", list(exercises.keys()))
        with col_b:
            preset_time = st.selectbox("Duration (min)", [5, 10, 15, 20, 30], index=2)
    
        if st.button("▶️ Start Timer"):
            st.session_state.exercise_timer = {
                "exercise": ex_choice,
                "duration": preset_time,
                "running": True
            }
    
        if st.session_state.exercise_timer:
            et = st.session_state.exercise_timer
            st.subheader(f"⏱️ {et['exercise']} — {et['duration']} min")
    
            timer_html = f"""
            <div id="timer" style="font-size:28px; font-weight:bold; margin:10px;"></div>
            <button id="pauseBtn" style="margin-right:10px;">⏸️ Pause</button>
            <button id="resumeBtn">▶️ Resume</button>
            <button id="stopBtn" style="margin-left:10px;">⏹️ Stop</button>
    
            <script>
            let totalSeconds = {et['duration']} * 60;
            let remaining = totalSeconds;
            let timerInterval;
            let isRunning = true;
    
            const timerEl = document.getElementById('timer');
            const pauseBtn = document.getElementById('pauseBtn');
            const resumeBtn = document.getElementById('resumeBtn');
            const stopBtn = document.getElementById('stopBtn');
    
            function updateTimer() {{
                let mins = Math.floor(remaining / 60);
                let secs = remaining % 60;
                timerEl.textContent = `${{mins.toString().padStart(2, '0')}}:${{secs.toString().padStart(2, '0')}}`;
            }}
    
            function startTimer() {{
                timerInterval = setInterval(() => {{
                    if (isRunning && remaining > 0) {{
                        remaining--;
                        updateTimer();
                    }}
                    if (remaining <= 0) {{
                        clearInterval(timerInterval);
                        timerEl.textContent = "✅ Complete!";
                    }}
                }}, 1000);
            }}
    
            pauseBtn.addEventListener('click', () => {{
                isRunning = false;
            }});
            resumeBtn.addEventListener('click', () => {{
                isRunning = true;
            }});
            stopBtn.addEventListener('click', () => {{
                remaining = totalSeconds;
                updateTimer();
                isRunning = false;
                clearInterval(timerInterval);
            }});
    
            updateTimer();
            startTimer();
            </script>
            """
            components.html(timer_html, height=180)
    
        # ---------------- LIFESTYLE INSIGHTS ---------------- #
        st.header("💡 Lifestyle Insights")
    
        diet_score = st.session_state.get("diet_score", 10)
        exercise_mins = st.session_state.get("exercise", 0)
    
        if total_cal and total_cal > daily_target * 1.1:
            st.warning("You’ve exceeded your calorie goal — try a light walk or reduce snacks.")
        elif total_cal and total_cal < daily_target * 0.8:
            st.info("Calorie intake low — make sure to eat balanced meals with carbs and protein.")
        elif not total_cal:
            st.info("Log some meals to get personalized nutrition advice.")
    
        if exercise_mins < 30:
            st.warning("Increase daily exercise to at least 30 minutes.")
        else:
            st.success("Exercise duration meets the daily recommendation!")
    
        if diet_score < 10:
            st.warning("Improve diet quality: add more vegetables, fiber, and lean protein.")
        elif diet_score > 20:
            st.success("Excellent diet quality — keep it up!")
    # --- EXERCISE TIMER CODE GOES HERE ---
    # (your timer, workout options, etc.)

    # --- SMART MEAL LOGGER GOES HERE ---
    st.header("🍽️ Smart Meal Logger & Personalized Nutrition Advisor")
st.header("🍽️ Smart Meal Logger & Personalized Nutrition Advisor")

if "meals" not in st.session_state:
    st.session_state.meals = []

# Expanded food database (per serving average kcal + nutrient category)
food_data = {
    "apple": {"cal": 95, "type": "carb"},
    "banana": {"cal": 105, "type": "carb"},
    "egg": {"cal": 70, "type": "protein"},
    "toast": {"cal": 75, "type": "carb"},
    "bread": {"cal": 80, "type": "carb"},
    "rice": {"cal": 200, "type": "carb"},
    "chicken": {"cal": 165, "type": "protein"},
    "chicken breast": {"cal": 165, "type": "protein"},
    "fish": {"cal": 180, "type": "protein"},
    "salmon": {"cal": 250, "type": "protein"},
    "steak": {"cal": 250, "type": "protein"},
    "beef": {"cal": 250, "type": "protein"},
    "pasta": {"cal": 350, "type": "carb"},
    "pizza": {"cal": 285, "type": "fat"},
    "burger": {"cal": 500, "type": "fat"},
    "fries": {"cal": 365, "type": "fat"},
    "salad": {"cal": 150, "type": "fiber"},
    "sandwich": {"cal": 300, "type": "mixed"},
    "oatmeal": {"cal": 150, "type": "carb"},
    "yogurt": {"cal": 100, "type": "protein"},
    "milk": {"cal": 120, "type": "protein"},
    "cheese": {"cal": 110, "type": "fat"},
    "nuts": {"cal": 160, "type": "fat"},
    "vegetables": {"cal": 50, "type": "fiber"},
    "fruit": {"cal": 60, "type": "carb"},
    "soup": {"cal": 120, "type": "mixed"},
    "beans": {"cal": 200, "type": "protein"},
    "lentils": {"cal": 180, "type": "protein"},
    "taco": {"cal": 200, "type": "fat"},
    "burrito": {"cal": 400, "type": "fat"},
    "soda": {"cal": 150, "type": "carb"},
    "juice": {"cal": 120, "type": "carb"},
    "dessert": {"cal": 300, "type": "fat"}
}

def estimate_calories_from_text(meal_text: str):
    import re
    text = meal_text.lower()
    total = 0
    found_items = []
    macro_types = {"protein": 0, "carb": 0, "fat": 0, "fiber": 0, "mixed": 0}

    for food, info in food_data.items():
        match = re.search(rf'(\d+)\s*{food}', text)
        if match:
            qty = int(match.group(1))
            total += qty * info["cal"]
            macro_types[info["type"]] += qty
            found_items.append(f"{qty}×{food}")
        elif food in text:
            total += info["cal"]
            macro_types[info["type"]] += 1
            found_items.append(food)

    if total == 0:
        total = 400
        found_items.append("general meal estimate")
        macro_types["mixed"] += 1

    return total, found_items, macro_types


def infer_diagnosis_from_meals(meals):
    """Infer likely glucose status if user skipped Home tab."""
    if not meals:
        return "Non-diabetic"

    carb_dominant = 0
    high_cal = 0
    for m in meals:
        if "carb" in m.get("macro_dominant", ""):
            carb_dominant += 1
        if m["calories"] > 600:
            high_cal += 1

    if high_cal >= 3 or carb_dominant >= 3:
        return "Diabetic"
    elif high_cal >= 2 or carb_dominant >= 2:
        return "Pre-diabetic"
    else:
        return "Non-diabetic"


def get_nutrition_advice(macro_types, diagnosis):
    """Return personalized feedback based on meal composition & diagnosis."""
    total = sum(macro_types.values())
    if total == 0:
        return "🤔 Please describe your meal to get advice."

    dominant = max(macro_types, key=macro_types.get)

    # General base messages
    base_advice = {
        "protein": "🍗 Great protein choice! Helps with glucose stability.",
        "carb": "🍞 Carb-heavy meal — pair with protein or fiber to slow absorption.",
        "fat": "🥑 High-fat meal — balance it with fiber or lean protein next time.",
        "fiber": "🥦 Excellent fiber intake! Helps improve insulin sensitivity.",
        "mixed": "🥗 Balanced meal! Nice mix of nutrients."
    }

    msg = base_advice.get(dominant, "👌 Looks balanced overall.")

    # Diagnosis-based modifiers
    if diagnosis == "Diabetic":
        if dominant == "carb":
            msg += " ⚠️ Try to limit high-carb foods to smaller portions and favor complex carbs."
        elif dominant == "fat":
            msg += " Watch out for saturated fats; prefer lean proteins or unsaturated sources."
        else:
            msg += " Keep checking your glucose response to this meal."
    elif diagnosis == "Pre-diabetic":
        msg += " 🧠 Good to be mindful of carbs — moderate portions and stay active after meals."
    else:
        msg += " ✅ Keep up the balance for healthy glucose control."

    return msg, dominant


# --- Determine user diagnosis context ---
diagnosis = st.session_state.get("diagnosis", None)

with st.form("meal_form", clear_on_submit=True):
    meal_name = st.text_input("Describe your meal (e.g., '2 eggs and toast')")
    guessed_cal, found_items, macros = estimate_calories_from_text(meal_name) if meal_name else (0, [], {})
    diagnosis_context = diagnosis or infer_diagnosis_from_meals(st.session_state.meals)

    if guessed_cal and meal_name:
        st.info(f"Estimated: ~{guessed_cal} kcal ({', '.join(found_items)})")

    meal_cal = st.number_input("Calories (adjust if needed)", value=guessed_cal or 0, step=10)
    add_meal = st.form_submit_button("➕ Add Meal")

    if add_meal:
        if not meal_name:
            st.warning("Please describe your meal.")
        else:
            advice, dominant = get_nutrition_advice(macros, diagnosis_context)
            st.session_state.meals.append({
                "meal": meal_name,
                "calories": meal_cal,
                "advice": advice,
                "macro_dominant": dominant,
                "time": datetime.now().strftime("%H:%M")
            })
            st.success(f"Meal added! Diagnosis context: **{diagnosis_context}**")
            st.info(advice)


# Display logged meals
if st.session_state.meals:
    st.subheader("📋 Logged Meals & Advice")
    for m in st.session_state.meals:
        st.markdown(f"""
        🍴 **{m['meal']}** — {m['calories']} kcal  
        🕒 {m['time']}  
        💬 {m['advice']}
        """)
    # now paste the full Smart Meal Logger & Nutrition Advisor code here
    # (make sure everything is indented one level under this tab)
elif selected_tab == "📝 Action Plan":
    st.title("📝 Personalized Action Plan")

    

    # ---------------- SIMULATION METRICS ---------------- #
    if has_simulation:
        glucose_col = df.columns[1] if df.shape[1] >= 2 else df.columns[0]
        glucose_series = pd.to_numeric(df[glucose_col], errors="coerce").dropna()

        avg_glucose = glucose_series.mean()
        time_in_range = np.mean((glucose_series >= 70) & (glucose_series <= 180)) * 100
        hypo = np.mean(glucose_series < 70) * 100
        hyper = np.mean(glucose_series > 180) * 100
        est_hba1c = round((avg_glucose + 46.7) / 28.7, 2)

        col1, col2, col3 = st.columns(3)
        col1.metric("Average Glucose", f"{avg_glucose:.1f} mg/dL")
        col2.metric("Estimated HbA1c", f"{est_hba1c}%")
        col3.metric("Time in Range", f"{time_in_range:.1f}%")

        st.markdown("---")

        st.subheader("📋 Glucose-Based Recommendations")

        if avg_glucose > 150:
            st.error("High average glucose — review carb intake, exercise, and medications.")
        elif avg_glucose < 80:
            st.warning("Low glucose — possible hypoglycemia. Adjust carb intake or medication timing.")
        else:
            st.success("✅ Glucose levels are within a healthy range!")

        if time_in_range < 70:
            st.warning("Time in range <70%. Consider reducing sugar or increasing post-meal activity.")
        if hypo > 5:
            st.error("Frequent low glucose events — discuss insulin or medication timing with a clinician.")
        if hyper > 30:
            st.error("Frequent high glucose — limit refined carbs and add aerobic activity after meals.")
    else:
        st.info("ℹ️ No CGM/simulation data detected. Using Home tab data for your plan.")
        avg_glucose, est_hba1c, time_in_range = None, None, None

    st.markdown("---")
   

  # ---------------- SMART MEAL CALORIE ESTIMATOR + PERSONALIZED NUTRITION ADVISOR ---------------- #


    
        

# ===================== TAB: HOW DIABETES WORKS (D3) ===================== #
elif selected_tab == "🔬 How Diabetes Works (Interactive)":
    st.title("🔬 How Diabetes Works — Interactive Diagram")
    st.markdown("""
    Click any node to see an explanation and practical tips.  
    Use mouse drag to move nodes, scroll to zoom, and click to get details on the right panel.
    """)

    d3_html = r"""
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial; }
        #container { display: flex; gap: 12px; align-items: flex-start; padding: 8px; }
        #chart { flex: 1 1 auto; min-width: 580px; height: 640px; background: linear-gradient(180deg, #ffffff, #f7fbff); border-radius: 8px; box-shadow: 0 6px 18px rgba(23,43,77,0.06); }
        #info { width: 360px; min-width: 260px; background:#ffffff; border-radius:8px; padding:14px; box-shadow: 0 6px 18px rgba(23,43,77,0.06); }
        #info h3 { margin: 0 0 8px 0; }
        #tips ul { margin: 6px 0 0 18px; padding: 0; }
        .node text { font-family: inherit; pointer-events: none; }
        .legend { font-size: 13px; margin-top: 8px; color:#444; }
        .caption { font-size: 13px; color:#666; margin-top:6px; }
      </style>
    </head>
    <body>
      <div id="container">
        <div id="chart"></div>
        <div id="info">
          <h3>Click a node to learn more</h3>
          <div id="desc">Select a node on the left diagram.</div>
          <div id="tips"></div>
          <div class="legend"><strong>Tip:</strong> drag nodes to rearrange • scroll to zoom</div>
          <div class="caption">Practical tips are plain-language actions you can try today.</div>
        </div>
      </div>

      <script src="https://d3js.org/d3.v7.min.js"></script>
      <script>
        const container = document.getElementById('chart');
        const width = container.clientWidth || 900;
        const height = 640;

        const nodes = [
          {id: "Food", emoji: "🍎", label: "Food (carbs)"},
          {id: "Digestion", emoji: "🔬", label: "Digestion"},
          {id: "Blood Glucose", emoji: "🩸", label: "Blood Glucose"},
          {id: "Pancreas", emoji: "🏭", label: "Pancreas (β-cells)"},
          {id: "Insulin", emoji: "💉", label: "Insulin"},
          {id: "Cells", emoji: "🦴", label: "Body Cells"},
          {id: "Liver", emoji: "🍖", label: "Liver"},
          {id: "Kidneys", emoji: "🧪", label: "Kidneys"},
          {id: "Insulin Resistance", emoji: "🚧", label: "Insulin Resistance"}
        ];

        const links = [
          {source:"Food", target:"Digestion"},
          {source:"Digestion", target:"Blood Glucose"},
          {source:"Blood Glucose", target:"Pancreas"},
          {source:"Pancreas", target:"Insulin"},
          {source:"Insulin", target:"Cells"},
          {source:"Insulin", target:"Liver"},
          {source:"Blood Glucose", target:"Kidneys"},
          {source:"Insulin Resistance", target:"Cells"},
          {source:"Insulin Resistance", target:"Liver"},
          {source:"Insulin Resistance", target:"Pancreas"}
        ];

        const explanations = {
          "Food": {
            "desc":"Foods that contain carbohydrates are broken down into glucose during digestion, increasing blood sugar.",
            "tips":["Pick whole grains and fibre-rich foods", "Pair carbs with protein or fat to slow absorption"]
          },
          "Digestion": {
            "desc":"Digestion releases glucose into the bloodstream after meals.",
            "tips":["Slower digestion = smaller glucose spikes", "Include fibre and protein"]
          },
          "Blood Glucose": {
            "desc":"The sugar circulating in your blood. The body tries to keep it within a safe range.",
            "tips":["Aim for stable meals, regular activity, and follow therapy"]
          },
          "Pancreas": {
            "desc":"Beta-cells in the pancreas sense glucose and release insulin to help clear it.",
            "tips":["Chronic high glucose stresses β-cells", "Medications or lifestyle changes can support function"]
          },
          "Insulin": {
            "desc":"Hormone that signals tissues to take up glucose and the liver to store it.",
            "tips":["Improve sensitivity with exercise & weight loss", "Match insulin timing to meals"]
          },
          "Cells": {
            "desc":"Muscle and fat cells take up glucose when signalled by insulin — exercise improves uptake.",
            "tips":["Even a short walk after meals helps", "Resistance training builds glucose-using muscle"]
          },
          "Liver": {
            "desc":"Stores glucose as glycogen and releases it when needed — may be dysregulated in diabetes.",
            "tips":["Consistent meal timing helps", "Some meds modify liver glucose output"]
          },
          "Kidneys": {
            "desc":"If blood glucose is very high, kidneys excrete glucose into urine — long-term high glucose damages kidneys.",
            "tips":["Protect kidneys by keeping average glucose in range", "Have regular kidney checks"]
          },
          "Insulin Resistance": {
            "desc":"Tissues don't respond well to insulin, requiring higher insulin to control glucose.",
            "tips":["Weight loss, resistance training and better sleep reduce resistance", "Medications like metformin may help"]
          }
        };

        const svg = d3.select("#chart")
                      .append("svg")
                      .attr("width", "100%")
                      .attr("height", height)
                      .attr("viewBox", `0 0 ${Math.max(width,800)} ${height}`);

        svg.append('defs').append('marker')
            .attr('id','arrow')
            .attr('viewBox','-0 -5 10 10')
            .attr('refX',30)
            .attr('refY',0)
            .attr('orient','auto')
            .attr('markerWidth',6)
            .attr('markerHeight',6)
          .append('path')
            .attr('d','M 0,-5 L 10,0 L 0,5')
            .attr('fill','#888');

        const gMain = svg.append("g");

        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(150).strength(1))
            .force("charge", d3.forceManyBody().strength(-700))
            .force("center", d3.forceCenter((Math.max(width,800)-360)/2, height/2))
            .force("collision", d3.forceCollide().radius(50));

        const link = gMain.append("g")
            .attr("stroke", "#9aa7b2")
            .selectAll("path")
            .data(links)
            .enter()
            .append("path")
            .attr("stroke-width", 2)
            .attr("fill", "none")
            .attr("marker-end","url(#arrow)");

        const nodeG = gMain.append("g")
            .selectAll("g")
            .data(nodes)
            .enter()
            .append("g")
            .attr("class","node")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

        nodeG.append("circle")
             .attr("r", 32)
             .attr("fill", (d,i) => d3.interpolateCool(i / nodes.length))
             .attr("stroke", "#fff")
             .attr("stroke-width", 2)
             .attr("opacity", 0.98)
             .on("click", (event, d) => { showInfo(d.id); });

        nodeG.append("text")
            .attr("text-anchor","middle")
            .style("font-family","inherit")
            .each(function(d) {
                const t = d3.select(this);
                t.append("tspan")
                  .attr("x", 0).attr("dy", "-6")
                  .style("font-size", "20px").text(d.emoji || "");
                t.append("tspan")
                  .attr("x", 0).attr("dy", "18")
                  .style("font-size", "12px").text(d.label || d.id);
            });

        simulation.on("tick", () => {
          link.attr("d", function(d) {
            return "M" + d.source.x + "," + d.source.y + " L " + d.target.x + "," + d.target.y;
          });
          nodeG.attr("transform", d => `translate(${d.x},${d.y})`);
        });

        svg.call(d3.zoom().scaleExtent([0.5, 2]).on("zoom", (event) => {
          gMain.attr("transform", event.transform);
        }));

        function dragstarted(event, d) {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        }

        function dragged(event, d) {
          d.fx = event.x;
          d.fy = event.y;
        }

        function dragended(event, d) {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = d.x;
          d.fy = d.y;
        }

        function showInfo(nodeId){
          const obj = explanations[nodeId];
          const desc = document.getElementById("desc");
          const tips = document.getElementById("tips");
          if(!obj){ desc.innerHTML = "No info available."; tips.innerHTML = ""; return; }
          desc.innerHTML = "<strong>" + nodeId + "</strong><p style='margin-top:6px;'>" + obj.desc + "</p>";
          tips.innerHTML = "<strong>Practical tips:</strong><ul>" + obj.tips.map(t => "<li>" + t + "</li>").join("") + "</ul>";
        }

        // initial selection
        showInfo("Blood Glucose");
      </script>
    </body>
    </html>
    """

    components.html(d3_html, height=680, scrolling=True)
