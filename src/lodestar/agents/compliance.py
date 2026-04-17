"""Compliance filter — classifies output before delivery to customer.

Pattern coverage spans the three supported locales (Vietnamese, English,
Korean) so a tri-lingual card is classified consistently regardless of
which locale's text is inspected. Classification is rule-based for the
PoC; swapping in an LLM classifier would slot in via ``classify_output``.
"""

import re

from lodestar.models import ComplianceClass

ADVICE_PATTERNS = [
    # Vietnamese
    r"(?i)bạn nên",
    r"(?i)chúng tôi khuyên",
    r"(?i)nên mua",
    r"(?i)nên đầu tư",
    r"(?i)hãy (mua|bán|đầu tư|chuyển)",
    # English
    r"(?i)we recommend",
    r"(?i)you should (buy|invest|switch|open|take out)",
    r"(?i)i (recommend|advise|suggest you)",
    # Korean
    r"추천(합니다|드립니다)",
    r"(투자|매수|매도|가입)\s*하(십시오|세요)",
    r"(사|드시)는 것이 좋습니다",
]

GUIDANCE_PATTERNS = [
    # Vietnamese
    r"(?i)có thể cân nhắc",
    r"(?i)có thể xem xét",
    r"(?i)có thể thử",
    r"(?i)một lựa chọn là",
    r"(?i)bạn có thể",
    r"(?i)hãy thử",
    r"(?i)nên thử",
    # English
    r"(?i)you (might|could|may) (consider|want to)",
    r"(?i)\bconsider\b",
    r"(?i)tip:",
    r"(?i)it (might|may) help to",
    # Korean
    r"고려(해|하는\s*것을|할\s*수)",
    r"(조정|검토)해\s*보(십시오|세요)",
    r"해\s*보는\s*것이\s*좋습니다",
    r"시도해\s*보(십시오|세요)",
]

DISCLAIMERS: dict[str, str] = {
    "vi": "Đây là thông tin tham khảo, không phải tư vấn tài chính.",
    "en": "This is informational content, not financial advice.",
    "ko": "본 내용은 참고용 정보이며 금융 자문이 아닙니다.",
}

REFUSALS: dict[str, str] = {
    "vi": (
        "Xin lỗi, tôi chỉ có thể cung cấp thông tin sản phẩm. "
        "Để được tư vấn tài chính, vui lòng liên hệ chuyên viên Shinhan."
    ),
    "en": (
        "I can only provide product information. "
        "For financial advice, please contact a Shinhan advisor."
    ),
    "ko": (
        "저는 상품 정보만 제공할 수 있습니다. "
        "금융 자문이 필요하시면 신한 상담원에게 문의해 주세요."
    ),
}

# Backwards-compat aliases for tests/code that imported the old constants.
DISCLAIMER_VI = DISCLAIMERS["vi"]
DISCLAIMER_EN = DISCLAIMERS["en"]


def classify_output(text: str) -> ComplianceClass:
    """Classify a response as information, guidance, or advice.

    Args:
        text: The response text to classify.

    Returns:
        ComplianceClass enum value.
    """
    for pattern in ADVICE_PATTERNS:
        if re.search(pattern, text):
            return ComplianceClass.ADVICE

    for pattern in GUIDANCE_PATTERNS:
        if re.search(pattern, text):
            return ComplianceClass.GUIDANCE

    return ComplianceClass.INFORMATION


_SEVERITY_RANK = {
    ComplianceClass.INFORMATION: 0,
    ComplianceClass.GUIDANCE: 1,
    ComplianceClass.ADVICE: 2,
}


def apply_compliance(text: str, language: str = "vi") -> tuple[str, ComplianceClass]:
    """Classify and gate a response, adding disclaimers as needed.

    Args:
        text: The response text to process.
        language: Language code — "vi", "en", or "ko". Unknown codes fall
            back to Vietnamese.

    Returns:
        Tuple of (processed text, classification).
        If classified as advice, text is replaced with a refusal.
        If classified as guidance, disclaimer is appended.
    """
    lang = language if language in DISCLAIMERS else "vi"
    classification = classify_output(text)

    if classification == ComplianceClass.ADVICE:
        return REFUSALS[lang], classification

    if classification == ComplianceClass.GUIDANCE:
        return f"{text}\n\n{DISCLAIMERS[lang]}", classification

    return text, classification


def apply_compliance_multilingual(
    texts_by_lang: dict[str, str],
) -> tuple[dict[str, str], ComplianceClass]:
    """Classify a multi-locale response bundle with a single severity.

    Classifies each locale independently, picks the most-restrictive class
    across all of them, then applies that class's gate to every locale so
    a Vietnamese refusal does not leak English advice-style text.

    Args:
        texts_by_lang: Mapping of language code -> authored text.

    Returns:
        Tuple of (gated_texts_by_lang, shared_classification).
    """
    worst = ComplianceClass.INFORMATION
    for lang, text in texts_by_lang.items():
        if not isinstance(text, str) or not text:
            continue
        cls = classify_output(text)
        if _SEVERITY_RANK[cls] > _SEVERITY_RANK[worst]:
            worst = cls

    gated: dict[str, str] = {}
    for lang, text in texts_by_lang.items():
        if not isinstance(text, str) or not text:
            # Mirrors the classification-loop guard. Without the empty
            # check, a locale stored as "" would receive a refusal or
            # disclaimer appended to nothing.
            continue
        resolved = lang if lang in DISCLAIMERS else "vi"
        if worst == ComplianceClass.ADVICE:
            gated[lang] = REFUSALS[resolved]
        elif worst == ComplianceClass.GUIDANCE:
            gated[lang] = f"{text}\n\n{DISCLAIMERS[resolved]}"
        else:
            gated[lang] = text
    return gated, worst
