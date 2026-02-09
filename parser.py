# parser.py
import re
import httpx

def parse_playlist_url(url: str):
    m = re.search(r"/users/([^/]+)/playlists/(\d+)", url)
    if not m:
        return None
    return {"owner": m.group(1), "playlist_id": m.group(2)}

def parse_tracks(data: dict) -> list[dict]:
    playlist = data.get("playlist")
    if not playlist:
        raise RuntimeError("Плейлист не найден")

    tracks = playlist.get("tracks")
    if not tracks:
        raise RuntimeError("Плейлист пуст")

    playlist_title = playlist.get("title")

    result = []

    for track in tracks:
        title = track.get("title")
        track_id = track.get("id")

        artists = [
            artist.get("name")
            for artist in track.get("artists", [])
            if artist.get("name")
        ]

        cover_uri = None
        album_id = None
        albums = track.get("albums", [])
        if albums:
            album_id = albums[0].get("id")
            cover_uri = albums[0].get("coverUri")
            if cover_uri and cover_uri.startswith("avatars.yandex.net"):
                cover_uri = "https://" + cover_uri.replace("%%", "400x400")

        iframe = f"""
        <iframe frameborder="0" allow="clipboard-write"
        style="border:none;width:614px;height:244px;"
        src="https://music.yandex.ru/iframe/album/{album_id}/track/{track_id}">
        </iframe>
        """

        result.append({
            "title": title,
            "artists": artists,
            "cover": cover_uri,
            "iframe": iframe
        })

    result.append({'playlist_title': playlist_title})

    return result

async def fetch_playlist(owner: str, kind: str):
    url = f"https://music.yandex.ru/handlers/playlist.jsx?owner={owner}&kinds={kind}"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url)
        r.raise_for_status()
        return parse_tracks(r.json())
