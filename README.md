# macedonian-music-discovery

## Scrape artists

Install the requirements and set Spotify Web API client-credentials before
running the scraper:

```bash
export SPOTIFY_CLIENT_ID="your-client-id"
export SPOTIFY_CLIENT_SECRET="your-client-secret"
python3 scrape-artists.py
```

By default, the scraper paginates through MusicBrainz artists associated with
North Macedonia, across all genres and locations, then uses their Spotify
relationships to fetch genres and images. It deduplicates artists by Spotify
ID, downloads images as JPEG files into `static/images/artists`, and merges
records into `artists.json`. Use `--query "..."` to run optional Spotify
keyword searches instead, or `--max-results 5000` to process more artists.

The scraper also reads `known-artists.json`, a manually reviewed seed list for
nationally recognizable and historically important artists. Each seed is
searched directly in Spotify and must have an exact normalized name match, so
an unrelated search result is not silently added. The seed's
`editorial_priority` places it ahead of long-tail discoveries. Edit this file
to expand or correct the list; it is kept separate from generated
`artists.json`.

Spotify artist popularity is stored with each record and is used as the
secondary ordering signal. The home API sorts by editorial priority, Spotify
popularity, and then artist name. Spotify popularity reflects Spotify activity,
so curated priority remains important for older artists and audiences using
other platforms.

## Sync artists to the database

The sync uses Google Gemini to validate each artist before persistence. Create a
Gemini API key from Google AI Studio, then configure it before running the sync:

```bash
export GEMINI_API_KEY="your-gemini-api-key"
export GEMINI_MODEL="gemini-3.5-flash-lite"  # optional
python3 -m pip install -r requirements.txt
```

Gemini's free tier is subject to account, model, region, and rate limits. The
model name can be changed with `GEMINI_MODEL` when Google changes availability.
Provider or malformed-response errors abort the batch without changing either
`artists.json` or SQLite. Artists that Gemini does not explicitly classify as
Macedonian are removed from `artists.json` and are not inserted into the
database. For accepted artists, unknown genre, decade, region, or biography
values are stored as `Unknown`; country-level regions such as `North Macedonia`
are never stored as a region. Gemini also returns a `region_is_valid` decision
for each artist, so legitimate Macedonian cities and regions do not depend on a
hardcoded application allowlist.

Preview changes first:

```bash
python3 sync-artists.py --dry-run
```

Apply new records and update existing records:

```bash
python3 sync-artists.py
```

Both commands call Gemini. `--dry-run` reports the proposed enrichment and
database changes but writes neither `artists.json` nor SQLite. The normal sync
atomically updates `artists.json` first, then matches artists by Spotify ID or
normalized name and updates name, genre, decade, region, image path, biography,
Spotify ID, popularity, and editorial priority in the database. Existing SQLite
databases receive the new columns automatically on application startup.

Requests are paced at five seconds apart by default, keeping the sync below the
free-tier limit of 15 requests per minute. Change the delay with either
`--request-interval 6` or `GEMINI_REQUEST_INTERVAL_SECONDS=6`. A large catalog
will therefore take several minutes, but pacing prevents the sync from rapidly
exhausting the per-minute quota.
