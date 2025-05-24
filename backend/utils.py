from flask import request, jsonify


def parse_json(required_fields=None):
    """Return parsed JSON data or an error response tuple."""
    if not request.is_json:
        return None, (jsonify({"error": "Content-Type must be application/json"}), 400)

    data = request.get_json(silent=True)
    if data is None:
        return None, (jsonify({"error": "Invalid JSON"}), 400)
    if required_fields:
        missing = [f for f in required_fields if f not in data]
        if missing:
            return None, (jsonify({"error": f"Missing required fields: {missing}"}), 400)
    return data, None
