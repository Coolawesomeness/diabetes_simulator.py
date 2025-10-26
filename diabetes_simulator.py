# diabetes_simulator_dashboard.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from random import uniform
from datetime import datetime, timedelta
import streamlit.components.v1 as components
import re

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    def st_autorefresh(interval=0, key=None):
        return None

# ---------------- PAGE CONFIG ---------------- #
st.set_page_config(page_title="Digital Diabetes Simulator", layout="wide", page_icon="💉")

# ---------------- IMPROVED VISUAL THEME ---------------- #
st.markdown(
    """
    <style>
      /* App background */
      .stApp {
        background: linear-gradient(180deg, #f4f5f7 0%, #eceff1 100%);
        color: #1a1a1a;
      }

      /* Card design */
      .card {
        background: #ffffff;
        border-radius: 14px;
        padding: 24px 26px;
        margin-bottom: 20px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
        border: 1px solid rgba(230, 230, 230, 0.9);
        transition: all 0.25s ease;
      }

      /* Hover animation */
      .card:hover {
        transform: translateY(-6px);
        box-shadow: 0 14px 32px rgba(0, 0, 0, 0.12);
        border-color: rgba(200, 200, 200, 0.8);
      }

      /* Section titles */
      .section-title {
        font-size: 20px;
        font-weight: 700;
        color: #0d1b2a;
        margin-bottom: 12px;
        text-shadow: 0 1px 0 rgba(255, 255, 255, 0.5);
      }

      /* Muted text */
      .muted {
        color: #6b7280;
        font-size: 13px;
        margin-top: 4px;
      }

      /* Metric highlights */
      .metric {
        font-weight: 600;
        color: #00796b;
      }

      /* Inputs and widgets styling */
      div[data-baseweb="select"], input, textarea {
        border-radius: 6px !important;
      }

      /* Buttons */
      .stButton>button {
        background: linear-gradient(90deg, #2b5876 0%, #4e4376 100%);
        color: #fff;
        border-radius: 8px;
        padding: 0.5em 1.2em;
        font-weight: 600;
        border: none;
        transition: all 0.25s ease;
      }

      .stButton>button:hover {
        transform: scale(1.03);
        background: linear-gradient(90deg, #3c6e91 0%, #5c51a0 100%);
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.15);
      }

      /* Sidebar */
      section[data-testid="stSidebar"] {
        background-color: #fafafa;
        border-right: 1px solid #e0e0e0;
      }

      /* Table refinement */
      .stDataFrame table {
        border-collapse: collapse;
        font-size: 13px;
      }

      /* Titles and headers */
      h1, h2, h3 {
        color: #0f1724;
        font-weight: 700;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------- SESSION DEFAULTS ---------------- #
for key, default in {
    "cgm_data": None,
    "sim_results": {},
    "meals": [],
    "exercise_timer": None,
    "daily_calories": None,
    "diet_score": None,
    "exercise_minutes": 0,
    "diagnosis": None,
    "selected_meds": [],
    "bp_meds": [],
    "chol_meds": [],
    "steroid_meds": [],
    "antidepressant_meds": [],
    "antipsychotic_meds": []
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ------------------ FOOD DB & HELPERS ------------------ #
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

def estimate_calories_from_text(text: str):
    txt = text.lower()
    total = 0
    found = []
    macros = {"protein":0, "carb":0, "fat":0, "fiber":0, "mixed":0}
    for food, info in FOOD_DB.items():
        m = re.search(rf'(\d+)\s*{re.escape(food)}', txt)
        if m:
            qty = int(m.group(1))
            total += qty * info["cal"]
            macros[info["type"]] += qty
            found.append(f"{qty}×{food}")
        elif food in txt:
            total += info["cal"]
            macros[info["type"]] += 1
            found.append(food)
    if total == 0:
        total = 400
        found.append("general meal estimate")
        macros["mixed"] += 1
    return total, found, macros

def infer_diagnosis_from_meals(meals_list):
    if not meals_list:
        return "Non-diabetic"
    carb_count = sum(1 for m in meals_list if m.get("macro_dominant") == "carb")
    heavy_count = sum(1 for m in meals_list if m.get("calories",0) > 600)
    if heavy_count >= 3 or carb_count >= 3:
        return "Diabetic"
    if heavy_count >= 2 or carb_count >= 2:
        return "Pre-diabetic"
    return "Non-diabetic"

def estimate_hba1c_from_avg(avg_glucose):
    try:
        return round((avg_glucose + 46.7) / 28.7, 2)
    except Exception:
        return None

def get_nutrition_advice(macros, diagnosis_context):
    total = sum(macros.values()) if macros else 0
    if total == 0:
        return "Describe the meal to get advice.", "mixed"
    dominant = max(macros, key=macros.get)
    base = {
        "protein":"🍗 Good protein — slows absorption and increases satiety.",
        "carb":"🍞 Carb-heavy — pair with protein/fiber to blunt spikes.",
        "fat":"🥑 High fat — balance with fiber/lean protein; watch portions.",
        "fiber":"🥦 High fiber — excellent for glucose stability.",
        "mixed":"🥗 Balanced meal — good mix of macros."
    }
    msg = base.get(dominant, "Looks balanced.")
    if diagnosis_context == "Diabetic":
        if dominant == "carb":
            msg += " ⚠️ Favor complex carbs, reduce portion sizes, and monitor post-meal readings."
        else:
            msg += " Continue monitoring glucose response."
    elif diagnosis_context == "Pre-diabetic":
        msg += " 🧠 Good to watch carbs and stay active after meals."
    else:
        msg += " ✅ Keep variety and portion control."
    return msg, dominant

# ------------------ SIDEBAR / NAV ------------------ #
TABS = [
    "🏠 Home",
    "📊 CGM Simulation",
    "📂 CGM Upload",
    "📝 Action Plan",
    "🔬 How Diabetes Works (Interactive)"
]
selected_tab = st.sidebar.radio("Navigate", TABS)

# ------------------ TAB: HOME ------------------ #
if selected_tab == "🏠 Home":
    st.title("📈 Diabetes Digital Twin — Patient Intake")
    st.markdown("**Created by: Siddharth Tirumalai** — Simulate glucose & HbA1c trends from meds, diet & lifestyle.")
    st.info("Educational simulator — not a substitute for medical care.")

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">👤 Patient Information</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        name = st.text_input("Full name", value=st.session_state.get("name",""))
        age = st.number_input("Age (years)", 10, 100, value=st.session_state.get("age",45))
    with col2:
        weight = st.number_input("Weight (lbs)", 60, 400, value=st.session_state.get("weight",150))
        sex = st.selectbox("Sex", ["Male","Female","Other"], index=0 if st.session_state.get("sex","Male")=="Male" else 1)
    with col3:
        activity_level = st.selectbox("Activity Level", ["Sedentary","Lightly Active","Moderately Active","Very Active","Athlete"], index=0)
        exercise_minutes = st.slider("Daily Exercise (minutes)", 0, 120, value=st.session_state.get("exercise_minutes",30))
    st.markdown('<div class="muted">Tip: accurate weight & activity make the simulation more useful.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Store into session_state for use in other tabs
    st.session_state["name"] = name
    st.session_state["age"] = age
    st.session_state["weight"] = weight
    st.session_state["sex"] = sex
    st.session_state["activity_level"] = activity_level
    st.session_state["exercise_minutes"] = exercise_minutes

    # medication blocks
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🩺 Diagnosis & Medications</div>', unsafe_allow_html=True)
    diagnosis = st.radio("Select Glucose Status:", ["Non-diabetic","Pre-diabetic","Diabetic"], index=0 if st.session_state.get("diagnosis","Non-diabetic")=="Non-diabetic" else 1)
    st.session_state["diagnosis"] = diagnosis

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

    # other med groups (restored)
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

    if diagnosis == "Diabetic":
        selected_meds = st.multiselect("Select Anti-Diabetic Medications:", list(medication_types.keys()), default=st.session_state.get("selected_meds", []))
    elif diagnosis == "Pre-diabetic":
        selected_meds = st.multiselect("Select Pre-Diabetic Medications:", list(prediabetic_meds.keys()), default=st.session_state.get("selected_meds", []))
    else:
        selected_meds = []

    st.session_state["selected_meds"] = selected_meds

    med_doses = {}
    meds_with_dose = list(medication_types.keys()) + list(prediabetic_meds.keys())
    for med in selected_meds:
        max_dose = medication_types.get(med, prediabetic_meds.get(med))[1]
        med_doses[med] = st.slider(f"Dose for {med} (mg/day)", 0, max_dose, min(50, max_dose))

    # other med selections (store in session_state)
    bp_meds = st.multiselect("Select Blood Pressure Medications:", ["None"] + list(bp_options.keys()), default=["None"])
    chol_meds = st.multiselect("Select Cholesterol Medications:", ["None"] + list(chol_options.keys()), default=["None"])
    steroid_meds = st.multiselect("Select Steroid Medications:", ["None"] + list(steroid_options.keys()), default=["None"])
    antidepressant_meds = st.multiselect("Select Antidepressant Medications:", ["None"] + list(antidepressant_options.keys()), default=["None"])
    antipsychotic_meds = st.multiselect("Select Antipsychotic Medications:", ["None"] + list(antipsychotic_options.keys()), default=["None"])

    st.session_state["bp_meds"] = bp_meds
    st.session_state["chol_meds"] = chol_meds
    st.session_state["steroid_meds"] = steroid_meds
    st.session_state["antidepressant_meds"] = antidepressant_meds
    st.session_state["antipsychotic_meds"] = antipsychotic_meds
    st.markdown('</div>', unsafe_allow_html=True)

    # insulin sensitivity calculator
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">💉 Insulin Sensitivity Calculator (Outpatient Use Only)</div>', unsafe_allow_html=True)
    st.markdown("ISF = 1800 / TDD for rapid-acting, or 1500 / TDD for regular insulin (approx).")
    insulin_type = st.selectbox("Select Insulin Type", ["Rapid-acting","Short-acting (Regular)","Intermediate-acting","Long-acting"])
    tdd = st.number_input("Total Daily Insulin Dose (units)", min_value=0.0, step=1.0, value=0.0)
    if insulin_type == "Rapid-acting" and tdd > 0:
        isf = round(1800 / tdd, 1)
        st.success(f"Estimated ISF: 1 unit ≈ {isf} mg/dL")
    elif insulin_type == "Short-acting (Regular)" and tdd > 0:
        isf = round(1500 / tdd, 1)
        st.success(f"Estimated ISF: 1 unit ≈ {isf} mg/dL")
    else:
        isf = None
        st.caption("ISF typically used for rapid/short-acting insulin only.")
    st.markdown('</div>', unsafe_allow_html=True)

    # Sleep & Diet
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
    st.caption(f"Diet quality score: {diet_score:.1f} (higher is better)")
    st.markdown('</div>', unsafe_allow_html=True)

    # Daily calorie target
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🔥 Estimated Daily Calorie Target</div>', unsafe_allow_html=True)
    weight_kg = weight * 0.45359237
    height_cm = 170
    if sex == "Male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    activity_multiplier = {"Sedentary":1.2,"Lightly Active":1.375,"Moderately Active":1.55,"Very Active":1.725,"Athlete":1.9}
    daily_calories = int(bmr * activity_multiplier.get(activity_level,1.2))
    st.session_state["daily_calories"] = daily_calories
    st.success(f"Estimated daily calories: {daily_calories} kcal")
    st.markdown('</div>', unsafe_allow_html=True)

    # Run Simulation (uses session_state med lists safely)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    if st.button("⏱️ Run Simulation"):
        st.success("Simulation started!")
        base_glucose = 110 if diagnosis == "Non-diabetic" else (125 if diagnosis == "Pre-diabetic" else 160)
        med_effect = 0.0
        for med in st.session_state.get("selected_meds", []):
            base_eff = medication_types.get(med,(0,0))[0] if diagnosis=="Diabetic" else prediabetic_meds.get(med,(0,0))[0]
            if med in meds_with_dose:
                med_effect += base_eff * (med_doses.get(med,0) / 1000)
            else:
                med_effect += base_eff
        if diagnosis == "Pre-diabetic":
            med_effect *= 0.7
        elif diagnosis == "Non-diabetic":
            med_effect *= 0.3
        if len(st.session_state.get("selected_meds", [])) > 1:
            med_effect *= 0.8
        base_glucose += 5 * len([m for m in st.session_state.get("bp_meds", []) if m != "None"])
        base_glucose += 7 * len([m for m in st.session_state.get("chol_meds", []) if m != "None"])
        base_glucose += 12 * len([m for m in st.session_state.get("steroid_meds", []) if m != "None"])
        base_glucose += 10 * len([m for m in st.session_state.get("antidepressant_meds", []) if m != "None"])
        base_glucose += 15 * len([m for m in st.session_state.get("antipsychotic_meds", []) if m != "None"])
        diet_factor = max(0.5, 1 - 0.01 * diet_score)
        adjusted_glucose = base_glucose - (med_effect * 15) - (st.session_state.get("exercise_minutes", exercise_minutes) * 0.2) + (weight * 0.05)
        adjusted_glucose *= diet_factor
        glucose_levels = [adjusted_glucose + uniform(-10,10) for _ in range(7)]
        avg_g = float(np.mean(glucose_levels))
        est_hba1c = estimate_hba1c_from_avg(avg_g)
        st.session_state["sim_results"] = {"avg_glucose": avg_g, "estimated_hba1c": est_hba1c, "diet_score": diet_score, "exercise_minutes": st.session_state.get("exercise_minutes", exercise_minutes)}
        st.subheader("📊 Simulation Results")
        st.metric("Average Glucose (mg/dL)", f"{round(avg_g,1)}")
        st.metric("Estimated HbA1c (%)", f"{est_hba1c}")
        fig, ax = plt.subplots()
        ax.plot(["Mon","Tue","Wed","Thu","Fri","Sat","Sun"], glucose_levels, marker="o")
        ax.set_ylabel("Glucose (mg/dL)")
        st.pyplot(fig)
    st.markdown('</div>', unsafe_allow_html=True)

# ------------------ TAB: CGM SIMULATION ------------------ #
elif selected_tab == "📊 CGM Simulation":
    st.title("📊 Simulate CGM Data")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    num_days = st.slider("Number of Days to Simulate", 1, 14, 7)
    readings_per_day = st.select_slider("Readings per Day", options=[24,48,96,144,288], value=96)
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
                meal_bump = meal_effect * np.sin(2*np.pi * r / max(1,(readings_per_day//3)))
                exercise_dip = -exercise_effect * np.cos(2*np.pi * r / max(1,(readings_per_day//4)))
                noise = np.random.normal(0, glucose_variability)
                val = baseline_glucose + meal_bump + exercise_dip + noise
                cgm_data.append(round(val,1))
                timestamps.append(t.strftime("%Y-%m-%d %H:%M"))
        df_cgm = pd.DataFrame({"Timestamp": timestamps, "Glucose (mg/dL)": cgm_data})
        st.session_state.cgm_data = df_cgm
        st.subheader("Simulated CGM (preview)")
        st.dataframe(df_cgm.head(200))
        st.line_chart(df_cgm.set_index("Timestamp")["Glucose (mg/dL)"])
        avg_gluc = np.mean(cgm_data)
        tir = sum((70 <= v <= 180) for v in cgm_data) / len(cgm_data) * 100
        st.metric("Average Glucose", f"{round(avg_gluc,1)} mg/dL")
        st.metric("Time in Range (70-180)", f"{round(tir,1)}%")
        st.metric("Estimated HbA1c", f"{estimate_hba1c_from_avg(avg_gluc)}%")
        st.download_button("📥 Download simulated CGM CSV", df_cgm.to_csv(index=False), "simulated_cgm.csv", "text/csv")
    st.markdown('</div>', unsafe_allow_html=True)

# ------------------ TAB: CGM UPLOAD ------------------ #
elif selected_tab == "📂 CGM Upload":
    st.title("📂 Upload Your CGM Data")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("Upload a CSV (timestamp first column, glucose second column).")
    uploaded_file = st.file_uploader("Upload CGM CSV", type=["csv"])
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.session_state.cgm_data = df
            st.subheader("Preview uploaded CGM data")
            st.dataframe(df.head(200))
            try:
                st.line_chart(df.set_index(df.columns[0])[df.columns[1]])
            except Exception:
                st.line_chart(df.set_index(df.columns[0]))
            st.success("Upload successful — data saved for Action Plan.")
        except Exception as e:
            st.error(f"Could not read CSV: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

# ------------------ TAB: ACTION PLAN ------------------ #
elif selected_tab == "📝 Action Plan":
    st.title("📝 Personalized Action Plan")
    st.markdown("Recommendations below combine Home intake and any CGM/simulation data you created or uploaded.")

    df_cgm = st.session_state.get("cgm_data")
    has_cgm = isinstance(df_cgm, pd.DataFrame) and not df_cgm.empty
    sim = st.session_state.get("sim_results", {})

    # SUMMARY CARD
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📊 Summary</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    if has_cgm:
        try:
            col_numeric = df_cgm.columns[1] if df_cgm.shape[1] >= 2 else df_cgm.columns[0]
            series = pd.to_numeric(df_cgm[col_numeric], errors="coerce").dropna()
            avg_g = series.mean()
            est_a1c = estimate_hba1c_from_avg(avg_g)
            tir = np.mean((series >= 70) & (series <= 180)) * 100
            col1.metric("Average Glucose", f"{avg_g:.1f} mg/dL")
            col2.metric("Estimated HbA1c", f"{est_a1c}%")
            col3.metric("Time in Range", f"{tir:.1f}%")
        except Exception:
            col1.write("CGM present — parsing error")
            col2.write("")
            col3.write("")
    elif sim:
        col1.metric("Avg Glucose (sim)", f"{sim.get('avg_glucose', '—')}")
        col2.metric("Estimated HbA1c", f"{sim.get('estimated_hba1c','—')}")
        col3.metric("Diet score", f"{sim.get('diet_score', '—')}")
    else:
        col1.write("No CGM or simulation yet.")
        col2.write("Use Home inputs to run the simulator.")
        col3.write("")
    st.markdown('</div>', unsafe_allow_html=True)

    # MEAL LOGGER & CALORIE ESTIMATOR
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🍽️ Smart Meal Logger & Nutrition Advisor</div>', unsafe_allow_html=True)
    with st.form("meal_form", clear_on_submit=True):
        meal_text = st.text_input("Describe your meal (e.g., '2 eggs and toast')", "")
        guessed_cal, found_items, macros = estimate_calories_from_text(meal_text) if meal_text else (0, [], {})
        if guessed_cal and meal_text:
            st.info(f"Estimated: ~{guessed_cal} kcal ({', '.join(found_items)})")
        meal_cal = st.number_input("Calories (adjust if needed)", value=int(guessed_cal or 0), step=10)
        submitted = st.form_submit_button("➕ Add Meal")
        if submitted:
            if not meal_text:
                st.warning("Please describe the meal.")
            else:
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

    if st.session_state.meals:
        df_meals = pd.DataFrame(st.session_state.meals)
        st.subheader("Logged Meals (today)")
        st.dataframe(df_meals[["time","meal","calories","macro_dominant","diagnosis_context"]].sort_values(by="time", ascending=False))
        total_cal = int(df_meals["calories"].sum())
        daily_target = st.session_state.get("daily_calories", 2000)
        c1, c2 = st.columns([2,1])
        with c1:
            st.metric("Total Calories Today", f"{total_cal} kcal")
            st.progress(min(total_cal / daily_target, 1.0))
        with c2:
            if total_cal > daily_target * 1.1:
                st.warning("Calories above daily target — consider lighter meals or extra activity.")
            elif total_cal < daily_target * 0.8:
                st.info("Calories below target — ensure adequate nutrition.")
            else:
                st.success("Calories near target — good balance.")
    else:
        st.info("No meals logged yet. Log meals to get personalized nutrition advice.")
    st.markdown('</div>', unsafe_allow_html=True)

    # EXERCISE RECOMMENDER & TIMER
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🏃 Exercise Recommendations & Timer</div>', unsafe_allow_html=True)

    # recommendation logic: prefer CGM avg, else sim, else home/exercise minutes
    cg_avg = None
    if has_cgm:
        try:
            col = df_cgm.columns[1] if df_cgm.shape[1] >= 2 else df_cgm.columns[0]
            cg_avg = pd.to_numeric(df_cgm[col], errors="coerce").dropna().mean()
        except Exception:
            cg_avg = None
    elif st.session_state.get("sim_results"):
        cg_avg = st.session_state["sim_results"].get("avg_glucose")

    base_ex = st.session_state.get("exercise_minutes", 0)
    if cg_avg and cg_avg > 150:
        st.info("Recommendation: Add 15–20 minutes of aerobic activity (e.g., brisk walk) after meals to reduce peaks.")
    elif base_ex < 30:
        st.info("Recommendation: Aim for ≥30 minutes of moderate activity most days to improve insulin sensitivity.")
    else:
        st.success("Activity looks reasonable — maintain current routine.")

    presets = [5,10,15,20,30]
    col1, col2 = st.columns([3,1])
    with col1:
        ex_choice = st.selectbox("Choose exercise", ["🚶 Brisk walk","🚴 Cycling","🏋️ Strength","🧘 Yoga/Stretch","🏊 Swim"])
    with col2:
        preset = st.selectbox("Duration (min)", presets, index=2)

    # Start timer — client-side JS gives live ticking:
    if st.button("▶️ Start Exercise Timer"):
        st.session_state["exercise_timer"] = {
            "exercise": ex_choice,
            "duration_min": int(preset),
            "started_at": datetime.now().isoformat()
        }
        timer_html = f"""
        <div style="display:flex;gap:12px;align-items:center">
          <div style="font-size:18px;font-weight:700">{ex_choice} — {preset} min</div>
        </div>
        <div id="timer" style="font-size:40px;font-weight:700;margin-top:10px">00:00</div>
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
        function upd(){{
          let m = Math.floor(remaining/60);
          let s = remaining % 60;
          timerEl.textContent = `${{String(m).padStart(2,'0')}}:${{String(s).padStart(2,'0')}}`;
        }}
        function tick(){{
          if(running && remaining>0){{ remaining--; upd(); if(remaining<=0) timerEl.textContent = "✅ Complete!"; }}
        }}
        document.getElementById('pause').onclick = ()=>{{ running=false; }};
        document.getElementById('resume').onclick = ()=>{{ running=true; }};
        document.getElementById('stop').onclick = ()=>{{ remaining=0; upd(); }};
        upd();
        setInterval(tick,1000);
        </script>
        """
        components.html(timer_html, height=170)
    # Show last started metadata if exists
    if st.session_state.get("exercise_timer"):
        last = st.session_state["exercise_timer"]
        st.caption(f"Last started: {last['exercise']} — {last['duration_min']} min at {last['started_at'][:19]}")

    st.markdown('</div>', unsafe_allow_html=True)

    # LIFESTYLE INSIGHTS
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">💡 Lifestyle Insights</div>', unsafe_allow_html=True)
    diet_score = st.session_state.get("diet_score", 0)
    sleep_hours = st.slider("Average Sleep (hours/night)", 3, 12, 7)
    if diet_score < 10:
        st.warning("Diet quality low — increase vegetables, reduce sugary snacks and fast food.")
    else:
        st.success("Diet quality looks good — maintain balanced meals.")
    if sleep_hours < 7:
        st.warning("Sleep <7 hours — aim for 7–9 hours nightly.")
    else:
        st.success("Sleep in a healthy range — supportive for glucose control.")
    ex_mins = st.session_state.get("exercise_minutes", 0)
    if ex_mins < 30:
        st.info("Try to increase daily activity to at least 30 minutes.")
    else:
        st.success("Activity targets being met — great!")
    if has_cgm:
        st.markdown("**CGM suggestions:** Address post-meal spikes with smaller carb portions and post-meal walks.")
    st.markdown('</div>', unsafe_allow_html=True)

# ------------------ TAB: DIABETES EDUCATION (D3) ------------------ #
elif selected_tab == "🔬 How Diabetes Works (Interactive)":
    st.title("🔬 How Diabetes Works — Interactive Diagram")
    st.markdown("Click a node to learn plain-language explanations and practical tips.")

    d3_html = """
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body { margin:0; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial; background:transparent; }
        #container{display:flex;gap:12px;padding:10px;}
        #chart{flex:1 1 auto;height:640px;border-radius:8px;background:linear-gradient(180deg,#fff,#f4f7fb);}
        #info{width:360px;padding:12px;background:#fff;border-radius:8px;box-shadow:0 6px 18px rgba(23,43,77,0.06);}
        h3{margin:0 0 8px 0;}
      </style>
    </head>
    <body>
      <div id="container"><div id="chart"></div><div id="info"><h3>Click a node to learn</h3><div id="desc">Select a node on the left.</div><div id="tips"></div></div></div>
      <script src="https://d3js.org/d3.v7.min.js"></script>
      <script>
        const nodes = [{id:'Food', emoji:'🍎'},{id:'Digestion',emoji:'🔬'},{id:'Blood Glucose',emoji:'🩸'},{id:'Pancreas',emoji:'🏭'},{id:'Insulin',emoji:'💉'},{id:'Cells',emoji:'🦴'},{id:'Liver',emoji:'🍖'},{id:'Kidneys',emoji:'🧪'},{id:'Insulin Resistance',emoji:'🚧'}];
        const links = [{source:'Food',target:'Digestion'},{source:'Digestion',target:'Blood Glucose'},{source:'Blood Glucose',target:'Pancreas'},{source:'Pancreas',target:'Insulin'},{source:'Insulin',target:'Cells'},{source:'Insulin',target:'Liver'},{source:'Blood Glucose',target:'Kidneys'},{source:'Insulin Resistance',target:'Cells'},{source:'Insulin Resistance',target:'Liver'},{source:'Insulin Resistance',target:'Pancreas'}];
        const explanations = {
          'Food':{desc:'Carbs in food break down into glucose — main driver of post-meal blood sugar.', tips:['Choose whole grains','Pair carbs with protein/fiber']},
          'Digestion':{desc:'Digestion speed affects glucose entry into blood.', tips:['Fibre slows absorption','Protein slows spikes']},
          'Blood Glucose':{desc:'Sugar circulating in blood, tightly regulated by the body.', tips:['Aim for consistent meals and activity']},
          'Pancreas':{desc:'Beta-cells secrete insulin in response to glucose.', tips:['Chronic high glucose stresses β-cells']},
          'Insulin':{desc:'Hormone that signals cells to take up glucose.', tips:['Exercise improves insulin sensitivity']},
          'Cells':{desc:'Muscle & fat cells use glucose — exercise increases uptake.', tips:['Walk after meals','Strength training builds muscle']},
          'Liver':{desc:'Stores/releases glucose; dysregulated in diabetes.', tips:['Consistent meal timing helps']},
          'Kidneys':{desc:'Excrete excess glucose when very high; long-term high glucose harms kidneys.', tips:['Keep average glucose in range']},
          'Insulin Resistance':{desc:'Tissues respond less to insulin, requiring more insulin to clear glucose.', tips:['Weight loss & exercise reduce resistance']}
        };
        const width = document.getElementById('chart').clientWidth || 900;
        const height = 640;
        const svg = d3.select('#chart').append('svg').attr('width','100%').attr('height',height);
        const g = svg.append('g');
        const sim = d3.forceSimulation(nodes).force('link', d3.forceLink(links).id(d=>d.id).distance(140)).force('charge', d3.forceManyBody().strength(-600)).force('center', d3.forceCenter(width/2 - 130, height/2));
        const link = g.append('g').selectAll('line').data(links).enter().append('line').attr('stroke','#9aa7b2').attr('stroke-width',2);
        const node = g.append('g').selectAll('g').data(nodes).enter().append('g').call(d3.drag().on('start',dragstarted).on('drag',dragged).on('end',dragended));
        node.append('circle').attr('r',34).attr('fill',(d,i)=>d3.interpolateCool(i/nodes.length)).attr('stroke','#fff').attr('stroke-width',2).on('click',(e,d)=>showInfo(d.id));
        node.append('text').attr('text-anchor','middle').each(function(d){const t=d3.select(this); t.append('tspan').attr('x',0).attr('dy','-6').style('font-size','20px').text(d.emoji||''); t.append('tspan').attr('x',0).attr('dy','18').style('font-size','12px').text(d.id);});
        sim.on('tick', ()=>{ link.attr('x1',d=>d.source.x).attr('y1',d=>d.source.y).attr('x2',d=>d.target.x).attr('y2',d=>d.target.y); node.attr('transform',d=>`translate(${d.x},${d.y})`); });
        function dragstarted(event,d){ if(!event.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }
        function dragged(event,d){ d.fx = event.x; d.fy = event.y; }
        function dragended(event,d){ if(!event.active) sim.alphaTarget(0); d.fx = d.x; d.fy = d.y; }
        function showInfo(id){ const obj = explanations[id]; document.getElementById('desc').innerHTML = '<strong>'+id+'</strong><p style="margin-top:8px">'+obj.desc+'</p>'; document.getElementById('tips').innerHTML = '<ul>'+obj.tips.map(t=>'<li>'+t+'</li>').join('')+'</ul>'; }
        showInfo('Blood Glucose');
      </script>
    </body>
    </html>
    """
    components.html(d3_html, height=680, scrolling=True)

# End of file
