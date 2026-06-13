"""BestechCare AI Doctor — multilingual rule-based bot."""

from __future__ import annotations

import re
from typing import Any

from i18n import (
    Lang,
    is_language_switch_request,
    resolve_language,
    specialty_name,
    topic_name,
    t,
    voice_lang_for,
    detect_language_from_text,
    reply_in_roman_urdu,
    resolve_reply_style,
)
from knowledge import EMERGENCY_KEYWORDS, SPECIALTY_SLUGS, SYMPTOM_RULES
from text_utils import normalize_text

URDU_EXTRA_KEYWORDS: dict[str, list[str]] = {
    "headache": ["sar dard", "sir dard", "sar ma dard", "sir ma dard", "sar mein dard", "سر درد"],
    "fever": ["bukhar", "tap teek", "tap dik", "بخار"],
    "cough_cold": ["khansi", "zukam", "gala kharab", "کھانسی", "گلا"],
    "stomach": ["pet dard", "pait dard", "pet ma dard", "پیٹ", "qay", "ishal", "متلی"],
    "skin": ["khujli", "kharish", "danay", "خارش"],
    "mental": ["pareshani", "tension", "udaasi", "پریشانی"],
    "dental": ["daant", "dant", "daant dard", "دانت"],
    "urinary": ["peshab", "peshab mein", "پیشاب", "jlana"],
}

ROMAN_SYMPTOM_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    "headache": [
        re.compile(r"sar\s*(ma|me|men|main|mein|may)?\s*dard", re.I),
        re.compile(r"sir\s*(ma|me|men|main|mein|may)?\s*dard", re.I),
        re.compile(r"(sar|sir|head).{0,25}dard", re.I),
    ],
    "fever": [
        re.compile(r"\bbukhar\b", re.I),
        re.compile(r"tap\s*(teek|tik|dik)", re.I),
    ],
    "cough_cold": [
        re.compile(r"\b(khansi|zukam|zukaam)\b", re.I),
        re.compile(r"gala\s*(kharab|dard|mein)", re.I),
    ],
    "stomach": [
        re.compile(r"pet\s*(ma|me|men|main|mein|may)?\s*dard", re.I),
        re.compile(r"pait\s*(ma|me|men|main|mein|may)?\s*dard", re.I),
        re.compile(r"(pet|pait).{0,20}dard", re.I),
    ],
    "skin": [re.compile(r"\b(khujli|kharish|kharash)\b", re.I)],
    "mental": [re.compile(r"\b(pareshani|tension|udaasi|depression)\b", re.I)],
    "dental": [re.compile(r"da?ant\s*(ma|me|men|main|mein|may)?\s*dard", re.I)],
    "urinary": [re.compile(r"peshab\s*(mein|ma|me)?\s*(dard|jlana|jalan)", re.I)],
}

ENGLISH_SYMPTOM_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    "headache": [
        re.compile(r"head\s*ache", re.I),
        re.compile(r"head\s*pain", re.I),
        re.compile(r"pain\s+(in\s+)?(my\s+)?head", re.I),
        re.compile(r"(my\s+)?head\s+(hurts|hurting|aches|aching|painful)", re.I),
        re.compile(r"migraine", re.I),
    ],
    "fever": [
        re.compile(r"\bfever\b", re.I),
        re.compile(r"high\s*temp", re.I),
        re.compile(r"\btemperature\b", re.I),
        re.compile(r"feeling\s+(hot|warm)", re.I),
        re.compile(r"body\s*ache", re.I),
    ],
    "cough_cold": [
        re.compile(r"\bcough", re.I),
        re.compile(r"runny\s+nose", re.I),
        re.compile(r"sore\s+throat", re.I),
        re.compile(r"\b(cold|flu)\b", re.I),
        re.compile(r"congestion", re.I),
    ],
    "stomach": [
        re.compile(r"stomach\s*(pain|ache|hurts|hurting)", re.I),
        re.compile(r"abdominal\s*pain", re.I),
        re.compile(r"pain\s+(in\s+)?(my\s+)?(stomach|belly|abdomen|tummy)", re.I),
        re.compile(r"\b(nausea|vomit|vomiting|diarrhea|diarrhoea|indigestion|heartburn|acidity)\b", re.I),
    ],
    "skin": [
        re.compile(r"\b(rash|itching|itchy|hives|eczema|acne)\b", re.I),
    ],
    "mental": [
        re.compile(r"\b(anxiety|depression|stress|panic|insomnia|cannot sleep)\b", re.I),
    ],
    "dental": [
        re.compile(r"tooth\s*(pain|ache|hurts)", re.I),
        re.compile(r"dental\s*pain", re.I),
        re.compile(r"teeth\s*(pain|hurt)", re.I),
    ],
    "urinary": [
        re.compile(r"urin(ary|e)\s*(pain|problem|infection)", re.I),
        re.compile(r"burning\s+(when\s+)?(i\s+)?(urinate|pee)", re.I),
        re.compile(r"frequent\s+urination", re.I),
    ],
}

