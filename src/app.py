import os
import sys
import uuid
import threading
import concurrent.futures
import asyncio
import flask as fk

# Ensure your project src is on the path (same as your original)
proj_root = os.path.dirname(__file__)          # project root if app.py is there
src_dir = os.path.join(proj_root, "src")
sys.path.insert(0, src_dir)
from lib import GemInterface
import time
import traceback

# Create the AiInterface instance (expected to have an async Archie method)
gemini = GemInterface.AiInterface()

app = fk.Flask(__name__)

def Archie(query: str) -> str:
    """
    Synchronous wrapper to run the async gemini.Archie in a new event loop.
    """
    return asyncio.run(gemini.Archie(query))


@app.route("/ask", methods=["POST"])
def ask():
    data = fk.request.json
    query = data.get("query", "").strip()
    if not query:
        return fk.jsonify({"error": "Query cannot be empty."}), 400

    response = Archie(query)
    return fk.jsonify({"response": response})

import json


@app.route("/", methods=["GET"])
def home():
    hometemplate = fk.render_template("index.html")
    return hometemplate



@app.route("/chats", methods=["GET"])
def chats():
    chatstemplate = fk.render_template("chats.html")
    return chatstemplate

def background_checker():
    urls = {
        "website": "https://www.arcadia.edu/",
        "events": "https://www.arcadia.edu/events/?mode=month",
        "about": "https://www.arcadia.edu/about-arcadia/",
        "weather": "https://weather.com/weather/today/l/b0f4fc1167769407f55347d55f492a46e194ccaed63281d2fa3db2e515020994",
        "diningHours": "https://www.arcadia.edu/life-arcadia/living-commuting/dining/",
        "ITresources": "https://www.arcadia.edu/life-arcadia/campus-life-resources/information-technology/",
        "Academic Calendar": "https://www.arcadia.edu/academics/resources/academic-calendars/2025-26/",
        }
    

    dictionary = {}
    for name, url in urls.items():
        result = gemini.scrape_website(url)
        dictionary[name] = result

    # ensure the data directory exists, then write the collected dictionary as JSON
    os.makedirs(os.path.dirname("data/scrape_results.json"), exist_ok=True)
    with open("data/scrape_results.json", "w", encoding="utf-8") as f:
        json.dump(dictionary, f, ensure_ascii=False, indent=4)

    
if __name__ == "__main__":
    # Use threaded=True so the dev server can serve other requests while background tasks run
    # For production, run with a WSGI/ASGI server (gunicorn/uvicorn) and a proper worker strategy.

    #run a seperate python file in a seperate terminal using os.system that scrapes the arcadia website every hour in the background
    threading.Thread(target=lambda: os.system("python src/helpers/scraper.py"), daemon=True).start()
    #print(Archie("What is Arcadia University short response please? What is the weather like there? Where is the dining hall located? What IT resources are available to students? When are finals for Fall 2025"))




    app.run(debug=True, threaded=True)