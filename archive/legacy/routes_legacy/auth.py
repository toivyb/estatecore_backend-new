from flask import Blueprint, jsonify
from ..models import db
from ..models.user import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login", methods=["POST"])
def login():
    return jsonify({"message": "Login OK"})
