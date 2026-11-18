from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse
from urllib.parse import urlparse
import httpx
import yt_dlp
import urllib.request
import json

app = FastAPI()


@app.get("/api/health")
@app.get("/health")
def health_check():
    return {"status": "ok", "mode": "zero-storage"}


@app.get("/api/resolve")
@app.get("/resolve")
def resolve_track(url: str = Query(..., description="YouTube or Spotify URL")):
    """
    Zero-storage resolver: extracts metadata and a direct playable audio stream URL
    without writing any media files to disk.
    """
    search_target = url
    source_label = "YouTube"

    if "spotify.com" in url:
        source_label = "spotDL / YouTube Match"
        try:
            oembed_url = f"https://open.spotify.com/oembed?url={url}"
            with urllib.request.urlopen(oembed_url, timeout=8) as resp:
                meta = json.loads(resp.read().decode("utf-8"))
                title = meta.get("title", "")
                if title:
                    search_target = f"ytsearch1:{title} audio"
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Spotify metadata lookup failed: {exc}")

    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "cachedir": False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_target, download=False)
            if "entries" in info and info["entries"]:
                info = info["entries"][0]

            stream_url = info.get("url")
            if not stream_url:
                raise HTTPException(status_code=502, detail="No direct audio stream URL found")

            return JSONResponse(
                {
                    "title": info.get("title", "Unknown Title"),
                    "artist": info.get("uploader") or info.get("artist") or "Unknown Artist",
                    "cover": info.get("thumbnail", ""),
                    "duration": info.get("duration", 0),
                    "source": source_label,
                    "stream_url": stream_url,
                }
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/stream")
@app.get("/stream")
async def stream_audio(request: Request, url: str = Query(..., description="Upstream CDN audio URL")):
    """
    Zero-storage async HTTP 206 byte-range audio proxy.
    Streams chunks directly from upstream CDN to the browser without touching disk.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise HTTPException(status_code=400, detail="Invalid upstream URL")

    host = parsed.hostname.lower()
    if not (host.endswith("googlevideo.com") or host.endswith("youtube.com")):
        raise HTTPException(status_code=403, detail="Unsupported upstream host")

    upstream_headers = {"User-Agent": "Mozilla/5.0"}
    if range_header := request.headers.get("range"):
        upstream_headers["Range"] = range_header

    client = httpx.AsyncClient(timeout=None, follow_redirects=True)
    req = client.build_request("GET", url, headers=upstream_headers)
    resp = await client.send(req, stream=True)

    response_headers = {"Cache-Control": "no-store"}
    for h in ("content-type", "content-length", "content-range", "accept-ranges"):
        if h in resp.headers:
            response_headers[h] = resp.headers[h]

    async def iter_bytes():
        try:
            async for chunk in resp.aiter_bytes(chunk_size=65536):
                yield chunk
        finally:
            await resp.aclose()
            await client.aclose()

    return StreamingResponse(
        iter_bytes(),
        status_code=resp.status_code,
        headers=response_headers,
    )
