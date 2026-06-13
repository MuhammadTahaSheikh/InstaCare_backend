"""BestechCare AI Doctor — multilingual rule-based bot."""

from __future__ import annotations

import re
from typing import Any

from i18n import (
    Lang,
    is_language_switch_request,
    resolve_language,
    specialty_name,
    t,
    voice_lang_for,
    detect_language_from_text,
)
from knowledge import EMERGENCY_KEYWORDS, SPECIALTY_SLUGS, SYMPTOM_RULES

URDU_EXTRA_KEYWORDS: dict[str, list[str]] = {
    "headache": ["sar dard", "sir dard", "سر درد"],
    "fever": ["bukhar", "بخار", "tap dik"],
    "cough_cold": ["khansi", "zukam", "کھانسی", "گلا"],
    "stomach": ["pet dard", "پیٹ", "qay", "ishal", "متلی"],
    "skin": ["khujli", "خارش", "danay"],
    "mental": ["pareshani", "tension", "udaasi", "پریشانی"],
    "dental": ["daant", "dant", "دانت"],
    "urinary": ["peshab", "پیشاب", "jlana"],
}

URDU_QUESTIONS: dict[str, dict[str, str]] = {
    "headache": {
        "duration": "یہ سر درد کب سے ہے — گھنٹوں، دنوں یا زیادہ؟",
        "severity": "1 سے 10 تک درد کتنی شدید ہے؟",
        "fever": "کیا بخار یا گردن میں اکڑاہٹ بھی ہے؟",
        "vision": "کیا نظر میں تبدیلی، متلی یا روشنی سے تکلیف ہے؟",
    },
    "fever": {
        "duration": "بخار کتنے دنوں سے ہے؟",
        "temperature": "درجہ حرارت ناپا؟ کتنا تھا؟",
        "other": "کھانسی، گلے میں درد، جسم درد یا خارش بھی ہے؟",
    },
    "cough_cold": {
        "duration": "یہ علامات کب سے ہیں؟",
        "type": "کھانسی خشک ہے یا بلغم کے ساتھ؟",
        "breathing": "سانس لینے میں مشکل یا گھونگھٹ؟",
    },
    "stomach": {
        "duration": "پیٹ کا مسئلہ کب سے؟",
        "location": "درد کہاں ہے — اوپر، نیچے، یا پورے پیٹ میں؟",
        "severity": "درد مسلسل ہے یا آتا جاتا؟ قے یا اسہال؟",
    },
    "skin": {
        "duration": "جلد کا مسئلہ کب سے؟",
        "spread": "ایک جگہ ہے یا پھیل رہا ہے؟",
        "trigger": "کیا کوئی نیا sabun, khana ya dawa use ki?",
    },
    "mental": {
        "duration": "کتنے عرصے سے ایسا محسوس ہو رہا ہے؟",
        "severity": "کam aur neend par asar ho raha hai?",
        "safety": "کya kabhi apne nuksan ke khayal aaye? (Aapki safety zaroori hai.)",
    },
    "dental": {
        "duration": "دانت درد کب سے؟",
        "type": "گرم/ٹھنڈا کھانے سے درد؟ مسوڑھوں میں سوجن؟",
    },
    "urinary": {
        "duration": "پیشاب کی تکلیف کب سے؟",
        "symptoms": "پیشاب میں خون، بخار یا کمر درد؟",
    },
}

URDU_EMERGENCY = [
    ("seene mein dard", "سینے میں درد — فوراً ایمرجنسی جانیں۔"),
    ("saans nahi", "سانس کی شدید تکلیف — فوراً ایمرجنسی۔"),
    ("khoon", "شدید خون بہنا — فوراً ایمرجنسی۔"),
    ("behosh", "بے ہوشی — فوراً ایمرجنسی کال کریں۔"),
]

URDU_FOLLOWUPS = [
    "براہ کرم اپنی عمر اور جنس بتائیں۔",
    "کya aap koi dawa le rahe hain ya sugar/BP jaise masail hain?",
    "Kya aap ne kuch azma kar dekha symptom kam karne ke liye?",
]

