"""Flask application entry point."""

import logging
import os
from flask import Flask
from flask_cors import CORS

try:
    from .database import (
        get_db,
        init_db,
        log_action_for_undo,
        get_pacific_time,
    )
    from .utils import parse_json, next_order_index, rows_to_dicts
except ImportError:  # pragma: no cover - executed only when run as script
    from database import (
        get_db,
        init_db,
        log_action_for_undo,
        get_pacific_time,
    )
    from utils import parse_json, next_order_index, rows_to_dicts

logging.basicConfig(level=logging.INFO)


def create_app() -> Flask:
    """Create and configure the Flask application."""
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

    try:
        from .routes import register_routes
    except ImportError:  # pragma: no cover - executed only when run as script
        from routes import register_routes

    register_routes(app)
    return app


app = create_app()

if __name__ == '__main__':  # pragma: no cover - manual run
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
