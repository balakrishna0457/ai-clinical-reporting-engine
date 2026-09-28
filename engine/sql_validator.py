"""
SQL Security & Schema Validation Guardrails Module
Enforces strict read-only execution, prevents SQL injection, and verifies schema adherence.
"""
import re
from typing import Tuple, List, Optional

FORBIDDEN_KEYWORDS = [
    r"\bDROP\b",
    r"\bDELETE\b",
    r"\bUPDATE\b",
    r"\bINSERT\b",
    r"\bALTER\b",
    r"\bTRUNCATE\b",
    r"\bCREATE\b",
    r"\bREPLACE\b",
    r"\bEXEC\b",
    r"\bEXECUTE\b",
    r"\bATTACH\b",
    r"\bDETACH\b",
    r"\bPRAGMA\b"
]

ALLOWED_TABLES = {"patients", "encounters", "clinical_orders", "lab_results"}

class SQLValidator:
    def __init__(self, allowed_tables: Optional[set] = None):
        self.allowed_tables = allowed_tables or ALLOWED_TABLES

    def validate(self, sql_query: str) -> Tuple[bool, str]:
        """
        Validates the SQL query against security policies and syntax guidelines.
        Returns: (is_valid: bool, error_or_sanitized_sql: str)
        """
        clean_query = sql_query.strip()

        if not clean_query:
            return False, "Query cannot be empty."

        # Remove trailing semicolon for standardization
        if clean_query.endswith(";"):
            clean_query = clean_query[:-1].strip()

        # 1. Reject Multiple Statements (prevent stacked queries SQL injection)
        # Check if there are unquoted semicolons
        if ";" in clean_query:
            return False, "Security Violation: Multiple SQL statements are strictly prohibited."

        # 2. Check for Forbidden DDL/DML Keywords
        upper_query = clean_query.upper()
        for pattern in FORBIDDEN_KEYWORDS:
            if re.search(pattern, upper_query, re.IGNORECASE):
                matched = re.search(pattern, upper_query, re.IGNORECASE).group(0)
                return False, f"Security Violation: Destructive or DDL operation '{matched}' is prohibited. Read-only queries only."

        # 3. Must be a SELECT query or WITH (CTE) query
        if not (upper_query.startswith("SELECT") or upper_query.startswith("WITH")):
            return False, "Syntax Violation: Query must begin with 'SELECT' or 'WITH'."

        # 4. Check that at least one recognized table is referenced
        query_words = set(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", clean_query.lower()))
        referenced_tables = query_words.intersection(self.allowed_tables)
        
        if not referenced_tables and not ("sqlite_master" in clean_query.lower()):
            return False, f"Schema Violation: Query does not reference any authorized tables ({', '.join(sorted(self.allowed_tables))})."

        # 5. Guardrail: Enforce a safe default LIMIT if not aggregating and no limit present
        if "GROUP BY" not in upper_query and "LIMIT" not in upper_query:
            clean_query = f"{clean_query} LIMIT 100"

        return True, clean_query + ";"
