from werkzeug.security import check_password_hash, generate_password_hash
from extensions import db

class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    genre = db.Column(db.String(50), nullable=False)
    decade = db.Column(db.String(20), nullable=False)
    region = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)  # <-- Make sure this line exists!
    spotify_artist_id = db.Column(db.String(100), nullable=True)
    spotify_link = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "genre": self.genre,
            "decade": self.decade,
            "region": self.region,
            "image_url": self.image_url,
            "description": self.description,
            "spotify_artist_id": self.spotify_artist_id,
            "spotify_link": self.spotify_link
        }

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)