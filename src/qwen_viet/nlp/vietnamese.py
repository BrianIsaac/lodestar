"""Vietnamese NLP utilities for transaction processing."""

import re

from underthesea import ner, text_normalize, word_tokenize


def normalise_transaction(desc: str) -> str:
    """Normalise a raw banking transaction description for downstream processing.

    Args:
        desc: Raw transaction description from core banking system.

    Returns:
        Normalised, tokenised string suitable for categorisation or LLM input.
    """
    desc = text_normalize(desc.upper().strip())
    desc = re.sub(r"[/\\|]+", " ", desc)
    desc = re.sub(r"\b(\d{6,})\b", "ACCTNUM", desc)
    return word_tokenize(desc, format="text")


def extract_financial_entities(text: str) -> dict:
    """Extract structured entities from a Vietnamese transaction description.

    Args:
        text: Vietnamese transaction description.

    Returns:
        Dictionary with keys ``ner_entities``, ``amounts``, ``dates``.
    """
    entities = ner(text)
    amounts = re.findall(r"\d[\d.,]*\s*(?:đồng|VND|k|tr|triệu)", text, re.I)
    dates = re.findall(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", text)
    return {
        "ner_entities": [(w, t) for *_, w, t in entities if t != "O"],
        "amounts": amounts,
        "dates": dates,
    }
