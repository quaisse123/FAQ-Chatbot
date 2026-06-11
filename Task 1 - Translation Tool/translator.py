"""
translator.py

Asynchronous translation module using MyMemory (primary) with automatic
fallback to Lingva (public instance) when MyMemory fails or rate-limits.

Usage:
  from translator import translate_text_async
  translated, detected = await translate_text_async(text, source, target)

Notes:
- MyMemory endpoint: https://api.mymemory.translated.net/get?q=...&langpair=src|tgt&de=email
- Lingva fallback: https://lingva.ml/{src}/{tgt}/{encoded_text}
"""

import os
from typing import Optional, Tuple
from urllib.parse import quote

import httpx

# Configurable endpoints / defaults via environment variables
MYMEMORY_URL = os.getenv("MYMEMORY_URL", "https://api.mymemory.translated.net/get")
MYMEMORY_DE_EMAIL = os.getenv("MYMEMORY_DE_EMAIL", "anon@example.com")
LINGVA_BASE_URL = os.getenv("LINGVA_BASE_URL", "https://lingva.ml")


class TranslationError(Exception):
    """Raised when no translation provider succeeds."""


async def _call_mymemory(text: str, source: str, target: str, client: httpx.AsyncClient, timeout: float = 10.0) -> str:
    """Call MyMemory public API and return the translated text.

    Raises httpx.HTTPStatusError or RuntimeError on failure.
    """
    params = {"q": text, "langpair": f"{source}|{target}"}
    if MYMEMORY_DE_EMAIL:
        params["de"] = MYMEMORY_DE_EMAIL

    resp = await client.get(MYMEMORY_URL, params=params, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()

    # Expected: response.responseData.translatedText
    translated = None
    resp_data = data.get("responseData") if isinstance(data, dict) else None
    if isinstance(resp_data, dict):
        translated = resp_data.get("translatedText")

    # Fallback: try matches list
    if not translated:
        matches = data.get("matches") if isinstance(data, dict) else None
        if isinstance(matches, list) and matches:
            # pick the best available translation candidate
            for m in matches:
                if isinstance(m, dict) and m.get("translation"):
                    translated = m.get("translation")
                    break

    if not translated:
        raise RuntimeError("MyMemory did not return a translated text")

    return translated


async def _call_lingva(text: str, source: str, target: str, client: httpx.AsyncClient, timeout: float = 10.0) -> str:
    """Call Lingva public instance and return translated text.

    Builds a path-based request: {base}/{src}/{tgt}/{encoded_text}
    """
    base = LINGVA_BASE_URL.rstrip("/")
    encoded = quote(text, safe="")
    url = f"{base}/{source}/{target}/{encoded}"

    resp = await client.get(url, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()

    # Accept several possible shapes: {"translation": ...} or {"response": {"translation": ...}}
    translation = None
    if isinstance(data, dict):
        if "translation" in data:
            translation = data.get("translation")
        elif "response" in data and isinstance(data["response"], dict):
            translation = data["response"].get("translation")
        elif "translatedText" in data:
            translation = data.get("translatedText")

    if not translation:
        raise RuntimeError("Lingva did not return a translated text")

    return translation


async def translate_text_async(text: str, source: str, target: str) -> Tuple[str, Optional[str]]:
    """Translate text from `source` to `target`.

    Tries MyMemory first (adds `de` email param if configured), then falls back
    to Lingva if MyMemory fails (network error, non-200, JSON missing, 429, etc.).

    Returns a tuple: (translated_text, detected_source_language_or_None)
    Detection is not provided by these public APIs, so the second item will be None.
    """
    if not text or not text.strip():
        return "", None

    if not source:
        source = "auto"

    async with httpx.AsyncClient() as client:
        # Try MyMemory
        try:
            translated = await _call_mymemory(text, source, target, client)
            return translated, None
        except Exception as e:
            # Attempt Lingva fallback
            try:
                translated = await _call_lingva(text, source, target, client)
                return translated, None
            except Exception as e2:
                # Chain errors for debugging
                raise TranslationError(f"MyMemory failed: {e!s}; Lingva failed: {e2!s}") from e2
