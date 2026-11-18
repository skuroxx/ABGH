# SonicBridge (Vercel Zero-Storage Edition)

A zero-storage audio streaming web app combining a static glassmorphic UI and a unified FastAPI backend (`api/resolve.py`) that extracts stream URLs and proxies HTTP 206 byte-ranges in memory with zero disk writes.

## Project Structure

```text
sonicbridge/
├── index.html          # Zero-storage glassmorphic web UI
├── pyproject.toml      # Vercel FastAPI entrypoint & dependencies
├── requirements.txt    # Python dependencies fallback
├── vercel.json         # Vercel serverless function timeout config
└── api/
    └── resolve.py      # /api/resolve (metadata) + /api/stream (HTTP 206 proxy)
```

## Deploy to Vercel

1. Push the contents of `sonicbridge/` to your GitHub repository root (so `index.html`, `pyproject.toml`, `vercel.json`, and `api/` are at the top level of the repo).
2. Trigger a redeploy in Vercel.

## Notes
- **Zero Disk Usage:** `skip_download=True` and `cachedir=False` ensure `/api/resolve` never writes audio files to `/tmp`, while `/api/stream` streams 64 KB chunks asynchronously via `httpx` with zero disk writes.
- **Rate Limits:** Because Vercel runs on cloud IP ranges, YouTube may occasionally rate-limit unauthenticated requests. You can configure `cookiefile` or `proxy` inside `ydl_opts` in `api/resolve.py` if needed.
