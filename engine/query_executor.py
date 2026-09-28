"""
Query Execution Engine Module
Executes validated SQL queries, benchmarks execution time (latency), and formats result sets.
"""
import time
from typing import Dict, Any, List
from database.db_manager import DatabaseManager

class QueryExecutor:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def execute(self, validated_sql: str) -> Dict[str, Any]:
        """
        Executes a validated SQL statement, measures execution duration, and returns telemetry.
        """
        start_time = time.perf_counter()
        
        try:
            records = self.db.execute_query(validated_sql)
            end_time = time.perf_counter()
            duration_ms = round((end_time - start_time) * 1000, 2)

            columns = list(records[0].keys()) if records else []

            return {
                "success": True,
                "sql": validated_sql,
                "latency_ms": duration_ms,
                "row_count": len(records),
                "columns": columns,
                "data": records,
                "error": None
            }
        except Exception as e:
            end_time = time.perf_counter()
            return {
                "success": False,
                "sql": validated_sql,
                "latency_ms": round((end_time - start_time) * 1000, 2),
                "row_count": 0,
                "columns": [],
                "data": [],
                "error": str(e)
            }
