# SonicBridge (Vercel Zero-Storage Edition)

A zero-storage audio streaming web app combining a glassmorphic UI (`public/index.html`) and a unified FastAPI backend (`api/resolve.py`) that serves the UI, extracts stream URLs, and proxies HTTP 206 byte-ranges in memory with zero disk writes.

## Project Structure

```text
sonicbridge/
├── public/
│   └── index.html      # Zero-storage glassmorphic web UI
├── index.html          # Root fallback copy of the UI
├── pyproject.toml      # Vercel FastAPI entrypoint & dependencies
├── requirements.txt    # Python dependencies fallback
├── vercel.json         # Vercel serverless routing & timeouts
└── api/
    └── resolve.py      # / (UI) + /api/resolve (metadata) + /api/stream (HTTP 206 proxy)
```

## Deploy to Vercel

1. Extract the contents of `sonicbridge/` directly into your GitHub repository root (`github.com/skuroxx/ABGH`) so `public/`, `api/`, `pyproject.toml`, and `vercel.json` are at the top level.
2. Redeploy in Vercel.
