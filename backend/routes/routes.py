from flask import Blueprint, jsonify

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    return jsonify({"message": "Investorly API", "status": "ok"}), 200


@bp.route("/health")
def health():
    return jsonify({"status": "healthy"}), 200
