
import json
import re
from datetime import date, timedelta
from pathlib import Path
from unicodedata import normalize

DATA_FILE = Path(__file__).parent / "data" / "festival.json"


def slugify(value: str) -> str:
    value = normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower())
    return value.strip("-")


def load_data() -> dict:
    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        raise ValueError("The festival data file was not found.") from None
    except json.JSONDecodeError:
        raise ValueError("The festival data file contains invalid JSON.") from None


def list_venues(data: dict) -> list[dict]:
    return [
        {
            "slug": slugify(venue["name"]),
            "name": venue["name"],
            "capacity": venue["capacity"],
            "address": venue["address"],
        }
        for venue in data["venues"]
    ]


def list_artists(data: dict) -> list[dict]:
    artists = [
        {
            "slug": slugify(artist["name"]),
            "name": artist["name"],
            "bio": artist["bio"],
            "photo_url": artist["photo_url"],
        }
        for artist in data["artists"]
    ]
    return sorted(artists, key=lambda artist: artist["slug"])


def festival_info(data: dict) -> dict:
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