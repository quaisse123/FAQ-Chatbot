"""
Simple Translation Tool (FastAPI)

Serves the single-page UI and uses MyMemory (primary) with Lingva fallback
for anonymous, no-credit-card translation usage.

Run locally:
  pip install -r requirements.txt
  uvicorn main:app --reload

The UI is served at http://127.0.0.1:8000/
"""

import os
import re
from typing import Optional, Tuple
from urllib.parse import quote_plus

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="Simple Translation Tool")

# Templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Minimal curated list of languages for the UI (code -> display name)
LANGUAGES = {
	"en": "English",
	"es": "Spanish",
	"fr": "French",
	"de": "German",
	"zh": "Chinese (Simplified)",
	"zh-TW": "Chinese (Traditional)",
	"ja": "Japanese",
	"ko": "Korean",
	"ar": "Arabic",
	"ru": "Russian",
	"pt": "Portuguese",
	"hi": "Hindi",
	"it": "Italian",
	"nl": "Dutch",
	"sv": "Swedish",
	"tr": "Turkish",
	"vi": "Vietnamese",
	"id": "Indonesian",
	"pl": "Polish",
	"th": "Thai",
	"he": "Hebrew",
	"cs": "Czech",
	"da": "Danish",
	"fi": "Finnish",
	"no": "Norwegian",
	"ro": "Romanian",
	"hu": "Hungarian",
	"el": "Greek",
	"bn": "Bengali",
	"ms": "Malay",
	"fa": "Persian",
}


class TranslateRequest(BaseModel):
	text: str
	source: Optional[str] = "en"
	target: str


_LANG_TAG_RE = re.compile(r"^[A-Za-z]{2}(?:-[A-Za-z0-9]+)*$")


def _normalize_lang(code: str) -> str:
	"""Normalize language tag: strip, replace underscores with hyphens.

	Returns the normalized tag (e.g. zh_cn -> zh-cn) or 'auto'.
	"""
	if not code:
		return ""
	code = code.strip()
	if code.lower() == "auto":
		return "auto"
	return code.replace("_", "-")


def _validate_lang_pair(source: str, target: str) -> Tuple[str, str]:
	"""Validate and normalize language pair for MyMemory/Lingva.

	Raises HTTPException(400) on invalid input.
	"""
	src = _normalize_lang(source or "")
	tgt = _normalize_lang(target or "")

	if not tgt or tgt.lower() == "auto":
		raise HTTPException(status_code=400, detail="Invalid target language: target must be a specific language (not 'auto'). Example: 'en' or 'zh-CN'.")

	# allow 'auto' only for source
	if src != "auto":
		if not _LANG_TAG_RE.match(src):
			raise HTTPException(status_code=400, detail=f"Invalid source language tag: {source!r}. Use 2-letter ISO or RFC3066 (e.g. 'en' or 'zh-CN').")

	if not _LANG_TAG_RE.match(tgt):
		raise HTTPException(status_code=400, detail=f"Invalid target language tag: {target!r}. Use 2-letter ISO or RFC3066 (e.g. 'en' or 'zh-CN').")

	return src, tgt


async def translate_mymemory(text: str, source: str, target: str) -> Tuple[str, Optional[str]]:
	"""Translate using the public MyMemory API (anonymous).

	Uses `MYMEMORY_ENDPOINT` override if set and `MYMEMORY_DE` (email) to increase quota.
	Returns (translated_text, detected_source_or_none).
	"""
	endpoint = os.getenv("MYMEMORY_ENDPOINT", "https://api.mymemory.translated.net/get")
	de = os.getenv("MYMEMORY_DE", "")

	params = {"q": text}
	# When source is provided and not 'auto', include langpair (e.g. en|fr).
	if source and source != "auto":
		params["langpair"] = f"{source}|{target}"
	else:
		# omit langpair to let MyMemory attempt detection when source == 'auto'
		pass

	if de:
		params["de"] = de

	async with httpx.AsyncClient(timeout=10) as client:
		resp = await client.get(endpoint, params=params)
		resp.raise_for_status()
		data = resp.json()

	# MyMemory usual response shape: { responseData: { translatedText: ... }, ... }
	translated = None
	detected = None
	if isinstance(data, dict):
		rd = data.get("responseData")
		if isinstance(rd, dict):
			translated = rd.get("translatedText")
		# Some proxies wrap under 'response'
		if not translated and "response" in data:
			rd2 = data.get("response", {}).get("responseData")
			if isinstance(rd2, dict):
				translated = rd2.get("translatedText")

		# best-effort detected language extraction (may be empty)
		detected = data.get("responseData", {}).get("detectedLanguage") or data.get("response", {}).get("detectedLanguage")

	if not translated:
		raise RuntimeError("MyMemory did not return a translated text")

	return translated, detected


async def translate_lingva(text: str, source: str, target: str) -> Tuple[str, Optional[str]]:
	"""Translate using a public Lingva instance as fallback.

	Tries a couple of common Lingva endpoints and parses likely response shapes.
	"""
	base = os.getenv("LINGVA_ENDPOINT", "https://lingva.ml").rstrip("/")
	encoded = quote_plus(text)
	candidates = [
		f"{base}/{source}/{target}/{encoded}",
		f"{base}/api/v1/{source}/{target}/{encoded}",
	]

	async with httpx.AsyncClient(timeout=10) as client:
		for url in candidates:
			try:
				resp = await client.get(url)
				resp.raise_for_status()
				data = resp.json()
				if isinstance(data, dict):
					# common keys
					translated = data.get("translation") or data.get("translatedText") or data.get("result") or data.get("text")
					if not translated and "response" in data:
						translated = data.get("response", {}).get("translation")
					if translated:
						return translated, None
			except Exception:
				# try next candidate
				continue

	raise RuntimeError("Lingva fallback failed to return a translation")


async def translate_text_async(text: str, source: str, target: str) -> Tuple[str, Optional[str]]:
	"""High-level translator: try MyMemory, then Lingva on error.

	Returns (translated_text, detected_source_or_none).
	"""
	if not text or not text.strip():
		return "", None

	# Try MyMemory first
	try:
		return await translate_mymemory(text, source, target)
	except Exception as e:
		# fallback to Lingva
		try:
			return await translate_lingva(text, source if source != "auto" else "auto", target)
		except Exception as e2:
			raise HTTPException(status_code=502, detail=f"Both providers failed: mymemory: {e}; lingva: {e2}")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
	"""Render the main UI (server-side provides the language list)."""
	return templates.TemplateResponse(request, "index.html", {"languages": LANGUAGES})


@app.post("/api/translate")
async def api_translate(payload: TranslateRequest):
	"""Translate text and return JSON with the translated text and detected source language."""
	try:
		translated, detected = await translate_text_async(payload.text, payload.source, payload.target)
		return JSONResponse({"translated_text": translated, "detected_source": detected})
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
	import uvicorn

	uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

