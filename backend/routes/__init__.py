"""Flask route blueprints for the backend API."""

from flask import Flask


def register_routes(app: Flask) -> None:
    """Register all API blueprints with the given Flask app."""
    from . import misc, areas, objectives, tasks, undo

    app.register_blueprint(misc.bp)
    app.register_blueprint(areas.bp)
    app.register_blueprint(objectives.bp)
    app.register_blueprint(tasks.bp)
    app.register_blueprint(undo.bp)
