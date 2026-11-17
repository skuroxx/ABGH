import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from innertube import InnerTube
from pytubefix import YouTube

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ytm_client = InnerTube("WEB_REMIX")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/search")
async def search_music(q: str):
    if not q or not q.strip():
        return []
    try:
        data = ytm_client.search(query=q.strip(), params="EgWKAQIIAWoKEAMQBBAJEAoQBQ%3D%3D")
        results = []

        tabs = data.get("contents", {}).get("tabbedSearchResultsRenderer", {}).get("tabs", [])
        if not tabs:
            return []

        sections = (
            tabs[0]
            .get("tabRenderer", {})
            .get("content", {})
            .get("sectionListRenderer", {})
            .get("contents", [])
        )

        for section in sections:
            shelf = section.get("musicShelfRenderer")
            if not shelf:
                continue
            for item in shelf.get("contents", []):
                renderer = item.get("musicResponsiveListItemRenderer", {})
                flex = renderer.get("flexColumns", [])
                if len(flex) < 2:
                    continue

                title_runs = (
                    flex[0]
                    .get("musicResponsiveListItemFlexColumnRenderer", {})
                    .get("text", {})
                    .get("runs", [])
                )
                artist_runs = (
                    flex[1]
                    .get("musicResponsiveListItemFlexColumnRenderer", {})
                    .get("text", {})
                    .get("runs", [])
                )

                if not title_runs:
                    continue

                title_obj = title_runs[0]
                video_id = (
                    title_obj.get("navigationEndpoint", {})
                    .get("watchEndpoint", {})
                    .get("videoId")
                )
                if not video_id:
                    video_id = renderer.get("playlistItemData", {}).get("videoId")

                artist_name = "".join(r.get("text", "") for r in artist_runs) if artist_runs else "Unknown Artist"

                if video_id:
                    results.append({
                        "id": video_id,
                        "title": title_obj.get("text", "Unknown Title"),
                        "artist": artist_name
                    })

        return results
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


def resolve_audio_stream(video_id: str):
    url = f"https://www.youtube.com/watch?v={video_id}"
    for client_name in ["ANDROID_VR", "WEB_CREATOR", "IOS", "ANDROID"]:
        try:
            yt = YouTube(url, client=client_name)
            stream = (
                yt.streams.filter(only_audio=True, audio_codec="opus")
                .order_by("abr")
                .desc()
                .first()
            )
            if not stream:
                stream = (
                    yt.streams.filter(only_audio=True)
                    .order_by("abr")
                    .desc()
                    .first()
                )
            if stream and stream.url:
                return stream
        except Exception:
            continue
    return None


@app.get("/api/stream/{video_id}")
async def stream_audio(video_id: str, request: Request):
    stream = resolve_audio_stream(video_id)
    if not stream:
        raise HTTPException(status_code=404, detail="Could not resolve audio stream (YouTube may have blocked this server IP).")

    range_header = request.headers.get("range", "bytes=0-")
    headers_to_send = {
        "Range": range_header,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    client = httpx.AsyncClient(follow_redirects=True, timeout=30.0)
    req = client.build_request("GET", stream.url, headers=headers_to_send)
    upstream = await client.send(req, stream=True)

    if upstream.status_code >= 400:
        await upstream.aclose()
        await client.aclose()
        raise HTTPException(status_code=upstream.status_code, detail="Upstream audio server rejected the stream request.")

    async def audio_generator():
        try:
            async for chunk in upstream.aiter_bytes(chunk_size=65536):
                yield chunk
        finally:
            await upstream.aclose()
            await client.aclose()

    resp_headers = {
        "Content-Type": stream.mime_type or 'audio/webm; codecs="opus"',
        "Accept-Ranges": "bytes",
        "Cache-Control": "no-store",
    }
    if "content-length" in upstream.headers:
        resp_headers["Content-Length"] = upstream.headers["content-length"]
    if "content-range" in upstream.headers:
        resp_headers["Content-Range"] = upstream.headers["content-range"]

    return StreamingResponse(
        audio_generator(),
        status_code=upstream.status_code,
        headers=resp_headers,
    )
