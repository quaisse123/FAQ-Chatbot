import json
import os
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from faqs_data import build_faqs


def load_environment():
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass


load_environment()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free"
)
OPENROUTER_URL = os.getenv(
    "OPENROUTER_URL", "https://openrouter.ai/api/v1/chat/completions"
)
OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL", "http://localhost")
OPENROUTER_APP_NAME = os.getenv("OPENROUTER_APP_NAME", "faq-chatbot")
OPENROUTER_TIMEOUT = float(os.getenv("OPENROUTER_TIMEOUT", "15"))
print(
    f"[LLM] OpenRouter enabled: {bool(OPENROUTER_API_KEY)} | model: {OPENROUTER_MODEL}",
    flush=True,
)


def build_vectorizer(faqs):
    questions = [item["q"] for item in faqs]
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(questions)
    return vectorizer, matrix


def rewrite_question_with_llm(question):
    if not question.strip():
        print("[LLM] skip: empty question", flush=True)
        return question
    if not OPENROUTER_API_KEY:
        print("[LLM] skip: missing API key", flush=True)
        return question

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Rewrite the user question into a short, clear FAQ search query. "
                    "Keep the meaning, remove filler. Return only the rewritten query."
                ),
            },
            {"role": "user", "content": question},
        ],
        "temperature": 0.2,
        "max_tokens": 48,
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": OPENROUTER_SITE_URL,
        "X-Title": OPENROUTER_APP_NAME,
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        request = urlrequest.Request(
            OPENROUTER_URL, data=data, headers=headers, method="POST"
        )
        with urlrequest.urlopen(request, timeout=OPENROUTER_TIMEOUT) as response:
            body = response.read().decode("utf-8")
        data = json.loads(body)
        choices = data.get("choices", [])
        message = choices[0].get("message", {}) if choices else {}
        content = message.get("content")
        if content:
            content = content.strip()
        else:
            content = ""
        print(f"[LLM] rewrite: {content}", flush=True)
        return content or question
    except HTTPError as exc:
        try:
            body = exc.read().decode("utf-8")
        except Exception:
            body = ""
        snippet = body[:400].replace("\n", " ") if body else ""
        print(
            f"[LLM] error: HTTPError {exc.code} {exc.reason} | {snippet}",
            flush=True,
        )
        return question
    except (URLError, KeyError, ValueError) as exc:
        print(f"[LLM] error: {type(exc).__name__}", flush=True)
        return question


def get_best_answer(user_question, faqs, vectorizer, matrix, threshold=0.2):
    if not user_question.strip():
        return "Please type a question so I can help."

    user_vector = vectorizer.transform([user_question])
    scores = cosine_similarity(user_vector, matrix)[0]
    best_index = int(scores.argmax())
    if float(scores[best_index]) < threshold:
        return "I am not sure about that. Try asking about delivery, payments, refunds, or scheduling."
    return faqs[best_index]["a"]


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
FAQS = build_faqs(total_target=500)
VECTORIZER, FAQ_MATRIX = build_vectorizer(FAQS)  # Precompute vectors once.


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})


class QuestionPayload(BaseModel):
    question: str = ""
    use_llm: bool = True


@app.post("/api/ask")
def ask(payload: QuestionPayload):
    question = payload.question or ""
    print(f"[LLM] request: use_llm={payload.use_llm} | q='{question}'", flush=True)
    if payload.use_llm:
        rewritten = rewrite_question_with_llm(question).strip() or question
    else:
        print("[LLM] disabled by toggle", flush=True)
        rewritten = question
    answer = get_best_answer(rewritten, FAQS, VECTORIZER, FAQ_MATRIX)
    return {"answer": answer}


