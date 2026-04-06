import json
import requests
from datetime import datetime, timedelta
import re

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3.2:latest"
BACKEND_URL = "http://localhost:8000"


# ─────────────────────────────────────────
# TOOLS
# ─────────────────────────────────────────
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": "Check availability using ISO datetime.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_time": {"type": "string"},
                    "end_time": {"type": "string"},
                    "target_email": {"type": "string"},
                },
                "required": ["start_time", "end_time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_meeting",
            "description": "Book meeting on calendar",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_time": {"type": "string"},
                    "end_time": {"type": "string"},
                    "target_email": {"type": "string"},
                },
                "required": ["start_time", "end_time"],
            },
        },
    },
]


# ─────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────
SYSTEM_PROMPT = f"""
You are a strict calendar scheduling agent.

RULES:
- ONLY handle scheduling tasks
- ALWAYS use tool_calls (never print JSON)
- ALWAYS call check_availability first
- If available → call book_meeting
- Use ISO format: YYYY-MM-DDTHH:MM:SS+07:00
- NEVER use 'tomorrow', etc.

Timezone: Asia/Ho_Chi_Minh
Today: {datetime.now().strftime("%Y-%m-%d")}
"""


# ─────────────────────────────────────────
# TOOL EXECUTION
# ─────────────────────────────────────────
def has_required_info(text: str) -> bool:
    text = text.lower()

    has_time = any(t in text for t in ["am", "pm", ":"])
    has_date = any(d in text for d in ["today", "tomorrow"]) or re.search(r"\d{4}-\d{2}-\d{2}", text)

    return has_time and has_date

def run_tool(name, args):
    try:
        if name == "check_availability":
            res = requests.post(f"{BACKEND_URL}/calendar/check", json=args)
            return json.dumps(res.json())

        if name == "book_meeting":
            res = requests.post(f"{BACKEND_URL}/calendar/book", json=args)
            return json.dumps(res.json())

        return json.dumps({"error": "unknown tool"})

    except Exception as e:
        return json.dumps({"error": str(e)})


# ─────────────────────────────────────────
# NORMALIZE ARGS
# ─────────────────────────────────────────
def normalize_args(args: dict) -> dict:
    if "start_date" in args and "time" in args:
        args["start_time"] = f"{args['start_date']}T{args['time']}+07:00"

    if "start_time" in args and "end_time" not in args:
        dt = datetime.fromisoformat(args["start_time"].replace("+07:00", ""))
        dt_end = dt + timedelta(hours=1)
        args["end_time"] = dt_end.isoformat() + "+07:00"

    return args


# ─────────────────────────────────────────
# DOMAIN FILTER
# ─────────────────────────────────────────
def is_calendar_request(text: str) -> bool:
    keywords = ["meeting", "schedule", "book", "calendar", "appointment"]
    return any(k in text.lower() for k in keywords)


# ─────────────────────────────────────────
# MAIN AGENT LOOP
# ─────────────────────────────────────────
def chat(history, user_input):
    # DOMAIN FILTER
    # 🚫 Missing info check

    if not is_calendar_request(user_input):
        return (
            "I can only help with calendar scheduling (meetings, bookings, availability).",
            history,
        )
    
    if not has_required_info(user_input):
        return "I need more details to schedule your meeting.", history
    

    history.append({"role": "user", "content": user_input})

    while True:
        res = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + history,
                "tools": TOOLS,
                "stream": False,
            },
        )

        msg = res.json()["message"]
        content = msg.get("content", "")

        # ❌ block fake JSON
        if re.search(r'\{\s*"name"\s*:', content):
            history.append({
                "role": "system",
                "content": "Do NOT output JSON. Use tool_calls."
            })
            continue

        # ❌ block tool mention without call
        if not msg.get("tool_calls") and "book_meeting" in content:
            history.append({
                "role": "system",
                "content": "You must call tools properly."
            })
            continue

        # ✅ normal response
        if "tool_calls" not in msg:
            history.append(msg)
            return msg.get("content", ""), history

        history.append(msg)

        last_tool = None
        last_result = None
        last_args = None

        # ── TOOL LOOP ──
        for tc in msg["tool_calls"]:
            name = tc["function"]["name"]
            args = tc["function"]["arguments"]

            if isinstance(args, str):
                args = json.loads(args)

            args = normalize_args(args)

            print(f"[tool call] {name} {args}")

            result = run_tool(name, args)
            print(f"[tool result] {result}")

            last_tool = name
            last_result = result
            last_args = args

            history.append({
                "role": "tool",
                "content": result
            })

            # ❌ if busy → stop immediately
            if name == "check_availability":
                data = json.loads(result)
                if not data.get("available"):
                    return "That time slot is not available. Please choose another time.", history

        # ── FORCE BOOKING ──
        if last_tool == "check_availability":
            data = json.loads(last_result)

            if data.get("available"):
                booking_result = run_tool("book_meeting", last_args)
                print("[FORCED BOOKING]", booking_result)

                history.append({
                    "role": "tool",
                    "content": booking_result
                })

                return "Meeting scheduled successfully 🎉", history


# ─────────────────────────────────────────
# CLI TEST
# ─────────────────────────────────────────
if __name__ == "__main__":
    history = []
    while True:
        user = input("You: ")
        if user == "exit":
            break

        reply, history = chat(history, user)
        print("Agent:", reply)