# Vercel InnerTube Audio Streamer

A serverless Python FastAPI application ready for Vercel that searches YouTube Music via the InnerTube API and resolves direct audio stream links without storing files or using `yt-dlp`.

## Project Structure

- `api/index.py` — FastAPI serverless endpoints (`/api/search` and `/api/stream/{video_id}`) using `RedirectResponse` to avoid serverless timeouts.
- `public/index.html` — Web frontend with search, direct Video ID/URL input, and an HTML5 `<audio>` player.
- `vercel.json` — Routing configuration for Vercel.
- `requirements.txt` — Python dependencies installed automatically by Vercel.

## Deploy to Vercel

1. Push this folder to a GitHub repository (or install the Vercel CLI with `npm i -g vercel`).
2. Import the repository on [vercel.com](https://vercel.com) or run `vercel --prod` inside this directory.
