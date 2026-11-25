"""Creates the PeerDesk database on SQL Server and loads the tables and sample data.

Run once:  python setup_database.py
Add --reset to delete an existing PeerDesk database and start again from the sample data:
           python setup_database.py --reset

What it does, step by step:
  1. Connects to the built-in "master" database (PeerDesk may not exist yet).
  2. Creates the PeerDesk database (dropping the old one first if --reset was given).
  3. Connects to PeerDesk and runs sql/01_create_tables.sql, then sql/02_sample_data.sql.
     These are the same scripts you can open and run yourself in SSMS.
  4. Prints how many rows each table now has.
"""
import os
import re
import sys

import pyodbc

import db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = ["01_create_tables.sql", "02_sample_data.sql"]   # run in this order (tables before data)
TABLES = ["administrator", "tutor", "client", "category", "service_listing", "time_slot", "booking"]


def batches(path):
    """Split a .sql script into batches on lines that contain only GO.

    GO is not SQL: it is a command for SSMS meaning "send everything above as one batch".
    pyodbc does not understand GO, so we split the script ourselves and run each batch.
    The regular expression matches a line with only "GO" on it (any case, spaces allowed).
    """
    with open(path, encoding="utf-8") as f:
        text = f.read()
    parts = re.split(r"^\s*GO\s*$", text, flags=re.MULTILINE | re.IGNORECASE)
    return [part.strip() for part in parts if part.strip()]    # drop empty pieces


def main():
    name = db.DATABASE
    reset = "--reset" in sys.argv

    # Step 1: connect to "master". autocommit=True because CREATE/DROP DATABASE
    # cannot run inside a transaction.
    print("Connecting to SQL Server:", db.SERVER)
    master = pyodbc.connect(db.connection_string(database="master"), autocommit=True, timeout=5)

    # Step 2: does the database already exist? (sys.databases lists every database on the server)
    exists = master.execute("SELECT COUNT(*) FROM sys.databases WHERE name = ?", name).fetchone()[0]
    if exists and not reset:
        print(f'The database "{name}" already exists. Nothing was changed.')
        print("Run  python setup_database.py --reset  to delete it and load the sample data again.")
        return 0
    if exists:
        print(f'Deleting the existing database "{name}" ...')
        # SINGLE_USER WITH ROLLBACK IMMEDIATE disconnects anyone still using the database
        # (e.g. an open SSMS window), otherwise DROP DATABASE would fail.
        master.execute(f"ALTER DATABASE [{name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
        master.execute(f"DROP DATABASE [{name}]")
    print(f'Creating database "{name}" ...')
    master.execute(f"CREATE DATABASE [{name}]")
    master.close()

    # Step 3: connect to the new database and run both scripts, batch by batch.
    conn = pyodbc.connect(db.connection_string(), autocommit=True, timeout=5)
    for script in SCRIPTS:
        path = os.path.join(BASE_DIR, "sql", script)
        for batch in batches(path):
            conn.execute(batch)
        print("Ran", script)

    # Step 4: count the rows in every table to show that the data loaded.
    counts = {}
    for table in TABLES:
        counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    conn.close()
    print("Rows loaded:", ", ".join(f"{table} {n}" for table, n in counts.items()))
    print("Done. Start the app with:  python main.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
