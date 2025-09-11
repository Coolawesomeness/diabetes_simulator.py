import streamlit as st
import matplotlib.pyplot as plt
from random import uniform
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import math

# ------------------ GLOBAL STATE ------------------ #
if "sim_results" not in st.session_state:
    st.session_state.sim_results = {}
if "cgm_results" not in st.session_state:
    st.session_state.cgm_results = {}
if "upload_results" not in st.session_state:
    st.session_state.upload_results = {}

# ------------------ SIDEBAR ------------------ #
selected_tab = st.sidebar.radio("Select a tab", [
    "🏠 Home", "📈 CGM Simulation", "📤 CGM Upload", "🧭 Action Plan"
])

# ------------------ HOME TAB ------------------ #
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

    # User info
    age = st.slider("Patient Age (years)", 10, 100, 45)
    weight = st.slider("Weight (lbs)", 60, 300, 117)
    exercise = st.slider("Daily Exercise (min)", 0, 120, 30)
    diagnosis = st.radio("Select Glucose Status:", ["Non-diabetic", "Pre-diabetic", "Diabetic"])

    # Medical explanations
    with st.expander("❓ What do these terms mean?"):
        st.markdown("""
        - **HbA1c (%)**: Reflects average blood sugar over the last 3 months.  
          - Normal: < 5.7%  
          - Pre-diabetic: 5.7–6.4%  
          - Diabetic: ≥ 6.5%  
        - **Fasting Glucose (mg/dL)**: Blood sugar before eating, typically in the morning.  
          - Normal: < 100 mg/dL  
          - Pre-diabetic: 100–125 mg/dL  
          - Diabetic: ≥ 126 mg/dL  
        - **Post-meal Glucose (mg/dL)**: Blood sugar 2 hours after eating.  
          - Normal: < 140 mg/dL  
          - Pre-diabetic: 140–199 mg/dL  
          - Diabetic: ≥ 200 mg/dL  
        """)

    # --- (Medication, ISF, Sleep, Diet questionnaire remain unchanged from your base code) ---

    # ------------------ SIMULATION ------------------ #
    if st.button("⏱️ Run Simulation"):
        st.success("Simulation started!")

        # Base glucose depending on diagnosis
        base_glucose = 110 if diagnosis == "Non-diabetic" else (125 if diagnosis == "Pre-diabetic" else 160)

        # (medication + diet/exercise adjustments logic stays the same from your code)

        # Simulated glucose levels over a week
        avg_glucose = base_glucose - (exercise * 0.2) + (weight * 0.05)
        glucose_levels = [avg_glucose + uniform(-10, 10) for _ in range(7)]
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        # Metrics
        estimated_hba1c = round((sum(glucose_levels) / 7 + 46.7) / 28.7, 2)
        fasting_glucose = round(avg_glucose - 10, 1)
        post_meal_glucose = round(avg_glucose + 25, 1)

        st.subheader("📊 Simulation Results")
        st.metric("Average Glucose (mg/dL)", f"{round(sum(glucose_levels)/7, 1)}")
        st.metric("Fasting Glucose (mg/dL)", f"{fasting_glucose}")
        st.metric("2-hour Post-Meal Glucose (mg/dL)", f"{post_meal_glucose}")
        st.metric("Estimated HbA1c (%)", f"{estimated_hba1c}")

        fig, ax = plt.subplots()
        ax.plot(days, glucose_levels, marker="o", color="blue")
        ax.set_title("Simulated Blood Glucose Over 7 Days")
        ax.set_ylabel("Glucose (mg/dL)")
        st.pyplot(fig)

        # Save results for Action Plan
        st.session_state.sim_results = {
            "avg_glucose": np.mean(glucose_levels),
            "estimated_hba1c": estimated_hba1c,
            "exercise": exercise,
            "diet_score": 10  # simplified for demo
        }

