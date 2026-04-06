import os
import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

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

# ================= GOOGLE =================
def get_calendar_service():
    if not os.path.exists("token.json"):
        raise Exception("token.json not found. Run auth.py first.")

    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    return build("calendar", "v3", credentials=creds)

# ================= SCHEMAS =================
class CheckReq(BaseModel):
    start_time: str
    end_time: str
    target_email: Optional[str] = None

class BookReq(BaseModel):
    start_time: str
    end_time: str
    summary: Optional[str] = "Meeting"
    target_email: Optional[str] = None

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

@app.get("/health")
def health():
    return {"status": "ok"}


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