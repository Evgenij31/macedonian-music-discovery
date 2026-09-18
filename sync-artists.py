"""Synchronize artists.json records with the local SQLite database."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from app import app, canonical_region, db
from models import Artist


ROOT = Path(__file__).resolve().parent
ARTISTS_FILE = ROOT / "artists.json"


def normalized_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", ascii_value.lower()).strip()


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
        "spotify_artist_id": record.get("spotify_artist_id"),
    }
    for field, value in fields.items():
        if value is not None and value != getattr(artist, field):
            setattr(artist, field, value)
            changed = True
    return changed


def sync_artists(dry_run: bool = False) -> tuple[int, int, int]:
    records = load_artist_records()
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
                genre=str(record.get("genre") or "Other"),
                decade=str(record.get("decade") or "Unknown"),
                region=canonical_region(record.get("region") or "Macedonia"),
                image_url=record.get("image"),
                description=record.get("description", ""),
                spotify_artist_id=spotify_id or None,
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

    return inserted, updated, skipped


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show inserts and updates without changing the database",
    )
    args = parser.parse_args()

    with app.app_context():
        inserted, updated, skipped = sync_artists(dry_run=args.dry_run)

    action = "would be " if args.dry_run else ""
    print(
        f"Sync complete: {inserted} {action}inserted, "
        f"{updated} {action}updated, {skipped} skipped."
    )


if __name__ == "__main__":
    main()
