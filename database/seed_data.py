"""
Synthetic Healthcare Data Generator
Seeds the relational EHR database with realistic, HIPAA-compliant clinical data.
"""
import random
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager

FIRST_NAMES = [
    "Aarav", "Priya", "Rahul", "Ananya", "Rohan", "Sneha", "Vikram", "Neha",
    "Aditya", "Kavya", "Suresh", "Pooja", "Arjun", "Meera", "Karan", "Divya",
    "Rajesh", "Swati", "Nikhil", "Deepika", "Amit", "Shruti", "Sanjay", "Ritu",
    "David", "Sarah", "Michael", "Emily", "James", "Jessica", "Robert", "Ashley"
]

LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Reddy", "Rao", "Nair", "Iyer", "Choudhury",
    "Mishra", "Gupta", "Kumar", "Singh", "Joshi", "Bhat", "Deshmukh", "Menon",
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"
]

DEPARTMENTS = ["Cardiology", "Oncology", "Neurology", "Emergency", "ICU", "Pediatrics"]
ENCOUNTER_TYPES = ["Inpatient", "Outpatient", "Emergency", "Observation"]
PHYSICIANS = [
    "Dr. Ramesh Chandra, MD", "Dr. Sunita Kulkarni, MD", "Dr. Arvind Swaminathan, MD",
    "Dr. Elizabeth Vance, MD", "Dr. Marcus Brody, MD", "Dr. Alok Verma, MD"
]

LAB_TEST_CATALOG = [
    # test_name, unit, ref_low, ref_high, abnormal_prob
    ("Troponin I", "ng/mL", 0.00, 0.04, 0.35),
    ("Fasting Blood Glucose", "mg/dL", 70.0, 99.0, 0.40),
    ("White Blood Cell (WBC)", "x10^3/uL", 4.5, 11.0, 0.30),
    ("Hemoglobin (Hgb)", "g/dL", 12.0, 17.5, 0.25),
    ("Serum Creatinine", "mg/dL", 0.6, 1.2, 0.30),
    ("Potassium", "mmol/L", 3.5, 5.0, 0.20),
    ("Platelet Count", "x10^3/uL", 150.0, 450.0, 0.15),
    ("Total Cholesterol", "mg/dL", 125.0, 200.0, 0.45)
]

def generate_dob(min_age=18, max_age=85) -> str:
    days = random.randint(min_age * 365, max_age * 365)
    dob = datetime.now() - timedelta(days=days)
    return dob.strftime("%Y-%m-%d")

def seed_database(db: DatabaseManager, num_patients: int = 50, clear_existing: bool = True):
    """Populates the database with realistic healthcare records."""
    conn = db.get_connection()
    cursor = conn.cursor()

    if clear_existing:
        cursor.execute("DELETE FROM lab_results;")
        cursor.execute("DELETE FROM clinical_orders;")
        cursor.execute("DELETE FROM encounters;")
        cursor.execute("DELETE FROM patients;")

    print(f"Generating {num_patients} patients and relational clinical records...")

    # 1. Insert Patients
    patients_data = []
    for i in range(1, num_patients + 1):
        mrn = f"MRN-{100000 + i}"
        fn = random.choice(FIRST_NAMES)
        ln = random.choice(LAST_NAMES)
        dob = generate_dob()
        gender = random.choice(["Male", "Female"])
        bg = random.choice(["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
        patients_data.append((mrn, fn, ln, dob, gender, bg))

    cursor.executemany(
        "INSERT INTO patients (mrn, first_name, last_name, dob, gender, blood_group) VALUES (?, ?, ?, ?, ?, ?);",
        patients_data
    )

    # 2. Insert Encounters (1 to 3 encounters per patient)
    encounters_data = []
    base_time = datetime.now() - timedelta(days=120)

    cursor.execute("SELECT patient_id FROM patients;")
    patient_ids = [row[0] for row in cursor.fetchall()]

    for p_id in patient_ids:
        num_encounters = random.randint(1, 3)
        for _ in range(num_encounters):
            admit_offset = random.randint(1, 110)
            admit_date = base_time + timedelta(days=admit_offset, hours=random.randint(1, 23))
            los_days = random.randint(1, 14)
            discharge_date = admit_date + timedelta(days=los_days)
            dept = random.choice(DEPARTMENTS)
            enc_type = random.choice(ENCOUNTER_TYPES)
            physician = random.choice(PHYSICIANS)
            disposition = random.choice(["Home", "Transferred", "Skilled Nursing Facility", "Home with Home Health"])

            encounters_data.append((
                p_id,
                admit_date.strftime("%Y-%m-%d %H:%M:%S"),
                discharge_date.strftime("%Y-%m-%d %H:%M:%S"),
                dept,
                enc_type,
                physician,
                disposition
            ))

    cursor.executemany(
        """INSERT INTO encounters 
           (patient_id, admit_date, discharge_date, department, encounter_type, attending_physician, discharge_disposition) 
           VALUES (?, ?, ?, ?, ?, ?, ?);""",
        encounters_data
    )

    # 3. Insert Orders & Lab Results
    cursor.execute("SELECT encounter_id, patient_id, admit_date FROM encounters;")
    encounters = cursor.fetchall()

    total_orders = 0
    total_labs = 0

    for enc_id, p_id, admit_date_str in encounters:
        enc_admit = datetime.strptime(admit_date_str, "%Y-%m-%d %H:%M:%S")
        num_orders = random.randint(2, 4)

        for _ in range(num_orders):
            test_info = random.choice(LAB_TEST_CATALOG)
            test_name, unit, ref_low, ref_high, abnormal_prob = test_info

            order_date = enc_admit + timedelta(hours=random.randint(1, 12))
            order_status = random.choice(["Completed", "Completed", "Completed", "In-Progress"])
            priority = random.choice(["Routine", "Stat", "Urgent"])

            cursor.execute(
                """INSERT INTO clinical_orders 
                   (encounter_id, patient_id, order_name, order_type, order_status, ordered_date, priority) 
                   VALUES (?, ?, ?, ?, ?, ?, ?);""",
                (
                    enc_id,
                    p_id,
                    f"Diagnostic: {test_name}",
                    "Laboratory",
                    order_status,
                    order_date.strftime("%Y-%m-%d %H:%M:%S"),
                    priority
                )
            )
            order_id = cursor.lastrowid
            total_orders += 1

            # If order is completed, generate corresponding lab result
            if order_status == "Completed":
                is_abnormal = 1 if random.random() < abnormal_prob else 0
                if is_abnormal:
                    if random.random() > 0.3:
                        val = round(random.uniform(ref_high * 1.05, ref_high * 2.5), 2)
                    else:
                        val = round(random.uniform(ref_low * 0.4, ref_low * 0.95), 2)
                else:
                    val = round(random.uniform(ref_low, ref_high), 2)

                result_date = order_date + timedelta(minutes=random.randint(30, 180))

                cursor.execute(
                    """INSERT INTO lab_results 
                       (order_id, test_name, test_value, unit, reference_low, reference_high, is_abnormal, result_date) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?);""",
                    (
                        order_id,
                        test_name,
                        val,
                        unit,
                        ref_low,
                        ref_high,
                        is_abnormal,
                        result_date.strftime("%Y-%m-%d %H:%M:%S")
                    )
                )
                total_labs += 1

    conn.commit()
    conn.close()
    print(f"Seeding complete! {len(patients_data)} patients, {len(encounters_data)} encounters, {total_orders} orders, {total_labs} lab results.")

if __name__ == "__main__":
    db = DatabaseManager()
    seed_database(db)
