"""Database access for PeerDesk (Microsoft SQL Server through pyodbc).

HOW THE APP TALKS TO THE DATABASE
---------------------------------
Every screen calls one of three small helper functions in this file:

    fetch_all(sql, params)  -> list of rows      (for SELECTs that return many rows)
    fetch_one(sql, params)  -> one row or None   (for SELECTs that return at most one row)
    execute(sql, params)    -> number / new id   (for INSERT, UPDATE and DELETE)

The SQL text itself always comes from queries.py. The values the user typed are passed
separately in `params` and fill the "?" placeholders in the SQL. This is called a
*parameterised query* (or prepared statement). Because the values are never pasted into
the SQL text, a user cannot change the meaning of the query (this prevents SQL injection).

    Example:  db.fetch_one("SELECT * FROM tutor WHERE email = ?", ("a@b.com",))
                                                             ^             ^
                                              placeholder ---+--- value that fills it
"""
import pyodbc         # the library that lets Python talk to SQL Server through ODBC

# ---------------------------------------------------------------------------
# Connection settings (Microsoft SQL Server) - edit these for your computer
# ---------------------------------------------------------------------------
# Change SERVER to your SQL Server instance name. You can see it in the
# "Connect to Server" box of SQL Server Management Studio (SSMS).
#   SQL Server Express (default install):  localhost\SQLEXPRESS
#   SQL Server Developer / full edition:    localhost
SERVER = r"localhost\SQLSERVER1"
DATABASE = "PeerDesk"

# The ODBC driver to use. ODBC does not choose one for you, so it must be named here.
# Change it to "ODBC Driver 17 for SQL Server" if that is the version you have installed.
DRIVER = "ODBC Driver 18 for SQL Server"

# Windows login (the usual setup with SSMS). Set to False and fill in USERNAME/PASSWORD
# to use a SQL Server login instead, for example the "sa" account.
TRUSTED_CONNECTION = True
USERNAME = "sa"
PASSWORD = "Fall2022.dbms"

# ODBC Driver 18 encrypts connections by default; this lets it accept the local
# server's self-signed certificate.
TRUST_SERVER_CERTIFICATE = True

# The one open connection to SQL Server. It starts as None and is opened the first time
# connect() is called; every query after that reuses the same connection.
_conn = None


# ---------------------------------------------------------------------------
# Building the connection
# ---------------------------------------------------------------------------
def connection_string(database=None):
    """Build the text pyodbc needs to connect, e.g.

        DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost\\SQLEXPRESS;DATABASE=PeerDesk;
        Trusted_Connection=yes;TrustServerCertificate=yes;

    `database` lets setup_database.py connect to the built-in "master" database instead
    (it has to, because the PeerDesk database does not exist yet when it starts).
    """
    parts = [
        "DRIVER={%s}" % DRIVER,
        "SERVER=%s" % SERVER,
        "DATABASE=%s" % (database or DATABASE),
    ]
    if TRUSTED_CONNECTION:
        # Windows login: SQL Server trusts the Windows user that is running the app.
        parts.append("Trusted_Connection=yes")
    else:
        # SQL Server login: a username and password stored in SQL Server (e.g. "sa").
        parts.append("UID=%s" % USERNAME)
        parts.append("PWD=%s" % PASSWORD)
    if TRUST_SERVER_CERTIFICATE:
        # A local SQL Server uses a self-signed certificate; this tells the driver to accept it.
        parts.append("TrustServerCertificate=yes")
    return ";".join(parts) + ";"


def connect():
    """Open the connection the first time it is needed and reuse it afterwards.

    autocommit=False means SQL Server does NOT save a change automatically. Every change
    is part of a *transaction* that we finish ourselves with commit() (save it) or
    rollback() (undo it). See execute() below.
    """
    global _conn      # "global" lets this function change the module-level variable _conn
    if _conn is None:
        _conn = pyodbc.connect(connection_string(), autocommit=False, timeout=5)
    return _conn


def close():
    """Close the connection when the app exits."""
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None


# ---------------------------------------------------------------------------
# Running queries
# ---------------------------------------------------------------------------
# A *cursor* is the object that actually sends one SQL statement and holds its results.
# We open a new cursor for each query and close it when we are done.

def fetch_all(sql, params=()):
    """Run a SELECT and return all rows as a list.

    Each row behaves like a tuple, so it can be unpacked:
        for category_id, name in db.fetch_all(Q.Q_3A1): ...
    """
    cur = connect().cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    return rows


def fetch_one(sql, params=()):
    """Run a SELECT and return only the first row, or None when there are no rows."""
    cur = connect().cursor()
    cur.execute(sql, params)
    row = cur.fetchone()
    cur.close()
    return row


def execute(sql, params=()):
    """Run an INSERT / UPDATE / DELETE as ONE transaction and return a result.

    What it returns:
      * For UPDATE and DELETE: how many rows were changed (cursor.rowcount).
        The screens use this to tell whether anything happened, e.g. 0 means
        "no row matched the WHERE clause, so nothing was updated".
      * For an INSERT that contains "OUTPUT INSERTED.<id>": the new ID that SQL Server
        generated for the row (so we can show "Booking #42 confirmed").

    Transactions: if the statement succeeds we commit() (the change is saved for good).
    If anything fails, for example a UNIQUE constraint rejects the row, we rollback()
    (the database is left exactly as it was) and re-raise the error so the screen can
    show a message. This is the A (atomicity) in ACID: all of it happens, or none of it.
    """
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        result = cur.rowcount
        # cursor.description is only set when the statement returned columns.
        # For our INSERTs that is the OUTPUT INSERTED.<id> column, so we read the new ID.
        if cur.description is not None:
            row = cur.fetchone()
            result = row[0] if row else None
        conn.commit()
        return result
    except Exception:
        conn.rollback()
        raise          # pass the same error on to the screen that called us
    finally:
        cur.close()    # "finally" runs whether we returned normally or raised an error


def is_unique_violation(err):
    """True when SQL Server rejected a row because of a UNIQUE or PRIMARY KEY constraint.

    SQL Server error numbers: 2627 = UNIQUE/PRIMARY KEY constraint violated,
                              2601 = duplicate key in a unique index.
    The screens use this to show a friendly message (e.g. "this slot was just booked")
    instead of a crash.
    """
    text = str(err)
    return "2627" in text or "2601" in text or "UNIQUE" in text.upper() or "duplicate" in text.lower()
