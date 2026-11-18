from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import yt_dlp

app = FastAPI()


@app.get("/api/resolve")
def resolve_track(url: str = Query(..., description="YouTube or Spotify URL")):
    """
    Zero-storage resolver: extracts metadata and a direct playable audio stream URL
    without writing any media files to disk.
    """
    search_target = url
    source_label = "YouTube"

    # If a Spotify URL is supplied, extract title/artist via oEmbed or page metadata
    # and resolve the matching audio stream via yt-dlp in memory.
    if "spotify.com" in url:
        source_label = "spotDL / YouTube Match"
        try:
            import urllib.request
            import json

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
