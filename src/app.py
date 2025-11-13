import os
import sys
import uuid
import threading
import asyncio
import time
import flask as fk
import json
proj_root = os.path.dirname(__file__)         
src_dir = os.path.join(proj_root, "src")
sys.path.insert(0, src_dir)
from lib import GemInterface
from lib import qrCodeGen
from lib.SessionManager import SessionManager
from lib.DataCollector import DataCollector
from werkzeug.security import generate_password_hash

gemini = GemInterface.AiInterface()

session_manager = SessionManager(data_dir="data")
data_collector = DataCollector(data_dir="data")

app = fk.Flask(__name__)

def Archie(query: str, conversation_history: list = None) -> str:
    """
    Synchronous wrapper to run the async gemini.Archie in a new event loop.
    """
    return asyncio.run(gemini.Archie(query, conversation_history=conversation_history))





@app.route("/", methods=["GET"])
def home():
    # Check if user has a session
    session_id = fk.request.cookies.get("session_id")
    if session_id:
        # User has session, redirect to chat
        return fk.redirect(fk.url_for("index"))
    # No session, show login page
    return fk.render_template("home.html")

@app.route("/index", methods=["GET"])
def index():
    # Main chat interface
    session_id = fk.request.cookies.get("session_id")
    if not session_id:
        # No session, redirect to login
        return fk.redirect(fk.url_for("home"))
    return fk.render_template("index.html")

@app.route("/api/archie", methods=["POST"])
def api_archie():
    start_time = time.time()
    
    data = fk.request.get_json()
    question = data.get("question", "")
    session_id = fk.request.cookies.get("session_id")
    user_email = fk.request.cookies.get("user_email")
    
    # Get conversation history if session exists
    conversation_history = []
    if session_id:
        conversation_history = session_manager.get_conversation_history(session_id)
    
    answer = Archie(question, conversation_history=conversation_history)
    
    # Calculate generation time
    generation_time = time.time() - start_time
    
    # Save to session if session_id exists
    if session_id:
        session_manager.add_message(session_id, "user", question)
        session_manager.add_message(session_id, "assistant", answer)
    
    # Collect analytics data
    data_collector.log_interaction(
        session_id=session_id if session_id else "no_session",
        user_email=user_email,
        ip_address=fk.request.remote_addr,
        device_info=fk.request.user_agent.string,
        question=question,
        answer=answer,
        generation_time_seconds=generation_time
    )
    
    print(f"Question: {question}\nAnswer: {answer}\n")
    return fk.jsonify({"answer": answer})
import datetime
@app.route("/api/archie/stream", methods=["POST"])
def api_archie_stream():
    """
    Streaming endpoint that returns AI responses token by token.
    This provides a better user experience by showing the AI "thinking" in real-time.
    """
    start_time = time.time()
    
    data = fk.request.get_json()
    question = data.get("question", "")
    session_id = fk.request.cookies.get("session_id")
    user_email = fk.request.cookies.get("user_email")
    
    # Capture request info for data collection
    ip_address = fk.request.remote_addr
    device_info = fk.request.user_agent.string
    
    def generate():
        full_response = ""
        loop = None
        try:
            # Get conversation history if session exists
            conversation_history = []
            if session_id:
                conversation_history = session_manager.get_conversation_history(session_id)
            
            # Create a new event loop for this request 
            loop = asyncio.new_event_loop()
            
            async_gen = gemini.Archie_streaming(question, conversation_history=conversation_history)
            while True:
                try:
                    # Get the next item from the async generator
                    chunk = loop.run_until_complete(async_gen.__anext__())
                    
                    
                    if isinstance(chunk, str):
                        # Append it to the full response and stream it.
                        full_response += chunk
                        yield f"data: {json.dumps({'token': chunk})}\n\n"
                    
                    elif isinstance(chunk, dict):
                        # Make it JSON-safe before streaming. because trial and error is the only way to figure this out apparently
                        
                        if chunk.get('tool_name'):
                            # Create a NEW, safe dictionary for the client
                            json_safe_payload = {
                                'tool_name': chunk.get('tool_name'),
                                'tool_result_preview': str(chunk.get('tool_result'))[:500]
                            }
                            yield f"data: {json.dumps({'tool_call': json_safe_payload})}\n\n"
                            
                        elif chunk.get('final'):
                            # This is just a signal, ignore it.
                            pass
                        
                    
                    else:
                        # Safely log it and send a debug message.
                        
                        chunk_type = type(chunk).__name__
                        print(f"Warning: Received unexpected chunk type: {chunk_type}")
                        
                        # Optionally send a safe representation to the client
                        yield f"data: {json.dumps({'debug_info': f'Received object: {chunk_type}'})}\n\n"
                except StopAsyncIteration:
                    # The generator is done.
                    break
            
            # Calculate generation time 
            generation_time = time.time() - start_time
            
            # Save to session if session_id exists
            if session_id:

                session_manager.add_message(session_id, "user", question)
                session_manager.add_message(session_id, "assistant", full_response)
            
            # Collect analytics data I LOVE DATA COLLECTION
            data_collector.log_interaction(
                session_id=session_id if session_id else "no_session",
                user_email=user_email,
                ip_address=ip_address,
                device_info=device_info,
                question=question,
                answer=full_response,
                generation_time_seconds=generation_time
            )
            
            
            print(f"Question: {question}\nAnswer: {full_response}\n")
            
            # Send completion signal
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            #print the traceback for debugging I may remove this but for now its useful
            print(f"Error during streaming generation: {e}")
            import traceback
            traceback.print_exc()
        finally:
            
            # Clean up the event loop
            if loop is not None and not loop.is_closed():
                loop.close()
    
    return fk.Response(generate(), mimetype='text/event-stream')

