"""Dynamic, context-aware reply composer — responds to what the user actually said."""

from __future__ import annotations

import re
from typing import Any

from i18n import Lang, t, voice_lang_for

MEDICINE_ASK_RE = re.compile(
    r"(suggest|recommend|give|tell|prescribe).{0,40}(medicine|medic|medication|dawai|tablet|pill|syrup)|"
    r"(any|koi|some)\s+(medicine|dawai|medic|medication)|"
    r"(medicine|dawai|medication)\s+(please|suggest|recommend|chahiye|dedo|batao|bata)",
    re.I,
)

DOCTOR_ASK_RE = re.compile(
    r"(which|what|recommend|suggest|find|need|book|see|consult|tell|give|list|share|name).{0,50}(doctor|dr\b|specialist|physician|doctors)|"
    r"(doctor|dr\b|specialist|physician|doctors).{0,40}(help|recommend|suggest|book|consult|for me|name|names|list|in |at |lahore|karachi|islamabad|rawalpindi|multan|faisalabad|peshawar)|"
    r"(name|names).{0,30}(doctor|dr\b|specialist|doctors)|"
    r"your doctor|"
    r"bestech\s*care|bestechcare|"
    r"on (the )?platform|"
    r"who should i see|"
    r"konsa doctor|kaun sa doctor|doctor batao|doctor suggest|doctor ka naam|doctor ke naam",
    re.I,
)


def is_medicine_request(text: str) -> bool:
    return bool(MEDICINE_ASK_RE.search(text or ""))


def is_doctor_request(text: str) -> bool:
    return bool(DOCTOR_ASK_RE.search(text or ""))


def compose_reply(analysis: dict[str, Any]) -> str:
    kind = analysis.get("kind", "chat")
    if kind == "opening":
        return _opening(analysis)
    if kind == "emergency":
        return _emergency(analysis)
    if kind == "lang_switch":
        return f"{t('lang_switched', analysis['lang'], roman=analysis['roman'])}\n\n⚠️ {_disclaimer(analysis)}"

    intent = analysis.get("intent", "unclear")
    if intent == "greeting":
        return _greeting(analysis)
    if intent == "identity":
        return _identity(analysis)
    if intent == "thanks":
        return _thanks(analysis)
    if intent == "goodbye":
        return _goodbye(analysis)
    if intent == "capabilities":
        return _capabilities(analysis)
    if intent == "off_topic":
        return _off_topic(analysis)
    if analysis.get("medicine_request") and analysis.get("guidance_ready"):
        return _medicine_guidance(analysis)
    if analysis.get("medicine_request") and analysis.get("next_question"):
        return _medicine_partial(analysis)
    if analysis.get("suggest_doctors") and not analysis.get("guidance_ready"):
        return _doctor_platform(analysis)
    if analysis.get("guidance_ready"):
        return _guidance(analysis)
    if analysis.get("next_question"):
        return _symptom_followup(analysis)
    if intent == "medical" or analysis.get("has_medical_intent"):
        return _ask_symptoms(analysis)
    return _unclear(analysis)


def _disclaimer(analysis: dict[str, Any]) -> str:
    return t("disclaimer", analysis["lang"], roman=analysis["roman"])


def _opening(analysis: dict[str, Any]) -> str:
    from i18n import opening_message

    gender = analysis.get("doctor_gender", "male")
    if analysis.get("roman"):
        return opening_message("ur", roman=True, gender=gender)
    return opening_message(analysis.get("lang", "en"), gender=gender)


def _emergency(analysis: dict[str, Any]) -> str:
    lang, roman = analysis["lang"], analysis["roman"]
    return (
        f"{t('emergency_header', lang, roman=roman)}\n\n{analysis['emergency_text']}\n\n"
        f"{t('emergency_footer', lang, roman=roman)}\n\n{_disclaimer(analysis)}"
    )


def _pick(options: list[str], seed: str) -> str:
    if not options:
        return ""
    return options[abs(hash(seed)) % len(options)]


def _greeting(analysis: dict[str, Any]) -> str:
    msg = analysis["last_user"].lower()
    roman = analysis["roman"]
    lang = analysis["lang"]

    if roman:
        if "salam" in msg or "assalam" in msg:
            opener = _pick(
                ["Walaikum assalam!", "Assalam o alaikum! Khair mubarak."],
                msg,
            )
        elif any(w in msg for w in ("kase", "kaise", "kese", "kesa", "kaisa")):
            opener = _pick(
                [
                    "Alhamdulillah, main bilkul theek hoon!",
                    "Shukriya poochhne ka — main khairyat se hoon!",
                    "Ji, main theek hoon — aap ka khayal rakhnay ka shukriya!",
                ],
                msg,
            )
        else:
            opener = _pick(["Main theek hoon!", "Alhamdulillah, sab theek hai!"], msg)

        body = _pick(
            [
                f"{opener} Aap sunao, aap kaise hain?\n\nMain BestechCare ka AI Doctor hoon — agar bukhar, sar dard, khansi ya koi aur alamat ho to seedha bata dein.",
                f"{opener} Aap kaise hain? Main yahan aap ki sehat mein madad ke liye hoon — jo bhi masla ho, araam se likh dein.",
            ],
            msg + "g",
        )
    elif lang == "ur":
        body = t("greeting_reply", "ur", roman=False)
    else:
        body = _pick(
            [
                "I'm doing well, thank you for asking! I'm your BestechCare AI Doctor assistant.\n\nWhat health concern or symptoms would you like to discuss today?",
                "Hello! I'm here and ready to help. Tell me what's bothering you — headache, fever, stomach pain, or anything else.",
            ],
            msg,
        )

    return f"{body}\n\n⚠️ {_disclaimer(analysis)}"


