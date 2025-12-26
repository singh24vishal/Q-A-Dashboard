from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime
from .db import add_user, verify_user_credentials, add_question, get_questions, mark_answered, escalate_question, get_user_by_username, add_answer

router = APIRouter()

class RegisterIn(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)

class LoginIn(BaseModel):
    username: str
    password: str

class QuestionIn(BaseModel):
    user_id: Optional[int] = 0
    message: str = Field(..., min_length=1, max_length=500)

class QuestionOut(BaseModel):
    question_id: int
    user_id: int
    message: str
    status: str
    timestamp: str
    username: str
    answers: List[dict] = []

class LoginOut(BaseModel):
    message: str
    user_id: int
    username: str
    email: str
    is_admin: bool

class RegisterOut(BaseModel):
    message: str
    user_id: int
    username: str
    email: str
    is_admin: bool

class ValidateIn(BaseModel):
    message: str

class ValidateOut(BaseModel):
    valid: bool
    reason: str = ""

broadcast = None 

@router.post("/validate", response_model=ValidateOut)
async def validate_question(payload: ValidateIn):
    msg = (payload.message or "").strip()
    if len(msg) == 0:
        return {"valid": False, "reason": "Question cannot be blank."}
    if len(msg) > 500:
        return {"valid": False, "reason": "Question too long. Maximum 500 characters."}
    import re
    if not re.search(r"[A-Za-z0-9]", msg):
        return {"valid": False, "reason": "Question must contain letters or numbers."}
    profane_list = ["badword1", "badword2"]
    low = msg.lower()
    for bad in profane_list:
        if bad in low:
            return {"valid": False, "reason": "Please avoid profanity."}
    return {"valid": True, "reason": ""}

@router.post("/register", response_model=RegisterOut)
async def register(payload: RegisterIn):
    import re
    pw = payload.password
    pw_regex = r"^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*]).{8,}$"
    if not re.match(pw_regex, pw):
        raise HTTPException(status_code=400, detail="Password must be 8+ chars, include uppercase, number, special char.")
    if get_user_by_username(payload.username):
        raise HTTPException(status_code=400, detail="Username already exists.")
    user = add_user(payload.username, payload.email, payload.password)
    return {"message": "registered", "user_id": user["user_id"], "username": user["username"], "email": user["email"], "is_admin": user.get("is_admin", False)}


@router.post("/login", response_model=LoginOut)
async def login(payload: LoginIn):
    user = verify_user_credentials(payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"message": "ok", "user_id": user["user_id"], "username": user["username"], "email": user["email"], "is_admin": user.get("is_admin", False)}


@router.post("/submit", response_model=QuestionOut)
async def submit_question(payload: QuestionIn):
    q = add_question(payload.user_id or 0, payload.message)
    q_out = q.copy()
    q_out["timestamp"] = q_out["timestamp"].isoformat()
    if "broadcast" in globals() and callable(globals()["broadcast"]):
        try:
            await globals()["broadcast"]("new_question", q_out)
        except Exception:
            pass
    return q_out


@router.get("/questions", response_model=List[QuestionOut])
async def list_questions(
    q: Optional[str] = None,
    user: Optional[str] = None,
    status: Optional[str] = None,
    from_ts: Optional[str] = None,
    to_ts: Optional[str] = None,
):
    
    qs = get_questions() 
    filtered = []

    user_id_filter = None
    if user:
        try:
            user_id_filter = int(user)
        except Exception:
            u = get_user_by_username(user)
            if u:
                user_id_filter = u["user_id"]
            else:
                return []

    from_dt = None
    to_dt = None
    try:
        if from_ts:
            from_dt = datetime.fromisoformat(from_ts)
    except Exception:
        from_dt = None
    try:
        if to_ts:
            to_dt = datetime.fromisoformat(to_ts)
    except Exception:
        to_dt = None

    q_lower = q.lower() if q else None
    status_norm = status.lower() if status else None

    for item in qs:
        if q_lower and q_lower not in (item["message"] or "").lower():
            continue

        if user_id_filter is not None and item.get("user_id", 0) != user_id_filter:
            continue

        if status_norm and (item.get("status", "").lower() != status_norm):
            continue

        try:
            item_ts = item["timestamp"]
            if isinstance(item_ts, str):
                item_dt = datetime.fromisoformat(item_ts)
            else:
                item_dt = item_ts
        except Exception:
            item_dt = None

        if from_dt and item_dt and item_dt < from_dt:
            continue
        if to_dt and item_dt and item_dt > to_dt:
            continue

        filtered.append(item)

    qs_out = []
    for q_item in filtered:
        q2 = q_item.copy()
        if isinstance(q2["timestamp"], str):
            q2["timestamp"] = q2["timestamp"]
        else:
            q2["timestamp"] = q2["timestamp"].isoformat()
        ans_out = []
        for a in q2.get("answers", []):
            a2 = a.copy()
            a2["timestamp"] = a2["timestamp"].isoformat()
            ans_out.append(a2)
        q2["answers"] = ans_out
        qs_out.append(q2)

    return qs_out

@router.post("/mark_answered")
async def mark_question_answered(question_id: int):
    q = mark_answered(question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    q_out = q.copy()
    q_out["timestamp"] = q_out["timestamp"].isoformat()
    if "broadcast" in globals() and callable(globals()["broadcast"]):
        try:
            await globals()["broadcast"]("answered", q_out)
        except Exception:
            pass
    return {"message": "marked", "question": q_out}

@router.post("/escalate")
async def escalate(question_id: int):
    q = escalate_question(question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    q_out = q.copy()
    q_out["timestamp"] = q_out["timestamp"].isoformat()
    if "broadcast" in globals() and callable(globals()["broadcast"]):
        try:
            await globals()["broadcast"]("escalated", q_out)
        except Exception:
            pass
    return {"message": "escalated", "question": q_out}

class AnswerIn(BaseModel):
    question_id: int
    user_id: Optional[int] = 0
    message: str = Field(..., min_length=1, max_length=1000)

@router.post("/answer")
async def post_answer(payload: AnswerIn):
    ans = add_answer(payload.question_id, payload.user_id or 0, payload.message)
    updated_q = None
    qs = get_questions()
    for q in qs:
        if q["question_id"] == payload.question_id:
            updated_q = q.copy()
            updated_q["timestamp"] = updated_q["timestamp"].isoformat()
            updated_q["answers"] = [
                {**a, "timestamp": a["timestamp"].isoformat()} for a in updated_q.get("answers", [])
            ]
            break

    try:
        if "broadcast" in globals() and callable(globals()["broadcast"]):
            await globals()["broadcast"]("new_answer", updated_q or {"question_id": payload.question_id})
    except Exception:
        pass

    out = {"answer": {**ans, "timestamp": ans["timestamp"].isoformat()}, "question": updated_q}
    return out