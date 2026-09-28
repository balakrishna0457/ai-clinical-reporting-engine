"""
Database Management Module
Provides thread-safe connections, schema initialization, and transactional query execution.
"""
import sqlite3
import os
from typing import List, Dict, Any, Tuple

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clinical_data.db")
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")

class DatabaseManager:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._initialize_schema()

    def get_connection(self) -> sqlite3.Connection:
        """Returns a SQLite connection with foreign keys enabled and row_factory configured."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_schema(self) -> None:
        """Executes schema.sql to ensure all relational tables and indexes exist."""
        if not os.path.exists(SCHEMA_PATH):
            raise FileNotFoundError(f"Schema file not found at: {SCHEMA_PATH}")

        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        with self.get_connection() as conn:
            conn.executescript(schema_sql)

    def execute_query(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """
        Executes a read-only SELECT query and returns results as a list of dictionaries.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def execute_script(self, script: str) -> None:
        """Executes a multi-statement SQL script."""
        with self.get_connection() as conn:
            conn.executescript(script)

    def get_table_names(self) -> List[str]:
        """Returns all user table names in the database."""
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        results = self.execute_query(query)
        return [r["name"] for r in results]

    def get_schema_summary(self) -> Dict[str, List[str]]:
        """Returns a dictionary mapping table names to their column definitions."""
        summary = {}
        for table in self.get_table_names():
            columns = self.execute_query(f"PRAGMA table_info({table});")
            summary[table] = [f"{c['name']} ({c['type']})" for c in columns]
        return summary
