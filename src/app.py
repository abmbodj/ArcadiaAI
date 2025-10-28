import os
import sys
import uuid
import threading
import asyncio
import flask as fk
import json
# Ensure your project src is on the path (same as your original)
proj_root = os.path.dirname(__file__)          # project root if app.py is there
src_dir = os.path.join(proj_root, "src")
sys.path.insert(0, src_dir)
from lib import GemInterface
from lib import qrCodeGen
from werkzeug.security import generate_password_hash

# Create the AiInterface instance (expected to have an async Archie method)
gemini = GemInterface.AiInterface()

app = fk.Flask(__name__)

def Archie(query: str) -> str:
    """
    Synchronous wrapper to run the async gemini.Archie in a new event loop.
    """
    return asyncio.run(gemini.Archie(query))





@app.route("/", methods=["GET"])
def home():
    hometemplate = fk.render_template("index.html")
    return hometemplate

@app.route("/api/archie", methods=["POST"])
def api_archie():
    data = fk.request.get_json()
    question = data.get("question", "")
    answer = Archie(question)
    with open("data/qna.json", "r", encoding="utf-8") as f:
        qna_data = json.load(f)
    qna_data[question] = answer
    with open("data/qna.json", "w", encoding="utf-8") as f:
        json.dump(qna_data, f, ensure_ascii=False, indent=4)
    print(f"Question: {question}\nAnswer: {answer}\n")
    return fk.jsonify({"answer": answer})

@app.route("/api/archie/stream", methods=["POST"])
def api_archie_stream():
    """
    Streaming endpoint that returns AI responses token by token.
    This provides a better user experience by showing the AI "thinking" in real-time.
    """
    data = fk.request.get_json()
    question = data.get("question", "")
    
    def generate():
        """Generator function for Server-Sent Events (SSE)"""
        full_response = ""
        loop = None
        try:
            # Create a new event loop for this request (don't set it globally)
            loop = asyncio.new_event_loop()
            
            async_gen = gemini.Archie_streaming(question)
            while True:
                try:
                    token = loop.run_until_complete(async_gen.__anext__())
                    full_response += token
                    # Send each token as a Server-Sent Event
                    yield f"data: {json.dumps({'token': token})}\n\n"
                except StopAsyncIteration:
                    break
            
            # Save the full response to qna.json
            with open("data/qna.json", "r", encoding="utf-8") as f:
                qna_data = json.load(f)
            qna_data[question] = full_response
            with open("data/qna.json", "w", encoding="utf-8") as f:
                json.dump(qna_data, f, ensure_ascii=False, indent=4)
            
            print(f"Question: {question}\nAnswer: {full_response}\n")
            
            # Send completion signal
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            # Log the full error for debugging, but only send a generic message to the user
            print(f"Error during streaming: {e}")
            yield f"data: {json.dumps({'error': 'An error occurred while generating the response'})}\n\n"
        finally:
            # Clean up the event loop
            if loop is not None and not loop.is_closed():
                loop.close()
    
    return fk.Response(generate(), mimetype='text/event-stream')

@app.route("/gchats", methods=["GET", "POST"])
def gchats():
    session_id = fk.request.cookies.get("session_id")
    if not session_id:
        session_id = uuid.uuid4().hex


    # render template and attach session cookie
    resp = fk.make_response(fk.redirect(fk.url_for("chats")))
    print(f"New guest session started: {session_id}")
    resp.set_cookie("session_id", session_id, httponly=True, samesite="Lax")
    return resp
@app.route("/chats", methods=["GET", "POST"])
def chats():
    if fk.request.method == "POST":
        email = fk.request.form.get("email", "").strip()
        password = fk.request.form.get("password", "")
        # replace the following simple check with your real authentication
        if email and password:
            session_id = fk.request.cookies.get("session_id")
            if not session_id:
                session_id = uuid.uuid4().hex
            # render template and attach session cookie 
            resp = fk.make_response(fk.redirect(fk.url_for("chats")))
            print(f"User {email} logged in with session: {session_id}")
            resp.set_cookie("session_id", session_id, httponly=True, samesite="Lax")
            chatstemplate = fk.render_template("index.html")
            return chatstemplate
            
            
        else:
            return fk.render_template("home.html", error="Please provide email and password")


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
    #threading.Thread(target=lambda: os.system("python src/helpers/scraper.py"), daemon=True).start()
    #print(Archie("What is Arcadia University short response please? What is the weather like there? Where is the dining hall located? What IT resources are available to students? When are finals for Fall 2025"))

    #qrCodeGen.make_qr(" https://cgs3mzng.use.devtunnels.ms:5000", show=True, save_path="websiteqr.png")


    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)