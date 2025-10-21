
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from random import uniform
from datetime import datetime, timedelta
import streamlit.components.v1 as components
import time
import re

# Optional helper for auto-refresh used by timer. If not installed, the app still runs.
try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    def st_autorefresh(interval=0, key=None):
        # no-op fallback
        return None

# ------------------ PAGE CONFIG ------------------ #
st.set_page_config(page_title="Digital Diabetes Simulator", layout="wide", page_icon="💉")

# ------------------ PROFESSIONAL STYLING (light) ------------------ #
st.markdown(
    """
    <style>
      .card { background: #ffffff; padding:16px; border-radius:8px; box-shadow: 0 4px 14px rgba(24,39,75,0.06); margin-bottom:16px;}
      .section-title { font-weight:700; color:#123; font-size:18px; margin-bottom:8px; }
      .muted { color: #6b7280; font-size:13px; }
      .small { font-size:13px; color:#374151; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------ SESSION STATE INIT ------------------ #
if "cgm_data" not in st.session_state:
    st.session_state.cgm_data = None
if "sim_results" not in st.session_state:
    st.session_state.sim_results = {}
if "meals" not in st.session_state:
    st.session_state.meals = []
if "exercise_timer" not in st.session_state:
    st.session_state.exercise_timer = None
if "daily_calories" not in st.session_state:
    st.session_state.daily_calories = None
if "diet_score" not in st.session_state:
    st.session_state.diet_score = None
if "exercise_minutes" not in st.session_state:
    st.session_state.exercise_minutes = 0
if "diagnosis" not in st.session_state:
    st.session_state.diagnosis = None

# ------------------ SIDEBAR NAVIGATION ------------------ #
TABS = [
    "🏠 Home",
    "📊 CGM Simulation",
    "📂 CGM Upload",
    "📝 Action Plan",
    "🔬 How Diabetes Works (Interactive)"
]
selected_tab = st.sidebar.radio("Navigate", TABS)

# ------------------ Helper utilities ------------------ #
def estimate_hba1c_from_avg(avg_glucose):
    """Estimate HbA1c from average glucose using common linear formula."""
    try:
        return round((avg_glucose + 46.7) / 28.7, 2)
    except Exception:
        return None

# Smart food database (calories per typical serving) and nutrient type
FOOD_DB = {
    "apple": {"cal":95, "type":"carb"}, "banana": {"cal":105, "type":"carb"},
    "egg": {"cal":70, "type":"protein"}, "toast": {"cal":75, "type":"carb"},
    "bread": {"cal":80, "type":"carb"}, "rice": {"cal":200, "type":"carb"},
    "chicken": {"cal":165, "type":"protein"}, "chicken breast": {"cal":165, "type":"protein"},
    "fish": {"cal":180, "type":"protein"}, "salmon": {"cal":250, "type":"protein"},
    "steak": {"cal":250, "type":"protein"}, "beef": {"cal":250, "type":"protein"},
    "pasta": {"cal":350, "type":"carb"}, "pizza": {"cal":285, "type":"fat"},
    "burger": {"cal":500, "type":"fat"}, "fries": {"cal":365, "type":"fat"},
    "salad": {"cal":150, "type":"fiber"}, "sandwich": {"cal":300, "type":"mixed"},
    "oatmeal": {"cal":150, "type":"carb"}, "yogurt": {"cal":100, "type":"protein"},
    "milk": {"cal":120, "type":"protein"}, "cheese": {"cal":110, "type":"fat"},
    "nuts": {"cal":160, "type":"fat"}, "vegetables": {"cal":50, "type":"fiber"},
    "fruit": {"cal":60, "type":"carb"}, "soup": {"cal":120, "type":"mixed"},
    "beans": {"cal":200, "type":"protein"}, "lentils": {"cal":180, "type":"protein"},
    "taco": {"cal":200, "type":"fat"}, "burrito": {"cal":400, "type":"fat"},
    "soda": {"cal":150, "type":"carb"}, "juice": {"cal":120, "type":"carb"},
    "dessert": {"cal":300, "type":"fat"}
}

def estimate_calories_from_text(meal_text: str):
    text = meal_text.lower()
    total = 0
    found = []
    macro_counts = {"protein":0, "carb":0, "fat":0, "fiber":0, "mixed":0}
    # look for explicit quantities e.g., "2 eggs"
    for food, info in FOOD_DB.items():
        # numeric match first
        m = re.search(rf'(\d+)\s*{re.escape(food)}', text)
        if m:
            qty = int(m.group(1))
            total += qty * info["cal"]
            macro_counts[info["type"]] += qty
            found.append(f"{qty}×{food}")
        elif food in text:
            total += info["cal"]
            macro_counts[info["type"]] += 1
            found.append(food)
    if total == 0:
        # fallback to average meal
        total = 400
        found.append("general meal estimate")
        macro_counts["mixed"] += 1
    return total, found, macro_counts

def infer_diagnosis_from_meals(meals):
    # simple heuristic: many heavy/high-carb meals => pre-diabetic/diabetic
    if not meals:
        return "Non-diabetic"
    carb_count = 0
    heavy_count = 0
    for m in meals:
        if m.get("macro_dominant") == "carb":
            carb_count += 1
        if m.get("calories",0) > 600:
            heavy_count += 1
    if heavy_count >= 3 or carb_count >= 3:
        return "Diabetic"
    if heavy_count >= 2 or carb_count >=2:
        return "Pre-diabetic"
    return "Non-diabetic"

def get_nutrition_advice(macro_counts, diagnosis_context):
    total = sum(macro_counts.values()) if macro_counts else 0
    if total == 0:
        return "Describe the meal to get advice.", "mixed"
    dominant = max(macro_counts, key=macro_counts.get)
    base = {
        "protein":"🍗 Good protein — adds satiety and slows glucose rise.",
        "carb":"🍞 Carb-heavy — pair with protein/fat and fibre to blunt spikes.",
        "fat":"🥑 High fat — balance with fiber and lean protein; watch portion.",
        "fiber":"🥦 High fiber — excellent for glucose stability.",
        "mixed":"🥗 Balanced meal — nice mix of macros."
    }
    advice = base.get(dominant, "Looks balanced.")
    # diagnosis modifiers
    if diagnosis_context == "Diabetic":
        if dominant == "carb":
            advice += " ⚠️ For diabetes, favor complex carbs and smaller portions."
        else:
            advice += " Keep monitoring glucose response to this meal."
    elif diagnosis_context == "Pre-diabetic":
        advice += " 🧠 Be mindful of portion sizes and activity after meals."
    else:
        advice += " ✅ Good habit — keep variety and portion control."
    return advice, dominant

# ------------------ TAB: HOME ------------------ #
if selected_tab == "🏠 Home":
    st.title("📈 Diabetes Digital Twin — Patient Intake")
    st.markdown("**Created by: Siddharth Tirumalai** — Simulate glucose & HbA1c trends from meds, diet & lifestyle.")
    st.info("This simulator is educational only — consult a clinician for medical decisions.")

    # Patient info card
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">👤 Patient Information</div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            name = st.text_input("Full name", value="")
            age = st.number_input("Age (years)", 10, 100, 45)
        with col2:
            weight = st.number_input("Weight (lbs)", 60, 400, 150)
            sex = st.selectbox("Sex", ["Male","Female","Other"])
        with col3:
            activity_level = st.selectbox("Activity Level", ["Sedentary","Lightly Active","Moderately Active","Very Active","Athlete"])
            exercise_minutes = st.slider("Daily Exercise (minutes)", 0, 120, 30)
        st.markdown('<div class="muted">Tips: accurate weight & activity improve simulation realism.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Diagnosis & meds
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🩺 Diagnosis & Medications</div>', unsafe_allow_html=True)
        diagnosis = st.radio("Select Glucose Status:", ["Non-diabetic","Pre-diabetic","Diabetic"])
        st.session_state["diagnosis"] = diagnosis

        # small subset for UI brevity — keep your full lists if desired
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
        meds_with_dose = list(medication_types.keys()) + list(prediabetic_meds.keys())
        for med in selected_meds:
            max_dose = medication_types.get(med, prediabetic_meds.get(med))[1]
            med_doses[med] = st.slider(f"Dose for {med} (mg/day)", 0, max_dose, min(max_dose, 50))
        st.markdown('</div>', unsafe_allow_html=True)

    # Insulin Sensitivity Factor
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">💉 Insulin Sensitivity Calculator</div>', unsafe_allow_html=True)
        st.markdown("ISF estimates how much 1 unit of insulin lowers blood glucose (outpatient use only).")
        insulin_type = st.selectbox("Insulin Type", ["Rapid-acting","Short-acting (Regular)","Intermediate-acting","Long-acting"])
        tdd = st.number_input("Total Daily Dose (TDD) — insulin units", min_value=0.0, step=1.0, value=0.0)
        if insulin_type == "Rapid-acting" and tdd > 0:
            isf = round(1800 / tdd, 1)
            st.success(f"Estimated ISF (1800 rule): 1 unit ≈ {isf} mg/dL")
        elif insulin_type == "Short-acting (Regular)" and tdd > 0:
            isf = round(1500 / tdd, 1)
            st.success(f"Estimated ISF (1500 rule): 1 unit ≈ {isf} mg/dL")
        else:
            isf = None
            st.caption("ISF not available for long/intermediate-acting insulin or TDD=0.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Sleep & Diet
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🛌 Sleep & Diet</div>', unsafe_allow_html=True)
        sleep_hours = st.slider("Average Sleep (hours/night)", 3, 12, 7)
        is_menstruating = st.checkbox("Currently menstruating?", value=False)
        is_pregnant = st.checkbox("Currently pregnant?", value=False)

        col1, col2 = st.columns(2)
        with col1:
            veg_servings = st.slider("Vegetable servings per week", 0, 70, 21)
            fruit_servings = st.slider("Fruit servings per week", 0, 70, 14)
            cook_freq = st.slider("Home-cooked meals/week", 0, 21, 5)
        with col2:
            sugary_snacks = st.slider("Sugary snacks/drinks per week", 0, 70, 14)
            fast_food = st.slider("Fast food meals/week", 0, 14, 3)
        diet_score = max(0, (veg_servings / 7) * 3 + (fruit_servings / 7) * 2 - sugary_snacks - fast_food + (cook_freq / 7) * 2)
        st.session_state["diet_score"] = diet_score
        st.progress(min(diet_score / 20, 1.0))
        st.caption(f"Diet quality score: {diet_score:.1f} (higher = better)")
        st.markdown('</div>', unsafe_allow_html=True)

    # Daily calorie target
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🔥 Estimated Daily Calorie Target</div>', unsafe_allow_html=True)
        # convert to kg for formulas
        weight_kg = weight * 0.45359237
        height_cm = 170  # placeholder
        if sex == "Male":
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
        else:
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
        activity_multiplier = {"Sedentary":1.2,"Lightly Active":1.375,"Moderately Active":1.55,"Very Active":1.725,"Athlete":1.9}
        daily_calories = int(bmr * activity_multiplier.get(activity_level,1.2))
        st.session_state["daily_calories"] = daily_calories
        st.success(f"Estimated daily calories: {daily_calories} kcal")
        st.markdown('</div>', unsafe_allow_html=True)

    # Simulation button (keeps logic similar to your previous code)
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        if st.button("⏱️ Run Simulation"):
            st.success("Simulation started!")
            base_glucose = 110 if diagnosis == "Non-diabetic" else (125 if diagnosis == "Pre-diabetic" else 160)
            med_effect = 0
            # compute med effect safely
            for med in selected_meds:
                base_eff = medication_types.get(med,(0,0))[0] if diagnosis == "Diabetic" else prediabetic_meds.get(med,(0,0))[0]
                if med in meds_with_dose:
                    med_effect += base_eff * (med_doses.get(med,0) / 1000)
                else:
                    med_effect += base_eff
            if diagnosis == "Pre-diabetic":
                med_effect *= 0.7
            elif diagnosis == "Non-diabetic":
                med_effect *= 0.3
            if len(selected_meds) > 1:
                med_effect *= 0.8
            # other med classes contributions
            base_glucose += 5 * len([m for m in bp_meds if m != "None"])
            base_glucose += 7 * len([m for m in chol_meds if m != "None"])
            base_glucose += 12 * len([m for m in steroid_meds if m != "None"])
            base_glucose += 10 * len([m for m in antidepressant_meds if m != "None"])
            base_glucose += 15 * len([m for m in antipsychotic_meds if m != "None"])
            diet_factor = max(0.5, 1 - 0.01 * diet_score)
            adjusted_glucose = base_glucose - (med_effect * 15) - (exercise_minutes * 0.2) + (weight * 0.05)
            adjusted_glucose *= diet_factor
            avg_glucose = adjusted_glucose
            glucose_levels = [avg_glucose + uniform(-10,10) for _ in range(7)]
            estimated_hba1c = estimate_hba1c_from_avg(np.mean(glucose_levels))
            st.session_state["sim_results"] = {
                "avg_glucose": float(np.mean(glucose_levels)),
                "estimated_hba1c": estimated_hba1c,
                "diet_score": diet_score,
                "exercise_minutes": exercise_minutes
            }
            # display
            st.subheader("📊 Simulation Results")
            st.metric("Average Glucose (mg/dL)", f"{round(np.mean(glucose_levels),1)}")
            st.metric("Estimated HbA1c (%)", f"{estimated_hba1c}")
            fig, ax = plt.subplots()
            ax.plot(["Mon","Tue","Wed","Thu","Fri","Sat","Sun"], glucose_levels, marker="o")
            ax.set_ylabel("Glucose (mg/dL)")
            st.pyplot(fig)
        st.markdown('</div>', unsafe_allow_html=True)

# ------------------ TAB: CGM SIMULATION ------------------ #
elif selected_tab == "📊 CGM Simulation":
    st.title("📊 Simulate CGM Data")
    st.markdown("Create simulated CGM time-series to test the Action Plan recommendations.")

    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        num_days = st.slider("Number of Days", 1, 14, 7)
        readings_per_day = st.select_slider("Readings per Day", options=[24,48,96,144,288], value=96)
        baseline_glucose = st.slider("Baseline Glucose (mg/dL)", 70, 180, 110)
        glucose_variability = st.slider("Glucose Variability (SD)", 0, 50, 15)
        meal_effect = st.slider("Meal Effect Amplitude (mg/dL)", 0, 100, 40)
        exercise_effect = st.slider("Exercise Dip Amplitude (mg/dL)", 0, 80, 25)
        if st.button("Run CGM Simulation"):
            cgm_data = []
            timestamps = []
            interval_minutes = int(24*60 / readings_per_day)
            for day in range(num_days):
                for r in range(readings_per_day):
                    minutes_since = day*1440 + r*interval_minutes
                    t = datetime.now() + timedelta(minutes=minutes_since)
                    meal_bump = meal_effect * np.sin(2*np.pi * r / max(1, (readings_per_day//3)))
                    exercise_dip = -exercise_effect * np.cos(2*np.pi * r / max(1, (readings_per_day//4)))
                    noise = np.random.normal(0, glucose_variability)
                    val = baseline_glucose + meal_bump + exercise_dip + noise
                    cgm_data.append(round(val,1))
                    timestamps.append(t.strftime("%Y-%m-%d %H:%M"))
            df_cgm = pd.DataFrame({"Timestamp": timestamps, "Glucose (mg/dL)": cgm_data})
            st.session_state.cgm_data = df_cgm
            st.subheader("Simulated CGM (preview)")
            st.dataframe(df_cgm.head(200))
            st.line_chart(df_cgm.set_index("Timestamp")["Glucose (mg/dL)"])
            avg_glucose = np.mean(cgm_data)
            time_in_range = sum((70 <= v <= 180) for v in cgm_data) / len(cgm_data) * 100
            est_hba1c = estimate_hba1c_from_avg(avg_glucose)
            col1, col2, col3 = st.columns(3)
            col1.metric("Average Glucose", f"{round(avg_glucose,1)} mg/dL")
            col2.metric("Time in Range (70-180)", f"{round(time_in_range,1)}%")
            col3.metric("Estimated HbA1c", f"{est_hba1c}%")
            st.download_button("📥 Download simulated CGM CSV", df_cgm.to_csv(index=False), "simulated_cgm.csv", "text/csv")
        st.markdown('</div>', unsafe_allow_html=True)

# ------------------ TAB: CGM UPLOAD ------------------ #
elif selected_tab == "📂 CGM Upload":
    st.title("📂 Upload Your CGM Data")
    st.markdown("Upload a CSV with timestamps and glucose values (timestamp first column, glucose second column).")

    uploaded_file = st.file_uploader("Upload CGM CSV", type=["csv"])
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.session_state.cgm_data = df
            st.subheader("Preview uploaded CGM data")
            st.dataframe(df.head(200))
            # plot sensible column
            try:
                st.line_chart(df.set_index(df.columns[0])[df.columns[1]])
            except Exception:
                st.line_chart(df.set_index(df.columns[0]))
            st.success("Upload successful — data saved for Action Plan.")
        except Exception as e:
            st.error(f"Could not read CSV: {e}")

# ------------------ TAB: ACTION PLAN ------------------ #
elif selected_tab == "📝 Action Plan":
    st.title("📝 Personalized Action Plan")
    st.markdown("Recommendations combine Home intake and any CGM or simulation data you created or uploaded.")

    # load data availability
    df_cgm = st.session_state.cgm_data
    has_cgm = isinstance(df_cgm, pd.DataFrame) and not df_cgm.empty
    has_home = st.session_state.get("daily_calories") is not None or st.session_state.get("diet_score") is not None

    # Basic summary card
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📊 Summary</div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        # prefer CGM/sim results if available
        sim = st.session_state.get("sim_results", {})
        if has_cgm:
            # attempt to extract numeric glucose column
            try:
                glucose_col = df_cgm.columns[1] if df_cgm.shape[1] >= 2 else df_cgm.columns[0]
                glucose_series = pd.to_numeric(df_cgm[glucose_col], errors="coerce").dropna()
                avg_g = glucose_series.mean()
                est_hba1c = estimate_hba1c_from_avg(avg_g)
                tir = np.mean((glucose_series >= 70) & (glucose_series <= 180)) * 100
                col1.metric("Average Glucose", f"{avg_g:.1f} mg/dL")
                col2.metric("Estimated HbA1c", f"{est_hba1c}%")
                col3.metric("Time in Range", f"{tir:.1f}%")
            except Exception:
                st.info("Uploaded CGM data present but couldn't parse columns for metrics.")
        elif sim:
            col1.metric("Avg Glucose (sim)", f"{sim.get('avg_glucose', '—'):.1f}" if sim.get("avg_glucose") else "—")
            col2.metric("Estimated HbA1c", f"{sim.get('estimated_hba1c','—')}")
            col3.metric("Diet score", f"{sim.get('diet_score', '—')}")
        else:
            col1.write("No CGM or simulation yet.")
            col2.write("Fill Home intake to get personalized plan.")
            col3.write("")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("")  # spacing

    # ---------- Meal Logger & Nutrition Advisor (only in Action Plan) ----------
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🍽️ Smart Meal Logger & Nutrition Advisor</div>', unsafe_allow_html=True)

        if "meals" not in st.session_state:
            st.session_state.meals = []

        with st.form("meal_form", clear_on_submit=True):
            meal_text = st.text_input("Describe your meal (e.g., '2 eggs and toast')", "")
            guessed_cal, found_items, macros = estimate_calories_from_text(meal_text) if meal_text else (0, [], {})
            if guessed_cal and meal_text:
                st.info(f"Estimated: ~{guessed_cal} kcal ({', '.join(found_items)})")
            meal_cal = st.number_input("Calories (adjust if needed)", value=int(guessed_cal or 0), step=10)
            submitted = st.form_submit_button("➕ Add Meal")
            if submitted:
                if not meal_text:
                    st.warning("Please describe the meal to log it.")
                else:
                    # determine diagnosis context: prefer Home diagnosis, else infer
                    diagnosis_context = st.session_state.get("diagnosis") or infer_diagnosis_from_meals(st.session_state.meals)
                    advice, dominant = get_nutrition_advice(macros, diagnosis_context)
                    st.session_state.meals.append({
                        "meal": meal_text,
                        "calories": int(meal_cal),
                        "advice": advice,
                        "macro_dominant": dominant,
                        "time": datetime.now().strftime("%H:%M"),
                        "diagnosis_context": diagnosis_context
                    })
                    st.success("Meal logged ✔️")
                    st.info(advice)

        # show logged meals table & daily totals
        if st.session_state.meals:
            df_meals = pd.DataFrame(st.session_state.meals)
            st.subheader("Logged Meals (today)")
            st.dataframe(df_meals[["time","meal","calories","macro_dominant","diagnosis_context"]].sort_values(by="time", ascending=False))
            total_cal = int(df_meals["calories"].sum())
            daily_target = st.session_state.get("daily_calories", None) or 2000
            col_a, col_b = st.columns([2,1])
            with col_a:
                st.metric("Total Calories Today", f"{total_cal} kcal")
                pct = total_cal / daily_target
                st.progress(min(pct,1.0))
            with col_b:
                if total_cal > daily_target * 1.1:
                    st.warning("Calories above target — consider lighter options or extra activity.")
                elif total_cal < daily_target * 0.8:
                    st.info("Calories below target — ensure adequate nutrition.")
                else:
                    st.success("Calories near target — good balance.")
        else:
            st.info("No meals logged yet. Use the form above to log meals and get tailored advice.")

        st.markdown('</div>', unsafe_allow_html=True)

    # ---------- Exercise Recommender & Live Timer ----------
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🏃 Exercise Recommendations & Timer</div>', unsafe_allow_html=True)
        # recommendation logic
        diagnosis_ctx = st.session_state.get("diagnosis") or infer_diagnosis_from_meals(st.session_state.meals)
        recommended_text = ""
        # use CGM avg if available
        cg_avg = None
        if has_cgm:
            try:
                glucose_col = df_cgm.columns[1] if df_cgm.shape[1] >= 2 else df_cgm.columns[0]
                cg_avg = pd.to_numeric(df_cgm[glucose_col], errors="coerce").dropna().mean()
            except Exception:
                cg_avg = None
        elif "sim_results" in st.session_state and st.session_state["sim_results"]:
            cg_avg = st.session_state["sim_results"].get("avg_glucose")
        if cg_avg and cg_avg > 150:
            recommended_text = "Add 15–20 minutes of aerobic activity (brisk walk) after meals to reduce peaks."
        elif st.session_state.get("exercise_minutes", exercise_minutes) < 30:
            recommended_text = "Aim for ≥30 minutes of moderate activity most days to improve insulin sensitivity."
        else:
            recommended_text = "Current activity looks reasonable — keep up the good work."

        st.info(recommended_text)

        # Timer UI (JS embedded) with presets
        presets = [5,10,15,20,30]
        col1, col2 = st.columns([2,1])
        with col1:
            ex_choice = st.selectbox("Choose exercise", ["🚶 Brisk walk","🚴 Cycling","🏋️ Strength","🧘 Yoga/Stretch","🏊 Swim"])
        with col2:
            preset = st.selectbox("Duration (min)", presets, index=2)
        # render JS timer — independent live ticking in browser
        if st.button("▶️ Start Exercise Timer"):
            # Show a JS-powered timer component which ticks in the browser
            timer_html = f"""
            <div style="display:flex;gap:12px;align-items:center">
              <div style="font-size:20px;font-weight:600">{ex_choice} — {preset} min</div>
            </div>
            <div id="timer" style="font-size:36px;font-weight:700;margin-top:12px">00:00</div>
            <div style="margin-top:10px">
              <button id="pause">⏸️ Pause</button>
              <button id="resume">▶️ Resume</button>
              <button id="stop">⏹️ Stop</button>
            </div>
            <script>
            let total = {preset} * 60;
            let remaining = total;
            let running = true;
            const timerEl = document.getElementById('timer');
            function update(){{
              let m = Math.floor(remaining/60);
              let s = remaining % 60;
              timerEl.textContent = `${{String(m).padStart(2,'0')}}:${{String(s).padStart(2,'0')}}`;
            }}
            function tick(){{
              if(running && remaining>0) {{
                remaining--;
                update();
                if(remaining<=0) {{
                  timerEl.textContent = "✅ Complete!";
                }}
              }}
            }}
            document.getElementById('pause').onclick = ()=>{{ running=false; }};
            document.getElementById('resume').onclick = ()=>{{ running=true; }};
            document.getElementById('stop').onclick = ()=>{{ remaining=0; update(); }};
            update();
            setInterval(tick, 1000);
            </script>
            """
            components.html(timer_html, height=160)
            # store last started
            st.session_state["last_exercise"] = {"name": ex_choice, "duration_min": preset, "started_at": datetime.now().isoformat()}
        st.markdown('</div>', unsafe_allow_html=True)

    # ---------- Lifestyle Insights (summary & tips) ----------
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">💡 Lifestyle Insights & Quick Tips</div>', unsafe_allow_html=True)
        # diet
        diet_score = st.session_state.get("diet_score", 0)
        if diet_score < 10:
            st.warning("Diet quality low — increase vegetables, reduce sugary snacks and fast food.")
        else:
            st.success("Diet quality looks good. Keep up the balanced meals.")
        # sleep
        if sleep_hours < 7:
            st.warning("Sleep <7 hours may worsen glucose control. Aim for 7–9 hours.")
        else:
            st.success("Sleep in a healthy range — good for metabolic health.")
        # exercise
        ex_mins = st.session_state.get("exercise_minutes", exercise_minutes)
        if ex_mins < 30:
            st.info("Try to increase daily activity to at least 30 minutes of moderate intensity.")
        else:
            st.success("Activity targets being met — great!")
        # CGM suggestions
        if has_cgm:
            st.markdown("**CGM-specific suggestions:** review high post-prandial spikes and consider smaller carb portions or post-meal walks.")
        st.markdown('</div>', unsafe_allow_html=True)

# ------------------ TAB: HOW DIABETES WORKS (D3) ------------------ #
elif selected_tab == "🔬 How Diabetes Works (Interactive)":
    st.title("🔬 How Diabetes Works — Interactive Diagram")
    st.markdown("Click a node to learn plain-language explanations and tips.")

    d3_html = """
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; }
        #container { display:flex; gap:12px; padding:10px; }
        #chart { flex:1 1 auto; height:640px; background:linear-gradient(180deg,#fff,#f4f7fb); border-radius:8px; }
        #info { width:360px; padding:12px; background:#fff; border-radius:8px; box-shadow:0 6px 18px rgba(23,43,77,0.06); }
        h3 { margin:0 0 8px 0; }
        .tip { font-size:14px; color:#111827; }
      </style>
    </head>
    <body>
      <div id="container">
        <div id="chart"></div>
        <div id="info">
          <h3>Click a node to learn</h3>
          <div id="desc">Select a node on the left.</div>
          <div id="tips"></div>
        </div>
      </div>
      <script src="https://d3js.org/d3.v7.min.js"></script>
      <script>
        const nodes = [
          {id:'Food', emoji:'🍎'}, {id:'Digestion', emoji:'🔬'}, {id:'Blood Glucose', emoji:'🩸'},
          {id:'Pancreas', emoji:'🏭'}, {id:'Insulin', emoji:'💉'}, {id:'Cells', emoji:'🦴'},
          {id:'Liver', emoji:'🍖'}, {id:'Kidneys', emoji:'🧪'}, {id:'Insulin Resistance', emoji:'🚧'}
        ];
        const links = [
          {source:'Food', target:'Digestion'}, {source:'Digestion', target:'Blood Glucose'},
          {source:'Blood Glucose', target:'Pancreas'}, {source:'Pancreas', target:'Insulin'},
          {source:'Insulin', target:'Cells'}, {source:'Insulin', target:'Liver'},
          {source:'Blood Glucose', target:'Kidneys'}, {source:'Insulin Resistance', target:'Cells'},
          {source:'Insulin Resistance', target:'Liver'}, {source:'Insulin Resistance', target:'Pancreas'}
        ];
        const explanations = {
          'Food':{desc:'Carbs in food break down into glucose — the primary driver of post-meal blood sugar.', tips:['Choose whole grains','Pair carbs with protein/fiber']},
          'Digestion':{desc:'Digestion timing affects how quickly glucose enters bloodstream.', tips:['Fibre slows absorption','Protein slows peaks']},
          'Blood Glucose':{desc:'Sugar circulating in blood — body tightly regulates it for safe function.', tips:['Aim for consistent meals & activity']},
          'Pancreas':{desc:'Beta cells secrete insulin in response to glucose.', tips:['Chronic high glucose stresses beta cells']},
          'Insulin':{desc:'Hormone signaling cells to take up glucose.', tips:['Exercise improves insulin sensitivity']},
          'Cells':{desc:'Muscle and fat cells use glucose — exercise increases usage.', tips:['Walk after meals','Strength training helps']},
          'Liver':{desc:'Stores/releases glucose; can be dysregulated in diabetes.', tips:['Consistent meal timing helps']},
          'Kidneys':{desc:'Excrete excess glucose when very high — long-term high glucose harms kidneys.', tips:['Keep average glucose in range']},
          'Insulin Resistance':{desc:'Cells respond less to insulin, needing higher insulin to clear glucose.', tips:['Weight loss & exercise reduce resistance']}
        };
        const width = document.getElementById('chart').clientWidth || 900;
        const height = 640;
        const svg = d3.select('#chart').append('svg').attr('width','100%').attr('height',height);
        const g = svg.append('g');
        const simulation = d3.forceSimulation(nodes).force('link', d3.forceLink(links).id(d=>d.id).distance(140)).force('charge', d3.forceManyBody().strength(-600)).force('center', d3.forceCenter(width/2 - 150, height/2));
        const link = g.append('g').selectAll('line').data(links).enter().append('line').attr('stroke','#9aa7b2').attr('stroke-width',2);
        const node = g.append('g').selectAll('g').data(nodes).enter().append('g').call(d3.drag().on('start',dragstarted).on('drag',dragged).on('end',dragended));
        node.append('circle').attr('r',34).attr('fill',(d,i)=>d3.interpolateCool(i/nodes.length)).attr('stroke','#fff').attr('stroke-width',2).on('click',(e,d)=>showInfo(d.id));
        node.append('text').attr('text-anchor','middle').each(function(d){const t=d3.select(this); t.append('tspan').attr('x',0).attr('dy','-6').style('font-size','20px').text(d.emoji||''); t.append('tspan').attr('x',0).attr('dy','18').style('font-size','12px').text(d.id);});
        simulation.on('tick', ()=>{ link.attr('x1',d=>d.source.x).attr('y1',d=>d.source.y).attr('x2',d=>d.target.x).attr('y2',d=>d.target.y); node.attr('transform',d=>`translate(${d.x},${d.y})`); });
        function dragstarted(event,d){ if(!event.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }
        function dragged(event,d){ d.fx = event.x; d.fy = event.y; }
        function dragended(event,d){ if(!event.active) simulation.alphaTarget(0); d.fx = d.x; d.fy = d.y; }
        function showInfo(id){ const obj = explanations[id]; document.getElementById('desc').innerHTML = '<strong>'+id+'</strong><p style="margin-top:8px">'+obj.desc+'</p>'; document.getElementById('tips').innerHTML = '<ul>'+obj.tips.map(t=>'<li>'+t+'</li>').join('')+'</ul>'; }
        showInfo('Blood Glucose');
      </script>
    </body>
    </html>
    """
    components.html(d3_html, height=680, scrolling=True)


