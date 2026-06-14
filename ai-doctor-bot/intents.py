"""Intent detection and dynamic conversational responses."""

from __future__ import annotations

import re
from typing import Literal

from i18n import Lang, t
from text_utils import normalize_text

Intent = Literal[
    "identity",
    "greeting",
    "capabilities",
    "thanks",
    "goodbye",
    "lang_switch",
    "off_topic",
    "medical",
    "general_health",
    "unclear",
]

PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("identity", re.compile(
        r"(are you (a |an )?(real |actual |human |licensed )?(doctor|dr\b|ai|bot|robot|machine|artificial)|"
        r"(you|u) (a |an )?(doctor|ai|bot|robot|human|real)|"
        r"(real|actual|human) doctor|"
        r"ai (or|ya|aur) doctor|doctor (or|ya|aur) ai|"
        r"not a real doctor|"
        r"kya aap (ai|doctor|insaan)|"
        r"aap (doctor|ai|bot) hain|"
        r"ap (doctor|ai) ho|"
        r"robot ho|machine ho|"
        r"who are you|what are you)",
        re.I,
    )),
    ("greeting", re.compile(
        r"(^|\b)(hello|hi\b|hey\b|good morning|good evening|good afternoon|good night|"
        r"how are you|how r u|how're you|"
        r"assalam|salam|adaab|salam alaikum|walaikum|"
        r"kaise ho|kaisa hai|kase ha|kese ho|kesa ha|kya hal|kyaa haal|"
        r"aap kaise|ap kaise|aap kaisay|ap kaisay|"
        r"aap kaise hain|ap kaise hain|kase ha ap|kese ho ap|ha ap|ho ap|"
        r"theek ho|theek hain|"
        r"آپ کیسے|کیسے ہو|السلام|سلام|ہیلو|ہیلو)",
        re.I,
    )),
    ("capabilities", re.compile(
        r"(what can you do|how can you help|help me with|what do you do|"
        r"aap kya kar sakte|kya kar sakte ho|madad kaise|"
        r"what (can|do) you (help|offer))",
        re.I,
    )),
    ("thanks", re.compile(
        r"(thank you|thanks|thank u|shukriya|shukria|jazak|جزاک|شکریہ|dhanyavad|شكر)",
        re.I,
    )),
    ("goodbye", re.compile(
        r"(bye|goodbye|see you|allah hafiz|khuda hafiz|اللہ حافظ|take care)",
        re.I,
    )),
    ("off_topic", re.compile(
        r"(weather|cricket|football|movie|song|joke|who is |what is the capital|"
        r"prime minister|election|bitcoin|stock)",
        re.I,
    )),
]

MEDICAL_RE = re.compile(
    r"(pain|hurt|ache|aches|aching|hurts|hurting|sore|fever|cough|vomit|nausea|rash|symptom|sick|ill|"
    r"swelling|bleeding|dard|bukhar|khansi|takleef|beemar|dawai|headache|stomach|diarrhea|"
    r"head\s*pain|head\s*hurt|my\s+head|pain\s+in\s+(my\s+)?head|"
    r"\bsar\b|\bsir\b|\bpet\b|\bpait\b|ho rha|ho rahi|"
    r"تکلیف|درد|بخار|علامات|بیمار|سر درد|پیٹ|کھانسی)",
    re.I,
)

