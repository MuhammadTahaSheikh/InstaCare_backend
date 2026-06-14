"""Language detection and multilingual strings for AI Doctor bot."""

from __future__ import annotations

import re
from typing import Any, Literal

Lang = Literal["en", "ur", "hi", "ar"]

URDU_SCRIPT_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]")
DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")

ROMAN_URDU_MARKERS = [
    "mujhe", "mjhe", "mera", "meri", "aap", "ap ", " hai", " ha ", "kya", "bukhar", "dard", "takleef",
    "beemar", "dawai", "ilaj", "tabiyat", "shukriya", "mein bol", "urdu mein",
    "pet dard", "sar dard", "zukam", "khansi", "bimaar", "masla",
    "ho rha", "ho rhi", "ho raha", "ho rahi", " rha ", " rhi ", " raha ", " rahi ",
    "din se", " se ", "kal se", "aaj se", " ghante", " sar ", " sir ", " pet ", " pait ",
    "mjhy", "mujhy", "mery", "apko", "aapko", "batao", "batayein", "theek", "nahi", "nahin",
    "kaise", "kaisa", "kase", "kese", "kesa", "kaisay", "salam", "assalam", "walaikum",
    "kaise ho", "kase ha", "kese ho", "kya hal", "ha ap", "ho ap", "sunao", "bhai",
    "alhamdulillah", "shukria", "ji ", " han ", "nhi ",
]

