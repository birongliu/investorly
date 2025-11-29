from flask import Flask, request
from os import getenv
from dotenv import load_dotenv
from flask_cors import cross_origin, CORS
load_dotenv()

app = Flask(__name__)
from chat import Chat

cors = CORS(app, origins=getenv("FRONTEND_URL"))
chat_instance = Chat()


@app.route("/api/v1/llm", methods=["POST"])
@cross_origin(supports_credentials=True)
def chat():
   if not request.json:
       return {"message": "Invalid request: JSON body required"}, 400
   message = request.json.get("messages")[-1]['content']
   context = request.json.get("context")
   return chat_instance.response(message, context=context), 200


if __name__ == "__main__":
    # Development server
    app.run(host="0.0.0.0", port=5000, debug=True)
