"""Task-related API routes."""
import logging
from flask import Blueprint, jsonify, request

bp = Blueprint('tasks', __name__)

@bp.route('/api/tasks', methods=['GET', 'POST'])
def handle_tasks():
    """List or create tasks."""
    from .. import app as app_module
    if request.method == 'GET':
        try:
            with app_module.get_db() as conn:
                tasks = conn.execute('''
                    SELECT t.*, o.status as parent_status
                    FROM tasks t
                    LEFT JOIN objectives o ON t.objective_key = o.key
                    ORDER BY t.order_index
                ''').fetchall()
                return jsonify([dict(task) for task in tasks])
        except Exception as e:  # pragma: no cover - exercise in tests
            logging.error(f"Error getting tasks: {e}")
            return jsonify({"error": str(e)}), 500

    if request.method == 'POST':
        try:
            data, error = app_module.parse_json(['key', 'text'])
            if error:
                return error
            with app_module.get_db() as conn:
                area_key = data.get('area_key') or None
                objective_key = data.get('objective_key') or None
                if (area_key is None) == (objective_key is None):
                    return jsonify({"error": "Exactly one of area_key or objective_key must be specified"}), 400
                parent_key = area_key or objective_key
                parent_type = 'area_key' if area_key else 'objective_key'
                max_order = conn.execute(
                    f'SELECT MAX(order_index) FROM tasks WHERE {parent_type} = ?',
                    (parent_key,)
                ).fetchone()[0]
                next_order = (max_order if max_order is not None else -1) + 1
                conn.execute(
                    '''INSERT INTO tasks (
                        key, area_key, objective_key, text,
                        date_time_created, status, date_time_completed, order_index
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                    (
                        data['key'],
                        area_key,
                        objective_key,
                        data['text'],
                        app_module.get_pacific_time(),
                        'open',
                        None,
                        next_order,
                    )
                )
                result = conn.execute('SELECT * FROM tasks WHERE key = ?', (data['key'],)).fetchone()
                conn.commit()
                return jsonify(dict(result))
        except Exception as e:  # pragma: no cover - exercise in tests
            logging.error(f"Error creating task: {e}")
            return jsonify({"error": str(e)}), 500


@bp.route('/api/tasks/<key>', methods=['PUT', 'PATCH', 'DELETE'])
def handle_task(key):
    """Update or delete a single task."""
    from .. import app as app_module
    if request.method == 'DELETE':
        try:
            with app_module.get_db() as conn:
                task = conn.execute('SELECT * FROM tasks WHERE key = ?', (key,)).fetchone()
                if not task:
                    return jsonify({"error": "Task not found"}), 404
                app_module.log_action_for_undo(conn, 'DELETE', 'tasks', key, dict(task))
                task_dict = dict(task)
                parent_key = task_dict['area_key'] if task_dict['area_key'] else task_dict['objective_key']
                parent_type = 'area_key' if task_dict['area_key'] else 'objective_key'
                conn.execute(
                    f'UPDATE tasks SET order_index = order_index - 1 WHERE {parent_type} = ? AND order_index > ?',
                    (parent_key, task_dict['order_index'])
                )
                conn.execute('DELETE FROM tasks WHERE key = ?', (key,))
                conn.commit()
                return jsonify({'status': 'success'})
        except Exception as e:  # pragma: no cover - exercise in tests
            logging.error(f"Error deleting task: {e}")
            return jsonify({"error": str(e)}), 500

    if request.method in ['PUT', 'PATCH']:
        try:
            data = request.json
            with app_module.get_db() as conn:
                current = conn.execute('SELECT * FROM tasks WHERE key = ?', (key,)).fetchone()
                if not current:
                    return jsonify({"error": f"Task {key} not found"}), 404
                current_dict = dict(current)
                app_module.log_action_for_undo(conn, 'UPDATE', 'tasks', key, current_dict)

                updates = []
                values = []
                if 'text' in data:
                    updates.append('text = ?')
                    values.append(data['text'])
                if 'status' in data:
                    updates.append('status = ?')
                    values.append(data['status'])
                    if data['status'] == 'complete':
                        updates.append('date_time_completed = ?')
                        values.append(app_module.get_pacific_time())
                    else:
                        updates.append('date_time_completed = ?')
                        values.append(None)

                new_area_key = data.get('area_key')
                new_objective_key = data.get('objective_key')
                new_order = data.get('order_index', current_dict['order_index'])

                if new_area_key is None and new_objective_key is None:
                    new_area_key = current_dict['area_key']
                    new_objective_key = current_dict['objective_key']
                else:
                    new_area_key = None if not new_area_key or new_area_key in ('', 'null') else new_area_key
                    new_objective_key = None if not new_objective_key or new_objective_key in ('', 'null') else new_objective_key
                    if new_area_key and new_objective_key:
                        return jsonify({"error": "Task cannot have both area and objective parent"}), 400
                    if not new_area_key and not new_objective_key:
                        return jsonify({"error": "Task must have either area or objective parent"}), 400

                if new_area_key:
                    area = conn.execute('SELECT key FROM areas WHERE key = ?', (new_area_key,)).fetchone()
                    if not area:
                        return jsonify({"error": f"Area {new_area_key} not found"}), 400
                if new_objective_key:
                    objective = conn.execute('SELECT key FROM objectives WHERE key = ?', (new_objective_key,)).fetchone()
                    if not objective:
                        return jsonify({"error": f"Objective {new_objective_key} not found"}), 400

                current_parent = current_dict['area_key'] if current_dict['area_key'] else current_dict['objective_key']
                new_parent = new_area_key if new_area_key else new_objective_key
                changing_parent = current_parent != new_parent

                if changing_parent:
                    if current_dict['area_key']:
                        conn.execute(
                            'UPDATE tasks SET order_index = order_index - 1 WHERE area_key = ? AND order_index > ?',
                            (current_dict['area_key'], current_dict['order_index'])
                        )
                    else:
                        conn.execute(
                            'UPDATE tasks SET order_index = order_index - 1 WHERE objective_key = ? AND order_index > ?',
                            (current_dict['objective_key'], current_dict['order_index'])
                        )
                    if new_area_key:
                        conn.execute(
                            'UPDATE tasks SET order_index = order_index + 1 WHERE area_key = ? AND order_index >= ?',
                            (new_area_key, new_order)
                        )
                    else:
                        conn.execute(
                            'UPDATE tasks SET order_index = order_index + 1 WHERE objective_key = ? AND order_index >= ?',
                            (new_objective_key, new_order)
                        )
                else:
                    current_order = current_dict['order_index']
                    if new_order > current_order:
                        if new_area_key:
                            conn.execute(
                                'UPDATE tasks SET order_index = order_index - 1 WHERE area_key = ? AND order_index > ? AND order_index <= ?',
                                (new_area_key, current_order, new_order)
                            )
                        else:
                            conn.execute(
                                'UPDATE tasks SET order_index = order_index - 1 WHERE objective_key = ? AND order_index > ? AND order_index <= ?',
                                (new_objective_key, current_order, new_order)
                            )
                    else:
                        if new_area_key:
                            conn.execute(
                                'UPDATE tasks SET order_index = order_index + 1 WHERE area_key = ? AND order_index >= ? AND order_index < ?',
                                (new_area_key, new_order, current_order)
                            )
                        else:
                            conn.execute(
                                'UPDATE tasks SET order_index = order_index + 1 WHERE objective_key = ? AND order_index >= ? AND order_index < ?',
                                (new_objective_key, new_order, current_order)
                            )
                updated_task = {
                    **current_dict,
                    'area_key': new_area_key,
                    'objective_key': new_objective_key,
                    'order_index': new_order,
                }

                updates.extend(['area_key = ?', 'objective_key = ?', 'order_index = ?'])
                values.extend([new_area_key, new_objective_key, new_order])
                values.append(key)
                query = f'UPDATE tasks SET {", ".join(updates)} WHERE key = ?'
                conn.execute(query, values)
                conn.commit()
                return jsonify(updated_task)
        except Exception as e:  # pragma: no cover - exercise in tests
            logging.error(f"Error updating task: {e}")
            return jsonify({"error": str(e)}), 500
