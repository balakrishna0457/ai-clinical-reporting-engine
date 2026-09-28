"""
Comprehensive Unit Test Suite
Validates database integrity, SQL security guardrails, NLP parsing, and reporting engine.
Runs with standard library `unittest` (Zero external packages required).
"""
import unittest
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database.db_manager import DatabaseManager
from database.seed_data import seed_database
from engine.sql_validator import SQLValidator
from engine.sql_generator import SQLGenerator
from engine.query_executor import QueryExecutor
from reporting.report_engine import ReportEngine

class TestClinicalEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Use an in-memory or test database
        cls.test_db_path = os.path.join(BASE_DIR, "tests", "test_clinical.db")
        cls.db = DatabaseManager(cls.test_db_path)
        seed_database(cls.db, num_patients=10, clear_existing=True)
        cls.validator = SQLValidator()
        cls.generator = SQLGenerator()
        cls.executor = QueryExecutor(cls.db)

    @classmethod
    def tearDownClass(cls):
        import gc
        cls.db = None
        cls.executor = None
        gc.collect()
        try:
            if os.path.exists(cls.test_db_path):
                os.remove(cls.test_db_path)
        except PermissionError:
            pass

    # 1. Database & Schema Tests
    def test_database_tables_exist(self):
        tables = self.db.get_table_names()
        expected = {"patients", "encounters", "clinical_orders", "lab_results"}
        self.assertTrue(expected.issubset(set(tables)), f"Missing tables. Found: {tables}")

    def test_patients_seeded(self):
        res = self.db.execute_query("SELECT COUNT(*) as cnt FROM patients;")
        self.assertGreater(res[0]["cnt"], 0, "Patients table should not be empty")

    # 2. Security & Guardrails Tests
    def test_validator_accepts_valid_select(self):
        query = "SELECT patient_id, mrn FROM patients LIMIT 10;"
        is_valid, sanitized = self.validator.validate(query)
        self.assertTrue(is_valid, f"Valid query was rejected: {sanitized}")

    def test_validator_rejects_drop_table(self):
        malicious = "DROP TABLE patients;"
        is_valid, err = self.validator.validate(malicious)
        self.assertFalse(is_valid)
        self.assertIn("Security Violation", err)

    def test_validator_rejects_delete(self):
        malicious = "DELETE FROM encounters WHERE 1=1;"
        is_valid, err = self.validator.validate(malicious)
        self.assertFalse(is_valid)
        self.assertIn("Security Violation", err)

    def test_validator_rejects_stacked_queries(self):
        malicious = "SELECT * FROM patients; DROP TABLE lab_results;"
        is_valid, err = self.validator.validate(malicious)
        self.assertFalse(is_valid)
        self.assertIn("Multiple SQL statements", err)

    def test_validator_rejects_unauthorized_tables(self):
        query = "SELECT * FROM user_passwords;"
        is_valid, err = self.validator.validate(query)
        self.assertFalse(is_valid)
        self.assertIn("Schema Violation", err)

    # 3. SQL Generator & Semantic Parser Tests
    def test_generator_cardiac_query(self):
        sql = self.generator.generate_sql("Show patients with abnormal Troponin levels in cardiology")
        self.assertIn("Troponin", sql)
        self.assertTrue(sql.upper().startswith("SELECT"))

    def test_generator_department_los_query(self):
        sql = self.generator.generate_sql("Show average length of stay by department")
        self.assertTrue("length of stay" in sql.lower() or "los_days" in sql.lower() or "avg_los_days" in sql.lower())

    # 4. Query Executor & Telemetry Tests
    def test_query_executor_latency_and_data(self):
        query = "SELECT p.mrn, e.department FROM patients p JOIN encounters e ON p.patient_id = e.patient_id LIMIT 5;"
        result = self.executor.execute(query)
        self.assertTrue(result["success"])
        self.assertIn("latency_ms", result)
        self.assertGreaterEqual(result["latency_ms"], 0.0)
        self.assertEqual(len(result["data"]), 5)

    # 5. Reporting Engine Tests
    def test_report_engine_ascii_and_csv(self):
        sample_data = [
            {"mrn": "MRN-101", "department": "Cardiology", "status": "Stable"},
            {"mrn": "MRN-102", "department": "ICU", "status": "Critical"}
        ]
        ascii_table = ReportEngine.generate_ascii_table(sample_data)
        self.assertIn("Cardiology", ascii_table)
        self.assertIn("MRN-101", ascii_table)

        csv_str = ReportEngine.export_to_csv(sample_data)
        self.assertIn("mrn,department,status", csv_str)

if __name__ == "__main__":
    unittest.main()