#Gets conversation history for current session
@app.route("/api/sessions/history", methods=["GET"])
def get_session_history():
    """Get conversation history for current session."""
    session_id = fk.request.cookies.get("session_id")
    if not session_id:
        return fk.jsonify({"error": "No session found"}), 401
    
    history = session_manager.get_conversation_history(session_id)
    return fk.jsonify({"history": history})

#List all sessions for current user
@app.route("/api/sessions/list", methods=["GET"])
def list_user_sessions():
    """List all sessions for logged-in user."""
    user_email = fk.request.cookies.get("user_email")
    if not user_email:
        return fk.jsonify({"error": "Not logged in"}), 401
    
    sessions = session_manager.get_all_user_sessions_with_preview(user_email)
    return fk.jsonify({"sessions": sessions})

#get details for a specific session
@app.route("/api/sessions/<session_id>", methods=["GET"])
def get_session_details(session_id):
    """Get details of a specific session."""
    user_email = fk.request.cookies.get("user_email")
    
    session_data = session_manager.get_session(session_id)
    if not session_data:
        return fk.jsonify({"error": "Session not found"}), 404
    
    # Check if user owns this session (or it's their current session)
    current_session_id = fk.request.cookies.get("session_id")
    if session_data.get("user_email") != user_email and session_id != current_session_id:
        return fk.jsonify({"error": "Unauthorized"}), 403
    
    return fk.jsonify(session_data)

#Delete a specific session
@app.route("/api/sessions/<session_id>", methods=["DELETE"])
def delete_session(session_id):
    """Delete a specific session."""
    user_email = fk.request.cookies.get("user_email")
    current_session_id = fk.request.cookies.get("session_id")
    
    session_data = session_manager.get_session(session_id)
    if not session_data:
        return fk.jsonify({"error": "Session not found"}), 404
    
    # Check if user owns this session
    if session_data.get("user_email") != user_email and session_id != current_session_id:
        return fk.jsonify({"error": "Unauthorized"}), 403
    
    success = session_manager.delete_session(session_id, user_email)
    if success:
        return fk.jsonify({"message": "Session deleted"})
    else:
        return fk.jsonify({"error": "Failed to delete session"}), 500

#Create a new session
@app.route("/api/sessions/new", methods=["POST"])
def create_new_session():
    """Create a new chat session for the current user."""
    user_email = fk.request.cookies.get("user_email")
    
    session_id = session_manager.create_session(user_email=user_email)
    
    resp = fk.make_response(fk.jsonify({"session_id": session_id}))
    resp.set_cookie("session_id", session_id, httponly=True, samesite="Strict")
    return resp

#Switch to a different session
@app.route("/api/sessions/switch/<session_id>", methods=["POST"])
def switch_session(session_id):
    """Switch to a different session."""
    user_email = fk.request.cookies.get("user_email")
    
    session_data = session_manager.get_session(session_id)
    if not session_data:
        return fk.jsonify({"error": "Session not found"}), 404
    
    # Check if user owns this session
    if session_data.get("user_email") != user_email:
        return fk.jsonify({"error": "Unauthorized"}), 403
    
    resp = fk.make_response(fk.jsonify({"message": "Session switched"}))
    resp.set_cookie("session_id", session_id, httponly=True, samesite="Lax")
    return resp

#This is not used and guests are no longer supported. I am keeping it for potential future use.
@app.route("/gchats", methods=["GET", "POST"])
def gchats():
    session_id = fk.request.cookies.get("session_id")
    if not session_id:
        # Create new guest session
        session_id = session_manager.create_session(user_email=None)

    # render template and attach session cookie
    resp = fk.make_response(fk.redirect(fk.url_for("index")))
    print(f"New guest session started: {session_id}")
    resp.set_cookie("session_id", session_id, httponly=True, samesite="Strict")
    return resp
@app.route("/chats", methods=["GET", "POST"])
def chats():
    if fk.request.method == "POST":
        email = fk.request.form.get("email", "").strip()
        password = fk.request.form.get("password", "")
        
        # Basic email validation
        if not email or "@" not in email or len(email) > 255:
            return fk.render_template("home.html", error="Please provide a valid email address")
        
        if not password:
            return fk.render_template("home.html", error="Password is required")

        if email and password:
            # Try to authenticate user
            if session_manager.authenticate_user(email, password):
                # Create new session for logged-in user
                session_id = session_manager.create_session(user_email=email)
                
                resp = fk.make_response(fk.redirect(fk.url_for("index")))
                print(f"User {email} logged in with session: {session_id}")

                resp.set_cookie("session_id", session_id, httponly=True, samesite="Strict")
                resp.set_cookie("user_email", email, httponly=True, samesite="Strict")
                return resp
            else:
                # User doesn't exist, create new account
                if session_manager.create_user(email, password, ip_address=fk.request.remote_addr, device_info=fk.request.user_agent.string):
                    session_id = session_manager.create_session(user_email=email)

                    resp = fk.make_response(fk.redirect(fk.url_for("index")))
                    print(f"New user {email} created with session: {session_id}")
                    resp.set_cookie("session_id", session_id, httponly=True, samesite="Strict")
                    resp.set_cookie("user_email", email, httponly=True, samesite="Strict")
                    return resp
                else:
                    return fk.render_template("home.html", error="Failed to create account")
        else:
            return fk.render_template("home.html", error="Please provide email and password")
    return fk.render_template("home.html")


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


    #qrCodeGen.make_qr(" https://cgs3mzng.use.devtunnels.ms:5000", show=True, save_path="websiteqr.png")
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)