PAIN_WORDS_RE = re.compile(
    r"\b(pain|hurt|ache|aches|aching|hurts|hurting|sore|painful)\b", re.I
)

BODY_PART_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(head|skull|forehead|temples?)\b", re.I), "headache"),
    (re.compile(r"\b(stomach|belly|abdomen|tummy|gut)\b", re.I), "stomach"),
    (re.compile(r"\b(tooth|teeth|dental|gum)\b", re.I), "dental"),
    (re.compile(r"\b(skin|rash|itch)\b", re.I), "skin"),
    (re.compile(r"\b(chest|cough|throat|nose)\b", re.I), "cough_cold"),
    (re.compile(r"\b(urin|pee|bladder|kidney)\b", re.I), "urinary"),
    (re.compile(r"\b(fever|temp|chills)\b", re.I), "fever"),
]

ROMAN_FOLLOWUP_MARKERS: dict[tuple[str, str], list[str]] = {
    ("headache", "duration"): ["din se", " se ", "ho rha", "ho rhi", "ho raha", "ghante", "since", "started", "kal se"],
    ("headache", "severity"): ["1 se 10", "1-10", "shadeed", "halka", "severe", "mild", "scale", "out of 10"],
    ("headache", "fever"): ["bukhar", "fever", "gardan", "neck"],
    ("headache", "vision"): ["nazar", "vision", "roshni", "mutli", "nausea"],
    ("fever", "duration"): ["din se", " se ", "ho rha", "kal se", "since", "days"],
    ("fever", "temperature"): ["degree", "102", "103", "104", "celsius", "tap", "temp"],
    ("fever", "other"): ["khansi", "gala", "jism", "kharish", "cough", "rash"],
    ("cough_cold", "duration"): ["din se", " se ", "ho rha", "since"],
    ("cough_cold", "type"): ["khushk", "dry", "balgham", "phlegm"],
    ("cough_cold", "breathing"): ["saans", "breath", "ghonghat"],
    ("stomach", "duration"): ["din se", " se ", "ho rha", "since"],
    ("stomach", "location"): ["opar", "neeche", "upar", "upper", "lower"],
    ("stomach", "severity"): ["qay", "vomit", "isha", "diarrhea", "ulti"],
}

