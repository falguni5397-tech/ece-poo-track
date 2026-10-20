
import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import ClassVar
from unicodedata import normalize


DATA_FILE = Path(__file__).parent / "data" / "festival.json"


def slugify(value: str) -> str:
    value = normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower())
    return value.strip("-")


@dataclass
class Venue:
    slug: str
    name: str
    capacity: int
    address: str

    def to_view(self) -> dict:
        return {
            "slug": self.slug,
            "name": self.name,
            "capacity": self.capacity,
            "address": self.address,
        }


@dataclass
class Artist:
    slug: str
    name: str
    bio: str
    photo_url: str

    def to_view(self) -> dict:
        return {
            "slug": self.slug,
            "name": self.name,
            "bio": self.bio,
            "photo_url": self.photo_url,
        }


@dataclass
class Performance(ABC):
    title: str
    venue: str
    start: datetime
    duration_minutes: int
    description: str
    capacity: int
    venue_name: str
    artists_by_slug: dict[str, Artist]

    kind: ClassVar[str] = ""

    def __post_init__(self):
        if not 1 <= self.duration_minutes <= 360:
            raise ValueError(
                "Duration must be between 1 and 360 minutes."
            )

    @property
    def end(self) -> datetime:
        return self.start + timedelta(minutes=self.duration_minutes)

    @property
    def festival_day(self) -> date:
        # Performances before 6 AM belong to the previous festival day.
        if self.start.hour < 6:
            return (self.start - timedelta(days=1)).date()
        return self.start.date()

    @property
    def id(self) -> str:
        return f"{self.venue}-{self.start:%Y-%m-%d-%H%M}"

    @property
    @abstractmethod
    def artists(self) -> list[dict]:
        pass

    @property
    @abstractmethod
    def summary(self) -> str:
        pass

    @abstractmethod
    def extra_view(self) -> dict:
        pass

    def involves(self, artist_slug: str) -> bool:
        return any(
            item["slug"] == artist_slug
            for item in self.artists
        )

    def to_view(self) -> dict:
        result = {
            "id": self.id,
            "kind": self.kind,
            "title": self.title,
            "venue": self.venue,
            "venue_name": self.venue_name,
            "start": self.start.isoformat(timespec="minutes"),
            "end": self.end.isoformat(timespec="minutes"),
            "duration_minutes": self.duration_minutes,
            "festival_day": self.festival_day.isoformat(),
            "description": self.description,
            "summary": self.summary,
            "capacity": self.capacity,
            "artists": self.artists,
        }
        result.update(self.extra_view())
        return result


@dataclass
class SoloShow(Performance):
    artist: str
    min_age: int = 0

    kind: ClassVar[str] = "solo"

    def __post_init__(self):
        super().__post_init__()

        if not 0 <= self.min_age <= 18:
            raise ValueError(
                "Minimum age must be between 0 and 18."
            )

        if self.artist not in self.artists_by_slug:
            raise ValueError(f"Unknown artist '{self.artist}'.")

    @property
    def artists(self) -> list[dict]:
        artist = self.artists_by_slug[self.artist]
        return [{"slug": self.artist, "name": artist.name}]

    @property
    def summary(self) -> str:
        return self.artists_by_slug[self.artist].name

    def extra_view(self) -> dict:
        return {
            "artist": self.artist,
            "min_age": self.min_age,
        }


@dataclass
class Lineup(Performance):
    host: str
    acts: list[str]

    kind: ClassVar[str] = "lineup"

    def __post_init__(self):
        super().__post_init__()

        if len(self.acts) < 2:
            raise ValueError(
                "A lineup must have at least two acts."
            )

        if len(set(self.acts)) != len(self.acts):
            raise ValueError(
                "Each act must appear only once."
            )

        if self.host in self.acts:
            raise ValueError(
                "The host cannot also be an act."
            )

        if self.host not in self.artists_by_slug:
            raise ValueError(f"Unknown host '{self.host}'.")

        for slug in self.acts:
            if slug not in self.artists_by_slug:
                raise ValueError(f"Unknown artist '{slug}'.")

        minimum_duration = (
            10 * len(self.acts)
            + 3 * (len(self.acts) - 1)
        )

        if self.duration_minutes < minimum_duration:
            raise ValueError(
                f"Lineup duration must be at least "
                f"{minimum_duration} minutes."
            )

    @property
    def artists(self) -> list[dict]:
        slugs = [self.host, *self.acts]
        return [
            {
                "slug": slug,
                "name": self.artists_by_slug[slug].name,
            }
            for slug in slugs
        ]

    @property
    def summary(self) -> str:
        host_name = self.artists_by_slug[self.host].name
        act_names = ", ".join(
            self.artists_by_slug[slug].name
            for slug in self.acts
        )
        return f"hosted by {host_name}, with {act_names}"

    def extra_view(self) -> dict:
        return {
            "host": self.host,
            "acts": self.acts,
        }


