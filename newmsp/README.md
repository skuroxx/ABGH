# InnerTube Opus Audio Streamer (Python)

A lightweight FastAPI project that searches YouTube Music via the InnerTube API, resolves direct Opus audio-only stream URLs without `yt-dlp` or FFmpeg, and streams live audio chunks directly to a web `<audio>` player without saving files to disk.

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the server:
   ```bash
   uvicorn app:app --reload --port 8000
   ```

3. Open `http://localhost:8000` in your browser.