RESPONSES: dict[str, dict[Lang, str]] = {
    "identity": {
        "en": (
            "Great question! I'm **BestechCare AI Doctor** — an **AI health assistant**, not a licensed human doctor.\n\n"
            "I can help you:\n"
            "• Understand your symptoms\n"
            "• Suggest possible causes (with disclaimers)\n"
            "• Recommend OTC options, precautions, and when to see a specialist\n\n"
            "For any real diagnosis or prescription, please consult a qualified doctor on BestechCare.\n\n"
            "What symptoms or health concern would you like to discuss?"
        ),
        "ur": (
            "اچھا سوال! میں **BestechCare AI Doctor** ہوں — **AI صحت کا معاون**، حقیقی انسان ڈاکٹر نہیں۔\n\n"
            "میں مدد کر سکتا ہوں:\n"
            "• علامات سمجھنے میں\n"
            "• ممکنہ وجوہات بتانے میں (تشخیص نہیں)\n"
            "• OTC دوائیں، احتیاط، اور کب specialist دکھانا ہے\n\n"
            "حقیقی تشخیص کے لیے BestechCare پر qualified doctor سے ملیں۔\n\n"
            "آپ کو کیا علامات یا مسئلہ ہے؟"
        ),
        "hi": (
            "अच्छा सवाल! मैं **BestechCare AI Doctor** हूँ — **AI स्वास्थ्य सहायक**, वास्तविक डॉक्टर नहीं۔\n\n"
            "मैं लक्षण समझने, संभावित कारण और OTC सुझाव दे सकता हूँ — निदान नहीं۔\n\n"
            "आपको क्या तकलीफ है?"
        ),
        "ar": (
            "سؤال جيد! أنا **BestechCare AI Doctor** — **مساعد صحي بالذكاء الاصطناعي**، لست طبيباً بشرياً۔\n\n"
            "ما الأعراض التي تريد مناقشتها؟"
        ),
    },
    "identity_followup": {
        "en": (
            "To be clear: I'm **100% AI**, not a human doctor. I'm trained to guide you on symptoms and next steps only.\n\n"
            "Tell me what's bothering you health-wise — headache, fever, stomach pain, or anything else?"
        ),
        "ur": (
            "واضح کر دوں: میں **پورا AI** ہوں، انسان ڈاکٹر نہیں۔ صرف علامات اور اگلے قدم میں رہنمائی کرتا ہوں۔\n\n"
            "بتائیں کیا تکلیف ہے — سر درد، بخار، پیٹ درد؟"
        ),
        "hi": (
            "स्पष्ट रूप से: मैं **AI** हूँ, इंसानी डॉक्टर नहीं۔ अपनी तकलीफ बताएं?"
        ),
        "ar": (
            "للتوضيح: أنا **AI بالكامل**، لست طبيباً بشرياً. ما الأعراض؟"
        ),
    },
    "capabilities": {
        "en": (
            "I can help you with:\n"
            "• Describing and understanding symptoms\n"
            "• Possible conditions (informational only)\n"
            "• OTC medicine suggestions for Pakistan\n"
            "• Precautions, self-care, and suggested tests\n"
            "• Recommending the right specialist on BestechCare\n"
            "• A downloadable PDF summary at the end\n\n"
            "Tell me your symptoms to get started!"
        ),
        "ur": (
            "میں یہ کر سکتا ہوں:\n"
            "• علامات سمجھنا\n"
            "• ممکنہ وجوہات (صرف معلومات)\n"
            "• پاکستان میں OTC دوائیں\n"
            "• احتیاط اور ٹیسٹ\n"
            "• BestechCare پر specialist\n"
            "• آخر میں PDF خلاصہ\n\n"
            "علامات بتائیں!"
        ),
        "hi": (
            "मैं लक्षण, OTC दवाएं, सावधानियां और specialist सुझाव दे सकता हूँ۔ लक्षण बताएं!"
        ),
        "ar": (
            "يمكنني مساعدتك في الأعراض والاحتياطات والأخصائيين. صف أعراضك!"
        ),
    },
    "off_topic": {
        "en": "I'm specialized in health guidance only. For medical concerns, tell me your symptoms — I'm happy to help with that!",
        "ur": "میں صرف صحت کے مسائل میں مدد کرتا ہوں۔ علامات بتائیں!",
        "hi": "मैं केवल स्वास्थ्य में मदद करता हूँ। अपने लक्षण बताएं!",
        "ar": "أنا متخصص في الصحة فقط. صف أعراضك!",
    },
}

RESPONSES_ROMAN: dict[str, str] = {
    "identity": (
        "Acha sawal! Main **BestechCare AI Doctor** hoon — **AI sehat ka muawan**, haqiqi insan doctor nahin.\n\n"
        "Main madad kar sakta hoon:\n"
        "• Alamat samajhne mein\n"
        "• Mumkin wajohat batane mein (tashkhees nahin)\n"
        "• OTC dawain, ehtiyat, aur kab specialist dikhana hai\n\n"
        "Haqiqi tashkhees ke liye BestechCare par qualified doctor se milen.\n\n"
        "Aap ko kya alamat ya masla hai?"
    ),
    "identity_followup": (
        "Wazeh kar doon: main **pura AI** hoon, insaan doctor nahin. Sirf alamat aur aglay qadam mein rehnumai karta hoon.\n\n"
        "Batayein kya takleef hai — sar dard, bukhar, pet dard?"
    ),
    "capabilities": (
        "Main yeh kar sakta hoon:\n"
        "• Alamat samajhna\n"
        "• Mumkin wajohat (sirf maloomat)\n"
        "• Pakistan mein OTC dawain\n"
        "• Ehtiyat aur tests\n"
        "• BestechCare par specialist\n"
        "• Akhir mein PDF khulasa\n\n"
        "Alamat batayein!"
    ),
    "off_topic": (
        "Main sirf sehat ke masail mein madad karta hoon. Alamat batayein — main khushi se madad karunga!"
    ),
    "unclear_nudge": (
        "Main sehat ke sawalat ke liye hoon. Misal: \"mujhe 2 din se bukhar hai\" ya \"sar mein dard hai\"."
    ),
    "goodbye": "Take care! Jab bhi sehat ka sawal ho wapas aayein.",
    "greeting_casual": (
        "Hi! Main theek hoon, shukriya poochhne ka.\n\n"
        "Main BestechCare ka AI Doctor hoon — agar koi alamat ya sehat ka masla ho "
        "(jaise bukhar, sar dard, khansi, pet dard) to bata dein, main madad karunga."
    ),
}


