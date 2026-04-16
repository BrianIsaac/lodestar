"""Lightweight on-demand translation via the LLM endpoint.

Used by the `/feed` endpoint to translate pre-generated Vietnamese insight
card titles and summaries into English or Korean when the client asks for
a non-Vietnamese language. Results are cached in process memory so each
(text, language) pair only costs one LLM round-trip per process lifetime.
"""

from __future__ import annotations

import asyncio
import logging

from openai import AsyncOpenAI

from lodestar.config import settings

logger = logging.getLogger(__name__)

SUPPORTED_LANGS = {"vi", "en", "ko"}

_LANG_NAME = {
    "vi": "Vietnamese",
    "en": "English",
    "ko": "Korean",
}

# (text, target_lang) -> translated text
_CACHE: dict[tuple[str, str], str] = {}
_LOCK = asyncio.Lock()


def _get_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
    )


async def translate_text(text: str, target_lang: str) -> str:
    """Translate a Vietnamese text snippet into the target language.

    Args:
        text: Source text in Vietnamese.
        target_lang: One of "vi", "en", "ko". "vi" is a no-op.

    Returns:
        The translated text, or the original if translation fails or the
        language is unsupported.
    """
    if not text or not text.strip():
        return text
    if target_lang == "vi" or target_lang not in SUPPORTED_LANGS:
        return text

    key = (text, target_lang)
    cached = _CACHE.get(key)
    if cached is not None:
        return cached

    async with _LOCK:
        cached = _CACHE.get(key)
        if cached is not None:
            return cached

        lang_name = _LANG_NAME[target_lang]
        # /no_think disables Qwen3's reasoning mode so the full token budget
        # goes to the translated output. Prompt is imperative and provides
        # examples to prevent the model from "helpfully" keeping the source.
        prompt = (
            f"Translate the following short financial text into {lang_name} ({target_lang}).\n"
            f"Rules:\n"
            f"- Output ONLY the translated text. Do not add explanations, quotes, or language tags.\n"
            f"- Preserve currency amounts and numeric values exactly.\n"
            f"- Translate even if the source is already in another language — always output {lang_name}.\n\n"
            f"Source:\n{text}\n\n"
            f"{lang_name} translation: /no_think"
        )

        try:
            client = _get_client()
            resp = await client.chat.completions.create(
                model=settings.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=400,
            )
            translated = (resp.choices[0].message.content or "").strip()
            # Strip leaked <think></think> blocks in case /no_think is ignored.
            if "</think>" in translated:
                translated = translated.split("</think>", 1)[1].strip()
            # Strip wrapping quotes the model sometimes adds.
            if len(translated) >= 2 and translated[0] in '"“' and translated[-1] in '"”':
                translated = translated[1:-1].strip()
            if not translated:
                return text
            _CACHE[key] = translated
            return translated
        except Exception:
            logger.exception("translate_text failed for lang=%s", target_lang)
            return text


async def translate_many(texts: list[str], target_lang: str) -> list[str]:
    """Translate multiple texts concurrently, preserving order.

    Args:
        texts: List of Vietnamese source strings.
        target_lang: Target language code.

    Returns:
        Translated strings in the same order as `texts`.
    """
    if target_lang == "vi" or target_lang not in SUPPORTED_LANGS:
        return list(texts)
    return await asyncio.gather(*[translate_text(t, target_lang) for t in texts])
