"""Compliance filter — classifies output before delivery to customer.

Uses rule-based classification for the PoC. In production, this would
be an LLM classifier with higher accuracy on edge cases.
"""

import re

from qwen_viet.models import ComplianceClass

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

DISCLAIMER_VI = "Đây là thông tin tham khảo, không phải tư vấn tài chính."
DISCLAIMER_EN = "This is informational content, not financial advice."


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
        language: Language code for disclaimer.

    Returns:
        Tuple of (processed text, classification).
        If classified as advice, text is replaced with a refusal.
        If classified as guidance, disclaimer is appended.
    """
    classification = classify_output(text)

    if classification == ComplianceClass.ADVICE:
        refusal = (
            "Xin lỗi, tôi chỉ có thể cung cấp thông tin sản phẩm. "
            "Để được tư vấn tài chính, vui lòng liên hệ chuyên viên Shinhan."
            if language == "vi"
            else "I can only provide product information. "
            "For financial advice, please contact a Shinhan advisor."
        )
        return refusal, classification

    if classification == ComplianceClass.GUIDANCE:
        disclaimer = DISCLAIMER_VI if language == "vi" else DISCLAIMER_EN
        return f"{text}\n\n{disclaimer}", classification

    return text, classification
