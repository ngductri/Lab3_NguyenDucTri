import os
import re
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime, timedelta
from src.agent.agent import chat
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Ensure src/ is on sys.path so we can import agent logic.
SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from agent.agent import chat  # type: ignore

# ================= CONFIG =================
PORT = 8000
SCOPES = ["https://www.googleapis.com/auth/calendar"]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")

if not os.path.exists(TOKEN_PATH):
    raise Exception("token.json not found. Run auth.py first.")

creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

# ================= GOOGLE =================
def get_calendar_service():
    if not os.path.exists(TOKEN_PATH):
        raise Exception("token.json not found. Run auth.py first.")

    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    return build("calendar", "v3", credentials=creds)

# ================= SCHEMAS =================
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class CheckReq(BaseModel):
    start_time: str
    end_time: str
    target_email: Optional[str] = None

class BookReq(BaseModel):
    start_time: str
    end_time: str
    summary: Optional[str] = "Meeting"
    target_email: Optional[str] = None


class ChatReq(BaseModel):
    session_id: Optional[str] = None
    message: str


class ChatRes(BaseModel):
    session_id: str
    reply: str

# ================= HELPERS =================

def is_valid_email(email: str) -> bool:
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None


def validate_iso(dt_str: str) -> bool:
    try:
        datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return True
    except:
        return False


def normalize_time(text: str) -> str:
    now = datetime.now()

    if "tomorrow" in text.lower():
        base = now + timedelta(days=1)

        hour = 15  # default

        if "pm" in text.lower():
            try:
                hour = int(text.split("pm")[0].split()[-1])
                if hour != 12:
                    hour += 12
            except:
                pass

        if "am" in text.lower():
            try:
                hour = int(text.split("am")[0].split()[-1])
            except:
                pass

        base = base.replace(hour=hour, minute=0, second=0, microsecond=0)
        return base.isoformat() + "+07:00"

    return text


def ensure_valid_time(start: str, end: str):
    if not validate_iso(start):
        start = normalize_time(start)

    if not validate_iso(end):
        if "hour" in end:
            start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
            end_dt = start_dt + timedelta(hours=1)
            end = end_dt.isoformat() + "+07:00"
        else:
            end = normalize_time(end)

    if not validate_iso(start) or not validate_iso(end):
        raise HTTPException(
            status_code=400,
            detail="Invalid datetime format. Must be ISO-8601.",
        )

    return start, end

# ================= ROUTES =================
@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    try:
        sid = req.session_id or "default"
        history = sessions.get(sid, [])

        reply, updated_history = chat(history, req.message)

        sessions[sid] = updated_history

        return {
            "reply": reply,
            "session_id": sid
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok"}


# ---------- CHAT ----------
# In-memory session store  {session_id: [history]}
sessions: dict[str, list[dict]] = {}


@app.post("/api/chat", response_model=ChatRes)
def chat_api(req: ChatReq):
    sid = req.session_id or str(uuid.uuid4())
    history = sessions.get(sid, [])

    reply, updated_history = chat(history, req.message)
    sessions[sid] = updated_history

    return ChatRes(session_id=sid, reply=reply)


# ---------- CHECK ----------
@app.post("/calendar/check")
def check(req: CheckReq):
    try:
        service = get_calendar_service()

        start, end = ensure_valid_time(req.start_time, req.end_time)

        emails = ["primary"]
        if req.target_email and is_valid_email(req.target_email):
            emails.append(req.target_email)

        body = {
            "timeMin": start,
            "timeMax": end,
            "items": [{"id": e} for e in emails],
        }

        result = service.freebusy().query(body=body).execute()

        for cal in result["calendars"].values():
            if cal["busy"]:
                return {"available": False}

        return {"available": True}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------- BOOK ----------
@app.post("/calendar/book")
def book(req: BookReq):
    try:
        service = get_calendar_service()

        start, end = ensure_valid_time(req.start_time, req.end_time)

        attendees = []
        if req.target_email and is_valid_email(req.target_email):
            attendees.append({"email": req.target_email})

        summary = req.summary if req.summary and req.summary != "Unspecified" else "Meeting"

        event = {
            "summary": summary,
            "start": {"dateTime": start},
            "end": {"dateTime": end},
            "attendees": attendees,
        }

        created = service.events().insert(
            calendarId="primary",
            body=event,
            sendUpdates="all"
        ).execute()

        return {
            "status": "success",
            "link": created.get("htmlLink")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ================= RUN =================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
