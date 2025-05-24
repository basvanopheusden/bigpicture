"""Miscellaneous API endpoints."""

from flask import Blueprint, jsonify

bp = Blueprint('misc', __name__)


@bp.route('/api/test', methods=['GET'])
def test() -> tuple:
    """Simple endpoint used by tests to verify API availability."""
    return jsonify({"status": "ok", "message": "API is working"})
