"""
Main Application Launcher
Initializes the EHR database, seeds data if needed, launches the reporting server, and opens the UI.
"""
import sys
import os
import webbrowser
import threading
import time

# Ensure project root is on sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database.db_manager import DatabaseManager
from database.seed_data import seed_database
from ui.server import start_server, PORT

def main():
    print("\n" + "=" * 70)
    print("AI-Powered Clinical Analytics & Automated SQL Reporting Engine")
    print("Modeled for Oracle Health / Cerner Millennium Data Architecture")
    print("=" * 70)

    # 1. Initialize DB and Seed Data
    print("\n[Step 1/3] Checking relational EHR database...")
    db = DatabaseManager()
    counts = db.execute_query("SELECT COUNT(*) as count FROM patients;")
    patient_count = counts[0]["count"] if counts else 0

    if patient_count == 0:
        print("  Database is empty. Populating with synthetic clinical records...")
        seed_database(db, num_patients=50)
    else:
        print(f"  Database ready! Active patient records: {patient_count}")

    # 2. Launch Browser in background thread after 1 second
    def open_browser():
        time.sleep(1.2)
        url = f"http://127.0.0.1:{PORT}"
        print(f"[Step 2/3] Opening dashboard in your default browser: {url}")
        webbrowser.open(url)

    threading.Thread(target=open_browser, daemon=True).start()

    # 3. Start Server
    print(f"[Step 3/3] Starting web server on port {PORT}...")
    start_server(PORT)

if __name__ == "__main__":
    main()
