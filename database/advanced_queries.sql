-- ============================================================================
-- Advanced Analytical SQL Queries (Reporting & PL/SQL Emulation)
-- Highlighting: Common Table Expressions (CTEs), Window Functions, Aggregations
-- ============================================================================

-- Query 1: Top 3 Longest Inpatient Stays per Department (Using Window Ranking)
-- Purpose: Evaluates hospital bed utilization and department-level patient flow
WITH InpatientEncounters AS (
    SELECT 
        e.encounter_id,
        p.mrn,
        p.first_name || ' ' || p.last_name AS patient_name,
        e.department,
        e.attending_physician,
        ROUND((JULIANDAY(e.discharge_date) - JULIANDAY(e.admit_date)), 1) AS length_of_stay_days,
        DENSE_RANK() OVER (
            PARTITION BY e.department 
            ORDER BY (JULIANDAY(e.discharge_date) - JULIANDAY(e.admit_date)) DESC
        ) AS dept_stay_rank
    FROM encounters e
    JOIN patients p ON e.patient_id = p.patient_id
    WHERE e.encounter_type = 'Inpatient'
)
SELECT 
    department,
    dept_stay_rank,
    patient_name,
    mrn,
    length_of_stay_days,
    attending_physician
FROM InpatientEncounters
WHERE dept_stay_rank <= 3
ORDER BY department, dept_stay_rank;


-- Query 2: Department-Level Clinical Quality & Abnormal Lab Detection Rate
-- Purpose: Executive dashboard metric showing rate of critical lab results
SELECT 
    e.department,
    COUNT(DISTINCT e.encounter_id) AS total_encounters,
    COUNT(DISTINCT o.order_id) AS total_lab_orders,
    SUM(CASE WHEN l.is_abnormal = 1 THEN 1 ELSE 0 END) AS abnormal_results_count,
    ROUND(
        (CAST(SUM(CASE WHEN l.is_abnormal = 1 THEN 1 ELSE 0 END) AS REAL) / NULLIF(COUNT(l.result_id), 0)) * 100.0, 
        2
    ) AS abnormal_percentage,
    ROUND(AVG(JULIANDAY(e.discharge_date) - JULIANDAY(e.admit_date)), 2) AS avg_los_days
FROM encounters e
JOIN clinical_orders o ON e.encounter_id = o.encounter_id
JOIN lab_results l ON o.order_id = l.order_id
GROUP BY e.department
ORDER BY abnormal_percentage DESC;


-- Query 3: High-Risk Cardiac Surveillance (Troponin I Elevation)
-- Purpose: Clinical decision support detecting patients with potential acute myocardial infarction
WITH CardiacAlerts AS (
    SELECT 
        p.patient_id,
        p.mrn,
        p.first_name || ' ' || p.last_name AS patient_name,
        p.gender,
        e.department,
        e.admit_date,
        l.test_value AS troponin_level,
        l.unit,
        l.reference_high,
        l.result_date,
        ROW_NUMBER() OVER (
            PARTITION BY p.patient_id 
            ORDER BY l.test_value DESC
        ) AS peak_troponin_rank
    FROM patients p
    JOIN encounters e ON p.patient_id = e.patient_id
    JOIN clinical_orders o ON e.encounter_id = o.encounter_id
    JOIN lab_results l ON o.order_id = l.order_id
    WHERE l.test_name LIKE '%Troponin%'
      AND l.is_abnormal = 1
)
SELECT 
    mrn,
    patient_name,
    department,
    admit_date,
    troponin_level,
    reference_high,
    unit,
    result_date
FROM CardiacAlerts
WHERE peak_troponin_rank = 1
ORDER BY troponin_level DESC;


-- Query 4: Physician Performance & Turnaround Surveillance
-- Purpose: Tracks ordering habits and stat test volumes by attending physician
SELECT 
    e.attending_physician,
    COUNT(DISTINCT e.encounter_id) AS patients_seen,
    COUNT(o.order_id) AS total_orders,
    SUM(CASE WHEN o.priority = 'Stat' THEN 1 ELSE 0 END) AS stat_orders_count,
    ROUND(
        (CAST(SUM(CASE WHEN o.priority = 'Stat' THEN 1 ELSE 0 END) AS REAL) / COUNT(o.order_id)) * 100.0, 
        1
    ) AS stat_order_pct
FROM encounters e
JOIN clinical_orders o ON e.encounter_id = o.encounter_id
GROUP BY e.attending_physician
ORDER BY total_orders DESC;
