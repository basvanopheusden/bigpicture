"""Area related API routes."""

import logging
from flask import Blueprint, request, jsonify
import backend.app as main_app
from ..utils import parse_json, next_order_index, rows_to_dicts

bp = Blueprint('areas', __name__)


@bp.route('/api/areas', methods=['GET', 'POST'])
def handle_areas():
    """Retrieve or create areas."""
    if request.method == 'GET':
        try:
            with main_app.get_db() as conn:
                areas = conn.execute('SELECT * FROM areas').fetchall()
                return jsonify(rows_to_dicts(areas))
        except Exception as e:  # pragma: no cover - exercise only via tests
            logging.error(f"Error getting areas: {e}")
            return jsonify({"error": str(e)}), 500

    if request.method == 'POST':
        try:
            data, error = parse_json(['key', 'text'])
            if error:
                return error

            with main_app.get_db() as conn:
                next_order = next_order_index(conn, 'areas')
                conn.execute(
                    'INSERT INTO areas (key, text, date_time_created, order_index) VALUES (?, ?, ?, ?)',
                    (data['key'], data['text'], main_app.get_pacific_time(), next_order)
                )
                conn.commit()
                return jsonify({'status': 'success'})
        except Exception as e:  # pragma: no cover - exercise only via tests
            logging.error(f"Error creating area: {e}")
            return jsonify({"error": str(e)}), 500


@bp.route('/api/areas/<key>', methods=['PUT', 'PATCH', 'DELETE'])
def handle_area(key):
    """Update or delete a single area."""
    if request.method in ['PUT', 'PATCH']:
        try:
            data = request.json
            with main_app.get_db() as conn:
                current = conn.execute('SELECT * FROM areas WHERE key = ?', (key,)).fetchone()
                if current:
                    main_app.log_action_for_undo(conn, 'UPDATE', 'areas', key, dict(current))

                updates = []
                values = []
                if 'text' in data:
                    updates.append('text = ?')
                    values.append(data['text'])
                if 'order_index' in data:
                    current_area = conn.execute('SELECT order_index FROM areas WHERE key = ?', (key,)).fetchone()
                    new_index = data['order_index']

                    if current_area and current_area['order_index'] != new_index:
                        if new_index > current_area['order_index']:
                            conn.execute(
                                'UPDATE areas SET order_index = order_index - 1 WHERE order_index > ? AND order_index <= ?',
                                (current_area['order_index'], new_index)
                            )
                        else:
                            conn.execute(
                                'UPDATE areas SET order_index = order_index + 1 WHERE order_index >= ? AND order_index < ?',
                                (new_index, current_area['order_index'])
                            )
                        updates.append('order_index = ?')
                        values.append(new_index)

                if updates:
                    values.append(key)
                    query = f'UPDATE areas SET {", ".join(updates)} WHERE key = ?'
                    conn.execute(query, values)
                    conn.commit()
                return jsonify({'status': 'success'})
        except Exception as e:
            logging.error(f"Error updating area: {e}")
            return jsonify({"error": str(e)}), 500

    if request.method == 'DELETE':
        try:
            with main_app.get_db() as conn:
                area = conn.execute('SELECT * FROM areas WHERE key = ?', (key,)).fetchone()

                objectives = conn.execute('SELECT * FROM objectives WHERE area_key = ?', (key,)).fetchall()
                for obj in objectives:
                    tasks = conn.execute('SELECT * FROM tasks WHERE objective_key = ?', (obj['key'],)).fetchall()
                    for task in tasks:
                        main_app.log_action_for_undo(conn, 'DELETE', 'tasks', task['key'], dict(task))
                    main_app.log_action_for_undo(conn, 'DELETE', 'objectives', obj['key'], dict(obj))

                area_tasks = conn.execute('SELECT * FROM tasks WHERE area_key = ?', (key,)).fetchall()
                for task in area_tasks:
                    main_app.log_action_for_undo(conn, 'DELETE', 'tasks', task['key'], dict(task))

                if area:
                    main_app.log_action_for_undo(conn, 'DELETE', 'areas', key, dict(area))

                conn.execute('DELETE FROM areas WHERE key = ?', (key,))
                conn.commit()
                return jsonify({'status': 'success'})
        except Exception as e:
            logging.error(f"Error deleting area: {e}")
            return jsonify({"error": str(e)}), 500
