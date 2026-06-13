"""Optional dynamic LLM backends — Groq (free) or Ollama (local)."""

from __future__ import annotations

import os
from typing import Any

import httpx

from i18n import Lang, resolve_language, resolve_roman_urdu, voice_lang_for

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
USE_OLLAMA = os.getenv("AI_DOCTOR_USE_OLLAMA", "").lower() in ("1", "true", "yes")

SYSTEM_PROMPT = """You are BestechCare AI Doctor — a friendly, dynamic health assistant for users in Pakistan.

CRITICAL RULES:
- You are an AI assistant, NOT a licensed human doctor. Say this clearly if asked.
- Reply in the SAME language AND script the patient uses:
  * Roman Urdu (Latin letters like "kase ha ap", "mjhe sar dard") → reply in Roman Urdu only
  * Urdu script → reply in Urdu script
  * English → reply in English
- Answer the patient's ACTUAL latest message first — do not ignore greetings or identity questions.
- Be conversational, warm, and natural like ChatGPT — never robotic or copy-pasted.
- If they greet you, greet back naturally before asking about symptoms.
- For health symptoms: ask 1-2 relevant follow-ups, suggest possible causes with disclaimers, OTC options in Pakistan.
- Never give a definitive diagnosis. Recommend a real doctor for serious issues.
- Flag emergencies (chest pain, breathing difficulty, stroke) urgently.
- Keep responses concise (under 180 words unless giving a summary).
- End health advice with: always consult a qualified doctor for professional evaluation."""


def _analysis_context(analysis: dict[str, Any] | None) -> str:
    if not analysis:
        return ""
    lines = [
        "INTERNAL CONTEXT (use to inform your reply, do not repeat verbatim):",
        f"- Reply language: {'Roman Urdu (Latin script)' if analysis.get('roman') else analysis.get('lang', 'en')}",
        f"- Patient intent: {analysis.get('intent', 'unknown')}",
        f"- Latest patient message: {analysis.get('last_user', '')}",
    ]
    if analysis.get("topic"):
        lines.append(f"- Symptom topic: {analysis['topic']}")
    if analysis.get("next_question"):
        lines.append(f"- Useful follow-up to ask: {analysis['next_question']}")
    if analysis.get("guidance_ready"):
        lines.append("- Enough info collected — provide informational guidance with OTC, precautions, specialist.")
    if analysis.get("kind") == "emergency":
        lines.append(f"- EMERGENCY: {analysis.get('emergency_text', '')}")
    return "\n".join(lines)


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


async def _call_groq(messages: list[dict], analysis: dict[str, Any] | None = None) -> str | None:
    if not GROQ_API_KEY:
        return None

    context = _analysis_context(analysis)
    chat_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if context:
        chat_messages.append({"role": "system", "content": context})
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
                    "temperature": 0.75,
                    "max_tokens": 700,
                },
            )
            if res.status_code != 200:
                return None
            data = res.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


async def _call_ollama(messages: list[dict], analysis: dict[str, Any] | None = None) -> str | None:
    if not await ollama_available():
        return None

    context = _analysis_context(analysis)
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
                    "system": SYSTEM_PROMPT + ("\n\n" + context if context else ""),
                    "prompt": prompt + "\nAI Doctor:",
                    "stream": False,
                },
            )
            if res.status_code != 200:
                return None
            return res.json().get("response", "").strip() or None
    except Exception:
        return None


async def dynamic_chat(
    messages: list[dict],
    analysis: dict[str, Any] | None = None,
) -> tuple[str, str, Lang, str] | None:
    """Try Groq then Ollama. Returns (reply, engine, lang, voice_lang) or None."""
    lang = analysis.get("lang") if analysis else resolve_language(messages)
    roman = analysis.get("roman", False) if analysis else resolve_roman_urdu(messages)
    if roman:
        lang = "ur"

    reply = await _call_groq(messages, analysis)
    if reply:
        return reply, "groq", lang, voice_lang_for(lang, roman=roman)

    reply = await _call_ollama(messages, analysis)
    if reply:
        return reply, "ollama", lang, voice_lang_for(lang, roman=roman)

    return None


async def get_llm_status() -> dict:
    groq = await groq_available()
    ollama = await ollama_available()
    engine = "groq" if groq else "ollama" if ollama else "dynamic-composer"
    return {
        "groq_configured": groq,
        "ollama_available": ollama,
        "dynamic_engine": engine,
    }
