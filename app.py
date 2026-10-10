import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

import requests
from flask import Flask, abort, flash, g, redirect, render_template, request, send_from_directory, url_for
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "hiking_mate.db"
UPLOAD_FOLDER = BASE_DIR / "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}

app = Flask(__name__)
app.config.update(SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "change-this-for-production"), UPLOAD_FOLDER=str(UPLOAD_FOLDER))
UPLOAD_FOLDER.mkdir(exist_ok=True)

HIKES = [
    {"slug": "rajmachi-fort", "name": "Rajmachi Fort", "place": "Lonavala", "region": "Pune", "distance": "16 km", "duration": "5–6 hr", "difficulty": "Moderate", "risk": 42, "elevation": "826 m", "coords": (18.827, 73.387), "image": "https://commons.wikimedia.org/wiki/Special:FilePath/Rajmachi%20fort%20-%20Pune%20-Maharashtra%20-DSC001.jpg?width=1400", "description": "A classic Sahyadri walk through forest trails to twin hill forts, best enjoyed after the monsoon.", "equipment": ["2L water", "Trekking shoes", "Rain jacket", "Energy snacks", "Torch"], "caution": "Slippery rock sections and reduced visibility in heavy rain."},
    {"slug": "visapur-fort", "name": "Visapur Fort", "place": "Malavli", "region": "Pune", "distance": "6 km", "duration": "3–4 hr", "difficulty": "Moderate", "risk": 51, "elevation": "1,084 m", "coords": (18.719, 73.489), "image": "https://commons.wikimedia.org/wiki/Special:FilePath/Visapur%20fort%20in%20monsoon.jpg?width=1400", "description": "A rewarding fort trek with monsoon waterfalls, stone steps and broad views across Lonavala.", "equipment": ["Grippy trekking shoes", "2L water", "Rain jacket", "First-aid kit", "Waterproof phone pouch"], "caution": "Avoid waterfall routes in extreme rain; steps can become very slick."},
    {"slug": "lohagad-fort", "name": "Lohagad Fort", "place": "Lonavala", "region": "Pune", "distance": "5 km", "duration": "2–3 hr", "difficulty": "Beginner", "risk": 24, "elevation": "1,033 m", "coords": (18.711, 73.475), "image": "https://commons.wikimedia.org/wiki/Special:FilePath/Panoramic%20view%20of%20the%20bastions%20of%20Lohagad%20Fort%202.jpg?width=1400", "description": "A short, well-loved fort trail with a clear stone approach and a dramatic Vinchu Kata ridge.", "equipment": ["1.5L water", "Walking shoes", "Cap", "Light snack", "Rain layer"], "caution": "Start early on weekends: the steps and parking area get crowded."},
    {"slug": "kalsubai-peak", "name": "Kalsubai Peak", "place": "Bari", "region": "Ahmednagar", "distance": "12 km", "duration": "6–8 hr", "difficulty": "Challenging", "risk": 66, "elevation": "1,646 m", "coords": (19.601, 73.702), "image": "https://commons.wikimedia.org/wiki/Special:FilePath/Kalsubai%2C%20Western%20Ghats.jpg?width=1400", "description": "Maharashtra’s highest peak, with ladders, exposed patches and sunrise views over the Sahyadris.", "equipment": ["3L water", "Proper trekking shoes", "Headlamp", "Warm layer", "First-aid kit", "Offline map"], "caution": "A long day with exposed ladder sections. Do not attempt in lightning or high winds."},
    {"slug": "harishchandragad", "name": "Harishchandragad", "place": "Pachnai", "region": "Ahmednagar", "distance": "14 km", "duration": "7–9 hr", "difficulty": "Challenging", "risk": 71, "elevation": "1,424 m", "coords": (19.387, 73.776), "image": "https://commons.wikimedia.org/wiki/Special:FilePath/Harishchandragad%20view%20from%20caves.jpg?width=1400", "description": "An epic hill fort known for Konkan Kada, caves and a full-day wilderness feel.", "equipment": ["3L water", "Trekking poles", "Headlamp", "Warm layer", "Food", "Emergency whistle"], "caution": "Know your route and turnaround time. Conditions around Konkan Kada can change quickly."},
    {"slug": "tikona-fort", "name": "Tikona Fort", "place": "Pawna", "region": "Pune", "distance": "4 km", "duration": "2–3 hr", "difficulty": "Beginner", "risk": 28, "elevation": "1,064 m", "coords": (18.642, 73.512), "image": "https://commons.wikimedia.org/wiki/Special:FilePath/Tikona%20Panorama.jpg?width=1400", "description": "A compact pyramid-shaped fort with a lively trail and sweeping Pawna Lake views.", "equipment": ["1.5L water", "Walking shoes", "Sun protection", "Snack", "Phone power bank"], "caution": "The final stairway is narrow—take it slowly and yield to descending hikers."},
]

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(_error):
    db = g.pop("db", None)
    if db: db.close()

def init_db():
    db = get_db()
    db.execute("""CREATE TABLE IF NOT EXISTS albums (
        id INTEGER PRIMARY KEY AUTOINCREMENT, hike_slug TEXT NOT NULL, title TEXT NOT NULL,
        hike_date TEXT, created_at TEXT NOT NULL)""")
    db.execute("""CREATE TABLE IF NOT EXISTS photos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, album_id INTEGER NOT NULL, filename TEXT NOT NULL,
        caption TEXT, uploaded_at TEXT NOT NULL, FOREIGN KEY(album_id) REFERENCES albums(id))""")
    db.commit()

