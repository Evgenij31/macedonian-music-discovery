from flask import Flask, render_template, jsonify, send_file, redirect, url_for, request, flash, session
from functools import wraps
import os
import json
from pathlib import Path
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

# Import db from the extensions file
from extensions import db 

app = Flask(__name__)

# Configure local sqlite db
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-only-change-me')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'music.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# connect database to app
db.init_app(app)

# import models since models no longer imports app.py
from models import Artist, User 


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
    
    # Check if the db is empty. If it is, seed it using artists.json
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
                    )
                    db.session.add(new_artist)
                db.session.commit()
                print("Database successfully seeded with artists.json data!")
            except Exception as seeding_error:
                db.session.rollback()
                print(f"Error seeding database: {seeding_error}")
# -------------------------

# Helper function to get distinct values for a given column
def get_distinct_values(column):
    rows = (
        db.session.query(column)
        .filter(column.isnot(None), column != "")
        .distinct()
        .order_by(column.asc())
        .all()
    )
    return [value for (value,) in rows]


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        user_id = session.get("user_id")
        admin_user = User.query.filter_by(id=user_id, user_type="admin").first() if user_id else None

        if admin_user is None:
            flash("Please log in with an admin account to access that page.")
            return redirect(url_for("admin_login"))

        return view(*args, **kwargs)

    return wrapped_view


def delete_artist_image(artist_id, image_url):
    """Delete an artist's unshared local image, if it is stored in our catalog."""
    original_image_url = image_url
    image_url = (image_url or "").replace("\\", "/").lstrip("/")
    if image_url.startswith("static/"):
        image_url = image_url[len("static/") :]

    images_dir = Path(BASE_DIR, "static", "images", "artists").resolve()
    image_path = Path(BASE_DIR, "static", image_url).resolve()

    if images_dir not in image_path.parents or not image_path.is_file():
        return

    is_shared = Artist.query.filter(
        Artist.id != artist_id,
        Artist.image_url == original_image_url,
    ).first()
    if not is_shared:
        image_path.unlink()

# Route to serve 404 page for any undefined routes
@app.route("/<path:path>")
def catch_all(path):
    return render_template("404.html"), 404

# Route to serve main HTML page
@app.route("/")
def home():
    filters = {
        "genres": get_distinct_values(Artist.genre),
        "decades": get_distinct_values(Artist.decade),
        "regions": get_distinct_values(Artist.region),
    }

    return render_template("index.html", active_page="home", filters=filters)

@app.route("/about")
def about():
    return render_template("about.html", active_page="about")

@app.route("/favorites")
def favorites():
    return render_template("favorites.html", active_page="favorites")

@app.route("/login")
def login():
    # If user is already logged in, redirect to home
    if "user_id" in session:
        flash("You are already logged in.")
        return redirect(url_for("home"))
    return render_template("login.html", active_page="login")

@app.route("/signup")
def signup():
    return render_template("signup.html", active_page="signup")

@app.route("/signup_auth", methods=["POST"])
def signup_auth():
    # Handle signup form submission
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    # Trim whitespace and validate inputs
    if not username or not email or not password:
        flash("All fields are required.")
        return redirect(url_for("signup"))

    # Check if the username or email already exists in the database
    existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
    if existing_user:
        flash("Username or email already exists. Please choose another.")
        return redirect(url_for("signup"))

    new_user = User(username=username, email=email, user_type="user")
    new_user.set_password(password)
    db.session.add(new_user)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("Username or email already exists. Please choose another.")
        return redirect(url_for("signup"))

    flash("Signup successful! You can now log in.")
    return redirect(url_for("login"))

@app.route("/login_auth", methods=["POST"])
def login_auth():
    # Handle login form submission
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not email or not password:
        flash("Both email and password are required.")
        return redirect(url_for("login"))

    user = User.query.filter_by(email=email).first()

    if user and user.check_password(password):
        session["user_id"] = user.id
        session["name"] = user.username
        flash(f"Welcome back, {user.username}!")
        return redirect(url_for("home"))

    else:
        flash("Invalid email or password. Please try again.")
        return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("home"))

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

@app.route("/admin")
@admin_required
def admin():
    artists = Artist.query.order_by(Artist.name.asc()).all()
    return render_template("admin/index.html", active_page="admin", artists=artists)

@app.route("/admin/edit_artist/<int:artist_id>", methods=["GET", "POST"])
@admin_required
def edit_artist(artist_id):
    artist = Artist.query.get_or_404(artist_id)

    if request.method == "POST":
        required_fields = ("name", "genre", "decade", "region")
        values = {
            field: request.form.get(field, "").strip()
            for field in required_fields
        }

        if any(not values[field] for field in required_fields):
            flash("Name, genre, decade, and region are required.")
            return render_template(
                "admin/edit_artist.html",
                active_page="admin",
                artist=artist,
            ), 400

        artist.name = values["name"]
        artist.genre = values["genre"]
        artist.decade = values["decade"]
        artist.region = values["region"]
        artist.description = request.form.get("description", "").strip()
        artist.image_url = request.form.get("image_url", "").strip()
        artist.spotify_artist_id = request.form.get("spotify_artist_id", "").strip()

        db.session.commit()
        flash(f"{artist.name} was updated successfully.")
        return redirect(url_for("admin"))

    return render_template(
        "admin/edit_artist.html",
        active_page="admin",
        artist=artist,
    )

@app.route("/admin/login")
def admin_login():
    return render_template("login.html", active_page="admin_login")

@app.route("/admin/login_auth", methods=["POST"])
def admin_login_auth():
    # Handle admin login form submission
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not email or not password:
        flash("Both email and password are required.")
        return redirect(url_for("login"))

    user = User.query.filter_by(email=email, user_type="admin").first()

    if user and user.check_password(password):
        session["user_id"] = user.id
        session["name"] = user.username
        flash(f"Welcome back, {user.username}!")
        return redirect(url_for("admin"))

    else:
        flash("Invalid admin credentials. Please try again.")
        return redirect(url_for("login"))
    

@app.route("/admin/delete_artist/<int:artist_id>", methods=["POST"])
@admin_required
def delete_artist(artist_id):
    artist = Artist.query.get_or_404(artist_id)
    image_url = artist.image_url
    db.session.delete(artist)
    db.session.commit()
    delete_artist_image(artist_id, image_url)
    return redirect(url_for("admin"))


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