from flask import Flask, render_template, jsonify
import os
import json

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
    with app.app_context():
        os.makedirs(os.path.join(BASE_DIR, 'instance'), exist_ok=True)
        db.create_all()
        
    app.run(debug=True, port=5000)