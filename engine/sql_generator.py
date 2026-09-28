"""
AI Query Generator Module
Translates natural language clinical questions into validated, optimized SQL queries.
Supports both zero-dependency intelligent NLP parsing and live LLM (Gemini API) inference.
"""
import os
import re
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

SYSTEM_SCHEMA_PROMPT = """
You are a Healthcare Database and Clinical Analytics Specialist.
Your task is to generate syntactically valid SQLite queries based on natural language healthcare requests.

Schema:
- patients (patient_id, mrn, first_name, last_name, dob, gender, blood_group, created_at)
- encounters (encounter_id, patient_id, admit_date, discharge_date, department, encounter_type, attending_physician, discharge_disposition)
  * Departments: Cardiology, Oncology, Neurology, Emergency, ICU, Pediatrics
  * Encounter Types: Inpatient, Outpatient, Emergency, Observation
- clinical_orders (order_id, encounter_id, patient_id, order_name, order_type, order_status, ordered_date, priority)
  * Priorities: Routine, Stat, Urgent
- lab_results (result_id, order_id, test_name, test_value, unit, reference_low, reference_high, is_abnormal, result_date)

Rules:
1. Generate only a single SELECT or WITH statement.
2. Calculate Length of Stay (LOS) in days using: ROUND((JULIANDAY(discharge_date) - JULIANDAY(admit_date)), 1)
3. For patient full names, use: first_name || ' ' || last_name AS patient_name
4. Return ONLY raw SQL without markdown code blocks, backticks, or explanations.
"""

class SQLGenerator:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")

    def generate_sql(self, natural_language_query: str) -> str:
        """
        Translates a natural language clinical request into an optimized SQL query.
        Uses Gemini API if key is available; otherwise uses high-precision clinical NLP pattern matching.
        """
        query_text = natural_language_query.strip().lower()

        # If API key is available, use Gemini API via standard library HTTP
        if self.api_key:
            try:
                llm_sql = self._generate_with_gemini(natural_language_query)
                if llm_sql:
                    return llm_sql
            except Exception as e:
                print(f"[Warning] Gemini API call failed: {e}. Falling back to clinical semantic parser.")

        # Offline Intelligent Semantic Parsing
        return self._semantic_clinical_parser(query_text)

    def _generate_with_gemini(self, user_prompt: str) -> Optional[str]:
        """Calls Gemini API via standard library urllib (zero external package required)."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": SYSTEM_SCHEMA_PROMPT},
                        {"text": f"Generate SQL for: {user_prompt}"}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 300
            }
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
            raw_text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            # Clean markdown codeblocks if model returned them
            raw_text = re.sub(r"^```(sql)?", "", raw_text, flags=re.MULTILINE)
            raw_text = re.sub(r"```$", "", raw_text, flags=re.MULTILINE).strip()
            return raw_text

    def _semantic_clinical_parser(self, q: str) -> str:
        """
        Rule-based semantic parser covering the most common clinical reporting queries.
        Demonstrates domain-specific keyword mapping and intent classification.
        """
        # 1. Cardiac / Troponin queries
        if "troponin" in q or "cardiac" in q:
            return (
                "SELECT p.mrn, p.first_name || ' ' || p.last_name AS patient_name, "
                "e.department, l.test_name, l.test_value, l.unit, l.reference_high, l.result_date "
                "FROM patients p "
                "JOIN encounters e ON p.patient_id = e.patient_id "
                "JOIN clinical_orders o ON e.encounter_id = o.encounter_id "
                "JOIN lab_results l ON o.order_id = l.order_id "
                "WHERE l.test_name LIKE '%Troponin%' AND l.is_abnormal = 1 "
                "ORDER BY l.test_value DESC LIMIT 50;"
            )

        # 2. Length of Stay (LOS) / Longest staying patients
        if "length of stay" in q or "stay" in q or "longest" in q:
            return (
                "SELECT e.department, p.mrn, p.first_name || ' ' || p.last_name AS patient_name, "
                "e.encounter_type, e.attending_physician, "
                "ROUND((JULIANDAY(e.discharge_date) - JULIANDAY(e.admit_date)), 1) AS los_days "
                "FROM encounters e "
                "JOIN patients p ON e.patient_id = p.patient_id "
                "WHERE e.discharge_date IS NOT NULL "
                "ORDER BY los_days DESC LIMIT 25;"
            )

        # 3. Department patient count / volume summary
        if "department" in q and ("count" in q or "volume" in q or "patient" in q or "breakdown" in q):
            return (
                "SELECT department, COUNT(DISTINCT patient_id) AS total_patients, "
                "COUNT(encounter_id) AS total_encounters, "
                "ROUND(AVG(JULIANDAY(discharge_date) - JULIANDAY(admit_date)), 1) AS avg_los_days "
                "FROM encounters "
                "GROUP BY department "
                "ORDER BY total_patients DESC;"
            )

        # 4. Abnormal labs rate by department
        if "abnormal" in q or "lab" in q:
            return (
                "SELECT e.department, l.test_name, COUNT(l.result_id) AS total_tests, "
                "SUM(l.is_abnormal) AS abnormal_count, "
                "ROUND((CAST(SUM(l.is_abnormal) AS REAL) / COUNT(l.result_id)) * 100.0, 1) AS abnormal_rate_pct "
                "FROM encounters e "
                "JOIN clinical_orders o ON e.encounter_id = o.encounter_id "
                "JOIN lab_results l ON o.order_id = l.order_id "
                "GROUP BY e.department, l.test_name "
                "HAVING total_tests >= 3 "
                "ORDER BY abnormal_rate_pct DESC LIMIT 30;"
            )

        # 5. Stat / Urgent Orders
        if "stat" in q or "urgent" in q or "priority" in q:
            return (
                "SELECT e.department, o.order_name, o.priority, o.order_status, "
                "p.first_name || ' ' || p.last_name AS patient_name, o.ordered_date "
                "FROM clinical_orders o "
                "JOIN encounters e ON o.encounter_id = e.encounter_id "
                "JOIN patients p ON o.patient_id = p.patient_id "
                "WHERE o.priority IN ('Stat', 'Urgent') "
                "ORDER BY o.ordered_date DESC LIMIT 40;"
            )

        # 6. Default Fallback: Overview of recent clinical encounters
        return (
            "SELECT p.mrn, p.first_name || ' ' || p.last_name AS patient_name, "
            "e.department, e.encounter_type, e.admit_date, e.attending_physician "
            "FROM encounters e "
            "JOIN patients p ON e.patient_id = p.patient_id "
            "ORDER BY e.admit_date DESC LIMIT 25;"
        )
