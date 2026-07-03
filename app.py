from flask import Flask, render_template, jsonify
import json
import os

app = Flask(__name__)


# Route to serve main HTML page
@app.route("/")
def home():
    return render_template("index.html")


# Route to serve artist data as an API endpoint
@app.route("/api/artists")
def get_artists():
    with open("artists.json", "r", encoding="utf-8") as file:
        data = json.load(file)
    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
