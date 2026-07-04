import json
import os
from app import app, db
from models import Artist

def seed_database():
    json_filename = "artists.json"
    
    # 1. Check if the JSON file exists
    if not os.path.exists(json_filename):
        print(f"Error: {json_filename} not found in the project directory.")
        return

    print("Reading data from artists.json...")
    with open(json_filename, "r", encoding="utf-8") as file:
        artists_data = json.load(file)

    # 2. Open Flask application context to access the database
    with app.app_context():
        print("Cleaning up old database entries...")
        # Drops tables and recreates them to prevent double-insertions if run twice
        db.drop_all()
        db.create_all()

        print(f"Found {len(artists_data)} artists. Starting migration...")
        
        for item in artists_data:
            # Map your exact JSON keys safely into your database columns
            new_artist = Artist(
                name=item.get("name"),
                genre=item.get("genre"),
                decade=item.get("decade"),
                region=item.get("region"),
                image_url=item.get("image"),  # Maps JSON "image" -> DB "image_url"
                description="AI description coming soon..."  # Placeholder for the AI feature
            )
            db.session.add(new_artist)
        
        # 3. Save all changes to the music.db file
        db.session.commit()
        print("Database successfully populated! 🎉")

if __name__ == "__main__":
    seed_database()