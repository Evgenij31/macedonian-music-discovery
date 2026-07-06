from flask import Flask, render_template, jsonify, send_file
import os
import json
from sqlalchemy import inspect, text

# 1. Import db from the extensions file
from extensions import db 

app = Flask(__name__)

# Configure local SQLite database
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'music.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 2. Hook up the database to our Flask app
db.init_app(app)

# 3. Safe to import models now since models no longer imports app.py!
from models import Artist 


def sync_artist_table_schema():
    """Add any missing Artist columns to an existing SQLite table."""
    inspector = inspect(db.engine)
    existing_columns = {column["name"] for column in inspector.get_columns("artists")}

    missing_columns = [
        column for column in Artist.__table__.columns if column.name not in existing_columns
    ]

    if not missing_columns:
        return

    with db.engine.begin() as connection:
        for column in missing_columns:
            column_type = column.type.compile(dialect=db.engine.dialect)
            connection.execute(
                text(f'ALTER TABLE artists ADD COLUMN "{column.name}" {column_type}')
            )

# --- LIVE SERVER SETUP ---
# This runs when PythonAnywhere imports the app, ensuring directories, tables, and data exist
with app.app_context():
    os.makedirs(os.path.join(BASE_DIR, 'instance'), exist_ok=True)
    db.create_all()
    sync_artist_table_schema()
    
    # Check if the database is empty. If it is, seed it using artists.json
    if Artist.query.count() == 0:
        json_path = os.path.join(BASE_DIR, "artists.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as file:
                    artists_data = json.load(file)
                    
                for data in artists_data:
                    new_artist = Artist(
                        name=data.get("name"),
                        genre=data.get("genre"),
                        decade=data.get("decade"),
                        region=data.get("region"),
                        image_url=data.get("image"),  # Maps 'image' from JSON to 'image_url' in DB
                        description=data.get("description", ""),
                        spotify_artist_id=data.get("spotify_artist_id"),
                        spotify_link=data.get("spotify_link")
                    )
                    db.session.add(new_artist)
                db.session.commit()
                print("Database successfully seeded with artists.json data!")
            except Exception as seeding_error:
                db.session.rollback()
                print(f"Error seeding database: {seeding_error}")
# -------------------------

# Route to serve main HTML page
@app.route("/")
def home():
    return render_template("index.html", active_page="home")

@app.route("/about")
def about():
    return render_template("about.html", active_page="about")

@app.route("/favorites")
def favorites():
    return render_template("favorites.html", active_page="favorites")

@app.route("/artist/<int:artist_id>")
def artist(artist_id):
    artist = Artist.query.get_or_404(artist_id)
    return render_template("artist.html", artist=artist, active_page="artist")

@app.route("/favicon.ico")
def favicon():
    return send_file(
        os.path.join(BASE_DIR, "static", "images", "favicon.png"),
        mimetype="image/png",
    )

# Route to serve artist data as an API endpoint
@app.route("/api/artists")
def get_artists():
    try:
        artists_query = Artist.query.all()
        artists_list = []
        for artist in artists_query:
            artists_list.append({
                "id": artist.id,
                "name": artist.name,
                "genre": artist.genre,
                "decade": artist.decade,
                "region": artist.region,
                "image": artist.image_url, 
                "description": artist.description
            })
        return jsonify(artists_list)
    except Exception as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Could not fetch artists from database"}), 500
    
if __name__ == "__main__":
    # This block only runs during local development (python app.py)
    app.run(debug=True, port=5000)