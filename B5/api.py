
from datetime import date, timedelta
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from festival import list_artists, list_venues, load_data

app = FastAPI(title="Deauville Festival du Rire 2027")


@app.get("/api/festival")
def get_festival() -> dict:
    data = load_data()
    first_day = date.fromisoformat(data["first_day"])
    last_day = date.fromisoformat(data["last_day"])

    days = [
        (first_day + timedelta(days=offset)).isoformat()
        for offset in range((last_day - first_day).days + 1)
    ]

    return {
        "name": data["name"],
        "first_day": data["first_day"],
        "last_day": data["last_day"],
        "days": days,
    }


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