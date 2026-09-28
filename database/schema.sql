-- ============================================================================
-- AI-Powered Clinical Analytics & Automated SQL Reporting Engine
-- Schema Architecture: Relational EHR (Modeled after Cerner Millennium / Oracle Health)
-- Entities: Patients, Encounters, Clinical Orders, Lab Results
-- ============================================================================

-- 1. Patients Table (Demographics & Baseline Attributes)
CREATE TABLE IF NOT EXISTS patients (
    patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
    mrn VARCHAR(20) UNIQUE NOT NULL,             -- Medical Record Number
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    dob DATE NOT NULL,
    gender VARCHAR(10) CHECK(gender IN ('Male', 'Female', 'Other')),
    blood_group VARCHAR(5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Encounters Table (Visits, Admissions, Discharges & Departmental Workflows)
CREATE TABLE IF NOT EXISTS encounters (
    encounter_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    admit_date TIMESTAMP NOT NULL,
    discharge_date TIMESTAMP,
    department VARCHAR(50) NOT NULL CHECK(department IN ('Cardiology', 'Oncology', 'Neurology', 'Emergency', 'ICU', 'Pediatrics')),
    encounter_type VARCHAR(20) NOT NULL CHECK(encounter_type IN ('Inpatient', 'Outpatient', 'Emergency', 'Observation')),
    attending_physician VARCHAR(100) NOT NULL,
    discharge_disposition VARCHAR(50) DEFAULT 'Home',
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
);

-- 3. Clinical Orders Table (Medications, Diagnostic Tests, Procedures)
CREATE TABLE IF NOT EXISTS clinical_orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    encounter_id INTEGER NOT NULL,
    patient_id INTEGER NOT NULL,
    order_name VARCHAR(100) NOT NULL,
    order_type VARCHAR(30) NOT NULL CHECK(order_type IN ('Laboratory', 'Radiology', 'Pharmacy', 'Procedure')),
    order_status VARCHAR(20) NOT NULL CHECK(order_status IN ('Completed', 'Pending', 'In-Progress', 'Cancelled')),
    ordered_date TIMESTAMP NOT NULL,
    priority VARCHAR(15) DEFAULT 'Routine' CHECK(priority IN ('Routine', 'Stat', 'Urgent')),
    FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id) ON DELETE CASCADE,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
);

-- 4. Lab Results Table (Quantitative and Qualitative Diagnostic Metrics)
CREATE TABLE IF NOT EXISTS lab_results (
    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    test_name VARCHAR(100) NOT NULL,
    test_value REAL NOT NULL,
    unit VARCHAR(20) NOT NULL,
    reference_low REAL,
    reference_high REAL,
    is_abnormal INTEGER DEFAULT 0 CHECK(is_abnormal IN (0, 1)),
    result_date TIMESTAMP NOT NULL,
    FOREIGN KEY (order_id) REFERENCES clinical_orders(order_id) ON DELETE CASCADE
);

-- ============================================================================
-- Performance Indexes (Optimizing Analytical Queries & Join Latency)
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_encounters_patient ON encounters(patient_id);
CREATE INDEX IF NOT EXISTS idx_encounters_dept ON encounters(department);
CREATE INDEX IF NOT EXISTS idx_encounters_admit ON encounters(admit_date);
CREATE INDEX IF NOT EXISTS idx_orders_encounter ON clinical_orders(encounter_id);
CREATE INDEX IF NOT EXISTS idx_orders_patient ON clinical_orders(patient_id);
CREATE INDEX IF NOT EXISTS idx_lab_order ON lab_results(order_id);
CREATE INDEX IF NOT EXISTS idx_lab_test_abnormal ON lab_results(test_name, is_abnormal);