EN_FOLLOWUPS = [
    "Could you tell me your age and gender?",
    "Are you taking any medications or do you have chronic conditions?",
    "Have you tried anything to relieve the symptoms?",
]

TOPIC_NAMES = {
    "headache": {"en": "headache", "ur": "سر درد", "hi": "सिरदर्द", "ar": "صداع"},
    "fever": {"en": "fever", "ur": "بخار", "hi": "बुखार", "ar": "حمى"},
    "cough_cold": {"en": "cold/cough", "ur": "زکام/کھانسی", "hi": "खांसी", "ar": "سعال"},
    "stomach": {"en": "stomach issues", "ur": "پیٹ کا مسئلہ", "hi": "पेट", "ar": "معدة"},
    "skin": {"en": "skin issues", "ur": "جلد کا مسئلہ", "hi": "त्वचा", "ar": "جلد"},
    "mental": {"en": "mental health", "ur": "ذہنی صحت", "hi": "मानसिक", "ar": "نفسية"},
    "dental": {"en": "dental pain", "ur": "دانت درد", "hi": "दांत", "ar": "أسنان"},
    "urinary": {"en": "urinary symptoms", "ur": "پیشاب کی تکلیف", "hi": "पेशाब", "ar": "بول"},
}

GREETING_RE = re.compile(
    r"(hello|hi\b|hey\b|salam|assalam|adaab|good morning|good evening|good afternoon|"
    r"how are you|how r u|kaise ho|kya hal|kaisa hai|آپ کیسے|کیسے ہو|ہیلو|السلام|سلام)",
    re.I,
)

THANKS_RE = re.compile(
    r"(thank you|thanks|shukriya|shukria|جزاک|شکریہ|dhanyavad|شكر)",
    re.I,
)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def _is_greeting(text: str) -> bool:
    normalized = _normalize(text)
    if GREETING_RE.search(normalized):
        return True
    # Short messages that are only greetings
    words = normalized.split()
    if len(words) <= 5 and any(w in normalized for w in ["hello", "hi", "hey", "salam", "کیسے", "ہیلو"]):
        return True
    return False


def _is_thanks(text: str) -> bool:
    return bool(THANKS_RE.search(text))


def _has_medical_intent(text: str) -> bool:
    """True if message likely describes a health concern, not just chitchat."""
    if _match_rules(text):
        return True
    medical_words = [
        "pain", "hurt", "ache", "fever", "cough", "vomit", "nausea", "rash", "symptom",
        "dard", "bukhar", "khansi", "takleef", "beemar", "medicine", "doctor", "sick",
        "ill", "problem", "issue", "feel", "swelling", "bleeding", "infection",
        "bukhar", "sar", "pet", "pait", "تکلیف", "درد", "بخار", "علامات",
    ]
    normalized = _normalize(text)
    return any(w in normalized for w in medical_words)


def _handle_no_symptoms(user_messages: list[dict], lang: Lang) -> str:
    last = user_messages[-1]["content"]

    if _is_greeting(last):
        return t("greeting_reply", lang)

    if _is_thanks(last):
        return t("thanks_reply", lang)

    if len(user_messages) == 1:
        return t("no_symptoms_first", lang)

    return t("unclear_reply", lang)


def _all_user_text(messages: list[dict]) -> str:
    return " ".join(m["content"] for m in messages if m.get("role") == "user")


def _all_text(messages: list[dict]) -> str:
    return " ".join(m["content"] for m in messages)


def _detect_emergency(text: str, lang: Lang) -> str | None:
    normalized = _normalize(text)
    for keyword, message in EMERGENCY_KEYWORDS:
        if keyword in normalized:
            if lang == "ur":
                return URDU_EMERGENCY[0][1] if "chest" in keyword or "breath" in keyword else message
            return message
    for keyword, urdu_msg in URDU_EMERGENCY:
        if keyword in normalized:
            return urdu_msg
    return None


def _match_rules(text: str) -> list[dict]:
    normalized = _normalize(text)
    matched = []
    for rule in SYMPTOM_RULES:
        keywords = list(rule["keywords"]) + URDU_EXTRA_KEYWORDS.get(rule["id"], [])
        if any(kw in normalized for kw in keywords):
            matched.append(rule)
    return matched


