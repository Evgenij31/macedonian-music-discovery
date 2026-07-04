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

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "genre": self.genre,
            "decade": self.decade,
            "region": self.region,
            "image_url": self.image_url,
            "description": self.description
        }