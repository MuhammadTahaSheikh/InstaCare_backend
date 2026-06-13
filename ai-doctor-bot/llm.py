"""Optional dynamic LLM backends — Groq (free) or Ollama (local)."""

from __future__ import annotations

import os

import httpx

from i18n import Lang, resolve_language, voice_lang_for

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
USE_OLLAMA = os.getenv("AI_DOCTOR_USE_OLLAMA", "").lower() in ("1", "true", "yes")

SYSTEM_PROMPT = """You are BestechCare AI Doctor — a friendly, dynamic health assistant for users in Pakistan.

CRITICAL RULES:
- You are an AI assistant, NOT a licensed human doctor. Say this clearly if asked.
- Reply in the SAME language the patient uses (English, Urdu, Roman Urdu, Hindi).
- Answer the patient's ACTUAL question first — if they ask who you are, explain you're AI before asking about symptoms.
- Be conversational, warm, and natural — not robotic or repetitive.
- For health symptoms: ask 1-2 follow-up questions, suggest possible causes with disclaimers, OTC options available in Pakistan.
- Never give a definitive diagnosis. Always recommend seeing a real doctor for serious issues.
- Flag emergencies (chest pain, breathing difficulty, stroke) urgently.
- Keep responses concise (under 150 words unless giving a summary).
- End with a brief medical disclaimer when giving health advice."""


async def groq_available() -> bool:
    return bool(GROQ_API_KEY)


async def ollama_available() -> bool:
    if not USE_OLLAMA:
        return False
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            res = await client.get(f"{OLLAMA_URL}/api/tags")
            return res.status_code == 200
    except Exception:
        return False


async def _call_groq(messages: list[dict]) -> str | None:
    if not GROQ_API_KEY:
        return None

    chat_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in messages:
        if m["role"] in ("user", "assistant"):
            chat_messages.append({"role": m["role"], "content": m["content"]})

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            res = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": chat_messages,
                    "temperature": 0.7,
                    "max_tokens": 600,
                },
            )
            if res.status_code != 200:
                return None
            data = res.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


async def _call_ollama(messages: list[dict]) -> str | None:
    if not await ollama_available():
        return None

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
                    "system": SYSTEM_PROMPT,
                    "prompt": prompt + "\nAI Doctor:",
                    "stream": False,
                },
            )
            if res.status_code != 200:
                return None
            return res.json().get("response", "").strip() or None
    except Exception:
        return None


async def dynamic_chat(messages: list[dict]) -> tuple[str, str, Lang, str] | None:
    """Try Groq then Ollama. Returns (reply, engine, lang, voice_lang) or None."""
    lang = resolve_language(messages)

    reply = await _call_groq(messages)
    if reply:
        return reply, "groq", lang, voice_lang_for(lang)

    reply = await _call_ollama(messages)
    if reply:
        return reply, "ollama", lang, voice_lang_for(lang)

    return None


async def get_llm_status() -> dict:
    groq = await groq_available()
    ollama = await ollama_available()
    engine = "groq" if groq else "ollama" if ollama else "smart-rules"
    return {
        "groq_configured": groq,
        "ollama_available": ollama,
        "dynamic_engine": engine,
    }
