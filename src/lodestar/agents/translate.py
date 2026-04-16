"""On-demand translation via the LLM endpoint with two-tier cache.

Tier 1: in-process dict (sub-ms hits, warm within a session).
Tier 2: SQLite `translation_cache` table (survives restarts).

Used by `/feed` to translate Vietnamese insight titles and summaries into
English or Korean when the client asks for a non-Vietnamese language. First
lookup goes: memory → DB → LLM → write-back to both caches.
"""

from __future__ import annotations

import asyncio
import logging

from openai import AsyncOpenAI

from lodestar.config import settings
from lodestar.database import get_db

logger = logging.getLogger(__name__)

SUPPORTED_LANGS = {"vi", "en", "ko"}

_LANG_NAME = {
    "vi": "Vietnamese",
    "en": "English",
    "ko": "Korean",
}

# In-process L1 cache: (text, target_lang) -> translated text
_CACHE: dict[tuple[str, str], str] = {}
_LOCK = asyncio.Lock()


def _get_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
    )


async def _db_lookup(text: str, target_lang: str) -> str | None:
    """Read a translation from the SQLite L2 cache."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT translated_text FROM translation_cache "
            "WHERE source_text = ? AND target_lang = ?",
            (text, target_lang),
        )
        row = await cursor.fetchone()
        return row[0] if row else None
    finally:
        await db.close()


async def _db_store(text: str, target_lang: str, translated: str) -> None:
    """Persist a translation to the SQLite L2 cache."""
    db = await get_db()
    try:
        await db.execute(
            "INSERT OR REPLACE INTO translation_cache "
            "(source_text, target_lang, translated_text) VALUES (?, ?, ?)",
            (text, target_lang, translated),
        )
        await db.commit()
    finally:
        await db.close()


async def translate_text(text: str, target_lang: str) -> str:
    """Translate short text into the target language with memoisation.

    Resolution order: in-process cache → SQLite cache → LLM call.
    Successful LLM calls write back to both tiers.

    Args:
        text: Source text. May be Vietnamese, English, or Korean.
        target_lang: One of "vi", "en", "ko". "vi" is a no-op only when
            the stored source is already Vietnamese — we pass through.

    Returns:
        Translated text, or the original if translation fails or the
        language is unsupported.
    """
    if not text or not text.strip():
        return text
    if target_lang not in SUPPORTED_LANGS:
        return text

    key = (text, target_lang)
    cached = _CACHE.get(key)
    if cached is not None:
        return cached

    if target_lang == "vi":
        # Canonical language — no translation needed.
        return text

    # L2: persistent DB cache.
    db_hit = await _db_lookup(text, target_lang)
    if db_hit is not None:
        _CACHE[key] = db_hit
        return db_hit

    async with _LOCK:
        cached = _CACHE.get(key)
        if cached is not None:
            return cached

        lang_name = _LANG_NAME[target_lang]
        # /no_think disables Qwen3's reasoning mode so the full token budget
        # goes to the translated output. Prompt is imperative and provides
        # guardrails to stop the model from "helpfully" keeping the source.
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
            # Best-effort DB persist; don't fail the request if it errors.
            try:
                await _db_store(text, target_lang, translated)
            except Exception:
                logger.exception("translation DB persist failed for lang=%s", target_lang)
            return translated
        except Exception:
            logger.exception("translate_text failed for lang=%s", target_lang)
            return text


async def translate_many(texts: list[str], target_lang: str) -> list[str]:
    """Translate multiple texts concurrently, preserving order.

    Args:
        texts: Source strings.
        target_lang: Target language code.

    Returns:
        Translated strings in the same order as `texts`.
    """
    if target_lang == "vi" or target_lang not in SUPPORTED_LANGS:
        return list(texts)
    return await asyncio.gather(*[translate_text(t, target_lang) for t in texts])


async def warm_cache_for_cards(
    pairs: list[tuple[str, str]],
    languages: tuple[str, ...] = ("en", "ko"),
) -> None:
    """Pre-translate titles and summaries across the non-Vietnamese locales.

    Called as a fire-and-forget task from the API lifespan so users who
    toggle language shortly after startup see the translated feed instantly
    instead of waiting for a cold LLM round-trip per card.

    Args:
        pairs: list of (title, summary) tuples from current insight cards.
        languages: Target languages to warm (defaults to en + ko).
    """
    texts: set[str] = set()
    for title, summary in pairs:
        if title:
            texts.add(title)
        if summary:
            texts.add(summary)

    for lang in languages:
        try:
            await translate_many(list(texts), lang)
            logger.info(
                "Translation cache warmed for lang=%s (%d entries)",
                lang,
                len(texts),
            )
        except Exception:
            logger.exception("Cache warmup failed for lang=%s", lang)
