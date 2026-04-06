"""
agent_server.py — thin HTTP wrapper around agent.py
Run with:  python agent_server.py
Listens on http://localhost:8001
"""
import uuid
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import chat          # import the agentic loop

app = FastAPI(title="Calendar Agent Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store  {session_id: [history]}
sessions: dict[str, list[dict]] = {}


from typing import Optional

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str


@app.post("/chat", response_model=ChatResponse)
async def handle_chat(req: ChatRequest):
    sid = req.session_id or str(uuid.uuid4())
    history = sessions.get(sid, [])

    reply, updated_history = chat(history, req.message)
    sessions[sid] = updated_history

    return ChatResponse(session_id=sid, reply=reply)


@app.delete("/chat/{session_id}")
async def clear_session(session_id: str):
    sessions.pop(session_id, None)
    return {"cleared": session_id}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)