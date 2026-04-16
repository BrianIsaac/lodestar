"""Compliance filter — classifies output before delivery to customer.

Uses rule-based classification for the PoC. In production, this would
be an LLM classifier with higher accuracy on edge cases.
"""

import re

from lodestar.models import ComplianceClass

ADVICE_PATTERNS = [
    r"(?i)bạn nên",
    r"(?i)chúng tôi khuyên",
    r"(?i)nên mua",
    r"(?i)nên đầu tư",
    r"(?i)hãy (mua|bán|đầu tư|chuyển)",
    r"(?i)we recommend",
    r"(?i)you should (buy|invest|switch|open)",
    r"(?i)i (recommend|advise|suggest you)",
]

GUIDANCE_PATTERNS = [
    r"(?i)có thể cân nhắc",
    r"(?i)một lựa chọn là",
    r"(?i)you (might|could|may) (consider|want to)",
    r"(?i)consider",
    r"(?i)tip:",
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