def _identity(analysis: dict[str, Any]) -> str:
    msg = analysis["last_user"].lower()
    roman = analysis["roman"]
    lang = analysis["lang"]

    if roman:
        if "doctor" in msg and ("ai" in msg or "bot" in msg or "real" in msg):
            body = (
                "Acha sawal! Seedhi baat: main **AI health assistant** hoon — BestechCare ka bot, "
                "insaan doctor nahin. Lekin main aap ki alamat samajh kar rehnumai de sakta hoon "
                "(OTC dawain, ehtiyat, kab doctor dikhana hai).\n\n"
                "Ab batayein — aap ko kya takleef hai?"
            )
        else:
            body = (
                "Main **BestechCare AI Doctor** hoon — aap ka digital sehat ka madadgar. "
                "Main AI hoon, licensed doctor nahin, lekin symptoms par maloomati rehnumai de sakta hoon.\n\n"
                "Aap ko kya masla hai?"
            )
    elif lang == "ur":
        from intents import get_conversational_response

        conv = get_conversational_response("identity", lang, analysis.get("messages", []), roman=False)
        return conv or f"{t('unclear_reply', lang)}\n\n⚠️ {_disclaimer(analysis)}"
    else:
        body = (
            "Good question! I'm **BestechCare AI Doctor** — an **AI assistant**, not a human doctor. "
            "I can help explain symptoms and suggest next steps, but I can't replace a real doctor.\n\n"
            "What symptoms would you like to talk about?"
        )

    return f"{body}\n\n⚠️ {_disclaimer(analysis)}"


def _thanks(analysis: dict[str, Any]) -> str:
    roman = analysis["roman"]
    if roman:
        body = _pick(
            [
                "Khush amdeed! Aur kuch poochna ho to zaroor batayein.",
                "Ji, koi baat nahi! Agar aur alamat hon to likh dein.",
            ],
            analysis["last_user"],
        )
    else:
        body = t("thanks_reply", analysis["lang"], roman=roman)
    return f"{body}\n\n⚠️ {_disclaimer(analysis)}"


def _goodbye(analysis: dict[str, Any]) -> str:
    if analysis["roman"]:
        return "Khuda hafiz! Jab bhi zaroorat ho wapas aayein — main yahan hoon.\n\n⚠️ " + _disclaimer(analysis)
    return "Take care! Come back anytime you have health questions.\n\n⚠️ " + _disclaimer(analysis)


def _capabilities(analysis: dict[str, Any]) -> str:
    roman = analysis["roman"]
    lang = analysis["lang"]
    if roman:
        body = (
            "Main yeh kar sakta hoon:\n"
            "• Aap ki alamat sun kar samajhna\n"
            "• Mumkin wajohat batana (tashkhees nahin)\n"
            "• Pakistan ki OTC dawain aur ehtiyat\n"
            "• Kab konsa specialist dikhana hai\n"
            "• Consultation ke akhir mein PDF report\n\n"
            "Bas apni takleef apni zaban mein likh dein!"
        )
    else:
        body = t("guidance_intro", lang, roman=False)  # fallback
        body = (
            "I can help with symptoms, possible causes, OTC suggestions for Pakistan, "
            "precautions, and specialist recommendations. Just describe how you feel!"
        )
    return f"{body}\n\n⚠️ {_disclaimer(analysis)}"


def _off_topic(analysis: dict[str, Any]) -> str:
    if analysis["roman"]:
        body = "Main sirf sehat ke masail mein madad karta hoon — koi alamat ya sawal ho to likh dein!"
    else:
        body = "I focus on health guidance only. Tell me your symptoms and I'll help with that."
    return f"{body}\n\n⚠️ {_disclaimer(analysis)}"


