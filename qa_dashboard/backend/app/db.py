
import sqlite3
from datetime import datetime
from pathlib import Path
import bcrypt
from typing import Optional, List, Dict

DB_PATH = Path(__file__).resolve().parent / "qa_dashboard.db"


DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_conn():
    return sqlite3.connect(str(DB_PATH), detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES, check_same_thread=False)


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS questions (
            question_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            status TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            username TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS answers (
            answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            username TEXT,
            message TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password_hash(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))

def add_user(username: str, email: str, password: str) -> Dict:
    pw_hash = hash_password(password)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)",
        (username, email, pw_hash, 0),
    )
    conn.commit()
    user_id = cur.lastrowid
    conn.close()
    return {"user_id": user_id, "username": username, "email": email, "is_admin": False}


def get_user_by_username(username: str) -> Optional[Dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id, username, email, password_hash, is_admin FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "user_id": row[0],
        "username": row[1],
        "email": row[2],
        "password_hash": row[3],
        "is_admin": bool(row[4]),
    }

def get_user_by_id(user_id: int) -> Optional[Dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id, username, email, password_hash, is_admin FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "user_id": row[0],
        "username": row[1],
        "email": row[2],
        "password_hash": row[3],
        "is_admin": bool(row[4]),
    }


def verify_user_credentials(username: str, password: str) -> Optional[Dict]:
    u = get_user_by_username(username)
    if not u:
        return None
    if verify_password_hash(password, u["password_hash"]):
        return {"user_id": u["user_id"], "username": u["username"], "email": u["email"], "is_admin": u.get("is_admin", False)}
    return None


def add_question(user_id: int, message: str) -> Dict:
    ts = datetime.utcnow().isoformat()
    user = get_user_by_id(user_id) if user_id else None
    username = user["username"] if user else "Guest"
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO questions (user_id, message, status, timestamp, username) VALUES (?, ?, ?, ?, ?)",
        (user_id or 0, message, "Pending", ts, username),
    )
    conn.commit()
    qid = cur.lastrowid
    conn.close()
    return {"question_id": qid, "user_id": user_id or 0, "message": message, "status": "Pending", "timestamp": datetime.fromisoformat(ts), "username": username}


def get_questions() -> List[Dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT question_id, user_id, message, status, timestamp, username FROM questions")
    rows = cur.fetchall()
    conn.close()
    qs = []
    for r in rows:
        q = {
            "question_id": r[0],
            "user_id": r[1],
            "message": r[2],
            "status": r[3],
            "timestamp": datetime.fromisoformat(r[4]),
            "username": r[5],
        }
        answers = get_answers_for_question(r[0])
        q["answers"] = answers
        qs.append(q)
    def sort_key(q):
        return (0 if q["status"] == "Escalated" else 1, -q["timestamp"].timestamp())
    return sorted(qs, key=sort_key)


def mark_answered(question_id: int) -> Optional[Dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE questions SET status = ? WHERE question_id = ?", ("Answered", question_id))
    conn.commit()
    cur.execute("SELECT question_id, user_id, message, status, timestamp, username FROM questions WHERE question_id = ?", (question_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "question_id": row[0],
        "user_id": row[1],
        "message": row[2],
        "status": row[3],
        "timestamp": datetime.fromisoformat(row[4]),
        "username": row[5],
    }


def escalate_question(question_id: int) -> Optional[Dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE questions SET status = ? WHERE question_id = ?", ("Escalated", question_id))
    conn.commit()
    cur.execute("SELECT question_id, user_id, message, status, timestamp, username FROM questions WHERE question_id = ?", (question_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "question_id": row[0],
        "user_id": row[1],
        "message": row[2],
        "status": row[3],
        "timestamp": datetime.fromisoformat(row[4]),
        "username": row[5],
    }


def add_answer(question_id: int, user_id: int, message: str) -> Dict:
    """
    Store an answer and return the stored answer dict.
    username can be provided (for guests or logged users).
    """
    ts = datetime.utcnow().isoformat()
    username = "Guest"
    if user_id and user_id != 0:
        u = get_user_by_id(user_id)
        if u:
            username = u["username"]
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO answers (question_id, user_id, username, message, timestamp) VALUES (?, ?, ?, ?, ?)",
        (question_id, user_id or 0, username, message, ts),
    )
    conn.commit()
    aid = cur.lastrowid
    conn.close()
    return {"answer_id": aid, "question_id": question_id, "user_id": user_id or 0, "username": username, "message": message, "timestamp": datetime.fromisoformat(ts)}


def get_answers_for_question(question_id: int) -> List[Dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT answer_id, question_id, user_id, username, message, timestamp FROM answers WHERE question_id = ? ORDER BY timestamp DESC",
        (question_id,),
    )
    rows = cur.fetchall()
    conn.close()
    answers = []
    for r in rows:
        answers.append(
            {
                "answer_id": r[0],
                "question_id": r[1],
                "user_id": r[2],
                "username": r[3],
                "message": r[4],
                "timestamp": datetime.fromisoformat(r[5]),
            }
        )
    return answers

def seed_admin_if_needed():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    cnt = cur.fetchone()[0]
    if cnt == 0:
        cur.execute(
            "INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)",
            ("admin", "admin@example.com", hash_password("Admin@123"), 1),
        )
        conn.commit()
    conn.close()

init_db()
seed_admin_if_needed()
