# uvicorn main:app --reload
from __future__ import annotations

import csv
import os
import re
from pathlib import Path
from typing import Any

import numpy as np
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from starlette.requests import Request
from starlette.templating import Jinja2Templates

# Paths and runtime configuration (overridable via environment variables).
BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "Dataset.csv"
DEFAULT_MODEL_NAME = os.getenv("FAQ_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
DEFAULT_THRESHOLD = float(os.getenv("FAQ_THRESHOLD", "0.50"))

# FastAPI app with static assets and HTML templates.
app = FastAPI(title="FAQ Chatbot", version="1.0.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


class ChatRequest(BaseModel):
    # Incoming user message.
    message: str


class ChatResponse(BaseModel):
    # What the chatbot returns to the UI.
    answer: str
    score: float
    matched_question: str | None
    category: str | None


# In-memory cache for the model, FAQs, and their embeddings.
_MODEL: SentenceTransformer | None = None
_FAQS: list[dict[str, str]] = []
_EMBEDDINGS: np.ndarray | None = None

_GREETING_WORDS = {
    "hi",
    "hello",
    "hey",
    "hola",
    "yo",
    "sup",
    "good morning",
    "good afternoon",
    "good evening",
}

_FALLBACK_MESSAGE = (
    "I did not find a good FAQ match for that. I can help with topics like shipping, "
    "returns, payments, orders, sizing, product info, account, support, and university "
    "services such as student records, IT support, accessibility, faculty support, and "
    "campus services. Try asking a more specific question."
)


def _maybe_fix_mojibake(text: str) -> str:
    # Fix common encoding artifacts if the CSV was saved with a different encoding.
    if any(ch in text for ch in ("\ufffd", "\u00c2", "\u00c3", "\u00e2", "\u201a", "\u00d4", "\u00f4")):
        try:
            return text.encode("latin1").decode("utf-8")
        except UnicodeError:
            return text
    return text


def _normalize_text(text: str) -> str:
    # Normalize quotes, dashes, and whitespace to keep matching stable.
    if not text:
        return ""
    text = _maybe_fix_mojibake(text)
    fixes = {
        "\u2019": "'",
        "\u2018": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u00a0": " ",
        "\u2026": "...",
        "\u201a\u00c4\u00f4": "'",
        "\u201a\u00c4\u00ec": "-",
        "\u201a\u00c4\u00f9": '"',
        "\u201a\u00c4\u00fa": '"',
    }
    for bad, good in fixes.items():
        text = text.replace(bad, good)
    return " ".join(text.split())


def _load_faqs(dataset_path: Path) -> list[dict[str, str]]:
    # Load the CSV using fallback encodings, then normalize content.
    if not dataset_path.exists():
        raise RuntimeError(f"Dataset not found: {dataset_path}")

    encodings = ["utf-8-sig", "utf-8", "cp1252"]
    last_error: Exception | None = None
    for encoding in encodings:
        try:
            with dataset_path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                rows: list[dict[str, str]] = []
                for row in reader:
                    if not row:
                        continue
                    question = _normalize_text(row.get("question", "").strip())
                    answer = _normalize_text(row.get("answer", "").strip())
                    category = _normalize_text(row.get("category", "").strip())
                    if question and answer:
                        rows.append({"question": question, "answer": answer, "category": category})
                if rows:
                    return rows
        except UnicodeError as exc:
            last_error = exc
            continue
    raise RuntimeError("Failed to read Dataset.csv with supported encodings") from last_error


def _is_greeting(message: str) -> bool:
    # Treat simple greetings as chatty small talk instead of a semantic FAQ query.
    normalized = re.sub(r"[^a-z0-9\s']+", " ", _normalize_text(message).lower()).strip()
    if not normalized:
        return False
    if normalized in _GREETING_WORDS:
        return True
    words = normalized.split()
    if len(words) > 3:
        return False
    return normalized in _GREETING_WORDS or words[0] in _GREETING_WORDS


def _greeting_response() -> ChatResponse:
    return ChatResponse(
        answer=(
            "Hello! I can help with shipping, returns, payments, orders, sizing, product info, "
            "account, support, and university services. Ask me a specific question whenever "
            "you are ready."
        ),
        score=1.0,
        matched_question=None,
        category="Greeting",
    )


def _get_model() -> SentenceTransformer:
    # Lazy-load the embedding model on first use.
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer(DEFAULT_MODEL_NAME)
    return _MODEL


def _ensure_index() -> None:
    # Build the FAQ embedding index once per process.
    global _FAQS, _EMBEDDINGS
    if _EMBEDDINGS is not None:
        return
    faqs = _load_faqs(DATASET_PATH)
    model = _get_model()
    questions = [faq["question"] for faq in faqs]
    embeddings = model.encode(questions, normalize_embeddings=True)
    _FAQS = faqs
    _EMBEDDINGS = np.array(embeddings, dtype=np.float32)


def _best_match(query: str, threshold: float) -> tuple[dict[str, str] | None, float]:
    # Cosine similarity for normalized vectors is just a dot product.
    _ensure_index()
    model = _get_model()
    query_vec = model.encode([query], normalize_embeddings=True)[0]
    scores = _EMBEDDINGS @ query_vec
    best_idx = int(np.argmax(scores))
    best_score = float(scores[best_idx])
    if best_score < threshold:
        return None, best_score
    return _FAQS[best_idx], best_score


def _build_response(match: dict[str, str] | None, score: float) -> ChatResponse:
    # Convert a match result into a structured API response.
    if match is None:
        return ChatResponse(
            answer=_FALLBACK_MESSAGE,
            score=score,
            matched_question=None,
            category=None,
        )
    return ChatResponse(
        answer=match["answer"],
        score=score,
        matched_question=match.get("question"),
        category=match.get("category"),
    )


# Serve the chat UI.
@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> Any:
    return templates.TemplateResponse(request, "index.html", {"request": request})


# Main chat endpoint used by the frontend.
@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    message = payload.message.strip()
    if not message:
        return ChatResponse(
            answer="Please type a question.",
            score=0.0,
            matched_question=None,
            category=None,
        )
    if _is_greeting(message):
        return _greeting_response()
    match, score = _best_match(message, DEFAULT_THRESHOLD)
    return _build_response(match, score)