def _ask_symptoms(analysis: dict[str, Any]) -> str:
    snippet = analysis["last_user"].strip()[:100]
    roman = analysis["roman"]
    if roman:
        body = (
            f"Shukriya — aap ne likha: \"{snippet}\"\n\n"
            "Thori aur detail batayein: kab se hai, kitni shadeed hai, aur koi aur alamat?"
        )
    else:
        body = (
            f"Thanks — you mentioned: \"{snippet}\"\n\n"
            "Could you share a bit more: how long, how severe, and any other symptoms?"
        )
    return f"{body}\n\n⚠️ {_disclaimer(analysis)}"


def _symptom_followup(analysis: dict[str, Any]) -> str:
    topic = analysis.get("topic") or "symptoms"
    question = analysis["next_question"]
    snippet = analysis["last_user"].strip()[:80]
    roman = analysis["roman"]
    first = analysis.get("user_message_count", 1) == 1

    if roman:
        if first:
            ack = _pick(
                [
                    f"Samajh gaya — aap ne bataya \"{snippet}\". {topic} ki takleef hai.",
                    f"Theek hai, note kar liya: {topic}. Aap ne likha \"{snippet}\".",
                ],
                snippet,
            )
        else:
            ack = _pick(
                ["Theek hai, samajh gaya.", "Shukriya — yeh information helpful hai.", "Ji, note kar liya."],
                snippet + question,
            )
    else:
        if first:
            ack = f"I understand you're dealing with {topic}. You said: \"{snippet}\"."
        else:
            ack = _pick(["Got it, thanks for that.", "Okay, that helps.", "I see."], snippet)

    return f"{ack}\n\n{question}\n\n⚠️ {_disclaimer(analysis)}"


def _doctor_platform(analysis: dict[str, Any]) -> str:
    topic = analysis.get("topic") or analysis.get("recommended_specialty_slug", "symptoms").replace("-", " ")
    roman = analysis["roman"]
    lang = analysis["lang"]

    if roman:
        body = (
            f"Bilkul! Aap ke **{topic}** ke liye BestechCare par verified doctors hain. "
            "Neeche un ki list hai — aap seedha book kar sakte hain."
        )
    elif lang == "en":
        body = (
            f"On BestechCare we have verified **{topic}** specialists who can help with your case. "
            "Here are the best matches from our platform — you can book directly:"
        )
    else:
        body = t("specialist_recommend", lang, roman=roman, specialty=topic)

    return f"{body}\n\n⚠️ {_disclaimer(analysis)}"


def _guidance(analysis: dict[str, Any]) -> str:
    return analysis["guidance_text"]


def _medicine_guidance(analysis: dict[str, Any]) -> str:
    data = analysis.get("guidance_data") or {}
    topic = analysis.get("topic") or "symptoms"
    roman = analysis["roman"]
    meds = data.get("medicines", [])

    if roman:
        lines = [
            f"Bilkul! Aap ke **{topic}** ke liye Pakistan mein yeh bina nuskhe ki dawain "
            "aam tor par use hoti hain (sirf maloomat — tashkhees nahin):",
        ]
        closer = "Aram karein, pani piyein, aur agar alamat barhein ya 3 din se zyada hon to doctor dikhayein."
    else:
        lines = [
            f"Sure! For your **{topic}**, these OTC medicines are commonly used in Pakistan "
            "(informational only — not a diagnosis):",
        ]
        closer = "Rest, stay hydrated, and see a doctor if symptoms worsen or last more than a few days."

    for m in meds:
        lines.append(f"• **{m['name']}** ({m['type']}): {m['usage']}. {m['precaution']}")

    if data.get("precautions"):
        lines.append("")
        lines.append("**Precautions:**" if not roman else "**Ehtiyat:**")
        for p in data["precautions"][:3]:
            lines.append(f"• {p}")

    lines.extend(["", closer, "", f"⚠️ {_disclaimer(analysis)}"])
    return "\n".join(lines)


def _medicine_partial(analysis: dict[str, Any]) -> str:
    topic = analysis.get("topic") or "symptoms"
    question = analysis["next_question"]
    roman = analysis["roman"]

    if roman:
        ack = (
            f"Main dawai suggest kar sakta hoon, lekin pehle **{topic}** ke bare mein "
            f"thori aur detail chahiye taake sahi option bata sakoon:"
        )
    else:
        ack = (
            f"I can suggest medicines, but first I need a bit more about your **{topic}** "
            f"so I can recommend the right options:"
        )

    return f"{ack}\n\n{question}\n\n⚠️ {_disclaimer(analysis)}"


def _unclear(analysis: dict[str, Any]) -> str:
    roman = analysis["roman"]
    if roman:
        body = (
            "Main samajhna chahta hoon — thora aur clear batayein. "
            "Misal: \"2 din se bukhar hai\" ya \"sar mein dard hai\"."
        )
    else:
        body = t("unclear_reply", analysis["lang"], roman=roman)
    return f"{body}\n\n⚠️ {_disclaimer(analysis)}"


def voice_for_analysis(analysis: dict[str, Any]) -> str:
    return voice_lang_for(analysis["lang"], roman=analysis.get("roman", False))
