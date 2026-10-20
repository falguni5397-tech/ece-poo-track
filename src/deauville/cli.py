
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def show_programme(data: dict, day: str) -> None:
    try:
        selected_day = datetime.strptime(day, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"'{day}' is not a day, use YYYY-MM-DD.") from None

    if selected_day.isoformat() != day:
        raise ValueError(f"'{day}' is not a day, use YYYY-MM-DD.")

    performances = [
        item
        for item in data["performances"]
        if datetime.fromisoformat(item["start"]).date() == selected_day
    ]

    if not performances:
        print(f"No performances scheduled for {selected_day}.")
        return

    for item in sorted(performances, key=lambda item: item["start"]):
        print(
            f"{item['start'][11:]} | "
            f"{item['venue']} | {item['title']}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(prog="deauville")
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("data/festival.json"),
        help="Path to the festival JSON file",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    programme_parser = subparsers.add_parser("programme")
    programme_parser.add_argument("day")
    subparsers.add_parser("serve")

    args = parser.parse_args()
    data_file = args.data.resolve()

    try:
        if args.command == "programme":
            with data_file.open("r", encoding="utf-8-sig") as file:
                data = json.load(file)
            show_programme(data, args.day)

        elif args.command == "serve":
            import uvicorn

            from deauville import festival
            from deauville.api import app

            festival.DATA_FILE = data_file
            uvicorn.run(app, host="127.0.0.1", port=8001)

    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()