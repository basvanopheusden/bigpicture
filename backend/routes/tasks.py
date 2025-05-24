"""Task related API routes."""

import logging
from flask import Blueprint, request, jsonify
import backend.app as main_app
from ..utils import parse_json, next_order_index, rows_to_dicts

bp = Blueprint('tasks', __name__)


@bp.route('/api/tasks', methods=['GET', 'POST'])
def handle_tasks():
    """Retrieve or create tasks."""
    if request.method == 'GET':
        try:
            with main_app.get_db() as conn:
                tasks = conn.execute(
                    '''SELECT t.*, o.status as parent_status FROM tasks t LEFT JOIN objectives o ON t.objective_key = o.key ORDER BY t.order_index'''
                ).fetchall()
                return jsonify(rows_to_dicts(tasks))
        except Exception as e:  # pragma: no cover
            logging.error(f"Error getting tasks: {e}")
            return jsonify({"error": str(e)}), 500

    if request.method == 'POST':
        try:
            data, error = parse_json(['key', 'text'])
            if error:
                return error

            with main_app.get_db() as conn:
                area_key = data.get('area_key') or None
                objective_key = data.get('objective_key') or None

                if (area_key is None) == (objective_key is None):
                    return jsonify({"error": "Exactly one of area_key or objective_key must be specified"}), 400

                if objective_key is not None:
                    objective = conn.execute('SELECT status FROM objectives WHERE key = ?', (objective_key,)).fetchone()
                    initial_status = 'complete' if objective and objective['status'] == 'complete' else 'open'
                    initial_completed = main_app.get_pacific_time() if initial_status == 'complete' else None
                else:
                    initial_status = 'open'
                    initial_completed = None

                parent_key = area_key or objective_key
                parent_type = 'area_key' if area_key else 'objective_key'
                next_order = next_order_index(conn, 'tasks', f'WHERE {parent_type} = ?', (parent_key,))

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
                        main_app.get_pacific_time(),
                        initial_status,
                        initial_completed,
                        next_order
                    )
                )
                result = conn.execute('SELECT * FROM tasks WHERE key = ?', (data['key'],)).fetchone()
                conn.commit()
                return jsonify(dict(result))
        except Exception as e:  # pragma: no cover
            logging.error(f"Error creating task: {e}")
            return jsonify({"error": str(e)}), 500


@bp.route('/api/tasks/<key>', methods=['PUT', 'PATCH', 'DELETE'])
def handle_task(key):
    """Update or delete a single task."""
    if request.method == 'DELETE':
        try:
            with main_app.get_db() as conn:
                task = conn.execute('SELECT * FROM tasks WHERE key = ?', (key,)).fetchone()
                if not task:
                    return jsonify({"error": "Task not found"}), 404
                main_app.log_action_for_undo(conn, 'DELETE', 'tasks', key, dict(task))

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
        except Exception as e:
            logging.error(f"Error deleting task: {e}")
            return jsonify({"error": str(e)}), 500

    if request.method in ['PUT', 'PATCH']:
        try:
            data = request.json
            with main_app.get_db() as conn:
                current = conn.execute('SELECT * FROM tasks WHERE key = ?', (key,)).fetchone()
                if not current:
                    return jsonify({"error": "Task not found"}), 404

                main_app.log_action_for_undo(conn, 'UPDATE', 'tasks', key, dict(current))

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
                        values.append(main_app.get_pacific_time())
                    else:
                        updates.append('date_time_completed = ?')
                        values.append(None)

                new_area_key = data.get('area_key', current['area_key'])
                new_objective_key = data.get('objective_key', current['objective_key'])
                new_order = data.get('order_index', current['order_index'])

                current_dict = dict(current)

                if new_area_key != current_dict['area_key'] or new_objective_key != current_dict['objective_key']:
                    parent_col = 'area_key' if current_dict['area_key'] else 'objective_key'
                    parent_key = current_dict['area_key'] or current_dict['objective_key']
                    conn.execute(
                        f'UPDATE tasks SET order_index = order_index - 1 WHERE {parent_col} = ? AND order_index > ?',
                        (parent_key, current_dict['order_index'])
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
                    'order_index': new_order
                }

                updates.extend(['area_key = ?', 'objective_key = ?', 'order_index = ?'])
                values.extend([new_area_key, new_objective_key, new_order])

                values.append(key)
                query = f'UPDATE tasks SET {", ".join(updates)} WHERE key = ?'
                conn.execute(query, values)

                conn.commit()
                return jsonify(updated_task)
        except Exception as e:
            logging.error(f"Error updating task: {e}")
            return jsonify({"error": str(e)}), 500
