"""Optional dynamic LLM backends — Groq (free) or Ollama (local)."""

from __future__ import annotations

import os
from typing import Any

import httpx

from i18n import Lang, language_lock_instruction, reply_matches_style, resolve_reply_style, voice_lang_for

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
USE_OLLAMA = os.getenv("AI_DOCTOR_USE_OLLAMA", "").lower() in ("1", "true", "yes")

SYSTEM_PROMPT = """You are BestechCare AI Doctor — a friendly, dynamic health assistant for users in Pakistan.

CRITICAL RULES:
- You are an AI assistant, NOT a licensed human doctor. Say this clearly if asked.
- ALWAYS follow the LANGUAGE LOCK instruction — it overrides chat history language.
- Answer the patient's LATEST message first — be natural like ChatGPT.
- For health symptoms: ask 1-2 relevant follow-ups, suggest OTC options in Pakistan with disclaimers.
- Never give a definitive diagnosis. Recommend a real doctor for serious issues.
- Flag emergencies (chest pain, breathing difficulty, stroke) urgently.
- Keep responses concise (under 180 words).
- End health advice with a brief doctor disclaimer."""


def _analysis_context(analysis: dict[str, Any] | None) -> str:
    if not analysis:
        return ""
    lines = [
        "INTERNAL CONTEXT (use to inform your reply, do not repeat verbatim):",
        f"- Patient intent: {analysis.get('intent', 'unknown')}",
        f"- Latest patient message: {analysis.get('last_user', '')}",
    ]
    if analysis.get("topic"):
        lines.append(f"- Symptom topic: {analysis['topic']}")
    if analysis.get("recommended_specialty_slug"):
        lines.append(f"- Best specialty on BestechCare: {analysis['recommended_specialty_slug']}")
    if analysis.get("suggest_doctors"):
        lines.append("- Patient wants doctor recommendations from BestechCare — mention booking on BestechCare.")
    if analysis.get("next_question"):
        lines.append(f"- Useful follow-up to ask: {analysis['next_question']}")
    if analysis.get("guidance_ready"):
        lines.append("- Provide informational guidance with OTC medicines, precautions, when to see a specialist.")
    if analysis.get("kind") == "emergency":
        lines.append(f"- EMERGENCY: {analysis.get('emergency_text', '')}")
    return "\n".join(lines)


def _build_llm_messages(
    messages: list[dict],
    analysis: dict[str, Any] | None,
    lang: Lang,
    roman: bool,
) -> list[dict]:
    """Build chat messages with strict language lock on the latest turn."""
    chat_messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    context = _analysis_context(analysis)
    if context:
        chat_messages.append({"role": "system", "content": context})

    # Keep recent history only — reduces language drift from old Urdu messages
    recent = [m for m in messages if m.get("role") in ("user", "assistant")][-8:]
    chat_messages.extend({"role": m["role"], "content": m["content"]} for m in recent)

    lock = language_lock_instruction(lang, roman=roman)
    chat_messages.append({"role": "system", "content": lock})
    return chat_messages


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


async def _call_groq(
    messages: list[dict],
    analysis: dict[str, Any] | None,
    lang: Lang,
    roman: bool,
) -> str | None:
    if not GROQ_API_KEY:
        return None

    chat_messages = _build_llm_messages(messages, analysis, lang, roman)

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
                    "temperature": 0.55,
                    "max_tokens": 700,
                },
            )
            if res.status_code != 200:
                return None
            data = res.json()
            reply = data["choices"][0]["message"]["content"].strip()
            reply = sanitize_llm_reply(reply)
            if not reply_matches_style(reply, lang, roman=roman):
                return None
            return reply
    except Exception:
        return None


async def _call_ollama(
    messages: list[dict],
    analysis: dict[str, Any] | None,
    lang: Lang,
    roman: bool,
) -> str | None:
    if not await ollama_available():
        return None

    lock = language_lock_instruction(lang, roman=roman)
    context = _analysis_context(analysis)
    system = SYSTEM_PROMPT + "\n\n" + lock
    if context:
        system += "\n\n" + context

    recent = [m for m in messages if m.get("role") in ("user", "assistant")][-8:]
    prompt = "\n".join(
        f"{'Patient' if m['role'] == 'user' else 'AI Doctor'}: {m['content']}"
        for m in recent
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
            reply = res.json().get("response", "").strip() or None
            if reply and not reply_matches_style(reply, lang, roman=roman):
                return None
            return reply
    except Exception:
        return None


async def dynamic_chat(
    messages: list[dict],
    analysis: dict[str, Any] | None = None,
) -> tuple[str, str, Lang, str] | None:
    """Try Groq then Ollama. Returns (reply, engine, lang, voice_lang) or None."""
    user_messages = [m for m in messages if m.get("role") == "user"]
    last_user = user_messages[-1]["content"] if user_messages else ""
    if analysis:
        lang = analysis.get("lang", "en")
        roman = analysis.get("roman", False)
    elif last_user:
        lang, roman = resolve_reply_style(last_user, messages)
    else:
        lang, roman = "en", False

    reply = await _call_groq(messages, analysis, lang, roman)
    if reply:
        return reply, "groq", lang, voice_lang_for(lang, roman=roman)

    reply = await _call_ollama(messages, analysis, lang, roman)
    if reply:
        return reply, "ollama", lang, voice_lang_for(lang, roman=roman)

    return None


def sanitize_llm_reply(reply: str) -> str:
    """Remove leaked system instructions from model output."""
    if not reply:
        return reply
    lines = [
        line
        for line in reply.split("\n")
        if not line.strip().upper().startswith("LANGUAGE LOCK")
    ]
    return "\n".join(lines).strip()


async def get_llm_status() -> dict:
    groq = await groq_available()
    ollama = await ollama_available()
    engine = "groq" if groq else "ollama" if ollama else "dynamic-composer"
    return {
        "groq_configured": groq,
        "ollama_available": ollama,
        "dynamic_engine": engine,
    }
