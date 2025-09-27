import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from random import uniform
from datetime import datetime, timedelta
from streamlit.components.v1 import html as st_html

# Optional helper for auto-refresh used by timer. If not installed, the app still runs.
try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    def st_autorefresh(interval=0, key=None):
        # no-op fallback
        return None

# ------------------ PAGE CONFIG ------------------ #
st.set_page_config(page_title="Diabetes Digital Twin", layout="wide")

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
TABS = ["🏠 Home", "📊 CGM Simulation", "📂 CGM Upload", "📝 Action Plan", "🔬 How Diabetes Works (Interactive)"]
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

    # ---------- Diagnosis & Meds (FULL block restored) ----------
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

        # insulin correction if user entered current_bg/target earlier (optional)
        # generate week
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

        st.subheader("📋 Lifestyle Feedback")
        if exercise < 30:
            st.warning("Try to exercise at least 30 minutes daily (walking, cycling, resistance training).")
        if diet_score < 10:
            st.error("Diet score is low — increase vegetables, reduce sugary snacks & fast food.")
        if sleep_hours < 7:
            st.warning("Sleep under 7 hours may worsen glucose control.")

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
elif selected_tab == "📝 Action Plan":
    st.title("📝 Personalized Action Plan")

    # ensure cgm_data exists or warn
    df = st.session_state.cgm_data
    if df is None:
        st.warning("No CGM data available. Run a CGM simulation or upload a CSV to get personalized recommendations.")
    else:
        # Attempt to extract glucose column
        glucose_col = None
        if df.shape[1] >= 2:
            glucose_col = df.columns[1]
        else:
            glucose_col = df.columns[0]
        glucose_series = pd.to_numeric(df[glucose_col], errors='coerce').dropna()

        avg_glucose = glucose_series.mean()
        time_in_range = np.mean((glucose_series>=70) & (glucose_series<=180)) * 100
        hypo = np.mean(glucose_series < 70) * 100
        hyper = np.mean(glucose_series > 180) * 100
        est_hba1c = round((avg_glucose + 46.7)/28.7, 2)

        # show metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Average Glucose", f"{avg_glucose:.1f} mg/dL")
        col2.metric("Estimated HbA1c", f"{est_hba1c}%")
        col3.metric("Time in Range (70-180)", f"{time_in_range:.1f}%")

        st.markdown("----")
        st.subheader("📋 Recommendations (based on CGM + Intake)")

        if avg_glucose > 150:
            st.error("High average glucose — review carbohydrate intake, meal timing, and medication adherence.")
        elif avg_glucose < 80:
            st.warning("Low average glucose — risk of hypoglycemia. Check insulin/medications and snack strategy.")
        else:
            st.success("Average glucose is in a reasonable range.")

        if time_in_range < 70:
            st.warning("Time in range <70% — aim for better consistency in meals & activity.")
        if hypo > 5:
            st.error("Frequent hypoglycemia — discuss adjusting medication timing or doses with your provider.")
        if hyper > 30:
            st.error("Frequent hyperglycemia — consider carb reduction and stepping up activity after meals.")

        # use intake data if available
        if "diet_score" in st.session_state and st.session_state["diet_score"] < 10:
            st.warning("Diet quality is low — increase vegetables, reduce sugary snacks & fast food.")
        if "exercise" in st.session_state and st.session_state["exercise"] < 30:
            st.warning("Daily exercise low — increasing to ≥30 min/day helps glucose.")

        st.markdown("---")

        # ---------- Meal Logger ----------
        st.header("🍽️ Meal Logger & Daily Calories")
        with st.form("meal_form", clear_on_submit=True):
            meal_name = st.text_input("Meal description (e.g., 'Chicken salad, 1 bowl')")
            meal_cal = st.number_input("Estimated calories", min_value=0, step=10)
            add_meal = st.form_submit_button("➕ Add meal")
            if add_meal:
                if not meal_name:
                    st.warning("Please describe the meal (helps with feedback).")
                else:
                    st.session_state.meals.append({"meal": meal_name, "calories": meal_cal, "time": datetime.now().strftime("%H:%M")})

        if st.session_state.meals:
            df_meals = pd.DataFrame(st.session_state.meals)
            st.table(df_meals)
            total_cal = df_meals["calories"].sum()
            st.metric("Total calories logged today", f"{total_cal} kcal")
            daily_target = st.session_state.get("daily_calories", None)
            if daily_target:
                if total_cal < daily_target * 0.9:
                    st.success(f"✅ {total_cal} / {daily_target} kcal — under target")
                elif total_cal <= daily_target * 1.1:
                    st.info(f"⚖️ {total_cal} / {daily_target} kcal — on target")
                else:
                    st.error(f"⚠️ {total_cal} / {daily_target} kcal — over target")

        st.markdown("---")

        # ---------- Exercise Recommender & Timer ----------
        st.header("🏃 Exercise Recommendations & Timer")
        recommended_exercises = {
            "🚶 Brisk walk": 20,
            "🚴 Cycling (moderate)": 15,
            "🏋️ Resistance (bodyweight)": 20,
            "🧘 Light Yoga/Stretch": 15,
            "🕺 Dance (fun cardio)": 15
        }

        st.write("Choose an exercise and press Start. Timer runs in the background (auto-updates every 60s if `streamlit-autorefresh` is installed).")
        cols = st.columns([3,1])
        with cols[0]:
            ex_choice = st.selectbox("Pick exercise", list(recommended_exercises.keys()))
        with cols[1]:
            if st.button("▶️ Start"):
                mins = recommended_exercises[ex_choice]
                end_time = datetime.now() + timedelta(minutes=mins)
                st.session_state.exercise_timer = {"exercise": ex_choice, "end_time": end_time, "duration": mins}
                st.success(f"Started {ex_choice} for {mins} minutes")

        # Show timer (auto-refresh)
        if st.session_state.exercise_timer:
            et = st.session_state.exercise_timer
            remaining_sec = int((et["end_time"] - datetime.now()).total_seconds())
            remaining_min = max(0, remaining_sec // 60)
            remaining_seconds_exact = max(0, remaining_sec % 60)
            if remaining_sec > 0:
                # auto-refresh page every 60s (if package present). Safe fallback if not installed.
                try:
                    st_autorefresh(interval=60*1000, key="ex_timer_refresh")
                except Exception:
                    pass
                st.subheader(f"⏱️ {et['exercise']}")
                st.info(f"{remaining_min} min {remaining_seconds_exact} sec remaining")
                st.caption("This timer updates automatically every minute if `streamlit-autorefresh` is installed; otherwise refresh manually.")
            else:
                st.success(f"✅ {et['exercise']} complete! Great job 🎉")
                st.session_state.exercise_timer = None

# ===================== TAB: HOW DIABETES WORKS (D3) ===================== #
elif selected_tab == "🔬 How Diabetes Works (Interactive)":
    st.title("🔬 How Diabetes Works — Interactive Diagram (D3)")

    st.markdown("""
    This interactive diagram explains the main components that control blood sugar.
    Click any node to see a plain-language explanation and practical tips.  
    (D3 visualization embedded; fully client-side interactivity.)
    """)

    # D3 HTML + JS — force-directed graph with click handlers (uses d3 v7 CDN)
    d3_html = r"""
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial; margin:0; }
        .node circle { stroke: #fff; stroke-width: 1.5px; }
        .node text { pointer-events: none; font-size: 12px; }
        .legend { font-size: 13px; margin: 8px; }
        .info { position: absolute; right: 20px; top: 20px; width: 360px; padding: 12px; border-radius: 8px; background: #f7f9fc; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
        .info h3 { margin: 0 0 6px 0; }
        .tip { margin: 6px 0; }
      </style>
    </head>
    <body>
      <div id="chart"></div>
      <div id="info" class="info">
        <h3>Click a node to learn more</h3>
        <div id="desc">Nodes: Food, Digestion, Blood Glucose, Pancreas, Insulin, Cells, Liver, Kidneys, Insulin Resistance</div>
        <div id="tips"></div>
      </div>

      <script src="https://d3js.org/d3.v7.min.js"></script>
      <script>
        const width = 900;
        const height = 600;

        const nodes = [
          {id: "Food", group: 1, label: "Food\n(carbs)"},
          {id: "Digestion", group: 1, label: "Digestion\n→ Glucose"},
          {id: "Blood Glucose", group: 2, label: "Blood Glucose"},
          {id: "Pancreas", group: 3, label: "Pancreas\n(β-cells)"},
          {id: "Insulin", group: 4, label: "Insulin"},
          {id: "Cells", group: 5, label: "Body Cells"},
          {id: "Liver", group: 6, label: "Liver"},
          {id: "Kidneys", group: 7, label: "Kidneys"},
          {id: "Insulin Resistance", group: 8, label: "Insulin Resistance"}
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

        const svg = d3.select("#chart").append("svg")
            .attr("width", width)
            .attr("height", height);

        // defs for arrowheads
        svg.append('defs').append('marker')
            .attr('id','arrowhead')
            .attr('viewBox','-0 -5 10 10')
            .attr('refX',23)
            .attr('refY',0)
            .attr('orient','auto')
            .attr('markerWidth',6)
            .attr('markerHeight',6)
            .attr('xoverflow','visible')
          .append('svg:path')
            .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
            .attr('fill', '#999')
            .style('stroke','none');

        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(120).strength(1))
            .force("charge", d3.forceManyBody().strength(-700))
            .force("center", d3.forceCenter(width / 2 - 150, height / 2))
            .force("collision", d3.forceCollide().radius(40));

        const link = svg.append("g")
            .attr("stroke", "#999")
            .attr("stroke-opacity", 0.6)
          .selectAll("path")
          .data(links)
          .enter().append("path")
            .attr("stroke-width", 2)
            .attr("marker-end", "url(#arrowhead)");

        const node = svg.append("g")
            .selectAll("g")
            .data(nodes)
            .enter().append("g")
            .attr("class","node")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

        node.append("circle")
            .attr("r", 28)
            .attr("fill", d => colorByGroup(d.group))
            .on("click", (event, d) => { showInfo(d.id); });

        node.append("text")
            .attr("dy", 4)
            .attr("text-anchor","middle")
            .text(d => d.id);

        simulation.on("tick", () => {
          link.attr("d", function(d) {
            const sx = d.source.x, sy = d.source.y, tx = d.target.x, ty = d.target.y;
            const dx = tx - sx, dy = ty - sy;
            const dr = Math.sqrt(dx * dx + dy * dy);
            return "M" + sx + "," + sy + "L" + tx + "," + ty;
          });

          node.attr("transform", d => `translate(${d.x},${d.y})`);
        });

        function dragstarted(event,d) {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        }

        function dragged(event,d) {
          d.fx = event.x;
          d.fy = event.y;
        }

        function dragended(event,d) {
          if (!event.active) simulation.alphaTarget(0);
          // keep node fixed after drag for user convenience
          d.fx = d.x;
          d.fy = d.y;
        }

        function colorByGroup(g){
          const palette = {
            1: "#FFD59E",
            2: "#FFB3B3",
            3: "#9AD3BC",
            4: "#A0C4FF",
            5: "#FFD6E0",
            6: "#E3F2FD",
            7: "#FFF0F3",
            8: "#F8D7DA"
          };
          return palette[g] || "#ddd";
        }

        // Explanations/tips mapping
        const explanations = {
          "Food": {
            "desc":"Carbohydrate-containing foods break down into glucose during digestion, which raises blood glucose.",
            "tips":[ "Prefer whole grains over refined carbs", "Pair carbs with protein and fiber to slow absorption" ]
          },
          "Digestion": {
            "desc":"Digestion converts foods into glucose that enters the bloodstream.",
            "tips":[ "Slower digestion = gentler glucose rise", "Fiber and protein slow the glucose spike" ]
          },
          "Blood Glucose": {
            "desc":"This is the sugar circulating in your blood. Too high or too low is harmful over time.",
            "tips":[ "Stay within target ranges via balanced meals and activity", "Monitor trends rather than single readings" ]
          },
          "Pancreas": {
            "desc":"Beta cells in the pancreas sense glucose and release insulin to lower blood glucose.",
            "tips":[ "Chronic high glucose can stress β-cells", "Medications and healthy lifestyle support β-cell function" ]
          },
          "Insulin": {
            "desc":"Hormone that signals cells to take up glucose and the liver to store it as glycogen.",
            "tips":[ "Insulin timing and dose are key to avoid hypo/hyperglycemia", "Improved insulin sensitivity reduces insulin needs" ]
          },
          "Cells": {
            "desc":"Muscle and fat cells take up glucose when signaled by insulin — exercise increases uptake.",
            "tips":[ "Regular activity increases glucose uptake", "Resistance training builds muscle which helps with glucose disposal" ]
          },
          "Liver": {
            "desc":"Stores glucose and releases it when blood sugar falls; in diabetes the liver may release glucose inappropriately.",
            "tips":[ "Consistent meals help coordinate liver glucose release", "Medications may influence liver glucose output" ]
          },
          "Kidneys": {
            "desc":"When blood glucose is very high, kidneys filter excess glucose into the urine and can be damaged over time.",
            "tips":[ "Maintain good average glucose to protect kidneys", "Regular check-ups are important" ]
          },
          "Insulin Resistance": {
            "desc":"When tissues don't respond well to insulin, more insulin is needed to keep glucose normal.",
            "tips":[ "Weight loss, resistance training, and sleep can reduce insulin resistance", "Some meds (metformin) can improve sensitivity" ]
          }
        };

        function showInfo(nodeId){
          const obj = explanations[nodeId];
          const descBox = document.getElementById("desc");
          const tipsBox = document.getElementById("tips");
          if(!obj) {
            descBox.innerHTML = "No data available";
            tipsBox.innerHTML = "";
            return;
          }
          descBox.innerHTML = "<strong>" + nodeId + "</strong><br/><br/>" + obj.desc;
          tipsBox.innerHTML = "<strong>Practical tips:</strong><ul>" + obj.tips.map(t => "<li class='tip'>" + t + "</li>").join("") + "</ul>";
        }

        // initial info
        showInfo("Blood Glucose");

      </script>
    </body>
    </html>
    """

    # embed the HTML (height set for good layout)
    st_html(d3_html, height=640)

    st.markdown("**Tip:** Click nodes, drag them around, and explore the practical tips. If you want this embedded diagram to trigger Action Plan items inside Streamlit (e.g., suggest exercises after clicking 'Insulin Resistance'), I can add a JS→Python messaging bridge using `streamlit.components.v1` API (slightly more advanced).")
