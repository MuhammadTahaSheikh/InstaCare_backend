"""BestechCare AI Doctor Bot — FastAPI microservice (no OpenAI key required)."""

from __future__ import annotations

import os
from typing import Literal

import httpx
from fastapi import FastAPI
from pydantic import BaseModel, Field

from bot import bot

app = FastAPI(title="BestechCare AI Doctor Bot", version="1.0.0")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
USE_OLLAMA = os.getenv("AI_DOCTOR_USE_OLLAMA", "").lower() in ("1", "true", "yes")


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    engine: str


class SummaryResponse(BaseModel):
    summary: str
    symptoms_discussed: list[str]
    possible_conditions: list[dict]
    medicines: list[dict]
    suggested_tests: list[str]
    precautions: list[str]
    self_care: list[str]
    urgent_care_required: bool
    urgent_care_reason: str | None
    recommended_specialty_slug: str
    disclaimer: str
    engine: str


async def _ollama_available() -> bool:
    if not USE_OLLAMA:
        return False
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            res = await client.get(f"{OLLAMA_URL}/api/tags")
            return res.status_code == 200
    except Exception:
        return False


async def _ollama_chat(messages: list[dict]) -> str | None:
    if not await _ollama_available():
        return None

    system = (
        "You are BestechCare AI Doctor for users in Pakistan. "
        "Give informational health guidance only, not diagnoses. "
        "Include disclaimers. Flag emergencies. Be concise."
    )
    prompt = "\n".join(
        f"{'Patient' if m['role'] == 'user' else 'AI Doctor'}: {m['content']}"
        for m in messages
        if m["role"] in ("user", "assistant")
    )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            res = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "system": system,
                    "prompt": prompt + "\nAI Doctor:",
                    "stream": False,
                },
            )
            if res.status_code != 200:
                return None
            return res.json().get("response", "").strip() or None
    except Exception:
        return None


@app.get("/health")
async def health():
    ollama = await _ollama_available()
    return {
        "status": "ok",
        "engine": "ollama" if ollama else "python-rules",
        "ollama_enabled": USE_OLLAMA,
        "ollama_available": ollama,
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    payload = [m.model_dump() for m in req.messages]

    ollama_reply = await _ollama_chat(payload)
    if ollama_reply:
        return ChatResponse(reply=ollama_reply, engine="ollama")

    reply = bot.chat(payload)
    return ChatResponse(reply=reply, engine="python-rules")


@app.post("/summary", response_model=SummaryResponse)
async def summary(req: ChatRequest):
    payload = [m.model_dump() for m in req.messages]
    result = bot.summarize(payload)
    result["engine"] = "python-rules"
    return SummaryResponse(**result)


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("AI_DOCTOR_BOT_PORT", "5003"))
    uvicorn.run("app:app", host="127.0.0.1", port=port, reload=False)
