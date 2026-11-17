import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from innertube import InnerTube
from pytubefix import YouTube

app = FastAPI(title="InnerTube Opus Audio Streamer")
app.mount("/static", StaticFiles(directory="static"), name="static")

ytm_client = InnerTube("WEB_REMIX")


@app.get("/")
async def serve_frontend():
    return FileResponse("static/index.html")


@app.get("/api/search")
async def search_music(q: str):
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")

    data = ytm_client.search(query=q, params="EgWKAQIIAWoKEAMQBBAJEAoQBQ%3D%3D")
    results = []

    try:
        tabs = data["contents"]["tabbedSearchResultsRenderer"]["tabs"]
        section_contents = tabs[0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"]
        shelf_contents = []
        for section in section_contents:
            if "musicShelfRenderer" in section:
                shelf_contents = section["musicShelfRenderer"]["contents"]
                break

        for item in shelf_contents:
            renderer = item.get("musicResponsiveListItemRenderer", {})
            flex = renderer.get("flexColumns", [])
            if len(flex) < 2:
                continue

            title_runs = flex[0]["musicResponsiveListItemFlexColumnRenderer"]["text"].get("runs", [])
            artist_runs = flex[1]["musicResponsiveListItemFlexColumnRenderer"]["text"].get("runs", [])
            if not title_runs:
                continue

            title_run = title_runs[0]
            artist_name = artist_runs[0]["text"] if artist_runs else "Unknown Artist"
            video_id = title_run.get("navigationEndpoint", {}).get("watchEndpoint", {}).get("videoId")

            if video_id:
                results.append({
                    "id": video_id,
                    "title": title_run["text"],
                    "artist": artist_name,
                })
    except (KeyError, IndexError, TypeError):
        pass

    return results


@app.get("/api/stream/{video_id}")
async def stream_opus(video_id: str, request: Request):
    try:
        yt = YouTube(f"https://music.youtube.com/watch?v={video_id}")
        opus_stream = (
            yt.streams.filter(only_audio=True, audio_codec="opus")
            .order_by("abr")
            .desc()
            .first()
        )

        if not opus_stream:
            opus_stream = (
                yt.streams.filter(only_audio=True)
                .order_by("abr")
                .desc()
                .first()
            )

        if not opus_stream:
            raise HTTPException(status_code=404, detail="No audio stream found")

        stream_url = opus_stream.url
        range_header = request.headers.get("range", "bytes=0-")

        client = httpx.AsyncClient(follow_redirects=True, timeout=30.0)
        req = client.build_request("GET", stream_url, headers={"Range": range_header})
        upstream = await client.send(req, stream=True)

        async def audio_generator():
            try:
                async for chunk in upstream.aiter_bytes(chunk_size=65536):
                    yield chunk
            finally:
                await upstream.aclose()
                await client.aclose()

        headers = {
            "Content-Type": opus_stream.mime_type or 'audio/webm; codecs="opus"',
            "Accept-Ranges": "bytes",
        }
        if "content-length" in upstream.headers:
            headers["Content-Length"] = upstream.headers["content-length"]
        if "content-range" in upstream.headers:
            headers["Content-Range"] = upstream.headers["content-range"]

        return StreamingResponse(
            audio_generator(),
            status_code=upstream.status_code,
            headers=headers,
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