ROMAN_URDU_QUESTIONS: dict[str, dict[str, str]] = {
    "headache": {
        "duration": "Yeh sar dard kab se hai — ghanton, dinon ya zyada?",
        "severity": "1 se 10 tak dard kitni shadeed hai?",
        "fever": "Kya bukhar ya gardan mein akrahat bhi hai?",
        "vision": "Kya nazar mein tabdeeli, matli ya roshni se takleef hai?",
    },
    "fever": {
        "duration": "Bukhar kitne dinon se hai?",
        "temperature": "Tap ka thermometer check kiya? Kitna tha?",
        "other": "Khansi, gale mein dard, jism dard ya kharish bhi hai?",
    },
    "cough_cold": {
        "duration": "Yeh alamat kab se hain?",
        "type": "Khansi khushk hai ya balgham ke sath?",
        "breathing": "Saans lene mein mushkil ya ghonghat?",
    },
    "stomach": {
        "duration": "Pet ka masla kab se hai?",
        "location": "Dard kahan hai — upar, neeche, ya poore pet mein?",
        "severity": "Dard musalsal hai ya aata jata? Qay ya ishaal?",
    },
    "skin": {
        "duration": "Jild ka masla kab se hai?",
        "spread": "Ek jagah hai ya phail raha hai?",
        "trigger": "Kya koi naya sabun, khana ya dawa use ki?",
    },
    "mental": {
        "duration": "Kitne arsay se aisa mehsoos ho raha hai?",
        "severity": "Kaam aur neend par asar ho raha hai?",
        "safety": "Kya kabhi apne nuksan ke khayal aaye? (Aapki safety zaroori hai.)",
    },
    "dental": {
        "duration": "Daant dard kab se hai?",
        "type": "Garam/thanda khane se dard? Masoodhon mein soojan?",
    },
    "urinary": {
        "duration": "Peshab ki takleef kab se hai?",
        "symptoms": "Peshab mein khoon, bukhar ya kamar dard?",
    },
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

ROMAN_FOLLOWUPS = [
    "Barah e karam apni umar aur jins batayein.",
    "Kya aap koi dawa le rahe hain ya sugar/BP jaise masail hain?",
    "Kya aap ne kuch azma kar dekha alamat kam karne ke liye?",
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
    return normalize_text(text)


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


def _handle_no_symptoms(user_messages: list[dict], lang: Lang, *, roman: bool = False) -> str:
    last = user_messages[-1]["content"]

    if _is_greeting(last):
        return t("greeting_reply", lang, roman=roman)

    if _is_thanks(last):
        return t("thanks_reply", lang, roman=roman)

    if len(user_messages) == 1:
        return t("no_symptoms_first", lang, roman=roman)

    return t("unclear_reply", lang, roman=roman)


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


def _infer_rules_from_context(text: str) -> list[dict]:
    """Match pain + body part phrasing that keyword lists miss (e.g. 'pain in my head')."""
    normalized = _normalize(text)
    if not PAIN_WORDS_RE.search(normalized) and "fever" not in normalized and "cough" not in normalized:
        return []

    inferred: list[dict] = []
    seen: set[str] = set()
    for pattern, rule_id in BODY_PART_RULES:
        if rule_id in seen:
            continue
        if pattern.search(normalized):
            rule = next((r for r in SYMPTOM_RULES if r["id"] == rule_id), None)
            if rule:
                inferred.append(rule)
                seen.add(rule_id)
    return inferred


def _match_rules(text: str) -> list[dict]:
    normalized = _normalize(text)
    matched: list[dict] = []
    seen: set[str] = set()
    for rule in SYMPTOM_RULES:
        if rule["id"] in seen:
            continue
        keywords = list(rule["keywords"]) + URDU_EXTRA_KEYWORDS.get(rule["id"], [])
        if any(kw in normalized for kw in keywords):
            matched.append(rule)
            seen.add(rule["id"])
            continue
        for pattern in (
            ROMAN_SYMPTOM_PATTERNS.get(rule["id"], [])
            + ENGLISH_SYMPTOM_PATTERNS.get(rule["id"], [])
        ):
            if pattern.search(normalized):
                matched.append(rule)
                seen.add(rule["id"])
                break

    if not matched:
        matched = _infer_rules_from_context(text)
    return matched


def _get_question(rule_id: str, topic: str, lang: Lang, rule: dict, *, roman: bool = False) -> str | None:
    if roman and rule_id in ROMAN_URDU_QUESTIONS and topic in ROMAN_URDU_QUESTIONS[rule_id]:
        return ROMAN_URDU_QUESTIONS[rule_id][topic]
    if lang == "ur" and rule_id in URDU_QUESTIONS and topic in URDU_QUESTIONS[rule_id]:
        return URDU_QUESTIONS[rule_id][topic]
    return rule.get("questions", {}).get(topic)


def _topic_covered(full_text: str, markers: list[str], rule_id: str = "", topic: str = "") -> bool:
    normalized = _normalize(full_text)
    if any(m in normalized for m in markers):
        return True
    extra = ROMAN_FOLLOWUP_MARKERS.get((rule_id, topic), [])
    return any(m in normalized for m in extra)


def _next_question(matched_rules: list[dict], full_text: str, lang: Lang, *, roman: bool = False) -> str | None:
    for rule in matched_rules:
        for topic, markers in rule.get("follow_ups", []):
            if not _topic_covered(full_text, markers, rule["id"], topic):
                q = _get_question(rule["id"], topic, lang, rule, roman=roman)
                if q:
                    return q

    followups = ROMAN_FOLLOWUPS if roman else (URDU_FOLLOWUPS if lang == "ur" else EN_FOLLOWUPS)
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


def _merge_rules(rules: list[dict], lang: Lang, *, roman: bool = False) -> dict:
    if not rules:
        if roman:
            return {
                "conditions": [],
                "medicines": [],
                "tests": [],
                "precautions": ["Alamat par nazar rakhein"],
                "self_care": ["Aaram karein aur pani piyein", "Alamat barhein to doctor dikhayein"],
                "specialty": "general-physician",
            }
        return {
            "conditions": [],
            "medicines": [],
            "tests": [],
            "precautions": ["علامات پر نظر رکھیں"] if lang == "ur" else ["Monitor your symptoms closely"],
            "self_care": (
                ["آرام کریں اور پانی پئیں", "علامات بڑھیں تو ڈاکٹر دکھائیں"]
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


def _likelihood_label(value: str, lang: Lang, *, roman: bool = False) -> str:
    if roman:
        mapping = {"low": "kam", "moderate": "darmiyani", "high": "zyada"}
        return mapping.get(value, value)
    mapping = {"low": {"ur": "کم", "en": "low"}, "moderate": {"ur": "درمیانی", "en": "moderate"}, "high": {"ur": "زیادہ", "en": "high"}}
    return mapping.get(value, {}).get(lang, value)


def _build_guidance(matched_rules: list[dict], lang: Lang, *, roman: bool = False) -> str:
    data = _merge_rules(matched_rules, lang, roman=roman)
    lines = [t("guidance_intro", lang, roman=roman), "", t("possible_conditions", lang, roman=roman)]

    for c in data["conditions"]:
        like = _likelihood_label(c.get("likelihood", "moderate"), lang, roman=roman)
        lines.append(f"• **{c['name']}** ({like}) — {c['note']}")

    if data["medicines"]:
        lines.extend(["", t("otc_heading", lang, roman=roman)])
        for m in data["medicines"]:
            lines.append(f"• **{m['name']}** ({m['type']}): {m['usage']}. {m['precaution']}")

    if data["tests"]:
        lines.extend(["", t("tests_heading", lang, roman=roman)])
        for test in data["tests"]:
            lines.append(f"• {test}")

    if data["precautions"]:
        lines.extend(["", t("precautions_heading", lang, roman=roman)])
        for p in data["precautions"]:
            lines.append(f"• {p}")

    if data["self_care"]:
        lines.extend(["", t("self_care_heading", lang, roman=roman)])
        for s in data["self_care"]:
            lines.append(f"• {s}")

    spec = specialty_name(data["specialty"], lang, roman=roman)
    lines.extend(["", t("specialist_recommend", lang, roman=roman, specialty=spec)])
    lines.extend(["", f"⚠️ {t('disclaimer', lang, roman=roman)}"])
    lines.append(t("end_consultation_hint", lang, roman=roman))
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
    def analyze(self, messages: list[dict[str, str]]) -> dict[str, Any] | None:
        """Build context for dynamic reply (composer or LLM)."""
        lang = resolve_language(messages)
        user_messages = [m for m in messages if m.get("role") == "user"]

        if not user_messages:
            return {"kind": "opening", "lang": lang, "roman": False, "messages": messages}

        last_user = user_messages[-1]["content"]
        lang, roman = resolve_reply_style(last_user, messages)

        switch = is_language_switch_request(last_user)
        if switch:
            lang = switch
            lang, roman = resolve_reply_style(last_user, messages)
            if switch == "ur" and reply_in_roman_urdu(last_user):
                roman = True
            if not _match_rules(_all_user_text(messages)):
                return {
                    "kind": "lang_switch",
                    "lang": lang,
                    "roman": roman,
                    "last_user": last_user,
                    "messages": messages,
                }

        user_text = _all_user_text(messages)
        full_text = _all_text(messages)
        matched = _match_rules(user_text)

        emergency = _detect_emergency(user_text, lang)
        if emergency:
            return {
                "kind": "emergency",
                "lang": lang,
                "roman": roman,
                "emergency_text": emergency,
                "last_user": last_user,
                "messages": messages,
            }

        from intents import classify_intent

        intent = classify_intent(last_user, messages)
        conversational = frozenset({"identity", "greeting", "capabilities", "thanks", "goodbye", "off_topic"})

        base: dict[str, Any] = {
            "kind": "chat",
            "lang": lang,
            "roman": roman,
            "intent": intent,
            "last_user": last_user,
            "user_message_count": len(user_messages),
            "matched": matched,
            "messages": messages,
            "has_medical_intent": _has_medical_intent(last_user),
        }

        from composer import is_doctor_request, is_medicine_request

        if is_doctor_request(last_user):
            base["suggest_doctors"] = True
            if matched:
                data = _merge_rules(matched, lang, roman=roman)
                base["recommended_specialty_slug"] = data["specialty"]
                base["guidance_data"] = data
                base["topic"] = topic_name(matched[0]["id"], lang, roman=roman)
            else:
                base["recommended_specialty_slug"] = "general-physician"
            if intent in conversational:
                return base

        if intent in conversational:
            return base

        if not matched:
            return base

        medicine_request = is_medicine_request(last_user)
        question = _next_question(matched, full_text, lang, roman=roman)
        data = _merge_rules(matched, lang, roman=roman)
        base["topic"] = topic_name(matched[0]["id"], lang, roman=roman)
        base["guidance_data"] = data
        base["recommended_specialty_slug"] = data["specialty"]
        base["medicine_request"] = medicine_request
        if medicine_request or base.get("guidance_ready") or is_doctor_request(last_user):
            base["suggest_doctors"] = True

        if question and len(user_messages) <= 5 and not (medicine_request and len(user_messages) >= 4):
            base["next_question"] = question
            return base

        base["guidance_ready"] = True
        base["guidance_text"] = _build_guidance(matched, lang, roman=roman)
        return base

    def chat(self, messages: list[dict[str, str]]) -> tuple[str, Lang, bool]:
        from composer import compose_reply

        analysis = self.analyze(messages)
        if not analysis:
            return t("opening", "en"), "en", False
        reply = compose_reply(analysis)
        return reply, analysis.get("lang", "en"), analysis.get("roman", False)

    def summarize(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        lang = resolve_language(messages)
        user_messages = [m for m in messages if m.get("role") == "user"]
        last_user = user_messages[-1]["content"] if user_messages else ""
        lang, roman = resolve_reply_style(last_user, messages) if last_user else ("en", False)
        user_text = _all_user_text(messages)
        matched = _match_rules(user_text)
        data = _merge_rules(matched, lang, roman=roman)
        symptoms = _extract_symptoms(user_text, matched)
        emergency = _detect_emergency(user_text, lang)

        if roman:
            summary = (
                f"Is mashware mein mareez ne {', '.join(symptoms[:3]) or 'alamat'} bataye. "
                "Mumkin wajohat aur OTC dawain maloomati tor par batayi gain — yeh tashkhees nahin. "
                "BestechCare par qualified doctor se muaina zaroori hai."
                if matched
                else "Sehat ke masail bataye gaye. Aam rehnumai di gayi — doctor se muaina karwayen."
            )
        elif lang == "ur":
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
            "disclaimer": t("disclaimer", lang, roman=roman),
            "language": lang,
            "voice_lang": voice_lang_for(lang, roman=roman),
        }


bot = AiDoctorBot()
