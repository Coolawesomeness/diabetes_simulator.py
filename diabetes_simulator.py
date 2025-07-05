import streamlit as st
import matplotlib.pyplot as plt
from random import uniform

st.title("💉 Diabetes Digital Twin Simulator!")
st.write("Use the sliders to simulate how lifestyle and medication impact glucose.")

# Sliders for user input
age = st.slider("Patient Age (years)", 10, 100, 55)
weight = st.slider("Weight (kg)", 30, 150, 80)
exercise = st.slider("Daily Exercise (min)", 0, 120, 30)
med_dose = st.slider("Medication Dose (units)", 0, 150, 50)

# Button to trigger simulation
if st.button("Run Simulation"):
    st.success("✅ Simulation started!")

    # Fake model: simulate glucose levels over 7 days
    base_glucose = 180 - (med_dose * 0.5) - (exercise * 0.2) + (weight * 0.1)
    glucose_levels = [base_glucose + uniform(-10, 10) for _ in range(7)]
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    # Plotting
    fig, ax = plt.subplots()
    ax.plot(days, glucose_levels, marker='o', color='blue')
    ax.set_title("Simulated Blood Glucose Over a Week")
    ax.set_ylabel("Glucose (mg/dL)")
    st.pyplot(fig)
