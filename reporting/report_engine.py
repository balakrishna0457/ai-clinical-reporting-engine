"""
Clinical Report Generation & Data Representation Module
Transforms raw database query outputs into structured analytical reports, CSVs, and executive summaries.
"""
import csv
import io
import json
from typing import Dict, Any, List

class ReportEngine:
    @staticmethod
    def generate_ascii_table(data: List[Dict[str, Any]], max_col_width: int = 25) -> str:
        """Renders tabular data as an aligned ASCII / plain-text table."""
        if not data:
            return "No records found."

        headers = list(data[0].keys())
        # Calculate column widths
        col_widths = {}
        for h in headers:
            col_widths[h] = min(max(len(str(h)), max(len(str(row.get(h, ""))) for row in data)), max_col_width)

        # Build separator
        sep = "+-" + "-+-".join("-" * col_widths[h] for h in headers) + "-+"

        # Build header line
        header_line = "| " + " | ".join(str(h).ljust(col_widths[h])[:col_widths[h]] for h in headers) + " |"

        lines = [sep, header_line, sep]

        # Build row lines
        for row in data:
            row_line = "| " + " | ".join(str(row.get(h, "")).ljust(col_widths[h])[:col_widths[h]] for h in headers) + " |"
            lines.append(row_line)

        lines.append(sep)
        return "\n".join(lines)

    @staticmethod
    def export_to_csv(data: List[Dict[str, Any]]) -> str:
        """Exports dataset as a CSV string."""
        if not data:
            return ""

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=list(data[0].keys()))
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue()

    @staticmethod
    def generate_clinical_summary(query_intent: str, execution_result: Dict[str, Any]) -> str:
        """Generates an executive medical overview based on the query results."""
        row_count = execution_result.get("row_count", 0)
        latency = execution_result.get("latency_ms", 0.0)
        data = execution_result.get("data", [])

        summary = [
            "=" * 70,
            "CLINICAL DECISION SUPPORT & ANALYTICS REPORT",
            "=" * 70,
            f"Query Intent      : {query_intent}",
            f"Total Records     : {row_count}",
            f"Execution Latency : {latency} ms",
            "-" * 70
        ]

        if not data:
            summary.append("Notice: No clinical records matched the specified filter criteria.")
            return "\n".join(summary)

        # Check for abnormal lab findings
        abnormal_flags = sum(1 for r in data if r.get("is_abnormal") == 1 or "troponin" in str(r).lower())
        if abnormal_flags > 0:
            summary.append(f"⚠️  CLINICAL ALERT: {abnormal_flags} critical/abnormal findings identified in this cohort.")

        summary.append("\nTop Records Preview:")
        summary.append(ReportEngine.generate_ascii_table(data[:5]))
        summary.append("=" * 70)

        return "\n".join(summary)
