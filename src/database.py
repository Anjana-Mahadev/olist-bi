import pandas as pd
import sqlite3
import os
from pathlib import Path


# =========================================================
# DATABASE PATH CONFIGURATION
# =========================================================

# Project root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SQLite DB lives in project root (outside src)
DB_PATH = os.path.join(BASE_DIR, "olist.db")


# =========================================================
# 1️⃣ DATABASE INITIALIZATION (Run Only Once)
# =========================================================

def init_database(data_folder='data'):
    """
    Converts Olist Kaggle CSV files into a structured SQLite database.
    Run this ONLY once to create the database.
    """
    conn = sqlite3.connect(DB_PATH)
    data_path = Path(os.path.join(BASE_DIR, data_folder))

    if not data_path.exists():
        print(f"❌ Folder '{data_folder}' not found in project root.")
        print("Create it and add Olist CSV files.")
        return

    csv_files = list(data_path.glob("*.csv"))

    if not csv_files:
        print("❌ No CSV files found in data folder.")
        return

    print(f"\n--- 🚀 Starting Database Initialization ---")

    for file_path in csv_files:
        table_name = (
            file_path.stem
            .replace('olist_', '')
            .replace('_dataset', '')
        )

        print(f"Processing table: {table_name}...")

        try:
            df = pd.read_csv(file_path)
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            print(f"✅ Loaded {len(df)} rows into '{table_name}'.")

        except Exception as e:
            print(f"❌ Failed to process {file_path.name}: {e}")

    conn.close()
    print("--- ✅ Database Initialization Complete ---\n")


# =========================================================
# 2️⃣ QUERY EXECUTION (Used by SQL Agent)
# =========================================================

def execute_query(query: str):
    """
    Executes a SQL query on the Olist database.
    Returns:
        {
            "columns": [...],
            "rows": [...]
        }
    OR
        {"error": "..."}
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

            columns = []
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]

            return {
                "columns": columns,
                "rows": rows
            }

    except Exception as e:
        return {"error": str(e)}


# =========================================================
# RUN THIS FILE DIRECTLY TO CREATE DATABASE
# =========================================================

if __name__ == "__main__":
    init_database()