def _normalize(text: str) -> str:
    return normalize_text(text)


def _count_prior_intent(messages: list[dict], intent: str) -> int:
    """Rough count — assistant messages after identity questions."""
    count = 0
    for i, msg in enumerate(messages):
        if msg.get("role") == "user" and classify_intent(msg.get("content", ""), messages[:i]) == intent:
            count += 1
    return count


def classify_intent(text: str, messages: list[dict] | None = None) -> Intent:
    normalized = _normalize(text)

    # Conversational intents first (before medical keywords)
    for name, pattern in PATTERNS:
        if pattern.search(normalized) or pattern.search(text):
            return name  # type: ignore

    if MEDICAL_RE.search(normalized) or MEDICAL_RE.search(text):
        return "medical"

    if len(normalized.split()) <= 12:
        return "unclear"

    return "unclear"


def get_conversational_response(intent: Intent, lang: Lang, messages: list[dict], *, roman: bool = False) -> str | None:
    last_user = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")

    if intent == "identity":
        prior = _count_prior_intent(messages, "identity")
        if roman:
            body = RESPONSES_ROMAN["identity_followup" if prior > 1 else "identity"]
        else:
            key = "identity_followup" if prior > 1 else "identity"
            body = RESPONSES[key].get(lang) or RESPONSES[key]["en"]
        return f"{body}\n\n⚠️ {t('disclaimer', lang, roman=roman)}"

    if intent == "greeting":
        if roman:
            body = RESPONSES_ROMAN["greeting_casual"]
            return f"{body}\n\n⚠️ {t('disclaimer', lang, roman=True)}"
        return f"{t('greeting_reply', lang, roman=roman)}\n\n⚠️ {t('disclaimer', lang, roman=roman)}"

    if intent == "thanks":
        return f"{t('thanks_reply', lang, roman=roman)}\n\n⚠️ {t('disclaimer', lang, roman=roman)}"

    if intent == "goodbye":
        if roman:
            return RESPONSES_ROMAN["goodbye"]
        goodbye = {
            "en": "Take care! Feel free to come back anytime you have health questions. Goodbye!",
            "ur": "Take care! جب بھی صحت کا سوال ہو واپس آئیں۔",
            "hi": "Take care! स्वास्थ्य के सवालों के लिए वापस आएं।",
            "ar": "Take care! عد في أي وقت تحتاج مساعدة صحية.",
        }
        return goodbye.get(lang) or goodbye["en"]

    if intent == "capabilities":
        if roman:
            body = RESPONSES_ROMAN["capabilities"]
        else:
            body = RESPONSES["capabilities"].get(lang) or RESPONSES["capabilities"]["en"]
        return f"{body}\n\n⚠️ {t('disclaimer', lang, roman=roman)}"

    if intent == "off_topic":
        if roman:
            body = RESPONSES_ROMAN["off_topic"]
        else:
            body = RESPONSES["off_topic"].get(lang) or RESPONSES["off_topic"]["en"]
        return f"{body}\n\n⚠️ {t('disclaimer', lang, roman=roman)}"

    if intent == "unclear":
        if _count_prior_intent(messages, "unclear") >= 3:
            if roman:
                nudge = RESPONSES_ROMAN["unclear_nudge"]
            else:
                nudge = {
                    "en": "I'm here for health questions. Try telling me something like: \"I have had fever for 2 days\" or \"my head hurts\".",
                    "ur": "میں صحت کے سوالات کے لیے ہوں۔ مثال: \"مجھے 2 دن سے بخار ہے\" یا \"سر میں درد ہے\"۔",
                    "hi": "मैं स्वास्थ्य के लिए हूँ। उदाहरण: \"2 दिन से बुखार है\"।",
                    "ar": "أنا للأسئلة الصحية. مثال: \"لدي حمى منذ يومين\".",
                }.get(lang, "I'm here for health questions. Try telling me something like: \"I have had fever for 2 days\" or \"my head hurts\".")
            return f"{nudge}\n\n⚠️ {t('disclaimer', lang, roman=roman)}"
        return f"{t('unclear_reply', lang, roman=roman)}\n\n⚠️ {t('disclaimer', lang, roman=roman)}"

    return None
