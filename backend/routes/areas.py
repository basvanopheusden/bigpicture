"""Area-related API routes."""
import logging
from flask import Blueprint, jsonify, request

bp = Blueprint('areas', __name__)

@bp.route('/api/areas', methods=['GET', 'POST'])
def handle_areas():
    """List or create areas."""
    from .. import app as app_module
    if request.method == 'GET':
        try:
            with app_module.get_db() as conn:
                areas = conn.execute('SELECT * FROM areas').fetchall()
                return jsonify([dict(area) for area in areas])
        except Exception as e:  # pragma: no cover - exercise in tests
            logging.error(f"Error getting areas: {e}")
            return jsonify({"error": str(e)}), 500

    if request.method == 'POST':
        try:
            data, error = app_module.parse_json(['key', 'text'])
            if error:
                return error

            with app_module.get_db() as conn:
                max_order = conn.execute('SELECT MAX(order_index) FROM areas').fetchone()[0]
                next_order = (max_order if max_order is not None else -1) + 1
                conn.execute(
                    'INSERT INTO areas (key, text, date_time_created, order_index) VALUES (?, ?, ?, ?)',
                    (data['key'], data['text'], app_module.get_pacific_time(), next_order)
                )
                conn.commit()
                return jsonify({'status': 'success'})
        except Exception as e:  # pragma: no cover - exercise in tests
            logging.error(f"Error creating area: {e}")
            return jsonify({"error": str(e)}), 500


@bp.route('/api/areas/<key>', methods=['PUT', 'PATCH', 'DELETE'])
def handle_area(key):
    """Update or delete a single area."""
    from .. import app as app_module
    if request.method in ['PUT', 'PATCH']:
        try:
            data = request.json
            with app_module.get_db() as conn:
                current = conn.execute('SELECT * FROM areas WHERE key = ?', (key,)).fetchone()
                if current:
                    app_module.log_action_for_undo(conn, 'UPDATE', 'areas', key, dict(current))

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
        except Exception as e:  # pragma: no cover - exercise in tests
            logging.error(f"Error updating area: {e}")
            return jsonify({"error": str(e)}), 500

    elif request.method == 'DELETE':
        try:
            with app_module.get_db() as conn:
                area = conn.execute('SELECT * FROM areas WHERE key = ?', (key,)).fetchone()
                objectives = conn.execute('SELECT * FROM objectives WHERE area_key = ?', (key,)).fetchall()
                for obj in objectives:
                    tasks = conn.execute('SELECT * FROM tasks WHERE objective_key = ?', (obj['key'],)).fetchall()
                    for task in tasks:
                        app_module.log_action_for_undo(conn, 'DELETE', 'tasks', task['key'], dict(task))
                    app_module.log_action_for_undo(conn, 'DELETE', 'objectives', obj['key'], dict(obj))
                area_tasks = conn.execute('SELECT * FROM tasks WHERE area_key = ?', (key,)).fetchall()
                for task in area_tasks:
                    app_module.log_action_for_undo(conn, 'DELETE', 'tasks', task['key'], dict(task))
                if area:
                    app_module.log_action_for_undo(conn, 'DELETE', 'areas', key, dict(area))
                conn.execute('DELETE FROM areas WHERE key = ?', (key,))
                conn.commit()
                return jsonify({'status': 'success'})
        except Exception as e:  # pragma: no cover - exercise in tests
            logging.error(f"Error deleting area: {e}")
            return jsonify({"error": str(e)}), 500
