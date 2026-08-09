import sqlite3
from datetime import datetime, timezone
from pathlib import Path


# Store memory.db inside the backend folder
DB_PATH = Path(__file__).resolve().parent.parent / "memory.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    conn = get_connection()

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            language_preference TEXT,
            schemes_checked TEXT,
            eligibility_answers TEXT,
            last_interaction TEXT
        )
        """
    )

    conn.commit()
    conn.close()


def get_user(user_id: str):
    conn = get_connection()

    cursor = conn.execute(
        "SELECT * FROM users WHERE user_id = ?",
        (user_id,),
    )

    user = cursor.fetchone()
    conn.close()

    if user is None:
        return None

    return dict(user)


def save_user(
    user_id: str,
    name: str,
    language_preference: str = "",
    schemes_checked: str = "",
    eligibility_answers: str = "",
):
    conn = get_connection()

    last_interaction = datetime.now(timezone.utc).isoformat()

    conn.execute(
        """
        INSERT INTO users (
            user_id,
            name,
            language_preference,
            schemes_checked,
            eligibility_answers,
            last_interaction
        )
        VALUES (?, ?, ?, ?, ?, ?)

        ON CONFLICT(user_id) DO UPDATE SET
            name = excluded.name,
            language_preference = excluded.language_preference,
            schemes_checked = excluded.schemes_checked,
            eligibility_answers = excluded.eligibility_answers,
            last_interaction = excluded.last_interaction
        """,
        (
            user_id,
            name,
            language_preference,
            schemes_checked,
            eligibility_answers,
            last_interaction,
        ),
    )

    conn.commit()
    conn.close()


# Create the database table when this module is imported.
init_database()