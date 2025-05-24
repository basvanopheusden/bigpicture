"""Objective-related API routes."""
import logging
from flask import Blueprint, jsonify, request

bp = Blueprint('objectives', __name__)

@bp.route('/api/objectives', methods=['GET', 'POST'])
def handle_objectives():
    """List or create objectives."""
    from .. import app as app_module
    if request.method == 'GET':
        try:
            with app_module.get_db() as conn:
                objectives = conn.execute('SELECT * FROM objectives ORDER BY order_index').fetchall()
                return jsonify([dict(objective) for objective in objectives])
        except Exception as e:  # pragma: no cover - exercise in tests
            logging.error(f"Error getting objectives: {e}")
            return jsonify({"error": str(e)}), 500

    if request.method == 'POST':
        try:
            data, error = app_module.parse_json(['key', 'area_key', 'text'])
            if error:
                return error

            with app_module.get_db() as conn:
                max_order = conn.execute(
                    'SELECT MAX(order_index) FROM objectives WHERE area_key = ?',
                    (data['area_key'],)
                ).fetchone()[0]
                next_order = (max_order if max_order is not None else -1) + 1
                conn.execute(
                    'INSERT INTO objectives (key, area_key, text, date_time_created, status, order_index) VALUES (?, ?, ?, ?, ?, ?)',
                    (data['key'], data['area_key'], data['text'], app_module.get_pacific_time(), 'open', next_order)
                )
                conn.commit()
                return jsonify({'status': 'success'})
        except Exception as e:  # pragma: no cover - exercise in tests
            logging.error(f"Error creating objective: {e}")
            return jsonify({"error": str(e)}), 500


@bp.route('/api/objectives/<key>', methods=['PUT', 'PATCH', 'DELETE'])
def handle_objective(key):
    """Update or delete a single objective."""
    from .. import app as app_module
    if request.method in ['PUT', 'PATCH']:
        try:
            data = request.json
            with app_module.get_db() as conn:
                current = conn.execute('SELECT * FROM objectives WHERE key = ?', (key,)).fetchone()
                if current:
                    app_module.log_action_for_undo(conn, 'UPDATE', 'objectives', key, dict(current))

                updates = []
                values = []
                if 'text' in data:
                    updates.append('text = ?')
                    values.append(data['text'])

                if 'order_index' in data or 'area_key' in data:
                    current_area = current['area_key']
                    new_area = data.get('area_key', current_area)
                    new_index = data.get('order_index', current['order_index'])
                    if new_area != current_area:
                        conn.execute(
                            'UPDATE objectives SET order_index = order_index - 1 WHERE area_key = ? AND order_index > ?',
                            (current_area, current['order_index'])
                        )
                        conn.execute(
                            'UPDATE objectives SET order_index = order_index + 1 WHERE area_key = ? AND order_index >= ?',
                            (new_area, new_index)
                        )
                        updates.extend(['area_key = ?', 'order_index = ?'])
                        values.extend([new_area, new_index])
                    elif new_index != current['order_index']:
                        if new_index > current['order_index']:
                            conn.execute(
                                'UPDATE objectives SET order_index = order_index - 1 WHERE area_key = ? AND order_index > ? AND order_index <= ?',
                                (current_area, current['order_index'], new_index)
                            )
                        else:
                            conn.execute(
                                'UPDATE objectives SET order_index = order_index + 1 WHERE area_key = ? AND order_index >= ? AND order_index < ?',
                                (current_area, new_index, current['order_index'])
                            )
                        updates.append('order_index = ?')
                        values.append(new_index)

                if 'status' in data:
                    updates.append('status = ?')
                    values.append(data['status'])
                    if data['status'] == 'complete':
                        updates.append('date_time_completed = ?')
                        values.append(app_module.get_pacific_time())
                    else:
                        updates.append('date_time_completed = ?')
                        values.append(None)

                if updates:
                    values.append(key)
                    query = f'UPDATE objectives SET {", ".join(updates)} WHERE key = ?'
                    conn.execute(query, values)
                    conn.commit()
                    updated = conn.execute('SELECT * FROM objectives WHERE key = ?', (key,)).fetchone()
                    return jsonify(dict(updated))
                return jsonify({"error": "No updates provided"}), 400
        except Exception as e:  # pragma: no cover - exercise in tests
            logging.error(f"Error patching objective: {e}")
            return jsonify({"error": str(e)}), 500

    elif request.method == 'DELETE':
        try:
            with app_module.get_db() as conn:
                objective = conn.execute('SELECT * FROM objectives WHERE key = ?', (key,)).fetchone()
                if objective:
                    tasks = conn.execute('SELECT * FROM tasks WHERE objective_key = ?', (key,)).fetchall()
                    for task in tasks:
                        app_module.log_action_for_undo(conn, 'DELETE', 'tasks', task['key'], dict(task))
                    app_module.log_action_for_undo(conn, 'DELETE', 'objectives', key, dict(objective))
                conn.execute('DELETE FROM objectives WHERE key = ?', (key,))
                conn.commit()
                return jsonify({'status': 'success'})
        except Exception as e:  # pragma: no cover - exercise in tests
            logging.error(f"Error deleting objective: {e}")
            return jsonify({"error": str(e)}), 500
