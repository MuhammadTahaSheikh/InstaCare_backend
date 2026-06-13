"""Language detection and multilingual strings for AI Doctor bot."""

from __future__ import annotations

import re
from typing import Literal

Lang = Literal["en", "ur", "hi", "ar"]

URDU_SCRIPT_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]")
DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")

ROMAN_URDU_MARKERS = [
    "mujhe", "mera", "meri", "aap", "ap ", " hai", "kya", "bukhar", "dard", "takleef",
    "beemar", "dawai", "ilaj", "tabiyat", "shukriya", "mein bol", "urdu mein",
    "pet dard", "sar dard", "zukam", "khansi", "bimaar", "masla",
]

LANGUAGE_SWITCH_PATTERNS: list[tuple[re.Pattern[str], Lang]] = [
    (re.compile(r"\b(urdu|اردو)\b|urdu mein|speak urdu|in urdu|urdu please|urdu main|urdu me", re.I), "ur"),
    (re.compile(r"\benglish\b|speak english|in english|english mein|english please", re.I), "en"),
    (re.compile(r"\bhindi\b|hindi mein|speak hindi|in hindi", re.I), "hi"),
    (re.compile(r"\barabic\b|speak arabic|in arabic|العربية", re.I), "ar"),
]

VOICE_LANG_MAP = {
    "en": "en-US",
    "ur": "ur-PK",
    "hi": "hi-IN",
    "ar": "ar-SA",
}