ROMAN_URDU_GREETING_RE = re.compile(
    r"(^|\b)(salam|assalam|adaab|walaikum|kaise|kaisa|kase|kese|kesa|kaisay|"
    r"kaise ho|kase ha|kese ho|kesa ha|kya hal|kyaa haal|theek ho|theek hain|"
    r"aap kaise|ap kaise|aap kaisay|ap kaisay|ha ap|ho ap|"
    r"salam alaikum|assalam o alaikum|assalamu alaikum)(\b|$|[^\w])",
    re.I,
)

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
        "en": "I'm here to help with health concerns. Please tell me what symptoms you have — for example fever, headache, cough, or stomach pain.",
        "ur": "میں آپ کی صحت میں مدد کے لیے یہاں ہوں۔ براہ کرم اپنی علامات بتائیں — جیسے بخار، سر درد، کھانسی، یا پیٹ درد۔",
        "hi": "मैं स्वास्थ्य में मदद के लिए यहाँ हूँ। अपने लक्षण बताएं — जैसे बुखार, सिरदर्द, खांसी।",
        "ar": "أنا هنا للمساعدة. صف أعراضك — مثل الحمى، الصداع، السعال.",
    },
    "greeting_reply": {
        "en": (
            "Hello! I'm doing well, thank you for asking. I'm your BestechCare AI Doctor assistant.\n\n"
            "How can I help you today? Please describe any symptoms or health concern you're experiencing."
        ),
        "ur": (
            "وعلیکم السلام! میں ٹھیک ہوں، پوچھنے کا شکریہ۔ میں BestechCare کا AI Doctor ہوں.\n\n"
            "آج آپ کو کیا علامات یا صحت کا مسئلہ ہے؟ براہ کرم تفصیل سے بتائیں."
        ),
        "hi": (
            "नमस्ते! मैं ठीक हूँ, धन्यवाद। मैं BestechCare AI Doctor हूँ.\n\n"
            "आज आपको क्या लक्षण हैं? कृपया बताएं."
        ),
        "ar": (
            "مرحباً! أنا بخير، شكراً. أنا مساعد BestechCare AI Doctor.\n\n"
            "ما الأعراض التي تعاني منها اليوم؟"
        ),
    },
    "thanks_reply": {
        "en": "You're welcome! Is there anything else about your health you'd like to discuss?",
        "ur": "خوش آمدید! کیا صحت کے بارے میں کuch aur poochna hai?",
        "hi": "आपका स्वागत है! क्या और कुछ पूछना है?",
        "ar": "عفواً! هل تريد مناقشة أي شيء آخر?",
    },
    "unclear_reply": {
        "en": "I want to make sure I help you correctly. Could you describe your main symptom or how you're feeling physically?",
        "ur": "میں صحیح مدد کرنا چاہتا ہوں۔ براہ کرم اپنی اصل علامت یا جسمانی تکلیف بیان کریں۔",
        "hi": "मैं सही मदद करना चाहता हूँ। अपना मुख्य लक्षण बताएं।",
        "ar": "أريد مساعدتك بشكل صحيح. صف عرضك الرئيسي.",
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

# Roman Urdu text (Latin script) — used when user writes in Roman Urdu, not Urdu script
ROMAN_STRINGS: dict[str, str] = {
    "disclaimer": "Hamesha doctor se mukammal checkup karwayen.",
    "opening": (
        "Assalam o alaikum! Main BestechCare ka AI Doctor hoon. Main aap ki alamat samajhne aur "
        "aglay qadam batane mein madad kar sakta hoon — lekin main haqiqi doctor ka badal nahin.\n\n"
        "Apni alamat Roman Urdu ya English mein bata dein, main usi zaban mein jawab doonga."
    ),
    "lang_switched": "Bilkul! Ab main Roman Urdu mein baat karunga. Apni alamat bata dein.",
    "emergency_header": "🚨 **FORI — abhi emergency medical madad hasil karein.**",
    "emergency_footer": "Qareebi hospital emergency mein jayein ya emergency number par call karein.",
    "no_symptoms_first": (
        "Shukriya. Barah e karam batayein:\n"
        "• Aap ko kya alamat hain?\n"
        "• Kab se hain?\n"
        "• Kitni shadeed hain?"
    ),
    "no_symptoms_followup": (
        "Main aap ki sehat mein madad ke liye yahan hoon. Apni alamat batayein — "
        "jaise bukhar, sar dard, khansi, ya pet dard."
    ),
    "greeting_reply": (
        "Alhamdulillah, main theek hoon! Aap sunao, aap kaise hain?\n\n"
        "Main BestechCare ka AI Doctor hoon — agar koi alamat ya sehat ka masla ho "
        "(jaise bukhar, sar dard, khansi, pet dard) to bata dein, main madad karunga."
    ),
    "thanks_reply": "Khush amdeed! Kya sehat ke bare mein kuch aur poochna hai?",
    "unclear_reply": (
        "Main sahi madad karna chahta hoon. Barah e karam apni asal alamat ya jismani takleef batayein."
    ),
    "guidance_intro": "Shukriya. Yeh **aam maloomati rehnumai** hai (tashkhees nahin):",
    "possible_conditions": "**Mumkin wajohat:**",
    "otc_heading": "**Bina nuskhe ki dawain:**",
    "tests_heading": "**Tajweez shuda tests:**",
    "precautions_heading": "**Ehtiyat:**",
    "self_care_heading": "**Gharailu ilaj:**",
    "specialist_recommend": "**{specialty}** se BestechCare par mashwara karein.",
    "end_consultation_hint": "**End Consultation** dabayein — khulasa, doctor aur PDF milega.",
    "prefix_symptom": "Samajh gaya — aap ko {topic} ki takleef hai. ",
    "prefix_see": "Theek hai. ",
}

TOPIC_NAMES_ROMAN: dict[str, str] = {
    "headache": "sar dard",
    "fever": "bukhar",
    "cough_cold": "zukam/khansi",
    "stomach": "pet ka masla",
    "skin": "jild ka masla",
    "mental": "zehni sehat",
    "dental": "daant dard",
    "urinary": "peshab ki takleef",
}

SPECIALTY_NAMES_ROMAN: dict[str, str] = {
    "general-physician": "General Physician",
    "neurologist": "Neurologist",
    "gastroenterologist": "Gastroenterologist",
    "dermatologist": "Dermatologist",
    "ent-specialist": "ENT Specialist",
    "psychiatrist": "Psychiatrist",
    "dentist": "Dentist",
    "urologist": "Urologist",
}

TOPIC_NAMES: dict[str, dict[Lang, str]] = {
    "headache": {"en": "headache", "ur": "سر درد", "hi": "सिरदर्द", "ar": "صداع"},
    "fever": {"en": "fever", "ur": "بخار", "hi": "बुखार", "ar": "حمى"},
    "cough_cold": {"en": "cold/cough", "ur": "زکام/کھانسی", "hi": "खांसी/सर्दी", "ar": "سعال/برد"},
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


def t(key: str, lang: Lang, *, roman: bool = False, **kwargs: str) -> str:
    if roman and lang == "ur" and key in ROMAN_STRINGS:
        text = ROMAN_STRINGS[key]
    else:
        bucket = STRINGS.get(key, {})
        text = bucket.get(lang) or bucket.get("en") or key
    return text.format(**kwargs) if kwargs else text


def topic_name(topic_id: str, lang: Lang, *, roman: bool = False) -> str:
    if roman and lang == "ur":
        return TOPIC_NAMES_ROMAN.get(topic_id, topic_id.replace("_", " "))
    return TOPIC_NAMES.get(topic_id, {}).get(lang) or topic_id.replace("_", " ")


def specialty_name(slug: str, lang: Lang, *, roman: bool = False) -> str:
    if roman and lang == "ur":
        return SPECIALTY_NAMES_ROMAN.get(slug, slug.replace("-", " ").title())
    return SPECIALTY_NAMES.get(slug, {}).get(lang) or slug.replace("-", " ").title()


def _looks_roman_urdu(text: str) -> bool:
    if not text or URDU_SCRIPT_RE.search(text):
        return False
    if _score_roman_urdu(text) >= 1:
        return True
    return bool(ROMAN_URDU_GREETING_RE.search(text))


def reply_in_roman_urdu(text: str) -> bool:
    """True when user writes Urdu in Latin script (Roman Urdu), not Urdu script."""
    return _looks_roman_urdu(text)


def resolve_reply_style(last_user: str, messages: list[dict]) -> tuple[Lang, bool]:
    """Reply language/script follows the patient's latest message."""
    if URDU_SCRIPT_RE.search(last_user):
        return "ur", False
    if _looks_english(last_user) and not _looks_roman_urdu(last_user):
        return "en", False
    if reply_in_roman_urdu(last_user):
        return "ur", True
    detected = detect_language_from_text(last_user)
    if detected == "en":
        return "en", False
    if detected == "ur":
        return "ur", False
    if detected:
        return detected, False
    return resolve_language(messages), False


def language_lock_instruction(lang: Lang, *, roman: bool = False) -> str:
    """Hard instruction appended for LLM — must match latest user message language."""
    if roman:
        return (
            "LANGUAGE LOCK (mandatory): Write your ENTIRE reply in Roman Urdu using Latin letters only "
            "(e.g. 'Main theek hoon', 'Aap ko kya alamat hain?'). Do NOT reply in English."
        )
    if lang == "en":
        return (
            "LANGUAGE LOCK (mandatory): Write your ENTIRE reply in ENGLISH only. "
            "Do NOT use Urdu, Roman Urdu, or Hindi — even if earlier chat messages were in Urdu."
        )
    if lang == "ur":
        return (
            "LANGUAGE LOCK (mandatory): Write your ENTIRE reply in Urdu script (Nastaliq) only. "
            "Do NOT use English or Roman Urdu."
        )
    if lang == "hi":
        return "LANGUAGE LOCK (mandatory): Write your ENTIRE reply in Hindi (Devanagari) only."
    return f"LANGUAGE LOCK (mandatory): Reply in {lang} only."


def reply_matches_style(reply: str, lang: Lang, *, roman: bool = False) -> bool:
    """Return False when LLM reply uses the wrong language/script."""
    if not reply or not reply.strip():
        return False
    if roman:
        if URDU_SCRIPT_RE.search(reply):
            return False
        # Roman reply should have some roman urdu markers OR be Latin without being pure English-only short
        return _score_roman_urdu(reply) >= 1 or bool(ROMAN_URDU_GREETING_RE.search(reply))
    if lang == "en":
        if URDU_SCRIPT_RE.search(reply):
            return False
        lower = f" {reply.lower()} "
        roman_hits = _score_roman_urdu(reply)
        # Reject if reply looks like Roman Urdu (multiple markers or common urdu words)
        urdu_words = [" mujhe ", " aap ", " ap ", " hai ", " hain ", " kya ", " nahi ", " dard ", " bukhar "]
        word_hits = sum(1 for w in urdu_words if w in lower)
        if roman_hits >= 2 or word_hits >= 2:
            return False
        return True
    if lang == "ur" and not roman:
        return bool(URDU_SCRIPT_RE.search(reply))
    return True


def _score_roman_urdu(text: str) -> int:
    lower = f" {text.lower()} "
    return sum(1 for m in ROMAN_URDU_MARKERS if m in lower)


ENGLISH_MARKERS = [
    "hello", "hi ", "hey", "how are you", "good morning", "good evening", "good night",
    "thank you", "thanks", "please", "what is", "what are", "i have", "i am", "i feel",
    "my head", "my stomach", "help me", "can you", "how do", "why do",
    "not feeling", "feeling well", "feeling unwell", "feel sick", "feel bad",
    "i'm not", "im not", "no feeling",
]


def _looks_english(text: str) -> bool:
    lower = f" {text.lower()} "
    return any(m in lower for m in ENGLISH_MARKERS)


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

    lower = text.lower()
    urdu_score = _score_roman_urdu(text)

    if _looks_roman_urdu(text):
        if not _looks_english(text) or urdu_score >= 1:
            return "ur"

    # Latin script: prefer English when clearly English and not Roman Urdu
    if _looks_english(text) and urdu_score == 0:
        return "en"

    if urdu_score >= 2:
        return "ur"
    if urdu_score >= 1 and not _looks_english(text):
        return "ur"

    # Default Latin script to English (Pakistan app, many users type English)
    if re.search(r"[a-zA-Z]", text):
        return "en"

    return None


def resolve_language(messages: list[dict]) -> Lang:
    """Use the most recent user message to determine reply language."""
    user_messages = [m for m in messages if m.get("role") == "user"]
    if not user_messages:
        return "en"

    for msg in reversed(user_messages):
        detected = detect_language_from_text(msg.get("content", ""))
        if detected:
            return detected

    return "en"


def is_language_switch_request(text: str) -> Lang | None:
    normalized = text.lower()
    if len(normalized.split()) <= 8:
        for pattern, target in LANGUAGE_SWITCH_PATTERNS:
            if pattern.search(text):
                return target
    return None


def voice_lang_for(lang: Lang, *, roman: bool = False) -> str:
    if roman and lang == "ur":
        return "hi-IN"
    return VOICE_LANG_MAP.get(lang, "en-US")


Gender = Literal["male", "female"]

OPENING_BY_GENDER: dict[str, dict[Lang, str]] = {
    "male": {
        "en": (
            "Hello! I'm your **BestechCare AI Doctor** (male assistant). I can help you understand your symptoms "
            "and suggest next steps — but I am not a replacement for a licensed doctor.\n\n"
            "Please describe your symptoms and I'll guide you in English."
        ),
        "ur": (
            "السلام علیکم! میں BestechCare کا **AI Doctor (مرد)** ہوں۔ میں آپ کی علامات سمجھنے اور "
            "اگلے قدم بتانے میں مدد کر سکتا ہوں — لیکن میں حقیقی ڈاکٹر کا متبادل نہیں ہوں۔\n\n"
            "براہ کرم اپنی علامات بیان کریں۔"
        ),
        "hi": (
            "नमस्ते! मैं BestechCare का **AI Doctor (पुरुष)** हूँ। मैं आपके लक्षण समझने में मदद कर सकता हूँ — "
            "लेकिन मैं वास्तविक डॉक्टर का विकल्प नहीं हूँ।\n\n"
            "कृपया अपने लक्षण बताएं।"
        ),
        "ar": (
            "مرحباً! أنا **BestechCare AI Doctor (ذكر)**. سأساعدك في فهم الأعراض "
            "— لكنني لست بديلاً عن طبيب مرخص.\n\n"
            "صف أعراضك وسأرد بالعربية."
        ),
    },
    "female": {
        "en": (
            "Hello! I'm your **BestechCare AI Doctor** (female assistant). I can help you understand your symptoms "
            "and suggest next steps — but I am not a replacement for a licensed doctor.\n\n"
            "Please describe your symptoms and I'll guide you in English."
        ),
        "ur": (
            "السلام علیکم! میں BestechCare کی **AI Doctor (خاتون)** ہوں۔ میں آپ کی علامات سمجھنے اور "
            "اگلے قدم بتانے میں مدد کر سکتی ہوں — لیکن میں حقیقی ڈاکٹر کا متبادل نہیں ہوں۔\n\n"
            "براہ کرم اپنی علامات بیان کریں۔"
        ),
        "hi": (
            "नमस्ते! मैं BestechCare की **AI Doctor (महिला)** हूँ। मैं आपके लक्षण समझने में मदद कर सकती हूँ — "
            "लेकिन मैं वास्तविक डॉक्टर का विकल्प नहीं हूँ।\n\n"
            "कृपया अपने लक्षण बताएं।"
        ),
        "ar": (
            "مرحباً! أنا **BestechCare AI Doctor (أنثى)**. سأساعدك في فهم الأعراض "
            "— لكنني لست بديلاً عن طبيب مرخص.\n\n"
            "صف أعراضك وسأرد بالعربية."
        ),
    },
}

OPENING_ROMAN_BY_GENDER: dict[str, str] = {
    "male": (
        "Assalam o alaikum! Main BestechCare ka **AI Doctor (mard)** hoon. Main aap ki alamat samajhne aur "
        "aglay qadam batane mein madad kar sakta hoon — lekin main haqiqi doctor ka badal nahin.\n\n"
        "Apni alamat Roman Urdu ya English mein bata dein."
    ),
    "female": (
        "Assalam o alaikum! Main BestechCare ki **AI Doctor (khatoon)** hoon. Main aap ki alamat samajhne aur "
        "aglay qadam batane mein madad kar sakti hoon — lekin main haqiqi doctor ka badal nahin.\n\n"
        "Apni alamat Roman Urdu ya English mein bata dein."
    ),
}


def opening_message(
    lang: Lang,
    *,
    roman: bool = False,
    gender: Gender = "male",
) -> str:
    if roman and lang == "ur":
        return OPENING_ROMAN_BY_GENDER.get(gender, OPENING_ROMAN_BY_GENDER["male"])
    gender_bucket = OPENING_BY_GENDER.get(gender, OPENING_BY_GENDER["male"])
    return gender_bucket.get(lang) or gender_bucket["en"]


def session_style(
    session_prefs: dict[str, Any] | None,
) -> tuple[Lang, bool, Gender]:
    if not session_prefs:
        return "en", False, "male"
    lang = session_prefs.get("preferred_language", "en")
    roman = bool(session_prefs.get("roman_urdu")) and lang == "ur"
    gender = session_prefs.get("doctor_gender", "male")
    if gender not in ("male", "female"):
        gender = "male"
    return lang, roman, gender  # type: ignore[return-value]
