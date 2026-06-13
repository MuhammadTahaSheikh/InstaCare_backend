"""Medical guidance knowledge base for the BestechCare AI Doctor bot."""

SPECIALTY_SLUGS = [
    "gynecologist",
    "dentist",
    "dermatologist",
    "cardiologist",
    "neurologist",
    "ent-specialist",
    "pediatrician",
    "gastroenterologist",
    "general-physician",
    "plastic-surgeon",
    "urologist",
    "psychiatrist",
]

EMERGENCY_KEYWORDS = [
    ("chest pain", "Chest pain can indicate a heart attack. Go to the nearest emergency room immediately or call emergency services."),
    ("heart attack", "Possible heart attack — seek emergency care immediately."),
    ("cannot breathe", "Severe breathing difficulty requires immediate emergency care."),
    ("can't breathe", "Severe breathing difficulty requires immediate emergency care."),
    ("difficulty breathing", "Breathing problems can be life-threatening. Seek emergency care now."),
    ("shortness of breath", "If breathing is severely restricted, go to the ER immediately."),
    ("stroke", "Stroke symptoms need emergency treatment within minutes."),
    ("face drooping", "This may be a stroke sign — call emergency services immediately."),
    ("slurred speech", "Combined with other symptoms, this may indicate a stroke — seek emergency care."),
    ("severe bleeding", "Uncontrolled bleeding needs immediate emergency attention."),
    ("unconscious", "Loss of consciousness is an emergency — call for help immediately."),
    ("suicide", "If you are in crisis, please contact a mental health helpline or emergency services immediately."),
    ("kill myself", "Please reach out to emergency services or a crisis helpline immediately. You are not alone."),
]

