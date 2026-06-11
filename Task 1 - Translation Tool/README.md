# Simple Translation Tool

This is a small FastAPI app that serves a polished single-page UI and a translation API endpoint.

Features
- Simple, professional UI (Bootstrap + custom CSS)
- Uses the public MyMemory API (primary) with a Lingva public instance fallback
- Copy result and browser-based text-to-speech (no server-side audio)

Quick start (Windows)

1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies

```powershell
pip install -r requirements.txt
```


3. Configure optional environment variables

By default the app uses the public MyMemory API and will work without any API keys. To increase anonymous quota, set a generic email in your env:

```powershell
setx MYMEMORY_DE "anon@example.com"
# restart your shell to pick up setx values
```

You can also override endpoints (not usually required):

```powershell
setx MYMEMORY_ENDPOINT "https://api.mymemory.translated.net/get"
setx LINGVA_ENDPOINT "https://lingva.ml"
```

4. Run the app

```powershell
uvicorn main:app --reload
```

5. Open the UI

Open http://127.0.0.1:8000 in your browser.

Extra steps outside VS Code

- Obtain Azure Translator credentials
  1. Go to https://portal.azure.com
  2. Create a new resource: Search for "Translator" (Cognitive Services / Translator)
  3. After deployment, open the resource and copy the **Key** and **Region**; use them in the env variables above.


- Run on a remote server
  - Expose port 8000, or run behind a production server (Gunicorn + Uvicorn workers) and a reverse proxy.

Privacy

Text is forwarded to the configured translation provider (Azure or Google). No logs are kept by this app beyond what your provider or server records.

Notes

- Browser's speech synthesis uses local voices; availability depends on the user's browser and OS.
- For production use, prefer Azure or Google official APIs and secure your keys.
