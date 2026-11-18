# SonicBridge (Vercel Zero-Storage Edition)

A zero-storage audio streaming web app combining a static glassmorphic UI, a Python metadata/stream resolver (`api/resolve.py`), and a Go HTTP 206 byte-range audio proxy (`api/stream.go`).

## Project Structure

```text
sonicbridge/
├── index.html          # Zero-storage glassmorphic web UI
├── requirements.txt    # Python dependencies for Vercel
├── go.mod              # Go module definition
├── vercel.json         # Vercel serverless routing & timeouts
└── api/
    ├── resolve.py      # Extracts track metadata & stream URL in memory
    └── stream.go       # Streams HTTP 206 byte-ranges with 0 B disk writes
```

## Deploy to Vercel

1. Install the Vercel CLI:
   ```bash
   npm i -g vercel
   ```
2. Deploy from the project root:
   ```bash
   vercel --prod
   ```

## Notes
- **Zero Disk Usage:** `skip_download=True` and `cachedir=False` ensure `resolve.py` never writes audio files to `/tmp`, while `stream.go` pipes bytes directly via `io.Copy`.
- **Rate Limits:** Because Vercel runs on cloud IP ranges, YouTube may occasionally rate-limit unauthenticated requests. You can configure `cookiefile` or `proxy` inside `ydl_opts` in `api/resolve.py` if needed.
