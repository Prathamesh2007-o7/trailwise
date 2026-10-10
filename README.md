#  Trailwise

**Find your next good climb.**

Trailwise is a hiking companion web app that helps users discover trails across Maharashtra, check weather conditions, assess potential risks, prepare for hikes, and save memories through photo albums.

##  Features

-  **Trail Discovery** — Explore hiking locations with difficulty, distance, elevation, and descriptions.
-  **Live Weather** — Check current weather conditions for a trail.
-  **Risk Assessment** — View an estimated risk score before your hike.
-  **AI Gear Checklist** — Get hiking preparation recommendations powered by Gemma 3 (4B).
-  **Photo Albums** — Upload and organize memories from your hikes.

##  Tech Stack

- **Frontend:** HTML, CSS, JavaScript
- **Backend:** Python, Flask
- **AI Model:** Gemma 3 (4B) via Ollama
- **Weather:** Open-Meteo API
- **Photo Storage:** Local `uploads/` directory

##  Getting Started

### Prerequisites

- Python 3
- [Ollama](https://ollama.com/)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Download the AI model**
   ```bash
   ollama pull gemma3:4b
   ```

4. **Start the Flask application**
   ```bash
   python app.py
   ```

Ensure Ollama is running so the AI-powered checklist can access the model.

5. **Open the application**

   Visit [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

## 📁 Photo Storage

Uploaded photos are stored locally in the `uploads/` directory.


## 🌱 Why Trailwise?

Trailwise combines open-weight AI with practical outdoor planning to help people explore nature more thoughtfully, prepare responsibly, and preserve their adventures.
