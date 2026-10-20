from datetime import date, datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles


from festival import (
    Lineup,
    SoloShow,
    Workshop,
    DATA_FILE,
    festival_info,
    load_data,
    load_festival,
    save_data,
    slugify,
)


app = FastAPI(title="Deauville Festival du Rire 2027")


@app.get("/api/festival")
def get_festival() -> dict:
    return festival_info(load_data())


@app.get("/api/venues")
def get_venues() -> list[dict]:
    festival = load_festival()
    return [venue.to_view() for venue in festival.venues]


@app.get("/api/artists")
def get_artists() -> list[dict]:
    festival = load_festival()
    return [
        artist.to_view()
        for artist in sorted(festival.artists, key=lambda item: item.slug)
    ]


@app.post("/api/artists", status_code=status.HTTP_201_CREATED)
def create_artist(body: dict) -> dict:
    name = body.get("name")

    if not isinstance(name, str) or not name.strip():
        raise HTTPException(
            status_code=422,
            detail="Artist name must not be empty.",
        )

    name = name.strip()
    slug = slugify(name)

    try:
        data = load_data()
    except ValueError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    if any(slugify(item["name"]) == slug for item in data["artists"]):
        raise HTTPException(
            status_code=409,
            detail=f"Artist '{name}' already exists.",
        )

    artist = {
        "name": name,
        "bio": body.get("bio", ""),
        "photo_url": body.get("photo_url", ""),
    }

    data["artists"].append(artist)

    try:
        save_data(data)
    except ValueError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    return {
        "slug": slug,
        **artist,
    }



@app.post("/api/performances", status_code=status.HTTP_201_CREATED)
def create_performance(body: dict) -> dict:
    try:
        data = load_data()
        festival = load_festival()

        kind = body.get("kind")
        required = {
            "solo": {"title", "venue", "start", "duration_minutes", "artist"},
            "lineup": {"title", "venue", "start", "duration_minutes", "host", "acts"},
            "workshop": {
                "title", "venue", "start", "duration_minutes",
                "teacher", "max_participants",
            },
        }

        if kind not in required:
            raise HTTPException(
                status_code=422,
                detail="Kind must be solo, lineup or workshop.",
            )

        missing = required[kind] - body.keys()
        if missing:
            raise HTTPException(
                status_code=422,
                detail=f"Missing required fields: {', '.join(sorted(missing))}.",
            )

        venue = festival.get_venue(body["venue"])
        start = datetime.fromisoformat(body["start"])

        if not body.get("title") or not isinstance(body["title"], str):
            raise HTTPException(status_code=422, detail="Title must not be empty.")

        duration = body["duration_minutes"]
        if isinstance(duration, bool) or not isinstance(duration, int):
            raise HTTPException(status_code=422, detail="Duration must be an integer.")

        common = {
            "title": body["title"].strip(),
            "venue": venue.slug,
            "start": start,
            "duration_minutes": duration,
            "description": body.get("description", ""),
            "capacity": venue.capacity,
            "venue_name": venue.name,
            "artists_by_slug": {a.slug: a for a in festival.artists},
        }

        if kind == "solo":
            performance = SoloShow(
                **common,
                artist=body["artist"],
                min_age=body.get("min_age", 0),
            )
        elif kind == "lineup":
            performance = Lineup(
                **common,
                host=body["host"],
                acts=body["acts"],
            )
        else:
            performance = Workshop(
                **common,
                teacher=body["teacher"],
                max_participants=body["max_participants"],
                participants=body.get("participants", []),
            )

        if not (
            festival.first_day
            <= performance.festival_day
            <= festival.last_day
        ):
            raise HTTPException(
                status_code=409,
                detail="Performance date is outside the festival.",
            )

        for existing in festival.performances:
            overlaps = (
                performance.start < existing.end
                and existing.start < performance.end
            )
            if not overlaps:
                continue

            if performance.venue == existing.venue:
                raise HTTPException(
                    status_code=409,
                    detail=f"Venue '{venue.slug}' is busy at that time.",
                )

            shared_artists = {
                artist["slug"] for artist in performance.artists
            } & {
                artist["slug"] for artist in existing.artists
            }
            if shared_artists:
                raise HTTPException(
                    status_code=409,
                    detail="An artist is already performing at that time.",
                )

        saved = {
            "kind": kind,
            "title": common["title"],
            "venue": venue.slug,
            "start": start.isoformat(timespec="minutes"),
            "duration_minutes": duration,
            "description": common["description"],
        }

        if kind == "solo":
            saved.update({
                "artist": performance.artist,
                "min_age": performance.min_age,
            })
        elif kind == "lineup":
            saved.update({
                "host": performance.host,
                "acts": performance.acts,
            })
        else:
            saved.update({
                "teacher": performance.teacher,
                "max_participants": performance.max_participants,
                "participants": performance.participants,
            })

        if any(
            item["venue"] == saved["venue"]
            and item["start"] == saved["start"]
            for item in data["performances"]
        ):
            raise HTTPException(
                status_code=409,
                detail="A performance already exists at that venue and time.",
            )

        data["performances"].append(saved)
        try:
            save_data(data)
        except ValueError as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

        return performance.to_view()

    except HTTPException:
        raise
    except ValueError as error:
        message = str(error)
        if message.startswith(("No venue ", "No artist ")):
            raise HTTPException(status_code=404, detail=message) from error
        raise HTTPException(status_code=422, detail=message) from error

