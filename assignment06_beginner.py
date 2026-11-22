# Assignment 06: Descriptive Statistics
# Beginner-friendly version for Visual Studio Code

import json
import requests
import pandas as pd
import matplotlib.pyplot as plt

# 1. Download the two datasets from the class website
demographics_url = (
    "https://ruby.ils.unc.edu/~kibria/chip705_2026_fall/patient_demographics.csv"
)
cmp_url = "https://ruby.ils.unc.edu/~kibria/chip705_2026_fall/cmp.json"

# Download the demographics CSV
response = requests.get(demographics_url, timeout=30)
response.raise_for_status()

from io import StringIO

# Download the demographics CSV
response = requests.get(demographics_url, timeout=30)
response.raise_for_status()

from io import StringIO

demographics = pd.read_csv(StringIO(response.text))

# Download the CMP JSON
response = requests.get(cmp_url, timeout=30)
response.raise_for_status()

cmp_data = response.json()

# 2. Find the column names in the demographics file.
# This allows for small differences in capitalization or spacing.
columns = {}
for column in demographics.columns:
    columns[column.strip().lower().replace(" ", "_")] = column

patient_id_column = columns["patient_id"]
age_column = columns["age"]
sex_column = columns["sex"]

# The assignment BMI formula needs height in inches and weight in pounds.
# If these names do not match your CSV, check the printed column names below.
print("Columns in demographics file:", list(demographics.columns))

height_column = columns["height_inches"]
weight_column = columns["weight_lbs"]

if height_column is None or weight_column is None:
    raise ValueError(
        "Could not find height and weight columns. "
        "Look at the column names printed above and update this code."
    )


# 3. Find a patient's serum creatinine measurement.
def find_creatinine(measurements):
    for item in measurements:
        if not isinstance(item, dict):
            continue

        measure_name = str(item.get("measure", "")).lower()

        if (
            "creatinine" in measure_name
            and "ratio" not in measure_name
            and "urine" not in measure_name
        ):
            try:
                value = float(item["patient_measure"])
                if value > 0:
                    return value
            except (ValueError, TypeError, KeyError):
                continue

    return None


# 4. Calculate eGFR using the same formula from Milestone 01.
def calculate_egfr(creatinine, age, sex):
    sex = str(sex).strip().lower()

    if sex.startswith("f"):
        k = 0.7
        a = -0.241
        sex_factor = 1.012
    elif sex.startswith("m"):
        k = 0.9
        a = -0.302
        sex_factor = 1.0
    else:
        return None

    low = min(creatinine / k, 1)
    high = max(creatinine / k, 1)

    egfr = 142 * (low**a) * (high**-1.200) * (0.9938**age) * sex_factor
    return round(egfr, 2)


# 5. Match patients and create a list of results.
results = []

for index, row in demographics.iterrows():
    patient_id = str(row[patient_id_column])

    measurements = cmp_data.get(patient_id)

    if measurements is None:
        measurements = cmp_data.get(row[patient_id_column])

    if measurements is None:
        continue

    creatinine = find_creatinine(measurements)

    if creatinine is None:
        continue

    age = float(row[age_column])
    sex = row[sex_column]
    height = float(row[height_column])
    weight = float(row[weight_column])

    if height <= 0 or weight <= 0:
        continue

    egfr = calculate_egfr(creatinine, age, sex)

    if egfr is None:
        continue

    # BMI formula from the assignment (weight in pounds, height in inches).
    bmi = (weight * 703) / (height**2)

    results.append(
        {
            "Patient Age": age,
            "Patient Height": height,
            "Patient Weight": weight,
            "Patient BMI": round(bmi, 2),
            "Patient Sex": sex,
            "Patient eGFR": egfr,
        }
    )

# 6. Turn the results into a Pandas DataFrame.
patients = pd.DataFrame(results)

print("\nAll patients with usable data:")
print(patients.head())

# 7. Keep only patients whose eGFR is 65 or lower.
screening_patients = patients[patients["Patient eGFR"] <= 65].copy()

print("\nNumber of patients with eGFR <= 65:")
print(len(screening_patients))

# 8. Show descriptive statistics for age, height, and weight.
print("\nDescriptive statistics:")
print(
    screening_patients[["Patient Age", "Patient Height", "Patient Weight"]].describe()
)


# 9. Put each patient into a BMI category.
def bmi_category(bmi):
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal Weight"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"


screening_patients["BMI Category"] = screening_patients["Patient BMI"].apply(
    bmi_category
)

# 10. Bar chart: average eGFR for each BMI category.
average_egfr = screening_patients.groupby("BMI Category")["Patient eGFR"].mean()

category_order = ["Underweight", "Normal Weight", "Overweight", "Obese"]
average_egfr = average_egfr.reindex(category_order).dropna()

average_egfr.plot(kind="bar")
plt.title("Average eGFR by BMI Category")
plt.xlabel("BMI Category")
plt.ylabel("Average eGFR")
plt.xticks(rotation=30)
plt.tight_layout()
plt.show()

# 11. Scatter plot: patient age and eGFR.
plt.scatter(screening_patients["Patient Age"], screening_patients["Patient eGFR"])
plt.title("Patient Age vs. eGFR")
plt.xlabel("Patient Age")
plt.ylabel("Patient eGFR")
plt.tight_layout()
plt.show()

# 12. Pie chart: patient sex.
sex_counts = screening_patients["Patient Sex"].value_counts()

if len(sex_counts) > 0:
    plt.pie(sex_counts, labels=sex_counts.index, autopct="%1.1f%%")
    plt.title("Patient Sex Distribution")
    plt.axis("equal")
    plt.show()
else:
    print("No patients available for the pie chart.")

# 13. Save the filtered patient data to a CSV file.
screening_patients.to_csv("patients_needing_screening.csv", index=False)

print("\nDone! Your results were saved to patients_needing_screening.csv")
