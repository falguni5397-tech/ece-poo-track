import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unicodedata import normalize


DATA_FILE = Path(__file__).parent / "data" / "festival.json"
GAP_MINUTES = 30


def slugify(value):
    """Convert a name into a simple slug."""
    value = normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower())
    return value.strip("-")


def load_data():
    """Load the festival JSON, reporting expected file errors clearly."""
    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        raise ValueError("The festival data file was not found.") from None
    except json.JSONDecodeError:
        raise ValueError("The festival data file contains invalid JSON.") from None


def save_data(data):
    """Save the festival JSON."""
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def get_artist_slugs(data):
    return {slugify(artist["name"]) for artist in data["artists"]}


def get_venue_slugs(data):
    return {slugify(venue["name"]) for venue in data["venues"]}


def get_performance_end(performance):
    start = datetime.fromisoformat(performance["start"])
    return start + timedelta(minutes=performance["duration_minutes"])


def get_performance_people(performance):
    """Return all artists involved in a performance, whatever their role."""
    people = []

    for role in ("artist", "host", "teacher"):
        if performance.get(role):
            people.append(performance[role])

    people.extend(performance.get("acts", []))
    return people


def check_new_performance(data, title, artist, venue, start, duration):
    """Raise ValueError if the new solo show breaks a festival rule."""
    if not title.strip():
        raise ValueError("The show title cannot be empty.")

    if venue not in get_venue_slugs(data):
        raise ValueError(f"Unknown venue: {venue}.")

    if artist not in get_artist_slugs(data):
        raise ValueError(f"Unknown artist: {artist}.")

    if not 1 <= duration <= 360:
        raise ValueError("Duration must be between 1 and 360 minutes.")

    try:
        start_time = datetime.strptime(start, "%Y-%m-%dT%H:%M")
    except ValueError:
        raise ValueError(
            f"'{start}' is not a valid start time. Use YYYY-MM-DDTHH:MM."
        ) from None

    first_day = datetime.fromisoformat(data["first_day"]).date()
    last_day = datetime.fromisoformat(data["last_day"]).date()

    if not first_day <= start_time.date() <= last_day:
        raise ValueError(
            f"{start_time.date()} is not a day of the festival."
        )

    new_end = start_time + timedelta(minutes=duration)

    for performance in data["performances"]:
        existing_start = datetime.fromisoformat(performance["start"])
        existing_end = get_performance_end(performance)

        # A venue must have a 30-minute gap between performances.
        if performance["venue"] == venue:
            if (
                start_time < existing_end + timedelta(minutes=GAP_MINUTES)
                and existing_start
                < new_end + timedelta(minutes=GAP_MINUTES)
            ):
                venue_name = next(
                    v["name"] for v in data["venues"]
                    if slugify(v["name"]) == venue
                )
                raise ValueError(
                    f"{venue_name} is busy with {performance['title']} "
                    f"({existing_start:%Y-%m-%d %H:%M}-"
                    f"{existing_end:%H:%M})."
                )

        # A performer cannot be involved in two shows too close together.
        if artist in get_performance_people(performance):
            if (
                start_time < existing_end + timedelta(minutes=GAP_MINUTES)
                and existing_start
                < new_end + timedelta(minutes=GAP_MINUTES)
            ):
                raise ValueError(
                    f"{artist.replace('-', ' ').title()} is on stage "
                    f"in {performance['title']}."
                )


def add_show(data):
    title = input("Title: ").strip()
    artist = input("Artist (slug): ").strip()
    venue = input("Venue (slug): ").strip()
    start = input("Start (YYYY-MM-DDTHH:MM): ").strip()
    duration_text = input("Duration (minutes): ").strip()

    try:
        duration = int(duration_text)
    except ValueError:
        raise ValueError(
            f"'{duration_text}' is not a number of minutes."
        ) from None

    check_new_performance(data, title, artist, venue, start, duration)

    performance_id = (
        f"{venue}-{datetime.strptime(start, '%Y-%m-%dT%H:%M'):%Y-%m-%d-%H%M}"
    )

    if any(
        p.get("id") == performance_id
        or (
            p["venue"] == venue
            and p["start"] == start
        )
        for p in data["performances"]
    ):
        raise ValueError(f"Performance ID already exists: {performance_id}.")

    data["performances"].append({
        "kind": "solo",
        "id": performance_id,
        "title": title,
        "venue": venue,
        "start": start,
        "duration_minutes": duration,
        "description": "",
        "artist": artist,
        "min_age": 0,
    })

    save_data(data)
    print(f"Added: {performance_id}, first line of programme {start[:10]}")


def cancel_show(data, performance_id):
    for index, performance in enumerate(data["performances"]):
        expected_id = (
            f"{performance['venue']}-"
            f"{datetime.fromisoformat(performance['start']):%Y-%m-%d-%H%M}"
        )
        if performance.get("id", expected_id) == performance_id:
            title = performance["title"]
            data["performances"].pop(index)
            save_data(data)
            print(f"Cancelled: {title}")
            return

    raise ValueError(f"Unknown performance ID: {performance_id}.")


def parse_day(day):
    try:
        parsed = datetime.strptime(day, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(
            f"'{day}' is not a day, use YYYY-MM-DD."
        ) from None

    if parsed.isoformat() != day:
        raise ValueError(f"'{day}' is not a day, use YYYY-MM-DD.")

    return parsed


def show_programme(data, day):
    selected_day = parse_day(day)
    performances = [
        p for p in data["performances"]
        if datetime.fromisoformat(p["start"]).date() == selected_day
    ]

    if not performances:
        print(f"No performances scheduled for {selected_day}.")
        return

    for performance in sorted(performances, key=lambda p: p["start"]):
        print(
            f"{performance['start'][11:]} | "
            f"{performance['venue']} | {performance['title']}"
        )


def main():
    try:
        if len(sys.argv) < 2:
            raise ValueError(
                "Use: uv run main.py add, cancel ID, or programme YYYY-MM-DD."
            )

        command = sys.argv[1]
        data = load_data()

        if command == "add":
            add_show(data)
        elif command == "cancel":
            if len(sys.argv) != 3:
                raise ValueError("Use: uv run main.py cancel ID.")
            cancel_show(data, sys.argv[2])
        elif command == "programme":
            if len(sys.argv) != 3:
                raise ValueError(
                    "Use: uv run main.py programme YYYY-MM-DD."
                )
            show_programme(data, sys.argv[2])
        else:
            raise ValueError(f"Unknown command: {command}.")

    except (ValueError, OSError) as error:
        print(f"Error: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
