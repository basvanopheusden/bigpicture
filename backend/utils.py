"""Utility helpers used across the Flask application."""

from flask import request, jsonify


def parse_json(required_fields=None):
    """Parse JSON from the request.

    Parameters
    ----------
    required_fields : list[str] | None
        A list of keys that must be present in the JSON payload.

    Returns
    -------
    tuple
        ``(data, error)`` where ``data`` is the parsed object on success and
        ``error`` is ``(response, status_code)`` when a problem occurs.
    """
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


def shift_tasks_after_delete(conn, parent_col, parent_key, start_order):
    """Compact order indices after deleting a task.

    Parameters
    ----------
    conn : sqlite3.Connection
        Database connection.
    parent_col : str
        Column name identifying the parent (``area_key`` or ``objective_key``).
    parent_key : str
        Value of the parent column for the task being removed.
    start_order : int
        ``order_index`` of the removed task.  All tasks with a greater index
        will be shifted down by one.
    """

    conn.execute(
        f"UPDATE tasks SET order_index = order_index - 1 "
        f"WHERE {parent_col} = ? AND order_index > ?",
        (parent_key, start_order),
    )