@app.get("/api/artists/{slug}")
def get_artist(slug: str) -> dict:
    festival = load_festival()

    artist = next(
        (item for item in festival.artists if item.slug == slug),
        None,
    )
    if artist is None:
        raise HTTPException(
            status_code=404,
            detail=f"No artist '{slug}'.",
        )

    result = artist.to_view()
    result["performances"] = [
        performance.to_view()
        for performance in festival.programme()
        if performance.involves(artist.slug)
    ]
    return result


@app.get("/api/programme")
def get_programme(
    day: date | None = None,
    venue: str | None = None,
) -> list[dict]:
    festival = load_festival()

    if venue is not None and not any(
        item.slug == venue for item in festival.venues
    ):
        raise HTTPException(
            status_code=404,
            detail=f"No venue '{venue}'.",
        )

    return [
        performance.to_view()
        for performance in festival.programme(day=day, venue=venue)
    ]


@app.get("/api/performances/{performance_id}")
def get_performance(performance_id: str) -> dict:
    festival = load_festival()

    performance = next(
        (
            item
            for item in festival.performances
            if item.id == performance_id
        ),
        None,
    )

    if performance is None:
        raise HTTPException(
            status_code=404,
            detail=f"No performance '{performance_id}'.",
        )

    return performance.to_view()


@app.put("/api/performances/{performance_id}")
def update_performance(performance_id: str, body: dict) -> dict:
    try:
        data = load_data()
        festival = load_festival()

        try:
            old_performance = festival.get_performance(performance_id)
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

        kind = body.get("kind")
        if kind not in {"solo", "lineup", "workshop"}:
            raise HTTPException(status_code=422, detail="Invalid performance kind.")

        required = {
            "solo": {"title", "venue", "start", "duration_minutes", "artist"},
            "lineup": {"title", "venue", "start", "duration_minutes", "host", "acts"},
            "workshop": {
                "title", "venue", "start", "duration_minutes",
                "teacher", "max_participants",
            },
        }

        missing = required[kind] - body.keys()
        if missing:
            raise HTTPException(
                status_code=422,
                detail=f"Missing required fields: {', '.join(sorted(missing))}.",
            )

        venue = festival.get_venue(body["venue"])
        start = datetime.fromisoformat(body["start"])
        common = {
            "title": body["title"],
            "venue": venue.slug,
            "start": start,
            "duration_minutes": body["duration_minutes"],
            "description": body.get("description", ""),
            "capacity": venue.capacity,
            "venue_name": venue.name,
            "artists_by_slug": {artist.slug: artist for artist in festival.artists},
        }

        if kind == "solo":
            updated = SoloShow(
                **common,
                artist=body["artist"],
                min_age=body.get("min_age", 0),
            )
        elif kind == "lineup":
            updated = Lineup(
                **common,
                host=body["host"],
                acts=body["acts"],
            )
        else:
            updated = Workshop(
                **common,
                teacher=body["teacher"],
                max_participants=body["max_participants"],
                participants=body.get("participants", []),
            )

        if not (
            festival.first_day <= updated.festival_day <= festival.last_day
        ):
            raise HTTPException(
                status_code=409,
                detail="Performance date is outside the festival.",
            )

        for existing in festival.performances:
            if existing.id == performance_id:
                continue

            overlaps = (
                updated.start < existing.end
                and existing.start < updated.end
            )
            if not overlaps:
                continue

            if updated.venue == existing.venue:
                raise HTTPException(
                    status_code=409,
                    detail=f"Venue '{updated.venue}' is busy at that time.",
                )

            if set(a["slug"] for a in updated.artists) & set(
                a["slug"] for a in existing.artists
            ):
                raise HTTPException(
                    status_code=409,
                    detail="An artist is already performing at that time.",
                )

        replacement = {
            "kind": kind,
            "title": updated.title,
            "venue": updated.venue,
            "start": updated.start.isoformat(timespec="minutes"),
            "duration_minutes": updated.duration_minutes,
            "description": updated.description,
        }

        if kind == "solo":
            replacement.update({
                "artist": updated.artist,
                "min_age": updated.min_age,
            })
        elif kind == "lineup":
            replacement.update({
                "host": updated.host,
                "acts": updated.acts,
            })
        else:
            replacement.update({
                "teacher": updated.teacher,
                "max_participants": updated.max_participants,
                "participants": updated.participants,
            })

        index = next(
            i for i, item in enumerate(data["performances"])
            if (
                item["venue"] == old_performance.venue
                and datetime.fromisoformat(item["start"]) == old_performance.start
            )
        )
        data["performances"][index] = replacement

        # Validate the complete updated dataset before writing it.
        original = load_data()
        try:
            save_data(data)
            load_festival()
        except Exception:
            save_data(original)
            raise

        return updated.to_view()

    except HTTPException:
        raise
    except ValueError as error:
        message = str(error)
        if message.startswith(("No venue ", "No artist ")):
            raise HTTPException(status_code=404, detail=message) from error
        raise HTTPException(status_code=422, detail=message) from error



