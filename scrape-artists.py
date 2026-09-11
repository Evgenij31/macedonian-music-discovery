"""Discover North Macedonian artists from MusicBrainz and save them for Flask.

Before running this script, set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET.
MusicBrainz provides the country-wide, genre-independent discovery list. Spotify
is used for IDs, genres, and images when an artist has a Spotify relationship.
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
import re
import socket
import sys
import time
import unicodedata
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from PIL import Image


ROOT = Path(__file__).resolve().parent
ARTISTS_FILE = ROOT / "artists.json"
IMAGE_DIR = ROOT / "static" / "images" / "artists"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_ARTISTS_URL = "https://api.spotify.com/v1/artists"
SPOTIFY_SEARCH_URL = "https://api.spotify.com/v1/search"
MUSICBRAINZ_SEARCH_URL = "https://musicbrainz.org/ws/2/artist"
MUSICBRAINZ_LOOKUP_URL = "https://musicbrainz.org/ws/2/artist/{}"
MUSICBRAINZ_TIMEOUT = 60


def api_request(url: str, *, headers: dict[str, str] | None = None) -> Any:
	request = Request(url, headers=headers or {})
	try:
		with urlopen(request, timeout=30) as response:
			return json.load(response)
	except HTTPError as error:
		body = error.read().decode("utf-8", errors="replace").strip()
		raise RuntimeError(
			f"API request failed with HTTP {error.code} for {url}: {body or error.reason}"
		) from error


def spotify_access_token() -> str:
	client_id = os.environ.get("SPOTIFY_CLIENT_ID")
	client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
	if not client_id or not client_secret:
		raise RuntimeError(
			"Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET before running."
		)

	credentials = base64.b64encode(
		f"{client_id}:{client_secret}".encode("utf-8")
	).decode("ascii")
	body = urlencode({"grant_type": "client_credentials"}).encode("ascii")
	request = Request(
		SPOTIFY_TOKEN_URL,
		data=body,
		headers={
			"Authorization": f"Basic {credentials}",
			"Content-Type": "application/x-www-form-urlencoded",
		},
	)
	with urlopen(request, timeout=30) as response:
		return json.load(response)["access_token"]


def spotify_artists(token: str, query: str, max_results: int) -> list[dict[str, Any]]:
	if max_results <= 0:
		return []
	artists: list[dict[str, Any]] = []
	headers = {"Authorization": f"Bearer {token}"}
	page_size = min(max_results, 10)
	for offset in range(0, min(max_results, 1000), page_size):
		params = urlencode(
			{"q": query, "type": "artist", "limit": page_size, "offset": offset}
		)
		result = api_request(f"{SPOTIFY_SEARCH_URL}?{params}", headers=headers)
		page = result.get("artists", {}).get("items", [])
		artists.extend(page)
		if len(page) < page_size:
			break
	return artists[:max_results]


def musicbrainz_request(url: str) -> Any:
	request = Request(
		url,
		headers={
			"User-Agent": os.environ.get(
				"MUSICBRAINZ_USER_AGENT",
				"MacedonianMusicDiscovery/1.0 (local scraper)",
			)
		},
	)
	last_error: Exception | None = None
	for attempt in range(5):
		try:
			with urlopen(request, timeout=MUSICBRAINZ_TIMEOUT) as response:
				return json.load(response)
		except (HTTPError, URLError, socket.timeout, TimeoutError) as error:
			last_error = error
			if attempt < 4:
				retry_after = None
				if isinstance(error, HTTPError):
					retry_after = error.headers.get("Retry-After")
				try:
					wait_seconds = min(float(retry_after), 60) if retry_after else 2 ** (attempt + 1)
				except ValueError:
					wait_seconds = 2 ** (attempt + 1)
				time.sleep(wait_seconds)
	if last_error is not None:
		raise RuntimeError(
			f"MusicBrainz did not respond after 5 attempts: {last_error}"
		) from last_error
	raise RuntimeError("MusicBrainz request failed without an error response")


def musicbrainz_artists(max_results: int) -> list[dict[str, Any]]:
	"""Return MusicBrainz artists associated with North Macedonia."""
	artists: dict[str, dict[str, Any]] = {}
	for query in ('country:MK', 'area:"North Macedonia"'):
		for offset in range(0, max_results, 100):
			params = urlencode(
				{"query": query, "fmt": "json", "limit": 100, "offset": offset}
			)
			try:
				page = musicbrainz_request(f"{MUSICBRAINZ_SEARCH_URL}?{params}").get(
					"artists", []
				)
			except (HTTPError, URLError) as error:
				print(f"MusicBrainz search failed for {query}: {error}", file=sys.stderr)
				break
			for artist in page:
				if artist.get("id") and artist.get("name"):
					artists[artist["id"]] = artist
			if len(page) < 100:
				break
			time.sleep(1)
	return list(artists.values())[:max_results]


def spotify_id_from_musicbrainz(musicbrainz_id: str) -> str | None:
	try:
		artist = musicbrainz_request(
			f"{MUSICBRAINZ_LOOKUP_URL.format(musicbrainz_id)}?inc=url-rels&fmt=json"
		)
	except (HTTPError, URLError, RuntimeError) as error:
		print(
			f"Skipping MusicBrainz artist {musicbrainz_id}: {error}",
			file=sys.stderr,
		)
		return None

	for relation in artist.get("relations", []):
		url = (relation.get("url") or {}).get("resource", "")
		match = re.search(r"open\.spotify\.com/artist/([A-Za-z0-9]+)", url)
		if match:
			return match.group(1)
	return None


def spotify_artist_details(token: str, artist_ids: list[str]) -> list[dict[str, Any]]:
	artists: list[dict[str, Any]] = []
	for start in range(0, len(artist_ids), 50):
		params = urlencode({"ids": ",".join(artist_ids[start : start + 50])})
		result = api_request(
			f"{SPOTIFY_ARTISTS_URL}?{params}",
			headers={"Authorization": f"Bearer {token}"},
		)
		artists.extend(artist for artist in result.get("artists", []) if artist)
	return artists


def spotify_artists_by_name(
	token: str, musicbrainz_matches: list[dict[str, Any]]
) -> list[dict[str, Any]]:
	"""Fallback for apps that cannot access Spotify's batch artist endpoint."""
	artists: dict[str, dict[str, Any]] = {}
	for match in musicbrainz_matches:
		name = match.get("name", "").strip()
		if not name:
			continue
		try:
			results = spotify_artists(token, f'artist:"{name}"', 1)
		except RuntimeError as error:
			print(f"Spotify search failed for {name}: {error}", file=sys.stderr)
			continue
		if results and results[0].get("id"):
			artists[results[0]["id"]] = results[0]
	return list(artists.values())


