
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from festival import festival_info, list_artists, list_venues, load_data

app = FastAPI(title="Deauville Festival du Rire 2027")


@app.get("/api/festival")
def get_festival() -> dict:
    return festival_info(load_data())


@app.get("/api/venues")
def get_venues() -> list[dict]:
    return list_venues(load_data())


@app.get("/api/artists")
def get_artists() -> list[dict]:
    return list_artists(load_data())


web_directory = Path(__file__).parent / "web" / "public"

if web_directory.is_dir():
    app.mount(
        "/",
        StaticFiles(directory=str(web_directory), html=True),
        name="website",
    )