STRINGS: dict[str, dict] = {
    "disclaimer": {
        "en": "Always consult a qualified doctor for professional evaluation.",
        "ur": "ہمیشہ پیشہ ور ڈاکٹر سے مکمل معائنہ کروائیں۔",
        "hi": "पेशेवर जांच के लिए हमेशा योग्य डॉक्टर से सलाह लें।",
        "ar": "استشر دائماً طبيباً مؤهلاً للتقييم الطبي.",
    },
    "opening": {
        "en": (
            "Hello! I'm your BestechCare AI Doctor assistant. I can help you understand your symptoms "
            "and suggest next steps — but I am not a replacement for a licensed doctor.\n\n"
            "Please describe your symptoms in any language (English, Urdu, Hindi) and I'll respond in the same language."
        ),
        "ur": (
            "السلام علیکم! میں BestechCare کا AI Doctor ہوں۔ میں آپ کی علامات سمجھنے اور "
            "اگلے قدم بتانے میں مدد کر سکتا ہوں — لیکن میں حقیقی ڈاکٹر کا متبادل نہیں ہوں۔\n\n"
            "براہ کرم اپنی علامات بیان کریں۔ آپ جس زبان میں بات کریں گے، میں اسی میں جواب دوں گا۔"
        ),
        "hi": (
            "नमस्ते! मैं BestechCare AI Doctor हूँ। मैं आपके लक्षण समझने में मदद कर सकता हूँ — "
            "लेकिन मैं वास्तविक डॉक्टर का विकल्प नहीं हूँ।\n\n"
            "कृपया अपने लक्षण बताएं — जिस भाषा में बोलेंगे, उसी में जवाब दूँगा।"
        ),
        "ar": (
            "مرحباً! أنا مساعد BestechCare AI Doctor. سأساعدك في فهم الأعراض "
            "— لكنني لست بديلاً عن طبيب مرخص.\n\n"
            "صف أعراضك بأي لغة وسأرد بنفس اللغة."
        ),
    },
    "lang_switched": {
        "en": "Sure! I'll speak in English now. Please describe your symptoms.",
        "ur": "بالکل! اب میں اردو میں بات کروں گا۔ براہ کرم اپنی علامات بیان کریں۔",
        "hi": "ठीक है! अब मैं हिंदी में बात करूँगा। कृपया अपने लक्षण बताएं।",
        "ar": "حسناً! سأتحدث بالعربية الآن. يرجى وصف أعراضك.",
    },
    "emergency_header": {
        "en": "🚨 **URGENT — Please seek emergency medical care immediately.**",
        "ur": "🚨 **فوری — فوراً ایمرجنسی طبی امداد حاصل کریں۔**",
        "hi": "🚨 **तत्काल — तुरंत आपात चिकित्सा सहायता लें।**",
        "ar": "🚨 **عاجل — اطلب الرعاية الطارئة فوراً.**",
    },
    "emergency_footer": {
        "en": "Go to the nearest hospital emergency or call emergency services.",
        "ur": "قریبی ہسپتال کے ایمرجنسی وارد جائیں یا ایمرجنسی نمبر پر کال کریں۔",
        "hi": "नज़दीकी अस्पताल की इमरजेंसी में जाएं।",
        "ar": "اذهب إلى أقرب طوارئ أو اتصل بالطوارئ.",
    },
    "no_symptoms_first": {
        "en": (
            "Thank you for reaching out. Please share:\n"
            "• What symptoms are you experiencing?\n"
            "• How long have they been present?\n"
            "• How severe are they?"
        ),
        "ur": (
            "رابطہ کا شکریہ۔ براہ کرم بتائیں:\n"
            "• آپ کو کیا علامات ہیں؟\n"
            "• کب سے ہیں؟\n"
            "• کتنی شدید ہیں؟"
        ),
        "hi": (
            "धन्यवाद। बताएं:\n"
            "• क्या लक्षण हैं?\n"
            "• कब से?\n"
            "• कितनी गंभीर?"
        ),
        "ar": (
            "شكراً. يرجى:\n"
            "• ما الأعراض?\n"
            "• منذ متى?\n"
            "• ما شدتها?"
        ),
    },
    "no_symptoms_followup": {
        "en": "Could you describe symptoms (fever, headache, stomach pain, cough)?",
        "ur": "علامات بتائیں (بخار، سر درد، پیٹ درد، کھansi)۔",
        "hi": "लक्षण बताएं (बुखार, सिरदर्द, पेट दर्द)।",
        "ar": "صف الأعراض (حمى، صداع، ألم بطن).",
    },
    "guidance_intro": {
        "en": "Thank you. Here is **informational guidance** (not a diagnosis):",
        "ur": "شکریہ۔ یہ **عام معلوماتی رہنمائی** ہے (تشخیص نہیں):",
        "hi": "धन्यवाद। यह **सामान्य जानकारी** है (निदान नहीं):",
        "ar": "شكراً. هذا **إرشاد معلوماتي** (ليس تشخيصاً):",
    },
    "possible_conditions": {
        "en": "**Possible considerations:**",
        "ur": "**ممکنہ وجوہات:**",
        "hi": "**संभावित कारण:**",
        "ar": "**احتمالات:**",
    },
    "otc_heading": {
        "en": "**Over-the-counter options:**",
        "ur": "**بغیر نسخے کی دوائیں:**",
        "hi": "**बिना पर्चे की दवाएं:**",
        "ar": "**أدوية بدون وصفة:**",
    },
    "tests_heading": {
        "en": "**Suggested tests:**",
        "ur": "**تجویز کردہ ٹیسٹ:**",
        "hi": "**सुझाए परीक्षण:**",
        "ar": "**فحوصات مقترحة:**",
    },
    "precautions_heading": {
        "en": "**Precautions:**",
        "ur": "**احتیاط:**",
        "hi": "**सावधानियां:**",
        "ar": "**احتياطات:**",
    },
    "self_care_heading": {
        "en": "**Self-care:**",
        "ur": "**گھریلو علاج:**",
        "hi": "**घरेलू देखभाल:**",
        "ar": "**الرعاية الذاتية:**",
    },
    "specialist_recommend": {
        "en": "I recommend consulting a **{specialty}** on BestechCare.",
        "ur": "**{specialty}** سے BestechCare پر مشورہ کریں۔",
        "hi": "BestechCare पर **{specialty}** से सलाह लें।",
        "ar": "أنصح باستشارة **{specialty}** على BestechCare.",
    },
    "end_consultation_hint": {
        "en": "Click **End Consultation** for summary, doctor recommendations, and PDF.",
        "ur": "**End Consultation** دبائیں — خلاصہ، ڈاکٹر اور PDF ملے گا۔",
        "hi": "**End Consultation** दबाएं — सारांश और PDF।",
        "ar": "اضغط **End Consultation** للملخص وPDF.",
    },
    "prefix_symptom": {
        "en": "I understand you're dealing with {topic}. ",
        "ur": "سمجھ گیا — آپ کو {topic} کی تکلیف ہے۔ ",
        "hi": "समझ गया — {topic} की समस्या है। ",
        "ar": "فهمت — مشكلة {topic}. ",
    },
    "prefix_see": {
        "en": "I see. ",
        "ur": "ٹھیک ہے۔ ",
        "hi": "ठीक है। ",
        "ar": "حسناً. ",
    },
}

