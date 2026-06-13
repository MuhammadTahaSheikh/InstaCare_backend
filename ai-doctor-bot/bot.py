"""BestechCare AI Doctor — rule-based health guidance bot (no OpenAI key required)."""

from __future__ import annotations

import re
from typing import Any

from knowledge import (
    DISCLAIMER,
    EMERGENCY_KEYWORDS,
    GENERAL_FOLLOW_UPS,
    OPENING_PROMPT,
    SPECIALTY_SLUGS,
    SYMPTOM_RULES,
)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def _all_user_text(messages: list[dict]) -> str:
    return " ".join(m["content"] for m in messages if m.get("role") == "user")


def _all_text(messages: list[dict]) -> str:
    return " ".join(m["content"] for m in messages)


def _detect_emergency(text: str) -> str | None:
    normalized = _normalize(text)
    for keyword, message in EMERGENCY_KEYWORDS:
        if keyword in normalized:
            return message
    return None


def _match_rules(text: str) -> list[dict]:
    normalized = _normalize(text)
    matched = []
    for rule in SYMPTOM_RULES:
        if any(kw in normalized for kw in rule["keywords"]):
            matched.append(rule)
    return matched


def _topic_asked(full_text: str, topic: str) -> bool:
    normalized = _normalize(full_text)
    rule = next((r for r in SYMPTOM_RULES if r["id"] == topic), None)
    if not rule:
        return False
    follow = rule.get("follow_ups", [])
    for _, markers in follow:
        if any(m in normalized for m in markers):
            return True
    return False


def _general_follow_up_index(full_text: str) -> int:
    normalized = _normalize(full_text)
    asked = 0
    if any(w in normalized for w in ["age", "years old", "year old", "male", "female", "gender"]):
        asked += 1
    if any(w in normalized for w in ["medication", "medicine", "diabetes", "hypertension", "chronic", "bp", "blood pressure"]):
        asked += 1
    if any(w in normalized for w in ["tried", "took", "already", "relief", "panadol", "medicine"]):
        asked += 1
    return asked


def _next_question(matched_rules: list[dict], full_text: str) -> str | None:
    for rule in matched_rules:
        for topic, markers in rule.get("follow_ups", []):
            if not any(m in _normalize(full_text) for m in markers):
                q = rule.get("questions", {}).get(topic)
                if q and q.lower()[:20] not in _normalize(full_text):
                    return q

    idx = _general_follow_up_index(full_text)
    if idx < len(GENERAL_FOLLOW_UPS):
        question = GENERAL_FOLLOW_UPS[idx]
        if question.lower()[:20] not in _normalize(full_text):
            return question

    return None