with app.app_context():
    init_db()

def find_hike(slug):
    return next((hike for hike in HIKES if hike["slug"] == slug), None)

def live_weather(hike):
    lat, lon = hike["coords"]
    try:
        response = requests.get("https://api.open-meteo.com/v1/forecast", params={"latitude": lat, "longitude": lon, "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m", "timezone": "Asia/Kolkata"}, timeout=4)
        current = response.json()["current"]
        codes = {0: "Clear", 1: "Mostly clear", 2: "Partly cloudy", 3: "Overcast", 45: "Foggy", 51: "Light drizzle", 61: "Rain", 80: "Rain showers", 95: "Thunderstorm"}
        return {"temp": round(current["temperature_2m"]), "feels": round(current["apparent_temperature"]), "wind": round(current["wind_speed_10m"]), "condition": codes.get(current["weather_code"], "Mixed conditions"), "live": True}
    except (requests.RequestException, KeyError, ValueError):
        return {"temp": 24, "feels": 25, "wind": 13, "condition": "Check local forecast", "live": False}

def ai_advice(hike, weather):
    prompt = f"You are a concise Maharashtra hiking safety guide. For {hike['name']} near {hike['place']}, a {hike['difficulty']} hike with risk score {hike['risk']}/100, weather is {weather['condition']}, {weather['temp']}C, wind {weather['wind']} km/h. Give exactly 3 short practical bullets: readiness, one safety warning, and a go/no-go recommendation. Don't invent current restrictions."
    try:
        response = requests.post("http://127.0.0.1:11434/api/generate", json={"model": os.environ.get("OLLAMA_MODEL", "gemma3:4b"), "prompt": prompt, "stream": False, "options": {"temperature": 0.3}}, timeout=35)
        response.raise_for_status()
        text = response.json().get("response", "").strip()
        if text:
            return text, True
    except requests.RequestException:
        pass
    return f"• Carry the listed essentials and begin with daylight to spare.\n• {hike['caution']}\n• {'Go if conditions remain stable; reassess at the trailhead.' if hike['risk'] < 55 else 'Plan only with experience, a reliable route plan, and favourable conditions.'}", False

@app.route("/")
def home():
    query = request.args.get("q", "").strip().lower()
    difficulty = request.args.get("difficulty", "")
    hikes = [h for h in HIKES if (not query or query in (h["name"] + h["place"] + h["region"]).lower()) and (not difficulty or h["difficulty"] == difficulty)]
    return render_template("home.html", hikes=hikes, query=query, selected_difficulty=difficulty)

@app.route("/hikes/<slug>")
def hike_detail(slug):
    hike = find_hike(slug)
    if not hike: abort(404)
    weather = live_weather(hike)
    advice, ai_available = ai_advice(hike, weather)
    albums = get_db().execute("SELECT * FROM albums WHERE hike_slug = ? ORDER BY created_at DESC", (slug,)).fetchall()
    return render_template("detail.html", hike=hike, weather=weather, advice=advice, ai_available=ai_available, albums=albums)

@app.route("/albums")
def albums():
    rows = get_db().execute("""SELECT a.*, COUNT(p.id) AS photo_count FROM albums a LEFT JOIN photos p ON p.album_id=a.id GROUP BY a.id ORDER BY a.created_at DESC""").fetchall()
    return render_template("albums.html", albums=rows)

@app.route("/albums/new", methods=["POST"])
def create_album():
    hike = find_hike(request.form.get("hike_slug", ""))
    title = request.form.get("title", "").strip()
    if not hike or not title:
        flash("Choose a hike and give your album a name.", "error")
        return redirect(request.referrer or url_for("albums"))
    db = get_db()
    db.execute("INSERT INTO albums (hike_slug, title, hike_date, created_at) VALUES (?, ?, ?, ?)", (hike["slug"], title, request.form.get("hike_date"), datetime.now().isoformat()))
    db.commit()
    flash("Album created—add your best trail moments.", "success")
    return redirect(url_for("albums"))

@app.route("/albums/<int:album_id>")
def album_detail(album_id):
    album = get_db().execute("SELECT * FROM albums WHERE id = ?", (album_id,)).fetchone()
    if not album: abort(404)
    hike = find_hike(album["hike_slug"])
    photos = get_db().execute("SELECT * FROM photos WHERE album_id = ? ORDER BY uploaded_at DESC", (album_id,)).fetchall()
    return render_template("album_detail.html", album=album, hike=hike, photos=photos)

@app.route("/albums/<int:album_id>/photos", methods=["POST"])
def upload_photo(album_id):
    album = get_db().execute("SELECT id FROM albums WHERE id = ?", (album_id,)).fetchone()
    photo = request.files.get("photo")
    if not album or not photo or not photo.filename or photo.filename.rsplit(".", 1)[-1].lower() not in ALLOWED_EXTENSIONS:
        flash("Choose a JPG, PNG, WEBP, or GIF photo.", "error")
        return redirect(url_for("album_detail", album_id=album_id))
    filename = f"{uuid.uuid4().hex}_{secure_filename(photo.filename)}"
    photo.save(UPLOAD_FOLDER / filename)
    get_db().execute("INSERT INTO photos (album_id, filename, caption, uploaded_at) VALUES (?, ?, ?, ?)", (album_id, filename, request.form.get("caption", "").strip(), datetime.now().isoformat()))
    get_db().commit()
    return redirect(url_for("album_detail", album_id=album_id))

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.context_processor
def globals_for_templates():
    return {"all_hikes": HIKES}

if __name__ == "__main__":
    app.run(debug=True)
