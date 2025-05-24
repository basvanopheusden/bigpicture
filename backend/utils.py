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


def next_order_index(conn, table, where_clause='', params=()):
    """Return the next order index for ``table`` satisfying ``where_clause``."""
    query = f'SELECT MAX(order_index) FROM {table} {where_clause}'
    max_order = conn.execute(query, params).fetchone()[0]
    return (max_order if max_order is not None else -1) + 1


def rows_to_dicts(rows):
    """Convert a sequence of ``sqlite3.Row`` objects to dictionaries."""
    return [dict(row) for row in rows]