def musicbrainz_metadata(name: str) -> tuple[str | None, str | None]:
	params = urlencode({"query": f'artist:"{name}"', "fmt": "json", "limit": 1})
	request = Request(
		f"{MUSICBRAINZ_SEARCH_URL}?{params}",
		headers={"User-Agent": "MacedonianMusicDiscovery/1.0 (local scraper)"},
	)
	try:
		with urlopen(request, timeout=30) as response:
			matches = json.load(response).get("artists", [])
	except (HTTPError, URLError):
		return None, None

	if not matches:
		return None, None
	match = matches[0]
	area = (match.get("begin-area") or match.get("area") or {}).get("name")
	begin = (match.get("life-span") or {}).get("begin", "")
	year_match = re.match(r"(\d{4})", begin)
	decade = f"{year_match.group(1)[:3]}0s" if year_match else None
	return area, decade


def musicbrainz_record_metadata(
	record: dict[str, Any] | None,
) -> tuple[str | None, str | None, str | None]:
	if not record:
		return None, None, None
	area = (record.get("begin-area") or record.get("area") or {}).get("name")
	begin = (record.get("life-span") or {}).get("begin", "")
	year_match = re.match(r"(\d{4})", begin)
	decade = f"{year_match.group(1)[:3]}0s" if year_match else None

	ignored_tags = {
		"favorites",
		"music",
		"seen live",
		"under 2000 listeners",
	}
	tags = [
		(tag.get("name") or "").strip()
		for tag in record.get("tags", [])
		if (tag.get("name") or "").strip().lower() not in ignored_tags
	]
	genre = tags[0] if tags else None
	return area, decade, genre


def slugify(name: str) -> str:
	normalized = unicodedata.normalize("NFKD", name)
	ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
	slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")
	return slug or "artist"


def download_jpeg(url: str, destination: Path) -> None:
	request = Request(url, headers={"User-Agent": "MacedonianMusicDiscovery/1.0"})
	with urlopen(request, timeout=30) as response:
		image_data = response.read()
	with Image.open(io.BytesIO(image_data)) as image:
		image.convert("RGB").save(destination, format="JPEG", quality=92, optimize=True)


