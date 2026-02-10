# parser.py
import re
import httpx

def parse_playlist_url(url: str):
    m = re.search(r"/users/([^/]+)/playlists/(\d+)", url)
    if m:
        return {
            "type": "user",
            "owner": m.group(1),
            "playlist_id": m.group(2),
        }
    m = re.search(r"/playlists/(\d+)", url)
    if m:
        return {
            "type": "lk",
            "playlist_id": m.group(1),
        }
    return None

def parse_tracks(data: dict) -> list[dict]:
    playlist = data.get("playlist")
    if not playlist:
        raise RuntimeError("Плейлист не найден/Playlist not found")

    tracks = playlist.get("tracks")
    if not tracks:
        raise RuntimeError("Плейлист пуст/Playlist is empty")

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

async def fetch_playlist(parsed: dict):
    async with httpx.AsyncClient(timeout=10) as client:

        if parsed["type"] == "user":
            url = (
                f"https://music.yandex.ru/handlers/playlist.jsx?owner={parsed['owner']}&kinds={parsed['playlist_id']}"
            )
        elif parsed["type"] == "lk":
            url = (
                f"https://api.music.yandex.by/playlist/{parsed['playlist_id']}?resumestream=false&richtracks=true"
            )
        else:
            raise ValueError("Неизвестный тип плейлиста")

        r = await client.get(url)
        if r.status_code == 302:
            return {
                "error": "Яндекс требует прохождение капчи/авторизацию",
                "type": parsed["type"],
            }
        r.raise_for_status()
        return r.json()
