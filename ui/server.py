"""
Dashboard Web Server Module
Provides a zero-dependency HTTP server delivering the clinical dashboard and REST API endpoints.
Uses Python's standard library `http.server`.
"""
import http.server
import json
import os
import urllib.parse
from database.db_manager import DatabaseManager
from engine.sql_generator import SQLGenerator
from engine.sql_validator import SQLValidator
from engine.query_executor import QueryExecutor

PORT = 8080
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UI_DIR = os.path.join(BASE_DIR, "ui")

class ClinicalDashboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.db = DatabaseManager()
        self.generator = SQLGenerator()
        self.validator = SQLValidator()
        self.executor = QueryExecutor(self.db)
        super().__init__(*args, directory=UI_DIR, **kwargs)

    def do_POST(self):
        """Handles POST requests to /api/query."""
        if self.path == "/api/query":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            
            try:
                payload = json.loads(body)
                user_prompt = payload.get("prompt", "")

                # 1. Generate SQL from prompt
                raw_sql = self.generator.generate_sql(user_prompt)

                # 2. Validate SQL via security guardrails
                is_valid, validated_or_error = self.validator.validate(raw_sql)
                if not is_valid:
                    self._send_json({"success": False, "error": validated_or_error, "sql": raw_sql}, status=400)
                    return

                # 3. Execute query and measure latency
                result = self.executor.execute(validated_or_error)
                self._send_json(result)

            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=500)
        else:
            self.send_error(404, "Endpoint not found")

    def _send_json(self, data: dict, status: int = 200):
        response_bytes = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(response_bytes)

def start_server(port: int = PORT):
    server_address = ("127.0.0.1", port)
    httpd = http.server.HTTPServer(server_address, ClinicalDashboardHandler)
    print(f"\n==================================================================")
    print(f"🏥 AI Clinical Analytics & Reporting Engine Server Running!")
    print(f"👉 Local URL: http://127.0.0.1:{port}")
    print(f"==================================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()

if __name__ == "__main__":
    start_server()
