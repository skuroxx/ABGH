from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from innertube import InnerTube
from pytubefix import YouTube

app = FastAPI()
ytm_client = InnerTube("WEB_REMIX")


@app.get("/api/search")
async def search_music(q: str):
    if not q.strip():
        return []
    data = ytm_client.search(query=q, params="EgWKAQIIAWoKEAMQBBAJEAoQBQ%3D%3D")
    results = []
    try:
        contents = (
            data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]
            ["content"]["sectionListRenderer"]["contents"][0]["musicShelfRenderer"]["contents"]
        )
        for item in contents:
            flex = item["musicResponsiveListItemRenderer"]["flexColumns"]
            title_run = flex[0]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"][0]
            artist_run = flex[1]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"][0]
            video_id = title_run.get("navigationEndpoint", {}).get("watchEndpoint", {}).get("videoId")
            if video_id:
                results.append({
                    "id": video_id,
                    "title": title_run["text"],
                    "artist": artist_run["text"]
                })
    except (KeyError, IndexError, TypeError):
        pass
    return results


@app.get("/api/stream/{video_id}")
async def stream_audio(video_id: str):
    try:
        yt = YouTube(f"https://music.youtube.com/watch?v={video_id}", client="IOS")
        audio_stream = (
            yt.streams.filter(only_audio=True)
            .order_by("abr")
            .desc()
            .first()
        )
        if not audio_stream:
            raise HTTPException(status_code=404, detail="No audio stream found")

        return RedirectResponse(url=audio_stream.url, status_code=302)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