def _get_question(rule_id: str, topic: str, lang: Lang, rule: dict) -> str | None:
    if lang == "ur" and rule_id in URDU_QUESTIONS and topic in URDU_QUESTIONS[rule_id]:
        return URDU_QUESTIONS[rule_id][topic]
    return rule.get("questions", {}).get(topic)


def _topic_covered(full_text: str, markers: list[str]) -> bool:
    return any(m in _normalize(full_text) for m in markers)


def _next_question(matched_rules: list[dict], full_text: str, lang: Lang) -> str | None:
    for rule in matched_rules:
        for topic, markers in rule.get("follow_ups", []):
            if not _topic_covered(full_text, markers):
                q = _get_question(rule["id"], topic, lang, rule)
                if q:
                    return q

    followups = URDU_FOLLOWUPS if lang == "ur" else EN_FOLLOWUPS
    asked = 0
    normalized = _normalize(full_text)
    if any(m in normalized for m in ["age", "umar", "saal", "years old", "male", "female", "jins"]):
        asked += 1
    if any(m in normalized for m in ["medication", "dawa", "dawai", "diabetes", "sugar", "bp", "chronic"]):
        asked += 1
    if any(m in normalized for m in ["tried", "azma", "koshish", "panadol", "already", "liya"]):
        asked += 1

    if asked < len(followups):
        return followups[asked]
    return None


def _merge_rules(rules: list[dict], lang: Lang) -> dict:
    if not rules:
        return {
            "conditions": [],
            "medicines": [],
            "tests": [],
            "precautions": ["علامات پر نظر رکھیں"] if lang == "ur" else ["Monitor your symptoms closely"],
            "self_care": (
                ["آرام کریں اور پani پئیں", "علامات بڑھیں تو ڈاکٹر دکھائیں"]
                if lang == "ur"
                else ["Rest and stay hydrated", "See a doctor if symptoms worsen"]
            ),
            "specialty": "general-physician",
        }

    primary = rules[0]
    conditions = list(primary.get("conditions", []))
    medicines = list(primary.get("medicines", []))
    tests = list(primary.get("tests", []))
    precautions = list(primary.get("precautions", []))
    self_care = list(primary.get("self_care", []))
    specialty = primary.get("specialty", "general-physician")

    for extra in rules[1:]:
        conditions.extend(extra.get("conditions", []))
        medicines.extend(extra.get("medicines", []))
        tests.extend(extra.get("tests", []))
        precautions.extend(extra.get("precautions", []))
        self_care.extend(extra.get("self_care", []))

    return {
        "conditions": conditions[:4],
        "medicines": medicines[:4],
        "tests": list(dict.fromkeys(tests))[:5],
        "precautions": list(dict.fromkeys(precautions))[:5],
        "self_care": list(dict.fromkeys(self_care))[:5],
        "specialty": specialty if specialty in SPECIALTY_SLUGS else "general-physician",
    }


def _likelihood_label(value: str, lang: Lang) -> str:
    mapping = {"low": {"ur": "کم", "en": "low"}, "moderate": {"ur": "درمیانی", "en": "moderate"}, "high": {"ur": "زیادہ", "en": "high"}}
    return mapping.get(value, {}).get(lang, value)


def _build_guidance(matched_rules: list[dict], lang: Lang) -> str:
    data = _merge_rules(matched_rules, lang)
    lines = [t("guidance_intro", lang), "", t("possible_conditions", lang)]

    for c in data["conditions"]:
        like = _likelihood_label(c.get("likelihood", "moderate"), lang)
        lines.append(f"• **{c['name']}** ({like}) — {c['note']}")

    if data["medicines"]:
        lines.extend(["", t("otc_heading", lang)])
        for m in data["medicines"]:
            lines.append(f"• **{m['name']}** ({m['type']}): {m['usage']}. {m['precaution']}")

    if data["tests"]:
        lines.extend(["", t("tests_heading", lang)])
        for test in data["tests"]:
            lines.append(f"• {test}")

    if data["precautions"]:
        lines.extend(["", t("precautions_heading", lang)])
        for p in data["precautions"]:
            lines.append(f"• {p}")

    if data["self_care"]:
        lines.extend(["", t("self_care_heading", lang)])
        for s in data["self_care"]:
            lines.append(f"• {s}")

    spec = specialty_name(data["specialty"], lang)
    lines.extend(["", t("specialist_recommend", lang, specialty=spec)])
    lines.extend(["", f"⚠️ {t('disclaimer', lang)}"])
    lines.append(t("end_consultation_hint", lang))
    return "\n".join(lines)


