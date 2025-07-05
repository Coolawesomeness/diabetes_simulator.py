import streamlit as st
import matplotlib.pyplot as plt
from random import uniform

st.title("💉 Diabetes Simulator!")
st.write("Use the sliders to simulate how medication impact glucose levels.")

# Add disclaimer with medication interaction warning
st.markdown("""
> ⚠️ **Disclaimer:** This simulation is for educational purposes only and is intended for individuals with diabetes who are **not** taking other medications that may affect blood sugar levels.  
> 
> It assumes a single anti-diabetic medication is being used. Other drugs such as **steroids (e.g., prednisone)**, **beta-blockers (e.g., metoprolol)**, **diuretics**, and **atypical antipsychotics (e.g., olanzapine)** can interfere with glucose control.  
> 
> Always consult with a healthcare provider before making any treatment changes.
""")

# Sliders for user input
age = st.slider("Patient Age (years)", 10, 100, 55)
weight = st.slider("Weight (lbs)", 30, 200, 115)
exercise = st.slider("Daily Exercise (min)", 0, 120, 30)
med_dose = st.slider("Medication Dose (units)", 0, 150, 50)

# Dropdown for medication type with relative effectiveness
med_type = st.selectbox(
    "Medication Type",
    ["Insulin", "Sulfonylureas", "Metformin", "SGLT2 Inhibitors","GLP-1 Receptor Agonists","Thiazolidinediones (TZDs)", "DPP-4 Inhibitors", "Meglitinides", "Alpha-glucosidase Inhibitors", "Amylin Analogs"]
)

# Relative effectiveness factors for different medications (fictional for simulation)
effectiveness_factors = {
    "Insulin": 1.00,
    "Sulfonylureas": 0.70,
    "Metformin": 0.50,
    "SGLT2 Inhibitors": 0.40,
    "GLP-1 Receptor Agonists": 0.60,
    "Thiazolidinediones (TZDs)": 0.45,
    "DPP-4 Inhibitors": 0.30,
    "Meglitinides": 0.55,
    "Alpha-glucosidase Inhibitors": 0.35,
    "Amylin Analogs": 0.25
}

# Simulation trigger
if st.button("Run Simulation"):
    st.success("✅ Simulation started!")

    # Calculate adjusted glucose levels
    effectiveness = effectiveness_factors[med_type]
    base_glucose = 180 - (med_dose * effectiveness) - (exercise * 0.2) + (weight * 0.1)
    glucose_levels = [base_glucose + uniform(-10, 10) for _ in range(7)]
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    # Plot
    fig, ax = plt.subplots()
    ax.plot(days, glucose_levels, marker='o', color='blue')
    ax.set_title("Simulated Blood Glucose Over a Week")
    ax.set_ylabel("Glucose (mg/dL)")
    st.pyplot(fig)
