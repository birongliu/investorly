from flask import Flask
from backend.routes.routes import bp
app = Flask(__name__)

app.register_blueprint(bp)

if __name__ == "__main__":
    # Development server
    app.run(host="127.0.0.1", port=5000, debug=True)
