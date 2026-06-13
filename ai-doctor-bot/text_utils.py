"""Shared text normalization for symptom and intent matching."""

from __future__ import annotations

import re

# Common user typos in English symptom messages
TYPO_FIXES: dict[str, str] = {
    "hvae": "have",
    "heache": "headache",
    "headach": "headache",
    "headace": "headache",
    "headahe": "headache",
    "headaces": "headaches",
    "stomache": "stomach",
    "stomack": "stomach",
    "feaver": "fever",
    "cought": "cough",
    "couhg": "cough",
    "vomitting": "vomiting",
    "diarhea": "diarrhea",
    "diarreha": "diarrhea",
    "nauseaous": "nauseous",
}


def normalize_text(text: str) -> str:
    normalized = re.sub(r"\s+", " ", (text or "").lower().strip())
    for typo, fix in TYPO_FIXES.items():
        normalized = re.sub(rf"\b{re.escape(typo)}\b", fix, normalized)
    return normalized
