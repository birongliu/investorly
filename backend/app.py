from flask import Flask
from routes.routes import bp
from supabase import create_client
import os
from dotenv import load_dotenv
app = Flask(__name__)
load_dotenv()

database_and_auth = create_client(os.getenv("SUPABASE_URL", ""), os.getenv("SUPBASE_KEY", ""))

app.register_blueprint(bp)

if __name__ == "__main__":
    # Development server
    app.run(host="127.0.0.1", port=5000, debug=True)