@dataclass
class Workshop(Performance):
    teacher: str
    max_participants: int
    participants: list[str] = field(default_factory=list)

    kind: ClassVar[str] = "workshop"

    def __post_init__(self):
        super().__post_init__()

        if self.max_participants < 1:
            raise ValueError(
                "A workshop must have at least one place."
            )

        if self.teacher not in self.artists_by_slug:
            raise ValueError(
                f"Unknown teacher '{self.teacher}'."
            )

        if len(set(self.participants)) != len(self.participants):
            raise ValueError(
                "A participant cannot be registered twice."
            )

        if len(self.participants) > self.effective_capacity:
            raise ValueError(
                "Participants exceed the workshop capacity."
            )

    @property
    def effective_capacity(self) -> int:
        return min(self.max_participants, self.capacity)

    @property
    def places_left(self) -> int:
        return self.effective_capacity - len(self.participants)

    @property
    def artists(self) -> list[dict]:
        teacher = self.artists_by_slug[self.teacher]
        return [
            {"slug": self.teacher, "name": teacher.name}
        ]

    @property
    def summary(self) -> str:
        teacher_name = self.artists_by_slug[self.teacher].name
        return (
            f"with {teacher_name}, "
            f"{len(self.participants)}/"
            f"{self.effective_capacity} places taken"
        )

    def extra_view(self) -> dict:
        return {
            "teacher": self.teacher,
            "max_participants": self.max_participants,
            "participants": self.participants,
            "places_left": self.places_left,
        }



@dataclass
class Festival:
    name: str
    first_day: date
    last_day: date
    venues: list[Venue]
    artists: list[Artist]
    performances: list[Performance]

    def programme(
        self,
        day: date | None = None,
        venue: str | None = None,
    ) -> list[Performance]:
        results = self.performances

        if day is not None:
            results = [
                performance
                for performance in results
                if performance.festival_day == day
            ]

        if venue is not None:
            results = [
                performance
                for performance in results
                if performance.venue == venue
            ]

        return sorted(results, key=lambda performance: performance.start)

    def get_performance(self, performance_id: str) -> Performance:
        for performance in self.performances:
            if performance.id == performance_id:
                return performance
        raise ValueError(f"No performance '{performance_id}'.")

    def get_venue(self, venue_slug: str) -> Venue:
        for venue in self.venues:
            if venue.slug == venue_slug:
                return venue
        raise ValueError(f"No venue '{venue_slug}'.")

    def get_artist(self, artist_slug: str) -> Artist:
        for artist in self.artists:
            if artist.slug == artist_slug:
                return artist
        raise ValueError(f"No artist '{artist_slug}'.")

def load_data() -> dict:
    
    try:
        with DATA_FILE.open("r", encoding="utf-8-sig") as file:
            return json.load(file)
    except FileNotFoundError:
        raise ValueError(
            "The festival data file was not found."
        ) from None
    except json.JSONDecodeError:
        raise ValueError(
            "The festival data file contains invalid JSON."
        ) from None


def save_data(data: dict) -> None:
    try:
        with DATA_FILE.open("w", encoding="utf-8") as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
            )
            file.write("\n")
    except OSError as error:
        raise ValueError(
            "The festival data file could not be written."
        ) from error


def load_festival() -> Festival:
    data = load_data()

    venues = [
        Venue(
            slug=slugify(item["name"]),
            name=item["name"],
            capacity=item["capacity"],
            address=item["address"],
        )
        for item in data["venues"]
    ]

    artists = [
        Artist(
            slug=slugify(item["name"]),
            name=item["name"],
            bio=item["bio"],
            photo_url=item["photo_url"],
        )
        for item in data["artists"]
    ]

    artists_by_slug = {
        artist.slug: artist for artist in artists
    }
    venues_by_slug = {
        venue.slug: venue for venue in venues
    }

    # Performance kind is used here to select the appropriate subclass.
    performance_classes = {
        "solo": SoloShow,
        "lineup": Lineup,
        "workshop": Workshop,
    }

    performances: list[Performance] = []

    for item in data["performances"]:
        venue_slug = item["venue"]

        if venue_slug not in venues_by_slug:
            raise ValueError(
                f"Unknown venue '{venue_slug}' in festival data."
            )

        performance_class = performance_classes.get(item["kind"])

        if performance_class is None:
            raise ValueError(
                f"Unknown performance kind '{item['kind']}'."
            )

        common_fields = {
            "title": item["title"],
            "venue": venue_slug,
            "start": datetime.fromisoformat(item["start"]),
            "duration_minutes": item["duration_minutes"],
            "description": item.get("description", ""),
            "capacity": venues_by_slug[venue_slug].capacity,
            "venue_name": venues_by_slug[venue_slug].name,
            "artists_by_slug": artists_by_slug,
        }

        if performance_class is SoloShow:
            performance = SoloShow(
                **common_fields,
                artist=item["artist"],
                min_age=item.get("min_age", 0),
            )
        elif performance_class is Lineup:
            performance = Lineup(
                **common_fields,
                host=item["host"],
                acts=item.get("acts", []),
            )
        else:
            performance = Workshop(
                **common_fields,
                teacher=item["teacher"],
                max_participants=item["max_participants"],
                participants=item.get("participants", []),
            )

        performances.append(performance)

    return Festival(
        name=data["name"],
        first_day=date.fromisoformat(data["first_day"]),
        last_day=date.fromisoformat(data["last_day"]),
        venues=venues,
        artists=artists,
        performances=performances,
    )


def list_venues(data: dict) -> list[dict]:
    return [
        {
            "slug": slugify(item["name"]),
            "name": item["name"],
            "capacity": item["capacity"],
            "address": item["address"],
        }
        for item in data["venues"]
    ]


def list_artists(data: dict) -> list[dict]:
    artists = [
        {
            "slug": slugify(item["name"]),
            "name": item["name"],
            "bio": item["bio"],
            "photo_url": item["photo_url"],
        }
        for item in data["artists"]
    ]
    return sorted(artists, key=lambda item: item["slug"])


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