# ------------------ CGM SIMULATION TAB ------------------ #
if selected_tab == "📈 CGM Simulation":
    st.header("📈 CGM Data Simulation")
    num_days = st.slider("Number of Days to Simulate", 1, 14, 7)
    readings_per_day = st.slider("Readings per Day", 24, 288, 96)
    baseline_glucose = st.slider("Baseline Glucose (mg/dL)", 70, 180, 110)

    if st.button("Run CGM Simulation"):
        total_readings = num_days * readings_per_day
        cgm_data = []
        timestamps = []
        for day in range(num_days):
            for reading in range(readings_per_day):
                minutes_since_start = day * 1440 + reading * (1440 // readings_per_day)
                time = datetime.now() + timedelta(minutes=minutes_since_start)
                value = baseline_glucose + np.sin(2*np.pi*reading/96)*40 + np.random.normal(0, 15)
                cgm_data.append(round(value, 1))
                timestamps.append(time.strftime("%Y-%m-%d %I:%M %p"))

        df_cgm = pd.DataFrame({"Timestamp": timestamps, "Glucose (mg/dL)": cgm_data})
        st.line_chart(df_cgm.set_index("Timestamp"))

        avg_glucose = np.mean(cgm_data)
        time_in_range = sum(70 <= val <= 180 for val in cgm_data) / len(cgm_data) * 100
        estimated_hba1c = round((avg_glucose + 46.7) / 28.7, 2)

        st.metric("Average Glucose", f"{round(avg_glucose, 1)} mg/dL")
        st.metric("Time in Range (70-180 mg/dL)", f"{round(time_in_range, 1)}%")
        st.metric("Estimated HbA1c", f"{estimated_hba1c}%")

        st.session_state.cgm_results = {
            "avg_glucose": avg_glucose,
            "time_in_range": time_in_range,
            "estimated_hba1c": estimated_hba1c
        }

        st.subheader("📋 Lifestyle Recommendations")
        if avg_glucose > 180:
            st.error("High glucose detected. Reduce sugary foods and increase daily physical activity.")
        elif avg_glucose < 70:
            st.warning("Glucose is low. Ensure balanced meals and monitor for hypoglycemia.")
        else:
            st.success("Glucose is in range. Maintain consistent diet and exercise routine.")

# ------------------ CGM UPLOAD TAB ------------------ #
if selected_tab == "📤 CGM Upload":
    st.header("📤 Upload CGM Data")
    uploaded_file = st.file_uploader("Upload a CSV file from your CGM", type=["csv"])
    
    if uploaded_file:
        df_upload = pd.read_csv(uploaded_file)
        st.write("Preview of uploaded data:", df_upload.head())

        # Expecting a column "Glucose (mg/dL)" or similar
        if "Glucose (mg/dL)" in df_upload.columns:
            avg_glucose = np.mean(df_upload["Glucose (mg/dL)"])
            time_in_range = sum(70 <= val <= 180 for val in df_upload["Glucose (mg/dL)"]) / len(df_upload) * 100
            estimated_hba1c = round((avg_glucose + 46.7) / 28.7, 2)

            st.metric("Average Glucose", f"{round(avg_glucose, 1)} mg/dL")
            st.metric("Time in Range (70-180 mg/dL)", f"{round(time_in_range, 1)}%")
            st.metric("Estimated HbA1c", f"{estimated_hba1c}%")

            st.line_chart(df_upload.set_index(df_upload.columns[0]))

            st.session_state.upload_results = {
                "avg_glucose": avg_glucose,
                "time_in_range": time_in_range,
                "estimated_hba1c": estimated_hba1c
            }

# ------------------ ACTION PLAN TAB ------------------ #
if selected_tab == "🧭 Action Plan":
    st.header("🧭 Personalized Action Plan")
    
    sources = []
    if st.session_state.sim_results:
        sources.append("Simulator")
    if st.session_state.cgm_results:
        sources.append("CGM Simulation")
    if st.session_state.upload_results:
        sources.append("CGM Upload")

    if not sources:
        st.info("No data available yet. Please run a simulation or upload CGM data first.")
    else:
        st.write(f"Results compiled from: {', '.join(sources)}")

        # Pick whichever is most recent / available
        results = st.session_state.upload_results or st.session_state.cgm_results or st.session_state.sim_results

        st.subheader("📊 Key Metrics")
        st.metric("Average Glucose", f"{round(results['avg_glucose'],1)} mg/dL")
        st.metric("Estimated HbA1c", f"{results['estimated_hba1c']}%")
        if "time_in_range" in results:
            st.metric("Time in Range", f"{round(results['time_in_range'],1)}%")

        st.subheader("📋 Recommendations")
        if results["avg_glucose"] > 180:
            st.error("➡ Reduce processed carbs, sugary drinks, and monitor medication adherence.")
        elif results["avg_glucose"] < 70:
            st.warning("➡ Ensure regular meals and avoid skipping food to prevent hypoglycemia.")
        else:
            st.success("➡ Maintain current habits! Focus on consistency in diet and activity.")

        st.markdown("""
        ✅ General tips:  
        - Eat more **vegetables, lean proteins, and whole grains**.  
        - Limit **fast food, sugary snacks, and late-night eating**.  
        - Aim for **30 min of daily exercise** (walking, cycling, or strength training).  
        - Sleep **7–9 hours** consistently.  
        """)