TOPIC_NAMES: dict[str, dict[Lang, str]] = {
    "headache": {"en": "headache", "ur": "سر درد", "hi": "सिरदर्द", "ar": "صداع"},
    "fever": {"en": "fever", "ur": "بخار", "hi": "बुखार", "ar": "حمى"},
    "cough_cold": {"en": "cold/cough", "ur": "زکام/کھansi", "hi": "खांसी/सर्दी", "ar": "سعال/برد"},
    "stomach": {"en": "stomach issues", "ur": "پیٹ کا مسئلہ", "hi": "पेट की समस्या", "ar": "معدة"},
    "skin": {"en": "skin issues", "ur": "جلد کا مسئلہ", "hi": "त्वचा", "ar": "جلد"},
    "mental": {"en": "mental health", "ur": "ذہنی صحت", "hi": "मानसिक स्वास्थ्य", "ar": "صحة نفسية"},
    "dental": {"en": "dental pain", "ur": "دانت درد", "hi": "दांत दर्द", "ar": "أسنان"},
    "urinary": {"en": "urinary symptoms", "ur": "پیشاب کی تکلیف", "hi": "पेशाब", "ar": "بول"},
}

SPECIALTY_NAMES: dict[str, dict[Lang, str]] = {
    "general-physician": {"en": "General Physician", "ur": "جنرل فزیشن", "hi": "सामान्य चिकित्सक", "ar": "طبيب عام"},
    "neurologist": {"en": "Neurologist", "ur": "نیورولوجسٹ", "hi": "न्यूरोलॉजिस्ट", "ar": "أخصائي أعصاب"},
    "gastroenterologist": {"en": "Gastroenterologist", "ur": "معدے کے ماہر", "hi": "गैस्ट्रोएंटेरोलॉजिस्ट", "ar": "جهاز هضمي"},
    "dermatologist": {"en": "Dermatologist", "ur": "جلد کے ماہر", "hi": "त्वचा विशेषज्ञ", "ar": "جلدية"},
    "ent-specialist": {"en": "ENT Specialist", "ur": "ناک کان گلے کے ماہر", "hi": "ईएनटी", "ar": "أنف وأذن"},
    "psychiatrist": {"en": "Psychiatrist", "ur": "ذہنی صحت کے ماہر", "hi": "मनोचिकित्सक", "ar": "نفسي"},
    "dentist": {"en": "Dentist", "ur": "دندان ساز", "hi": "दंत चिकित्सक", "ar": "أسنان"},
    "urologist": {"en": "Urologist", "ur": "گردے و پیشاب کے ماہر", "hi": "यूरोलॉजिस्ट", "ar": "مسالك"},
}


def t(key: str, lang: Lang, **kwargs: str) -> str:
    bucket = STRINGS.get(key, {})
    text = bucket.get(lang) or bucket.get("en") or key
    return text.format(**kwargs) if kwargs else text


def specialty_name(slug: str, lang: Lang) -> str:
    return SPECIALTY_NAMES.get(slug, {}).get(lang) or slug.replace("-", " ").title()


def _score_roman_urdu(text: str) -> int:
    lower = f" {text.lower()} "
    return sum(1 for m in ROMAN_URDU_MARKERS if m in lower)


def detect_language_from_text(text: str) -> Lang | None:
    if not text or not text.strip():
        return None
    if URDU_SCRIPT_RE.search(text):
        return "ur"
    if DEVANAGARI_RE.search(text):
        return "hi"

    for pattern, lang in LANGUAGE_SWITCH_PATTERNS:
        if pattern.search(text):
            return lang

    score = _score_roman_urdu(text)
    if score >= 2:
        return "ur"
    if score >= 1:
        return "ur"

    return None


def resolve_language(messages: list[dict]) -> Lang:
    lang: Lang = "en"
    for msg in messages:
        if msg.get("role") != "user":
            continue
        detected = detect_language_from_text(msg.get("content", ""))
        if detected:
            lang = detected
    return lang


def is_language_switch_request(text: str) -> Lang | None:
    normalized = text.lower()
    if len(normalized.split()) <= 8:
        for pattern, target in LANGUAGE_SWITCH_PATTERNS:
            if pattern.search(text):
                return target
    return None


def voice_lang_for(lang: Lang) -> str:
    return VOICE_LANG_MAP.get(lang, "en-US")