def _extract_symptoms(user_text: str, matched_rules: list[dict]) -> list[str]:
    symptoms = []
    normalized = _normalize(user_text)
    for rule in matched_rules:
        keywords = list(rule["keywords"]) + URDU_EXTRA_KEYWORDS.get(rule["id"], [])
        for kw in keywords:
            if kw in normalized and kw not in symptoms:
                symptoms.append(kw)
    if not symptoms and user_text.strip():
        symptoms.append(user_text.strip().split(".")[0][:80])
    return symptoms[:6]


class AiDoctorBot:
    def chat(self, messages: list[dict[str, str]]) -> tuple[str, Lang]:
        lang = resolve_language(messages)
        user_messages = [m for m in messages if m.get("role") == "user"]

        if not user_messages:
            return t("opening", lang), lang

        last_user = user_messages[-1]["content"]
        lang = detect_language_from_text(last_user) or resolve_language(messages)

        switch = is_language_switch_request(last_user)
        if switch:
            lang = switch
            if not _match_rules(_all_user_text(messages)):
                return t("lang_switched", lang), lang

        user_text = _all_user_text(messages)
        full_text = _all_text(messages)

        emergency = _detect_emergency(user_text, lang)
        if emergency:
            return (
                f"{t('emergency_header', lang)}\n\n{emergency}\n\n"
                f"{t('emergency_footer', lang)}\n\n{t('disclaimer', lang)}"
            ), lang

        matched = _match_rules(user_text)
        if not matched:
            body = _handle_no_symptoms(user_messages, lang)
            return f"{body}\n\n⚠️ {t('disclaimer', lang)}", lang

        question = _next_question(matched, full_text, lang)
        if question and len(user_messages) <= 3:
            topic = TOPIC_NAMES.get(matched[0]["id"], {}).get(lang, matched[0]["id"])
            prefix = t("prefix_symptom", lang, topic=topic) if len(user_messages) == 1 else t("prefix_see", lang)
            return f"{prefix}{question}\n\n⚠️ {t('disclaimer', lang)}", lang

        return _build_guidance(matched, lang), lang

    def summarize(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        lang = resolve_language(messages)
        user_text = _all_user_text(messages)
        matched = _match_rules(user_text)
        data = _merge_rules(matched, lang)
        symptoms = _extract_symptoms(user_text, matched)
        emergency = _detect_emergency(user_text, lang)

        if lang == "ur":
            summary = (
                f"اس مشاورت میں مریض نے {', '.join(symptoms[:3]) or 'علامات'} بیان کیں۔ "
                "ممکنہ وجوہات اور OTC دوائیں معلوماتی طور پر بتائی گئیں — یہ تشخیص نہیں۔ "
                "BestechCare پر qualified doctor سے معائنہ ضروری ہے۔"
                if matched
                else "صحت کے مسائل بیان کیے گئے۔ عمومی رہنمائی دی گئی — ڈاکٹر سے معائنہ کروائیں۔"
            )
        else:
            summary = (
                f"Symptoms discussed: {', '.join(symptoms[:3])}. Informational guidance only — not a diagnosis. "
                "See a qualified doctor on BestechCare."
                if matched
                else "Health concerns discussed. General guidance provided. Professional evaluation recommended."
            )

        return {
            "summary": summary,
            "symptoms_discussed": symptoms,
            "possible_conditions": data["conditions"],
            "medicines": data["medicines"],
            "suggested_tests": data["tests"],
            "precautions": data["precautions"],
            "self_care": data["self_care"],
            "urgent_care_required": bool(emergency),
            "urgent_care_reason": emergency,
            "recommended_specialty_slug": data["specialty"],
            "disclaimer": t("disclaimer", lang),
            "language": lang,
            "voice_lang": voice_lang_for(lang),
        }


bot = AiDoctorBot()
