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

## Sync artists to the database

Preview changes first:

```bash
python3 sync-artists.py --dry-run
```

Apply new records and update existing records:

```bash
python3 sync-artists.py
```

The sync matches artists by Spotify ID, then by normalized name, and updates
name, genre, decade, region, image path, and Spotify ID.
