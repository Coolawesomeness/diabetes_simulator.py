import streamlit as st
import matplotlib.pyplot as plt
from random import uniform

st.title("💉 Diabetes Simulator")
st.write("Use the sliders to simulate how medication impacts glucose based on age, weight, and daily exercise.")
st.write("Disclaimer: Simulation is not for patients using antibiotics, corticosteroids, diuretics, beta-blockers, antipsychotics, statins, or any other medication that conflict with anti-diabetic medication")

# Sliders for user input
age = st.slider("Patient Age (years)", 10, 100, 55)
weight = st.slider("Weight (lbs)", 30, 200, 80)
exercise = st.slider("Daily Exercise (min)", 0, 240, 30)
med_dose = st.slider("Medication Dose (units)", 0, 150, 50)

# Button to trigger simulation
if st.button("Run Simulation"):
    st.success("✅ Simulation started!")

    # Fake model: simulate glucose levels over 14 days
    base_glucose = 180 - (med_dose * 0.5) - (exercise * 0.2) + (weight * 0.1)
    glucose_levels = [base_glucose + uniform(-10, 10) for _ in range(14)]
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    # Plotting
    fig, ax = plt.subplots()
    ax.plot(days, glucose_levels, marker='o', color='blue')
    ax.set_title("Simulated Blood Glucose Over 2 Weeks")
    ax.set_ylabel("Glucose (mg/dL)")
    st.pyplot(fig)
