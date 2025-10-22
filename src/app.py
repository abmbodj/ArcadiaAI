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




@app.route("/", methods=["GET"])
def home():
    response = Archie("When is fall break?")
    return response


@app.route("/chats", methods=["GET"])
def chats():
    chatstemplate = fk.render_template("chats.html")
    return chatstemplate


if __name__ == "__main__":
    print("Working Directory:", os.getcwd())
    gemini.start_datascraper()
    # Use threaded=True so the dev server can serve other requests while background tasks run
    # For production, run with a WSGI/ASGI server (gunicorn/uvicorn) and a proper worker strategy.

    app.run(debug=True, threaded=True)