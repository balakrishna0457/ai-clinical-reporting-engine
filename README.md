# AI-Powered Clinical Analytics & Automated SQL Reporting Engine

An intelligent healthcare reporting system modeling enterprise Electronic Health Record (EHR) workflows (Cerner Millennium / Oracle Health architecture). It translates natural language clinical inquiries into validated, optimized SQL/PL-SQL queries, applies AST security guardrails, executes against relational schemas, and renders interactive analytical reports.

---

## 🌟 Key Architecture & Highlights

```
+--------------------------+
|  Clinician / Researcher  |  (Natural Language Inquiries)
+--------------------------+
             |
             v
+--------------------------+
|    AI Query Generator    |  (Intelligent Semantic NLP Parser / Gemini API)
+--------------------------+
             |
             v
+--------------------------+
| SQL Security Guardrails  |  (Enforces Read-Only SELECT, Blocks DML/DDL, Prevents Injection)
+--------------------------+
             |
             v
+--------------------------+
|   Query Latency Engine   |  (Executes with < 5ms latency, indexes, query plans)
+--------------------------+
             |
             v
+--------------------------+
|  Relational EHR Database |  (Patients -> Encounters -> Clinical Orders -> Lab Results)
+--------------------------+
             |
             v
+--------------------------+
|  Report Engine & Web UI  |  (Interactive Dashboard, Summary Metrics, CSV/Tabular Export)
+--------------------------+
```

### Relational Data Model (Modeled after Cerner Millennium):
* **`patients`**: Core demographic identity, MRN, date of birth, blood group.
* **`encounters`**: Clinical admissions, visit types (Inpatient, Outpatient, Emergency), attending physicians, departments (Cardiology, ICU, Oncology, etc.), and length of stay (LOS).
* **`clinical_orders`**: Medication, diagnostic, and laboratory orders categorized by clinical urgency (Routine, Urgent, Stat).
* **`lab_results`**: Quantitative diagnostic measurements (Troponin, WBC, Fasting Glucose, Creatinine) with normal reference ranges and abnormal flag triggers.

---

## 🚀 Quick Start (Zero External Packages Required)

The entire core application and web dashboard run directly on **standard Python 3.10+** without needing any `pip install` commands.

### 1. Launch the Application
Open your terminal inside the project directory and run:
```bash
python run.py
```
* The script automatically initializes the relational schema.
* Seeds 50+ realistic clinical patient journeys, encounters, and lab results.
* Starts the web server and automatically opens `http://127.0.0.1:8080` in your default browser.

### 2. Run the Automated Unit Tests
To verify all database constraints, security guardrails, and query parsers:
```bash
python -m unittest discover tests
```

---

## 🛡️ Security & Execution Guardrails

1. **Read-Only Enforcement:** Queries containing DML/DDL operations (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`) are immediately rejected.
2. **Anti-Injection:** Semicolons and stacked SQL statements are stripped or blocked.
3. **Schema Verification:** Ensures queries only reference authorized clinical tables (`patients`, `encounters`, `clinical_orders`, `lab_results`).
4. **Denial-of-Service Prevention:** Unbounded queries automatically have safety limits applied to prevent memory exhaustion during tabular rendering.

---

## 📊 Sample Pre-Built Clinical Queries

* **Cardiac Troponin Alerts:**
  > *"Show cardiac patients with abnormal Troponin levels and admission history"*  
  Identifies patients with elevated cardiac biomarkers, flagging potential acute myocardial infarctions.
* **Department Stay & Patient Volume:**
  > *"Department patient volume and average length of stay summary"*  
  Computes hospital bed utilization metrics and patient turnover rates.
* **Abnormal Lab Test Surveillance:**
  > *"List abnormal lab results with high failure rates by department"*  
  Identifies laboratory testing anomalies across hospital departments.
* **Stat Orders in Emergency & ICU:**
  > *"Show stat and urgent clinical orders across all departments"*  
  Tracks priority turnaround metrics for critical care interventions.

---

## 💬 Oracle Interview Talking Points (How to Pitch This Project)

* **Why did you build this?**  
  *"Enterprise EHR systems like Oracle Health / Cerner Millennium contain vast relational data across millions of clinical records. Hospital administrators and clinicians often need quick ad-hoc reports without waiting days for IT tickets. I built this engine to safely bridge natural language queries to high-performance, validated SQL statements with strict security guardrails."*

* **How did you handle database performance?**  
  *"I created composite B-tree indexes on foreign keys (`encounters.patient_id`, `lab_results.order_id`) and frequently filtered columns (`department`, `admit_date`, `is_abnormal`). In the reporting queries, I utilized Common Table Expressions (CTEs) and Window Functions like `DENSE_RANK() OVER (PARTITION BY department ORDER BY los DESC)` to compute departmental rankings efficiently in a single query pass."*

* **How did you prevent SQL injection / hallucination?**  
  *"I implemented an AST and regex-based validation guardrail before execution. The engine enforces read-only access, forbids any mutating SQL operations, checks table names against the schema dictionary, and tracks execution latency in milliseconds."*
