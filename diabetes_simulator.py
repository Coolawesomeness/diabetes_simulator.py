import streamlit as st
import matplotlib.pyplot as plt
from random import uniform

st.title("💉 Diabetes Digital Simulator!")
st.write("Use the sliders and survey to simulate how lifestyle, medication, and diet impact glucose levels.")

# Health status selection
status = st.radio(
    "What is your blood glucose status?",
    ("Diabetic", "Pre-diabetic", "Non-diabetic")
)

st.info("""
**Simulation Details:**
- 🟥 Diabetic: Full simulation with medication and insulin sensitivity.
- 🟧 Pre-diabetic: Moderate glucose drop with adjusted sensitivity.
- 🟩 Non-diabetic: Simulation disabled.
""")

if status == "Non-diabetic":
    st.warning("⚠️ This simulation is not intended for individuals without blood sugar regulation issues.")

if status in ("Diabetic", "Pre-diabetic"):
    # Disclaimer
    st.markdown("""
    > ⚠️ **Disclaimer:** This simulation is for educational purposes only and is intended for individuals with diabetes or pre-diabetes who are **not** taking other medications that may affect blood sugar levels.
    >
    > It assumes a single anti-diabetic medication is being used. Other drugs such as **steroids**, **beta-blockers**, **diuretics**, and **antipsychotics** can interfere with glucose control.
    >
    > Always consult with a healthcare provider before making any treatment changes.
    """)

    # Inputs
    age = st.slider("Patient Age (years)", 10, 100, 55)
    weight = st.slider("Weight (lbs)", 30, 200, 117)
    exercise = st.slider("Daily Exercise (min)", 0, 120, 30)
    med_dose = st.slider("Medication Dose (units)", 0, 150, 50)

    med_type = st.selectbox(
        "Medication Type (for blood glucose control)",
        [
            "Insulin",
            "Sulfonylureas",
            "Metformin",
            "SGLT2 Inhibitors",
            "GLP-1 Receptor Agonists",
            "Thiazolidinediones (TZDs)",
            "DPP-4 Inhibitors",
            "Meglitinides",
            "Alpha-glucosidase Inhibitors",
            "Amylin Analogs"
        ]
    )

    # Medication effectiveness dictionary
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

    # Diet Survey
    st.subheader("📝 Diet Habits Survey")
    st.write("Please answer the following questions regarding your diet:")

    veg_fruit = st.selectbox(
        "How many servings of vegetables and fruits do you eat daily?",
        [
            "0 servings",
            "1-2 servings",
            "3-4 servings",
            "5 or more servings"
        ]
    )
    veg_fruit_score = {
        "0 servings": 10,
        "1-2 servings": 5,
        "3-4 servings": 2,
        "5 or more servings": 0
    }[veg_fruit]

    sugary_drinks = st.selectbox(
        "How many sugary drinks (soda, sweet tea, juice) do you consume per week?",
        [
            "More than 7",
            "4-7",
            "1-3",
            "None"
        ]
    )
    sugary_drinks_score = {
        "More than 7": 10,
        "4-7": 7,
        "1-3": 3,
        "None": 0
    }[sugary_drinks]

    snacks_fastfood = st.selectbox(
        "How often do you eat processed snacks or fast food per week?",
        [
            "More than 5 times",
            "3-5 times",
            "1-2 times",
            "Rarely or never"
        ]
    )
    snacks_fastfood_score = {
        "More than 5 times": 10,
        "3-5 times": 7,
        "1-2 times": 3,
        "Rarely or never": 0
    }[snacks_fastfood]

    refined_grains = st.selectbox(
        "How often do you consume refined grains (white bread, white rice) instead of whole grains?",
        [
            "Mostly refined grains",
            "About half refined, half whole grains",
            "Mostly whole grains"
        ]
    )
    refined_grains_score = {
        "Mostly refined grains": 10,
        "About half refined, half whole grains": 5,
        "Mostly whole grains": 0
    }[refined_grains]

    meal_patterns = st.selectbox(
        "How often do you skip meals or binge eat late at night?",
        [
            "Often",
            "Sometimes",
            "Rarely or never"
        ]
    )
    meal_patterns_score = {
        "Often": 5,
        "Sometimes": 3,
        "Rarely or never": 0
    }[meal_patterns]

    portion_control = st.selectbox(
        "Do you track or control your portion sizes?",
        [
            "No, I don’t track portions",
            "Sometimes",
            "Yes, regularly"
        ]
    )
    portion_control_score = {
        "No, I don’t track portions": 5,
        "Sometimes": 2,
        "Yes, regularly": 0
    }[portion_control]

    diet_quality = (
        veg_fruit_score +
        sugary_drinks_score +
        snacks_fastfood_score +
        refined_grains_score +
        meal_patterns_score +
        portion_control_score
    )

    if diet_quality <= 10:
        st.success("✅ Your diet appears quite healthy!")
    elif diet_quality <= 30:
        st.info("⚠️ Your diet could be improved. Consider adding more fiber and reducing sugar.")
    else:
        st.warning("🚨 Your diet may significantly raise your glucose levels. Improvements recommended.")

    st.write(f"**Estimated Diet Impact Score:** {diet_quality} (higher = worse)")

    # Insulin sensitivity slider
    insulin_sensitivity = st.slider("Insulin Sensitivity (1 = normal)", 0.1, 2.0, 1.0)

    # Adjust insulin sensitivity based on diet quality
    diet_factor = max(0.5, 1 - 0.01 * diet_quality)  # minimum 0.5
    adjusted_insulin_sensitivity = insulin_sensitivity * diet_factor

    if status == "Diabetic":
        base_glucose = 180
        med_effect_scale = 1.0
    else:
        base_glucose = 140
        med_effect_scale = 0.5

    if st.button("Run Simulation"):
        st.success("✅ Simulation started!")

        med_effectiveness = effectiveness_factors[med_type] * med_effect_scale * adjusted_insulin_sensitivity

        adjusted_glucose = (
            base_glucose
            - (med_dose * med_effectiveness)
            - (exercise * 0.2)
            + (weight * 0.1)
            + diet_quality
        )
        glucose_levels = [adjusted_glucose + uniform(-10, 10) for _ in range(7)]
        avg_glucose = sum(glucose_levels) / len(glucose_levels)

        estimated_hba1c = (avg_glucose + 46.7) / 28.7

        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        fig, ax = plt.subplots()
        ax.plot(days, glucose_levels, marker='o', color='blue')
        ax.set_title(f"Simulated Blood Glucose Over a Week ({status})")
        ax.set_ylabel("Glucose (mg/dL)")
        st.pyplot(fig)

        st.metric("📈 Average Glucose", f"{avg_glucose:.1f} mg/dL")
        st.metric("🧪 Estimated HbA1c", f"{estimated_hba1c:.2f} %")
        st.metric("⚖️ Adjusted Insulin Sensitivity", f"{adjusted_insulin_sensitivity:.2f} (1 = normal)")

else:
    st.info("ℹ️ Select 'Diabetic' or 'Pre-diabetic' above to run the simulation.")
