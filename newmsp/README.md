# InnerTube Opus Audio Streamer (Fixed)

## Local Run (Windows / macOS / Linux)
```bash
python -m pip install -r requirements.txt
python -m uvicorn api.index:app --reload --port 8000
```
Open `http://localhost:8000` in your browser.

## Deploy to Vercel
1. Upload all files in this folder to a GitHub repository.
2. Import the repository into Vercel and click **Deploy**.
3. If Vercel's cloud IP is blocked by YouTube (`403` error during playback), deploy this exact same repo to **Render** (`uvicorn api.index:app --host 0.0.0.0 --port $PORT`).