def load_existing() -> list[dict[str, Any]]:
	if not ARTISTS_FILE.exists():
		return []
	with ARTISTS_FILE.open("r", encoding="utf-8") as file:
		data = json.load(file)
	return data if isinstance(data, list) else []


def save_artists(artists: list[dict[str, Any]]) -> None:
	temporary_file = ARTISTS_FILE.with_suffix(".json.tmp")
	with temporary_file.open("w", encoding="utf-8") as file:
		json.dump(artists, file, ensure_ascii=False, indent=2)
		file.write("\n")
	temporary_file.replace(ARTISTS_FILE)


def artist_record(
	spotify_artist: dict[str, Any],
	region: str,
	decade: str,
	enrich: bool,
	musicbrainz_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
	name = spotify_artist["name"].strip()
	metadata_region, metadata_decade, musicbrainz_genre = (
		musicbrainz_record_metadata(musicbrainz_record)
	)
	if enrich:
		if not musicbrainz_record:
			metadata_region, metadata_decade = musicbrainz_metadata(name)
			time.sleep(1)

	genres = spotify_artist.get("genres") or []
	image_url = (spotify_artist.get("images") or [{}])[0].get("url")
	image_name = f"{slugify(name)}.jpg"
	image_path = IMAGE_DIR / image_name
	if image_url and not image_path.exists():
		try:
			download_jpeg(image_url, image_path)
		except (HTTPError, URLError, OSError, ValueError) as error:
			print(f"Could not download image for {name}: {error}", file=sys.stderr)

	return {
		"name": name,
		"genre": (
			genres[0].replace("-", " ").title()
			if genres
			else musicbrainz_genre.replace("-", " ").title()
			if musicbrainz_genre
			else "Other"
		),
		"decade": metadata_decade or decade,
		"region": metadata_region or region,
		"image": f"static/images/artists/{image_name}",
		"spotify_artist_id": spotify_artist["id"],
	}


def main() -> None:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument(
		"--query",
		action="append",
		help="Optional Spotify search query; default discovery uses all MusicBrainz genres",
	)
	parser.add_argument(
		"--max-results",
		type=int,
		default=1000,
		help="Maximum MusicBrainz artists to process",
	)
	parser.add_argument("--max-per-query", type=int, default=200)
	parser.add_argument("--region", default="Macedonia", help="Fallback region")
	parser.add_argument("--decade", default="Unknown", help="Fallback decade")
	parser.add_argument(
		"--no-enrich", action="store_true", help="Skip MusicBrainz lookups"
	)
	args = parser.parse_args()

	IMAGE_DIR.mkdir(parents=True, exist_ok=True)
	token = spotify_access_token()
	discovered: dict[str, dict[str, Any]] = {}
	musicbrainz_by_spotify_id: dict[str, dict[str, Any]] = {}
	if args.query:
		for query in args.query:
			print(f"Searching Spotify: {query}")
			for artist in spotify_artists(token, query, args.max_per_query):
				if artist.get("id") and artist.get("name"):
					discovered[artist["id"]] = artist
	else:
		print("Discovering all MusicBrainz artists associated with North Macedonia")
		musicbrainz_matches = musicbrainz_artists(args.max_results)
		spotify_ids = []
		for match in musicbrainz_matches:
			spotify_id = spotify_id_from_musicbrainz(match["id"])
			if spotify_id:
				spotify_ids.append(spotify_id)
				musicbrainz_by_spotify_id[spotify_id] = match
			time.sleep(1)
		try:
			spotify_matches = spotify_artist_details(token, spotify_ids)
		except RuntimeError as error:
			print(
				f"Spotify batch artist lookup unavailable; using name search: {error}",
				file=sys.stderr,
			)
			spotify_matches = spotify_artists_by_name(token, musicbrainz_matches)
		for artist in spotify_matches:
			if artist.get("id") and artist.get("name"):
				discovered[artist["id"]] = artist

	existing_by_id = {
		artist.get("spotify_artist_id"): artist
		for artist in load_existing()
		if artist.get("spotify_artist_id")
	}
	for artist_id, spotify_artist in discovered.items():
		musicbrainz_record = musicbrainz_by_spotify_id.get(artist_id)
		existing_by_id[artist_id] = artist_record(
			spotify_artist,
			args.region,
			args.decade,
			not args.no_enrich,
			musicbrainz_record,
		)
		print(f"Saved: {spotify_artist['name']}")

	save_artists(list(existing_by_id.values()))
	print(f"Wrote {len(existing_by_id)} artists to {ARTISTS_FILE}")


if __name__ == "__main__":
	main()
