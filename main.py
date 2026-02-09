# main.py
import json
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from parser import parse_playlist_url, fetch_playlist

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@app.get("/api/playlist")
async def get_playlist(url: str):
    info = parse_playlist_url(url)
    if not info:
        return {"error": "Неверная ссылка"}

    playlist = await fetch_playlist(
        info["owner"],
        info["playlist_id"]
    )

    with open("playlist.json", "w", encoding="utf-8") as file:
        json.dump(playlist, file, ensure_ascii=False, indent=4)

    #браузер сразу скачивает файл без согласия на то пользователя
    return FileResponse(
        "playlist.json",
        media_type="application/json",
        filename="playlist.json"
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