@app.delete(
    "/api/performances/{performance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_performance(performance_id: str) -> None:
    try:
        data = load_data()
        festival = load_festival()
        performance = festival.get_performance(performance_id)

        matching_index = next(
            (
                index
                for index, item in enumerate(data["performances"])
                if (
                    item["venue"] == performance.venue
                    and datetime.fromisoformat(item["start"]) == performance.start
                )
            ),
            None,
        )

        if matching_index is None:
            raise HTTPException(
                status_code=404,
                detail=f"No performance '{performance_id}'.",
            )

        data["performances"].pop(matching_index)

        try:
            save_data(data)
        except ValueError as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    except HTTPException:
        raise
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

@app.post(
    "/api/performances/{performance_id}/participants",
    status_code=status.HTTP_201_CREATED,
)
def add_participant(performance_id: str, body: dict) -> dict:
    name = body.get("name")

    if not isinstance(name, str) or not name.strip():
        raise HTTPException(
            status_code=422,
            detail="Participant name must not be empty.",
        )

    try:
        data = load_data()
        festival = load_festival()
        performance = festival.get_performance(performance_id)

        if not isinstance(performance, Workshop):
            raise HTTPException(
                status_code=422,
                detail="Participants can only be added to workshops.",
            )

        name = name.strip()

        if name in performance.participants:
            raise HTTPException(
                status_code=409,
                detail="This participant is already registered.",
            )

        if performance.places_left <= 0:
            raise HTTPException(
                status_code=409,
                detail="The workshop is full.",
            )

        item = next(
            (
                item for item in data["performances"]
                if (
                    item["venue"] == performance.venue
                    and datetime.fromisoformat(item["start"]) == performance.start
                )
            ),
            None,
        )

        if item is None:
            raise HTTPException(
                status_code=404,
                detail=f"No performance '{performance_id}'.",
            )

        item.setdefault("participants", []).append(name)

        try:
            save_data(data)
        except ValueError as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

        return load_festival().get_performance(performance_id).to_view()

    except HTTPException:
        raise
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

@app.get("/api/now")
def get_now(at: datetime | None = None) -> dict:
    festival = load_festival()
    moment = at if at is not None else datetime.now()

    now_playing = [
        performance.to_view()
        for performance in festival.programme()
        if performance.start <= moment < performance.end
    ]

    up_next = [
        performance.to_view()
        for performance in festival.programme()
        if performance.start > moment
    ][:3]

    return {
        "at": moment.isoformat(timespec="minutes"),
        "now_playing": now_playing,
        "up_next": up_next,
    }

admin_directory = Path(__file__).parent / "web" / "admin"

if admin_directory.is_dir():
    app.mount(
        "/admin",
        StaticFiles(directory=str(admin_directory), html=True),
        name="admin",
    )

web_directory = Path(__file__).parent / "web" / "public"
if web_directory.is_dir():
    app.mount(
        "/",
        StaticFiles(directory=str(web_directory), html=True),
        name="website",
    )