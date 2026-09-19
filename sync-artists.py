"""Synchronize artists.json records with the local SQLite database."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import time
import unicodedata
from pathlib import Path
from typing import Any

os.environ.setdefault("SKIP_ARTIST_SEED", "1")

from app import app, canonical_region, db
from models import Artist


ROOT = Path(__file__).resolve().parent
ARTISTS_FILE = ROOT / "artists.json"
DEFAULT_GEMINI_MODEL = "gemini-3.5-flash-lite"
DEFAULT_REQUEST_INTERVAL_SECONDS = 5.0
UNKNOWN = "Unknown"
MAX_DESCRIPTION_LENGTH = 500
INVALID_REGION_LABELS = {
    "macedonia",
    "north macedonia",
    "republic of macedonia",
    "republic of north macedonia",
}


class EnrichmentError(RuntimeError):
    """Raised when Gemini cannot return a trustworthy batch result."""


def normalize_decade(value: Any) -> str:
    decade = str(value or "").strip()
    return decade if decade == UNKNOWN or re.fullmatch(r"\d{4}s", decade) else UNKNOWN


def normalize_region(value: Any, is_valid: Any) -> str:
    """Trust a region only when Gemini identifies it as a Macedonian location."""
    region = canonical_region(value)
    if is_valid is not True or region.casefold() in INVALID_REGION_LABELS:
        return UNKNOWN
    return region


def normalize_genre(value: Any) -> str:
    genre = " ".join(str(value or "").split())
    if genre.casefold() == UNKNOWN.casefold():
        return UNKNOWN
    return genre if genre and len(genre) <= 50 else UNKNOWN


def normalize_description(value: Any) -> str:
    description = " ".join(str(value or "").split())
    if not description or description.casefold() == UNKNOWN.casefold():
        return UNKNOWN
    return description[:MAX_DESCRIPTION_LENGTH].rstrip() or UNKNOWN


def gemini_client() -> Any:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnrichmentError("Set GEMINI_API_KEY before running the artist sync.")
    try:
        from google import genai
    except ImportError as error:
        raise EnrichmentError(
            "Install dependencies first: python3 -m pip install -r requirements.txt"
        ) from error
    return genai.Client(api_key=api_key)


def normalized_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", ascii_value.lower()).strip()


def enrich_artist(client: Any, record: dict[str, Any]) -> dict[str, Any] | None:
    """Return an enriched record, or None for a non-Macedonian artist."""
    try:
        from google.genai import types
    except ImportError as error:
        raise EnrichmentError(
            "Install dependencies first: python3 -m pip install -r requirements.txt"
        ) from error

    name = str(record.get("name", "")).strip()
    prompt = (
        "You validate a music catalog record for Macedonian music discovery. "
        "Classify an artist as Macedonian only when they are Macedonian by "
        "nationality, origin, or recognized Macedonian music career. Do not use "
        "a performance location or a country-level search association as proof. "
        "If uncertain, set is_macedonian to false. Return only JSON matching "
        "the schema. Use Unknown for facts you cannot establish. Decide whether "
        "the supplied region is a real Macedonian city or region and set "
        "region_is_valid accordingly. Return only the canonical city or region "
        "name, never a country name. Write a factual bio in at most two short "
        "sentences, or Unknown.\n\nArtist: "
        f"{name}\n"
        f"Existing metadata: {json.dumps({key: record.get(key) for key in ('genre', 'decade', 'region')}, ensure_ascii=False)}"
    )
    try:
        response = client.models.generate_content(
            model=os.environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL),
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json",
                response_schema={
                    "type": "OBJECT",
                    "properties": {
                        "is_macedonian": {"type": "BOOLEAN"},
                        "region_is_valid": {"type": "BOOLEAN"},
                        "genre": {"type": "STRING"},
                        "decade": {"type": "STRING"},
                        "region": {"type": "STRING"},
                        "description": {"type": "STRING"},
                    },
                    "required": [
                        "is_macedonian", "region_is_valid", "genre", "decade",
                        "region", "description",
                    ],
                },
            ),
        )
        result = json.loads(response.text)
    except Exception as error:
        raise EnrichmentError(f"Gemini enrichment failed for {name}: {error}") from error

    if not isinstance(result, dict):
        raise EnrichmentError(f"Gemini returned an invalid result for {name}")
    if result.get("is_macedonian") is not True:
        return None

    enriched = dict(record)
    enriched.update(
        {
            "genre": normalize_genre(result.get("genre")),
            "decade": normalize_decade(result.get("decade")),
            "region": normalize_region(
                result.get("region"), result.get("region_is_valid")
            ),
            "description": normalize_description(result.get("description")),
        }
    )
    return enriched


def enrich_records(
    records: list[dict[str, Any]], request_interval: float
) -> tuple[list[dict[str, Any]], list[str]]:
    client = gemini_client()
    accepted: list[dict[str, Any]] = []
    rejected: list[str] = []
    next_request_at = 0.0
    for record in records:
        name = str(record.get("name", "")).strip()
        if not name:
            rejected.append("<unnamed record>")
            continue

        wait_seconds = next_request_at - time.monotonic()
        if wait_seconds > 0:
            time.sleep(wait_seconds)
        request_started_at = time.monotonic()
        enriched = enrich_artist(client, record)
        next_request_at = request_started_at + request_interval
        if enriched is None:
            rejected.append(name)
        else:
            accepted.append(enriched)
    return accepted, rejected


def write_artist_records(records: list[dict[str, Any]]) -> None:
    """Replace artists.json atomically after the complete batch succeeds."""
    temporary_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=ARTISTS_FILE.parent, delete=False
        ) as file:
            json.dump(records, file, ensure_ascii=False, indent=2)
            file.write("\n")
            temporary_path = file.name
        os.replace(temporary_path, ARTISTS_FILE)
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.unlink(temporary_path)


def load_artist_records() -> list[dict[str, Any]]:
    with ARTISTS_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        raise ValueError("artists.json must contain a JSON array")
    return [record for record in data if isinstance(record, dict)]


def update_artist(artist: Artist, record: dict[str, Any]) -> bool:
    changed = False
    fields = {
        "name": record.get("name"),
        "genre": record.get("genre"),
        "decade": record.get("decade"),
        "region": canonical_region(record.get("region")),
        "image_url": record.get("image"),
        "description": record.get("description", UNKNOWN),
        "spotify_artist_id": record.get("spotify_artist_id"),
        "popularity": int(record.get("popularity") or 0),
        "editorial_priority": int(record.get("editorial_priority") or 0),
    }
    for field, value in fields.items():
        if value is not None and value != getattr(artist, field):
            setattr(artist, field, value)
            changed = True
    return changed


def sync_artists(
    dry_run: bool = False,
    request_interval: float = DEFAULT_REQUEST_INTERVAL_SECONDS,
) -> tuple[int, int, int, int]:
    if request_interval < 0:
        raise ValueError("request_interval cannot be negative")
    source_records = load_artist_records()
    records, rejected = enrich_records(source_records, request_interval)
    if not dry_run:
        write_artist_records(records)

    inserted = 0
    updated = 0
    skipped = 0
    seen_ids: set[str] = set()

    existing_by_id = {
        artist.spotify_artist_id: artist
        for artist in Artist.query.all()
        if artist.spotify_artist_id
    }
    existing_by_name = {
        normalized_name(artist.name): artist for artist in Artist.query.all()
    }

    for record in records:
        name = str(record.get("name", "")).strip()
        if not name:
            skipped += 1
            print("Skipped record without a name")
            continue

        spotify_id = str(record.get("spotify_artist_id", "")).strip()
        if spotify_id and spotify_id in seen_ids:
            skipped += 1
            print(f"Skipped duplicate JSON record: {name} ({spotify_id})")
            continue
        if spotify_id:
            seen_ids.add(spotify_id)

        artist = existing_by_id.get(spotify_id) if spotify_id else None
        if artist is None:
            artist = existing_by_name.get(normalized_name(name))

        if artist is None:
            artist = Artist(
                name=name,
                genre=str(record.get("genre") or UNKNOWN),
                decade=str(record.get("decade") or UNKNOWN),
                region=canonical_region(record.get("region") or UNKNOWN),
                image_url=record.get("image"),
                description=record.get("description", UNKNOWN),
                spotify_artist_id=spotify_id or None,
                popularity=int(record.get("popularity") or 0),
                editorial_priority=int(record.get("editorial_priority") or 0),
            )
            db.session.add(artist)
            inserted += 1
            print(f"Insert: {name}")
        elif update_artist(artist, record):
            updated += 1
            print(f"Update: {name}")

    if dry_run:
        db.session.rollback()
    else:
        db.session.commit()

    return inserted, updated, skipped, len(rejected)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show inserts and updates without changing the database",
    )
    parser.add_argument(
        "--request-interval",
        type=float,
        default=float(
            os.environ.get(
                "GEMINI_REQUEST_INTERVAL_SECONDS",
                DEFAULT_REQUEST_INTERVAL_SECONDS,
            )
        ),
        help="Seconds between Gemini requests (default: 5; free tier safe)",
    )
    args = parser.parse_args()

    with app.app_context():
        inserted, updated, skipped, rejected = sync_artists(
            dry_run=args.dry_run,
            request_interval=args.request_interval,
        )

    action = "would be " if args.dry_run else ""
    print(
        f"Sync complete: {inserted} {action}inserted, "
        f"{updated} {action}updated, {skipped} skipped."
    )
    print(f"{rejected} rejected as non-Macedonian or uncertain.")


if __name__ == "__main__":
    main()
