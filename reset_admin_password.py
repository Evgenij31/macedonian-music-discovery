from getpass import getpass
from pathlib import Path

from app import app
from extensions import db
from models import User


USERNAME = "EvgenijAdmin"


def main():
    password = getpass("New password: ")
    if not password:
        raise SystemExit("Password cannot be empty")

    with app.app_context():
        database_uri = app.config["SQLALCHEMY_DATABASE_URI"]
        print(f"Database: {database_uri}")

        users = User.query.filter_by(username=USERNAME).all()
        if len(users) != 1:
            raise SystemExit(f"Expected one user named {USERNAME}, found {len(users)}")

        user = users[0]
        user.set_password(password)
        db.session.commit()

        if not user.check_password(password):
            raise SystemExit("Password verification failed after saving")

        database_path = Path(database_uri.removeprefix("sqlite:///"))
        print(f"Updated {user.username} ({user.email}) in {database_path}")
        print("Password hash verified. Restart the PythonAnywhere web app before testing login.")


if __name__ == "__main__":
    main()