"""BestechCare AI Doctor Bot — FastAPI microservice."""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Literal

from bot import bot
from composer import compose_reply, voice_for_analysis
from llm import dynamic_chat, get_llm_status, sanitize_llm_reply

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
    recommended_specialty_slug: str | None = None
    suggest_doctors: bool = False


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


def _chat_meta(analysis: dict[str, Any] | None) -> dict[str, Any]:
    if not analysis:
        return {"recommended_specialty_slug": None, "suggest_doctors": False}
    slug = analysis.get("recommended_specialty_slug")
    if not slug and analysis.get("guidance_data"):
        slug = analysis["guidance_data"].get("specialty")
    if not slug and analysis.get("matched"):
        slug = analysis["matched"][0].get("specialty") or analysis["matched"][0].get("id")
    suggest = bool(analysis.get("suggest_doctors") or analysis.get("guidance_ready"))
    return {
        "recommended_specialty_slug": slug,
        "suggest_doctors": suggest and bool(slug),
    }


def _make_chat_response(reply: str, engine: str, analysis: dict[str, Any] | None) -> ChatResponse:
    meta = _chat_meta(analysis)
    lang = analysis.get("lang", "en") if analysis else "en"
    return ChatResponse(
        reply=sanitize_llm_reply(reply),
        engine=engine,
        language=lang,
        voice_lang=voice_for_analysis(analysis) if analysis else "en-US",
        recommended_specialty_slug=meta["recommended_specialty_slug"],
        suggest_doctors=meta["suggest_doctors"],
    )


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
        return _make_chat_response(compose_reply(analysis), "dynamic-composer", analysis)

    dynamic = await dynamic_chat(payload, analysis)
    if dynamic:
        reply, engine, lang, vlang = dynamic
        meta = _chat_meta(analysis)
        return ChatResponse(
            reply=sanitize_llm_reply(reply),
            engine=engine,
            language=lang,
            voice_lang=vlang,
            recommended_specialty_slug=meta["recommended_specialty_slug"],
            suggest_doctors=meta["suggest_doctors"],
        )

    if not analysis:
        return _make_chat_response(
            compose_reply({"kind": "opening", "lang": "en", "roman": False}),
            "dynamic-composer",
            {"kind": "opening", "lang": "en", "roman": False},
        )

    return _make_chat_response(compose_reply(analysis), "dynamic-composer", analysis)


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
