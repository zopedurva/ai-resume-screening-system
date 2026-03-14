import hashlib
from database import get_connection


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(username: str, password: str):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, hash_password(password))
        )
        conn.commit()
        return True, "User registered successfully."
    except Exception as e:
        return False, f"Registration failed: {e}"
    finally:
        conn.close()


def login_user(username: str, password: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, username FROM users WHERE username = ? AND password_hash = ?",
        (username, hash_password(password))
    )
    user = cur.fetchone()
    conn.close()

    return user


def save_analysis(user_id, resume_name, job_description, match_score, keywords):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO analysis_history
        (user_id, resume_name, job_description, match_score, keywords)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, resume_name, job_description, match_score, keywords))

    conn.commit()
    conn.close()


def get_user_history(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT resume_name, match_score, keywords, created_at
        FROM analysis_history
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))

    rows = cur.fetchall()
    conn.close()

    return rows