def _merge_rules(rules: list[dict]) -> dict:
    if not rules:
        return {
            "conditions": [],
            "medicines": [],
            "tests": [],
            "precautions": ["Monitor your symptoms closely"],
            "self_care": ["Rest and stay hydrated", "Seek medical care if symptoms worsen"],
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


def _extract_symptoms(user_text: str, matched_rules: list[dict]) -> list[str]:
    symptoms = []
    normalized = _normalize(user_text)
    for rule in matched_rules:
        for kw in rule["keywords"]:
            if kw in normalized and kw not in symptoms:
                symptoms.append(kw)
    if not symptoms and user_text.strip():
        first_sentence = user_text.strip().split(".")[0][:80]
        symptoms.append(first_sentence)
    return symptoms[:6]


def _build_guidance(matched_rules: list[dict]) -> str:
    data = _merge_rules(matched_rules)
    lines = [
        "Thank you for sharing those details. Here is my **informational guidance** (not a medical diagnosis):\n",
        "**Possible considerations** (with disclaimers):",
    ]

    for c in data["conditions"]:
        lines.append(f"• **{c['name']}** ({c['likelihood']} likelihood) — {c['note']}")

    if data["medicines"]:
        lines.append("\n**Over-the-counter options** (confirm with a pharmacist/doctor):")
        for m in data["medicines"]:
            lines.append(f"• **{m['name']}** ({m['type']}): {m['usage']}. {m['precaution']}")

    if data["tests"]:
        lines.append("\n**Suggested tests** (if your doctor agrees):")
        for t in data["tests"]:
            lines.append(f"• {t}")

    if data["precautions"]:
        lines.append("\n**Precautions:**")
        for p in data["precautions"]:
            lines.append(f"• {p}")

    if data["self_care"]:
        lines.append("\n**Self-care & lifestyle:**")
        for s in data["self_care"]:
            lines.append(f"• {s}")

    lines.append(
        f"\nBased on your symptoms, I recommend consulting a **{data['specialty'].replace('-', ' ').title()}** "
        f"or General Physician on BestechCare for a proper evaluation."
    )
    lines.append(f"\n⚠️ **Reminder:** {DISCLAIMER}")
    lines.append(
        "\nWhen you're ready, click **End Consultation** to get a full summary, doctor recommendations, and a downloadable PDF."
    )

    return "\n".join(lines)


class AiDoctorBot:
    """Stateless conversational bot driven by symptom rules."""

    def chat(self, messages: list[dict[str, str]]) -> str:
        user_messages = [m for m in messages if m.get("role") == "user"]

        if not user_messages:
            return OPENING_PROMPT

        user_text = _all_user_text(messages)
        full_text = _all_text(messages)

        emergency = _detect_emergency(user_text)
        if emergency:
            return (
                f"🚨 **URGENT — Please seek emergency medical care immediately.**\n\n"
                f"{emergency}\n\n"
                f"Go to the nearest hospital emergency room or call emergency services.\n\n"
                f"{DISCLAIMER}"
            )

        matched = _match_rules(user_text)

        if not matched:
            if len(user_messages) == 1:
                return (
                    "Thank you for describing your concern. To help you better, could you share:\n"
                    "• What symptoms are you experiencing?\n"
                    "• How long have they been present?\n"
                    "• How severe are they (mild, moderate, severe)?\n\n"
                    f"⚠️ {DISCLAIMER}"
                )
            return (
                "I understand you're not feeling well. Could you describe your main symptoms more specifically "
                "(e.g. fever, headache, stomach pain, cough, skin rash)?\n\n"
                f"⚠️ {DISCLAIMER}"
            )

        question = _next_question(matched, full_text)
        user_count = len(user_messages)

        if question and user_count <= 3:
            prefix = "I see. "
            if user_count == 1:
                prefix = f"I understand you're dealing with symptoms related to {matched[0]['id'].replace('_', ' ')}. "
            return f"{prefix}{question}\n\n⚠️ {DISCLAIMER}"

        return _build_guidance(matched)

    def summarize(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        user_text = _all_user_text(messages)
        matched = _match_rules(user_text)
        data = _merge_rules(matched)
        symptoms = _extract_symptoms(user_text, matched)
        emergency = _detect_emergency(user_text)

        summary_parts = []
        if matched:
            summary_parts.append(
                f"During this AI-assisted consultation, the patient discussed symptoms including "
                f"{', '.join(symptoms[:3])}. "
            )
            summary_parts.append(
                "Based on the information provided, several possible conditions were discussed with appropriate "
                "medical disclaimers. Over-the-counter options, self-care measures, and suggested diagnostic tests "
                "were shared for informational purposes only."
            )
        else:
            summary_parts.append(
                "The patient described health concerns during this AI-assisted consultation. "
                "General guidance was provided and a qualified doctor evaluation was recommended."
            )

        summary_parts.append(
            "This consultation does not constitute a medical diagnosis. "
            "The patient should book an appointment with a qualified healthcare provider on BestechCare."
        )

        return {
            "summary": " ".join(summary_parts),
            "symptoms_discussed": symptoms,
            "possible_conditions": data["conditions"],
            "medicines": data["medicines"],
            "suggested_tests": data["tests"],
            "precautions": data["precautions"],
            "self_care": data["self_care"],
            "urgent_care_required": bool(emergency),
            "urgent_care_reason": emergency,
            "recommended_specialty_slug": data["specialty"],
            "disclaimer": DISCLAIMER,
        }


bot = AiDoctorBot()
