import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from random import uniform

# ------------------ APP LAYOUT ------------------ #
st.set_page_config(page_title="Diabetes Digital Twin", layout="wide")

# Store CGM data globally across tabs
if "cgm_data" not in st.session_state:
    st.session_state.cgm_data = None

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

    # ------------------ SLEEP AND DIET ------------------ #
    sleep_hours = st.slider("Sleep (hours/night)", 3, 12, 7)
    veg_servings = st.slider("Vegetable servings/week", 0, 70, 21)
    fruit_servings = st.slider("Fruit servings/week", 0, 70, 14)
    sugary_snacks = st.slider("Sugary snacks/week", 0, 70, 14)
    fast_food = st.slider("Fast food meals/week", 0, 14, 3)
    cook_freq = st.slider("Home-cooked meals/week", 0, 21, 5)

    # Calculate diet score
    diet_score = max(0, (veg_servings / 7) * 3 + (fruit_servings / 7) * 2 - sugary_snacks - fast_food + (cook_freq / 7) * 2)
    st.session_state.diet_score = diet_score
    st.session_state.exercise = exercise
    st.session_state.sleep_hours = sleep_hours

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

    # Save simulated data
    st.session_state.cgm_data = df

    st.download_button("📥 Download Simulated CGM CSV", df.to_csv(index=False), "simulated_cgm.csv", "text/csv")

# ========================================================= #
# =================== CGM UPLOAD TAB ====================== #
# ========================================================= #
elif selected_tab == "📂 CGM Upload":
    st.title("📂 Upload Your CGM Data")
    uploaded_file = st.file_uploader("Upload CGM CSV", type=["csv"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.session_state.cgm_data = df
        st.write(df.head())
        st.line_chart(df.set_index(df.columns[0]))



# ========================================================= #
# ================== ACTION PLAN TAB ====================== #
# ========================================================= #
elif selected_tab == "📝 Action Plan":
    st.title("📝 Personalized Action Plan")

    if st.session_state.cgm_data is None:
        st.warning("⚠️ Please upload or simulate CGM data first.")
    else:
        df = st.session_state.cgm_data.copy()
        glucose = df[df.columns[1]]  # Assume 2nd column is glucose

        # Compute metrics
        avg_glucose = glucose.mean()
        time_in_range = np.mean((glucose >= 70) & (glucose <= 180)) * 100
        hypo = np.mean(glucose < 70) * 100
        hyper = np.mean(glucose > 180) * 100
        est_hba1c = round((avg_glucose + 46.7) / 28.7, 2)

        # Display metrics
        st.metric("📊 Average Glucose", f"{avg_glucose:.1f} mg/dL")
        st.metric("📊 Estimated HbA1c", f"{est_hba1c}%")
        st.metric("✅ Time in Range (70–180)", f"{time_in_range:.1f}%")
        st.metric("⚠️ Hypoglycemia (<70)", f"{hypo:.1f}%")
        st.metric("⚠️ Hyperglycemia (>180)", f"{hyper:.1f}%")

        # Lifestyle guidance based on metrics
        st.subheader("📋 Lifestyle Recommendations")

        if avg_glucose > 150:
            st.error("High average glucose – consider improving diet or adjusting medications.")
        elif avg_glucose < 80:
            st.warning("Low average glucose – risk of hypoglycemia, check insulin/meds with provider.")
        else:
            st.success("Glucose levels are in good control!")

        if time_in_range < 70:
            st.warning("Time in Range is below recommended (>70%). Try improving consistency in meals and exercise.")
        if hypo > 5:
            st.error("Frequent hypoglycemia – reduce insulin or adjust meal timing.")
        if hyper > 30:
            st.error("Frequent hyperglycemia – check carb intake, exercise, and medication adherence.")

        # ------------------ EXERCISE RECOMMENDATIONS ------------------ #
        st.subheader("💪 Exercise Plan")

        if avg_glucose > 140 or st.session_state.get("exercise", 0) < 30:
            st.info("Recommended exercises for today:")

            exercises = {
                "🚶 Brisk Walking": 20,
                "🚴 Cycling": 15,
                "🏋️ Resistance Training": 25,
                "🧘 Yoga/Stretching": 15
            }

            choice = st.selectbox("Pick an exercise:", list(exercises.keys()))
            duration = exercises[choice]

            st.write(f"⏱ Recommended duration: **{duration} minutes**")

            if st.button("▶️ Start Exercise Timer"):
                with st.empty():
                    for i in range(duration, 0, -1):
                        st.metric("Time Remaining", f"{i} min")
                        time.sleep(1)
                st.success("✅ Exercise complete! Great job 🎉")

        else:
            st.success("👍 Exercise level looks good today!")

        # ------------------ MEAL LOGGING ------------------ #
        st.subheader("🍽️ Meal Logging & Nutrition Advice")

        meal = st.text_input("What did you eat?")
        calories = st.number_input("Estimated Calories", min_value=0, max_value=2000, step=50)

        if st.button("Analyze Meal"):
            if calories > 800:
                st.error("⚠️ That’s a high-calorie meal. Try reducing portion size or balancing with more veggies.")
            elif calories < 300:
                st.warning("🤔 That meal seems too light — make sure you’re getting enough protein and fiber.")
            else:
                st.success("✅ Balanced calorie intake for one meal!")

            # Simple keyword checks
            unhealthy = ["pizza", "burger", "fries", "soda", "candy"]
            healthy = ["salad", "chicken", "fish", "tofu", "vegetables", "brown rice"]

            if any(food in meal.lower() for food in unhealthy):
                st.error("⚠️ That meal contains refined carbs or fried foods. Try swapping for whole grains or grilled options.")
            elif any(food in meal.lower() for food in healthy):
                st.success("💡 Great choice! High nutrient value meal.")
            else:
                st.info("ℹ️ Couldn’t identify meal quality — but portion size and balance matter most.")





