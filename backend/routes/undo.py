"""Undo API route."""
import json
import logging
from flask import Blueprint, jsonify, current_app

bp = Blueprint('undo', __name__)

@bp.route('/api/undo', methods=['POST'])
def undo_last_action():
    """Undo the most recent logged action."""
    app_module = current_app
    try:
        with app_module.get_db() as conn:
            last_action = conn.execute(
                'SELECT * FROM undo_log ORDER BY id DESC LIMIT 1'
            ).fetchone()
            if not last_action:
                return jsonify({"error": "No actions to undo"}), 404
            action_data = dict(last_action)
            old_data = json.loads(action_data['old_data'])
            if 'text' in old_data:
                old_data['text'] = old_data['text'].strip()
            if action_data['action_type'] == 'DELETE':
                if action_data['table_name'] == 'areas':
                    conn.execute(
                        'UPDATE areas SET order_index = order_index + 1 WHERE order_index >= ?',
                        (old_data['order_index'],)
                    )
                    conn.execute(
                        'INSERT INTO areas (key, text, order_index, date_time_created) VALUES (?, ?, ?, ?)',
                        (old_data['key'], old_data['text'], old_data['order_index'], old_data['date_time_created'])
                    )
                elif action_data['table_name'] == 'objectives':
                    conn.execute(
                        'UPDATE objectives SET order_index = order_index + 1 WHERE area_key = ? AND order_index >= ?',
                        (old_data['area_key'], old_data['order_index'])
                    )
                    conn.execute(
                        'INSERT INTO objectives (key, area_key, text, order_index, date_time_created, date_time_completed, status) VALUES (?, ?, ?, ?, ?, ?, ?)',
                        (
                            old_data['key'], old_data['area_key'], old_data['text'],
                            old_data['order_index'], old_data['date_time_created'],
                            old_data['date_time_completed'], old_data['status']
                        )
                    )
                elif action_data['table_name'] == 'tasks':
                    parent_col = 'area_key' if old_data['area_key'] else 'objective_key'
                    parent_key = old_data['area_key'] or old_data['objective_key']
                    conn.execute(
                        f'UPDATE tasks SET order_index = order_index + 1 WHERE {parent_col} = ? AND order_index >= ?',
                        (parent_key, old_data['order_index'])
                    )
                    conn.execute(
                        'INSERT INTO tasks (key, area_key, objective_key, text, order_index, date_time_created, date_time_completed, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                        (
                            old_data['key'], old_data['area_key'], old_data['objective_key'],
                            old_data['text'], old_data['order_index'], old_data['date_time_created'],
                            old_data['date_time_completed'], old_data['status']
                        )
                    )
            elif action_data['action_type'] == 'UPDATE':
                if action_data['table_name'] == 'areas':
                    conn.execute(
                        'UPDATE areas SET text = ?, order_index = ? WHERE key = ?',
                        (old_data['text'], old_data['order_index'], old_data['key'])
                    )
                    if old_data['text'] == '':
                        related = conn.execute('SELECT 1 FROM objectives WHERE area_key = ? LIMIT 1', (old_data['key'],)).fetchone()
                        if not related:
                            conn.execute('DELETE FROM areas WHERE key = ?', (old_data['key'],))
                elif action_data['table_name'] == 'objectives':
                    conn.execute(
                        'UPDATE objectives SET text = ?, area_key = ?, order_index = ?, status = ?, date_time_completed = ? WHERE key = ?',
                        (
                            old_data['text'], old_data['area_key'], old_data['order_index'],
                            old_data['status'], old_data['date_time_completed'], old_data['key']
                        )
                    )
                    if old_data['text'] == '':
                        related = conn.execute('SELECT 1 FROM tasks WHERE objective_key = ? LIMIT 1', (old_data['key'],)).fetchone()
                        if not related:
                            conn.execute('DELETE FROM objectives WHERE key = ?', (old_data['key'],))
                elif action_data['table_name'] == 'tasks':
                    conn.execute(
                        'UPDATE tasks SET text = ?, area_key = ?, objective_key = ?, order_index = ?, status = ?, date_time_completed = ? WHERE key = ?',
                        (
                            old_data['text'], old_data['area_key'], old_data['objective_key'],
                            old_data['order_index'], old_data['status'], old_data['date_time_completed'],
                            old_data['key']
                        )
                    )
                    if old_data['text'] == '':
                        parent_col = 'area_key' if old_data['area_key'] else 'objective_key'
                        parent_key = old_data['area_key'] or old_data['objective_key']
                        app_module.shift_tasks_after_delete(conn, parent_col, parent_key, old_data['order_index'])
                        conn.execute('DELETE FROM tasks WHERE key = ?', (old_data['key'],))
            conn.execute('DELETE FROM undo_log WHERE id = ?', (action_data['id'],))
            conn.commit()
            return jsonify({'status': 'success'})
    except Exception as e:  # pragma: no cover - exercise in tests
        logging.error(f"Error during undo: {e}")
        return jsonify({"error": str(e)}), 500
