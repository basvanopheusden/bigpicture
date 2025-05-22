import os
import sqlite3
import json
from datetime import datetime
import pytz

# Determine where the SQLite database should live. This mirrors the old logic in app.py
DB_PATH = os.environ.get('DATABASE_URL', 'tasks.db')


def get_pacific_time():
    """Return the current time in America/Los_Angeles timezone."""
    pacific = pytz.timezone('America/Los_Angeles')
    return datetime.now(pacific).isoformat()


def init_db():
    """Initialise the database and create tables if required."""
    print(f"Initializing database at {DB_PATH}...")
    try:
        dir_name = os.path.dirname(DB_PATH)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()

            c.execute('''
                CREATE TABLE IF NOT EXISTS areas (
                    key TEXT PRIMARY KEY,
                    text TEXT NOT NULL,
                    date_time_created TEXT NOT NULL,
                    order_index INTEGER NOT NULL DEFAULT 0
                )
            ''')

            c.execute('''
                CREATE TABLE IF NOT EXISTS objectives (
                    key TEXT PRIMARY KEY,
                    area_key TEXT NOT NULL,
                    text TEXT NOT NULL,
                    date_time_created TEXT NOT NULL,
                    date_time_completed TEXT,
                    status TEXT DEFAULT 'open' CHECK(status IN ('open', 'complete', 'secondary')),
                    order_index INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (area_key) REFERENCES areas (key) ON DELETE CASCADE
                )
            ''')

            c.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    key TEXT PRIMARY KEY,
                    area_key TEXT,
                    objective_key TEXT,
                    text TEXT NOT NULL,
                    date_time_created TEXT NOT NULL,
                    date_time_completed TEXT,
                    status TEXT DEFAULT 'open' CHECK(status IN ('open', 'complete', 'secondary')),
                    order_index INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (area_key) REFERENCES areas (key) ON DELETE CASCADE,
                    FOREIGN KEY (objective_key) REFERENCES objectives (key) ON DELETE CASCADE,
                    CHECK ((area_key IS NOT NULL AND objective_key IS NULL) OR
                           (area_key IS NULL AND objective_key IS NOT NULL))
                )
            ''')

            c.execute('''
                CREATE TABLE IF NOT EXISTS undo_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_type TEXT NOT NULL,
                    table_name TEXT NOT NULL,
                    record_key TEXT NOT NULL,
                    old_data TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            ''')

            print("Database initialized successfully")
    except sqlite3.Error as e:
        print(f"Error initializing database: {e}")
        raise


def get_db():
    """Return a connection to the configured database."""
    print(f"Attempting to connect to DB at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def log_action_for_undo(conn, action_type, table_name, record_key, old_data):
    """Persist an action so that it can be undone later."""
    json_data = json.dumps(old_data)
    conn.execute(
        'INSERT INTO undo_log (action_type, table_name, record_key, old_data, timestamp) VALUES (?, ?, ?, ?, ?)',
        (action_type, table_name, record_key, json_data, get_pacific_time())
    )
    conn.commit()
