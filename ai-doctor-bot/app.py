"""BestechCare AI Doctor Bot — FastAPI microservice."""

from __future__ import annotations

import os

from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Literal

from bot import bot
from composer import compose_reply, voice_for_analysis
from llm import dynamic_chat, get_llm_status

app = FastAPI(title="BestechCare AI Doctor Bot", version="2.0.0")


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    engine: str
    language: str = "en"
    voice_lang: str = "en-US"


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
    language: str = "en"
    voice_lang: str = "en-US"


@app.get("/health")
async def health():
    llm_status = await get_llm_status()
    return {
        "status": "ok",
        "engine": llm_status["dynamic_engine"],
        **llm_status,
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    payload = [m.model_dump() for m in req.messages]
    analysis = bot.analyze(payload)

    if analysis and analysis.get("kind") == "emergency":
        reply = compose_reply(analysis)
        return ChatResponse(
            reply=reply,
            engine="dynamic-composer",
            language=analysis["lang"],
            voice_lang=voice_for_analysis(analysis),
        )

    dynamic = await dynamic_chat(payload, analysis)
    if dynamic:
        reply, engine, lang, vlang = dynamic
        return ChatResponse(reply=reply, engine=engine, language=lang, voice_lang=vlang)

    # Groq failed or wrong language — reliable composer enforces language correctly
    if not analysis:
        return ChatResponse(
            reply=compose_reply({"kind": "opening", "lang": "en", "roman": False}),
            engine="dynamic-composer",
            language="en",
            voice_lang="en-US",
        )

    reply = compose_reply(analysis)
    return ChatResponse(
        reply=reply,
        engine="dynamic-composer",
        language=analysis.get("lang", "en"),
        voice_lang=voice_for_analysis(analysis),
    )


@app.post("/summary", response_model=SummaryResponse)
async def summary(req: ChatRequest):
    payload = [m.model_dump() for m in req.messages]
    result = bot.summarize(payload)
    result["engine"] = "smart-rules"
    return SummaryResponse(**result)


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("AI_DOCTOR_BOT_PORT", "5003"))
    uvicorn.run("app:app", host="127.0.0.1", port=port, reload=False)
