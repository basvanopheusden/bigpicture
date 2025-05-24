"""Flask application entry point."""
import os
import logging
logging.basicConfig(level=logging.INFO)
from flask import Flask, jsonify
from flask_cors import CORS

try:
    from .database import get_db, init_db, log_action_for_undo, get_pacific_time
    from .utils import parse_json
    from .routes import areas, objectives, tasks, undo
except ImportError:  # pragma: no cover - executed only when run as script
    from database import get_db, init_db, log_action_for_undo, get_pacific_time
    from utils import parse_json
    from routes import areas, objectives, tasks, undo

app = Flask(__name__)

app.config['CORS_HEADERS'] = 'Content-Type'
CORS(
    app,
    resources={r"/api/*": {
        "origins": [
            "http://localhost:5173",
            "https://bigpicture-frontend-ancient-night-2172.fly.dev",
            "https://foo.boulos.ca",
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True,
        "expose_headers": ["Access-Control-Allow-Origin"],
    }},
    supports_credentials=True,
)

with app.app_context():
    init_db()
    # expose helpers for blueprints and tests
    app.get_db = get_db
    app.log_action_for_undo = log_action_for_undo
    app.get_pacific_time = get_pacific_time
    app.parse_json = parse_json

@app.route('/api/test', methods=['GET'])
def test():
    """Simple health check used by tests."""
    return jsonify({"status": "ok", "message": "API is working"})

# Register API blueprints
app.register_blueprint(areas.bp)
app.register_blueprint(objectives.bp)
app.register_blueprint(tasks.bp)
app.register_blueprint(undo.bp)

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