SYMPTOM_RULES = [
    {
        "id": "headache",
        "keywords": ["headache", "head pain", "migraine", "head ache", "throbbing head"],
        "follow_ups": [
            ("duration", ["how long", "since when", "started", "days ago", "hours"]),
            ("severity", ["scale", "severe", "mild", "worst", "1-10", "intensity"]),
            ("fever", ["fever", "temperature", "temp"]),
            ("vision", ["vision", "blurry", "light sensitive", "photophobia"]),
        ],
        "questions": {
            "duration": "How long have you had this headache — hours, days, or longer?",
            "severity": "On a scale of 1–10, how severe is the pain?",
            "fever": "Do you have a fever or neck stiffness with the headache?",
            "vision": "Any vision changes, nausea, or sensitivity to light?",
        },
        "conditions": [
            {"name": "Tension headache", "likelihood": "moderate", "note": "Common; often stress or dehydration related — not a definitive diagnosis."},
            {"name": "Migraine", "likelihood": "moderate", "note": "May need doctor evaluation if frequent or severe."},
        ],
        "medicines": [
            {"name": "Paracetamol (Panadol)", "type": "OTC", "usage": "500mg–1g every 6 hours as needed (max 4g/day)", "precaution": "Avoid if liver disease; consult pharmacist."},
            {"name": "Ibuprofen", "type": "OTC", "usage": "400mg every 6–8 hours with food", "precaution": "Avoid if stomach ulcers or kidney issues."},
        ],
        "tests": ["Blood pressure check", "Eye examination if vision affected"],
        "precautions": ["Rest in a quiet, dark room", "Stay hydrated", "Avoid screen time"],
        "self_care": ["Regular sleep schedule", "Manage stress", "Drink adequate water"],
        "specialty": "neurologist",
    },
    {
        "id": "fever",
        "keywords": ["fever", "temperature", "high temp", "burning up", "chills", "bukhar"],
        "follow_ups": [
            ("duration", ["how long", "since when", "days"]),
            ("temperature", ["degree", "102", "103", "104", "celsius", "fever reading"]),
            ("other", ["cough", "body ache", "rash", "throat"]),
        ],
        "questions": {
            "duration": "How many days have you had the fever?",
            "temperature": "Do you know your temperature reading (in °C or °F)?",
            "other": "Any cough, sore throat, body aches, or rash along with the fever?",
        },
        "conditions": [
            {"name": "Viral infection", "likelihood": "moderate", "note": "Common cause of fever — needs clinical confirmation."},
            {"name": "Bacterial infection", "likelihood": "low", "note": "Possible if fever persists beyond 3 days."},
        ],
        "medicines": [
            {"name": "Paracetamol (Panadol)", "type": "OTC", "usage": "500mg–1g every 6 hours to reduce fever", "precaution": "Do not exceed recommended dose."},
        ],
        "tests": ["Complete Blood Count (CBC)", "Malaria test if in endemic area", "Chest X-ray if cough persists"],
        "precautions": ["Sponge with lukewarm water", "Wear light clothing", "Monitor temperature every 4–6 hours"],
        "self_care": ["Rest and fluids (ORS, water, clear soups)", "Light, easy-to-digest meals"],
        "specialty": "general-physician",
    },
    {
        "id": "cough_cold",
        "keywords": ["cough", "cold", "runny nose", "sneezing", "congestion", "sore throat", "flu", "zukam"],
        "follow_ups": [
            ("duration", ["how long", "days", "week"]),
            ("type", ["dry", "wet", "phlegm", "blood", "mucus"]),
            ("breathing", ["breath", "wheezing", "chest tight"]),
        ],
        "questions": {
            "duration": "How long have you had these symptoms?",
            "type": "Is your cough dry or producing phlegm/mucus? Any blood?",
            "breathing": "Any difficulty breathing or wheezing?",
        },
        "conditions": [
            {"name": "Upper respiratory infection (common cold)", "likelihood": "high", "note": "Usually viral and self-limiting."},
            {"name": "Bronchitis", "likelihood": "low", "note": "Possible if cough persists beyond 2 weeks."},
        ],
        "medicines": [
            {"name": "Steam inhalation + saline gargle", "type": "OTC", "usage": "2–3 times daily", "precaution": "Be careful with hot water."},
            {"name": "Honey in warm water", "type": "OTC", "usage": "1 tsp in warm water for cough relief", "precaution": "Not for children under 1 year."},
            {"name": "Lozenges (Strepsils)", "type": "OTC", "usage": "As directed for sore throat", "precaution": "Follow package instructions."},
        ],
        "tests": ["Chest X-ray if cough > 3 weeks", "COVID/flu test if exposure suspected"],
        "precautions": ["Cover mouth when coughing", "Avoid cold drinks", "Isolate if fever present"],
        "self_care": ["Warm fluids", "Adequate rest", "Vitamin C rich foods"],
        "specialty": "ent-specialist",
    },
    {
        "id": "stomach",
        "keywords": ["stomach", "abdomen", "abdominal", "nausea", "vomit", "diarrhea", "diarrhoea", "pet dard", "gas", "acidity", "heartburn", "indigestion"],
        "follow_ups": [
            ("duration", ["how long", "since", "days"]),
            ("location", ["upper", "lower", "right", "left", "around navel"]),
            ("severity", ["severe", "mild", "cramping", "sharp"]),
        ],
        "questions": {
            "duration": "When did the stomach issue start?",
            "location": "Where exactly is the pain — upper, lower, or all over?",
            "severity": "Is the pain constant or comes and goes? Any vomiting or diarrhea?",
        },
        "conditions": [
            {"name": "Gastritis / acidity", "likelihood": "moderate", "note": "Common with spicy food or stress."},
            {"name": "Gastroenteritis", "likelihood": "moderate", "note": "If vomiting/diarrhea present — stay hydrated."},
        ],
        "medicines": [
            {"name": "ORS (Oral Rehydration Solution)", "type": "OTC", "usage": "Sip frequently if vomiting/diarrhea", "precaution": "Essential to prevent dehydration."},
            {"name": "Antacid (e.g. Gaviscon, Mucaine)", "type": "OTC", "usage": "After meals for acidity", "precaution": "Consult pharmacist if symptoms persist."},
        ],
        "tests": ["Stool test if diarrhea > 3 days", "Ultrasound abdomen if severe localized pain"],
        "precautions": ["Avoid spicy/oily food", "Eat small frequent meals", "Seek ER if severe right-side lower pain"],
        "self_care": ["BRAT diet (banana, rice, apple, toast)", "Avoid caffeine and alcohol"],
        "specialty": "gastroenterologist",
    },
    {
        "id": "skin",
        "keywords": ["skin", "rash", "itch", "itching", "acne", "pimple", "eczema", "allergy", "hives", "red spots"],
        "follow_ups": [
            ("duration", ["how long", "since when"]),
            ("spread", ["spreading", "whole body", "face", "arms"]),
            ("trigger", ["new product", "food", "medication", "sun"]),
        ],
        "questions": {
            "duration": "How long have you noticed the skin issue?",
            "spread": "Is it localized to one area or spreading?",
            "trigger": "Any new soaps, foods, medications, or sun exposure recently?",
        },
        "conditions": [
            {"name": "Allergic reaction / urticaria", "likelihood": "moderate", "note": "Watch for facial/lip swelling — seek ER if breathing affected."},
            {"name": "Eczema or dermatitis", "likelihood": "moderate", "note": "Chronic conditions need dermatologist evaluation."},
        ],
        "medicines": [
            {"name": "Calamine lotion", "type": "OTC", "usage": "Apply to itchy areas", "precaution": "For external use only."},
            {"name": "Cetirizine (Zyrtec)", "type": "OTC", "usage": "10mg once daily for itching", "precaution": "May cause drowsiness."},
        ],
        "tests": ["Allergy panel if recurrent", "Skin scraping if fungal suspected"],
        "precautions": ["Avoid scratching", "Use fragrance-free moisturizer", "Avoid known triggers"],
        "self_care": ["Keep skin clean and dry", "Wear loose cotton clothing"],
        "specialty": "dermatologist",
    },
    {
        "id": "mental",
        "keywords": ["anxiety", "depression", "stress", "panic", "sad", "sleep", "insomnia", "mental", "worried", "tension"],
        "follow_ups": [
            ("duration", ["how long", "weeks", "months"]),
            ("severity", ["daily", "affecting work", "unable to function"]),
            ("safety", ["hurt myself", "suicide", "hopeless"]),
        ],
        "questions": {
            "duration": "How long have you been feeling this way?",
            "severity": "Is it affecting your daily work, sleep, or relationships?",
            "safety": "Have you had thoughts of harming yourself? (Your safety matters — please be honest.)",
        },
        "conditions": [
            {"name": "Anxiety / stress-related symptoms", "likelihood": "moderate", "note": "Very common; professional support is recommended."},
            {"name": "Depressive symptoms", "likelihood": "moderate", "note": "Requires evaluation by a mental health professional."},
        ],
        "medicines": [],
        "tests": ["Mental health screening by psychiatrist or psychologist"],
        "precautions": ["Talk to someone you trust", "Maintain a regular sleep routine", "Limit caffeine and alcohol"],
        "self_care": ["Daily walk or light exercise", "Deep breathing exercises", "Reduce social media if it increases stress"],
        "specialty": "psychiatrist",
    },
    {
        "id": "dental",
        "keywords": ["tooth", "teeth", "dental", "gum", "cavity", "toothache", "jaw pain"],
        "follow_ups": [
            ("duration", ["how long"]),
            ("type", ["sharp", "constant", "cold", "hot", "swelling"]),
        ],
        "questions": {
            "duration": "How long have you had the tooth/gum pain?",
            "type": "Is the pain triggered by hot/cold food? Any swelling or bleeding gums?",
        },
        "conditions": [
            {"name": "Dental caries (cavity)", "likelihood": "moderate", "note": "Needs dentist examination."},
            {"name": "Gingivitis", "likelihood": "moderate", "note": "Gum inflammation — dental cleaning recommended."},
        ],
        "medicines": [
            {"name": "Paracetamol", "type": "OTC", "usage": "For pain relief until dental visit", "precaution": "Temporary relief only — see a dentist."},
        ],
        "tests": ["Dental X-ray", "Oral examination"],
        "precautions": ["Avoid very hot/cold foods", "Gentle brushing", "Salt water rinse"],
        "self_care": ["Brush twice daily", "Floss regularly"],
        "specialty": "dentist",
    },
    {
        "id": "urinary",
        "keywords": ["urine", "urinary", "burning urination", "frequent urination", "uti", "bladder", "kidney pain"],
        "follow_ups": [
            ("duration", ["how long"]),
            ("symptoms", ["blood", "fever", "back pain", "cloudy"]),
        ],
        "questions": {
            "duration": "How long have you had urinary symptoms?",
            "symptoms": "Any blood in urine, fever, or lower back pain?",
        },
        "conditions": [
            {"name": "Urinary tract infection (UTI)", "likelihood": "moderate", "note": "Common; antibiotics usually required — see a doctor."},
        ],
        "medicines": [
            {"name": "Increased water intake", "type": "OTC", "usage": "Drink plenty of fluids", "precaution": "Does not replace medical treatment for UTI."},
        ],
        "tests": ["Urine routine examination", "Urine culture"],
        "precautions": ["Do not hold urine", "Maintain hygiene", "See doctor promptly — UTIs need antibiotics"],
        "self_care": ["Cranberry juice may help prevention", "Complete full antibiotic course if prescribed"],
        "specialty": "urologist",
    },
]

DISCLAIMER = "Always consult a qualified doctor for professional evaluation."

OPENING_PROMPT = (
    "Hello! I'm your BestechCare AI Doctor assistant. I can help you understand your symptoms "
    "and suggest next steps — but I am **not** a replacement for a licensed doctor.\n\n"
    "Please describe your symptoms or health concern, and I'll ask a few follow-up questions."
)

GENERAL_FOLLOW_UPS = [
    "Could you tell me your age and gender? This helps me give more relevant guidance.",
    "Are you currently taking any medications or do you have any chronic conditions (diabetes, hypertension, etc.)?",
    "Have you tried anything so far to relieve the symptoms?",
]
