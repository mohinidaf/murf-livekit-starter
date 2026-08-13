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

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS call_logs (
            call_id TEXT PRIMARY KEY,
            room_name TEXT NOT NULL,
            channel TEXT NOT NULL DEFAULT 'browser',
            started_at TEXT NOT NULL,
            ended_at TEXT,
            outcome TEXT NOT NULL DEFAULT 'failed',
            success_reason TEXT
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


# ============================================================
# CALL LOGGING
# ============================================================


def log_call_start(call_id: str, room_name: str, channel: str = "browser"):
    conn = get_connection()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO call_logs (call_id, room_name, channel, started_at, outcome)
        VALUES (?, ?, ?, ?, 'failed')
        """,
        (call_id, room_name, channel, now),
    )
    conn.commit()
    conn.close()


def log_call_end(
    call_id: str,
    outcome: str = "failed",
    success_reason: str = "",
):
    conn = get_connection()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        UPDATE call_logs
        SET ended_at = ?, outcome = ?, success_reason = ?
        WHERE call_id = ?
        """,
        (now, outcome, success_reason, call_id),
    )
    conn.commit()
    conn.close()


def get_call_stats() -> dict:
    conn = get_connection()
    row = conn.execute(
        """
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN outcome = 'success' THEN 1 ELSE 0 END) as successful,
            SUM(CASE WHEN outcome = 'failed' THEN 1 ELSE 0 END) as failed
        FROM call_logs
        """
    ).fetchone()
    conn.close()
    return {
        "total": row["total"] or 0,
        "successful": row["successful"] or 0,
        "failed": row["failed"] or 0,
    }


def get_recent_calls(limit: int = 20) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT call_id, room_name, channel, started_at, ended_at,
               outcome, success_reason
        FROM call_logs
        ORDER BY started_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
