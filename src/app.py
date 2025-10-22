import os
import sys
import flask as fk
proj_root = os.path.dirname(__file__)          # project root if app.py is there
src_dir = os.path.join(proj_root, "src")
sys.path.insert(0, src_dir)
from lib import GemInterface

gemini = GemInterface.AiInterface()



app = fk.Flask(__name__)

@app.route("/ask", methods=["POST"])
def ask():
    user_input = fk.request.json.get("question")
    response = gemini.Archie(user_input)
    return fk.jsonify({"response": response}) 

@app.route("/", methods=["GET"])
def home():
    indextemplate = fk.render_template("index.html")
    return indextemplate

@app.route("/chats", methods=["GET"])
def chats():
    chatstemplate = fk.render_template("chats.html")
    return chatstemplate

if __name__ == "__main__":
    print("Working Directory:", os.getcwd())
    app.run(debug=True)