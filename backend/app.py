import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

from .database import (
    get_db,
    init_db,
    log_action_for_undo,
    get_pacific_time,
)
from .utils import parse_json

app = Flask(__name__)

app.config['CORS_HEADERS'] = 'Content-Type'
CORS(app,
     resources={r"/api/*": {
         "origins": [
             "http://localhost:5173",
             "https://bigpicture-frontend-ancient-night-2172.fly.dev",
             "https://foo.boulos.ca"
         ],
         "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
         "allow_headers": ["Content-Type"],
         "supports_credentials": True,
         "expose_headers": ["Access-Control-Allow-Origin"]
     }},
    supports_credentials=True)

with app.app_context():
    init_db()


@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    if origin in [
        "http://localhost:5173",
        "https://bigpicture-frontend-ancient-night-2172.fly.dev"
    ]:
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, PATCH, OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({"status": "ok", "message": "API is working"})

@app.route('/api/areas', methods=['GET', 'POST'])
def handle_areas():
    if request.method == 'GET':
        try:
            with get_db() as conn:
                areas = conn.execute('SELECT * FROM areas').fetchall()
                result = [dict(area) for area in areas]
                return jsonify(result)
        except Exception as e:
            print(f"Error getting areas: {e}")
            return jsonify({"error": str(e)}), 500
    
    if request.method == 'POST':
        try:
            data, error = parse_json(['key', 'text'])
            if error:
                return error
            
            with get_db() as conn:
                # Get max order_index
                max_order = conn.execute('SELECT MAX(order_index) FROM areas').fetchone()[0]
                next_order = (max_order or -1) + 1
                
                conn.execute(
                    'INSERT INTO areas (key, text, date_time_created, order_index) VALUES (?, ?, ?, ?)',
                    (data['key'], data['text'], get_pacific_time(), next_order)
                )
                conn.commit()
                return jsonify({'status': 'success'})
        except Exception as e:
            print(f"Error creating area: {e}")
            return jsonify({"error": str(e)}), 500

@app.route('/api/areas/<key>', methods=['PUT', 'PATCH', 'DELETE'])
def handle_area(key):
    if request.method in ['PUT', 'PATCH']:
        try:
            data = request.json
            with get_db() as conn:
                # Get current state for undo
                current = conn.execute('SELECT * FROM areas WHERE key = ?', (key,)).fetchone()
                if current:
                    log_action_for_undo(conn, 'UPDATE', 'areas', key, dict(current))

                updates = []
                values = []
                if 'text' in data:
                    updates.append('text = ?')
                    values.append(data['text'])
                if 'order_index' in data:
                    # Get current area's order index
                    current_area = conn.execute('SELECT order_index FROM areas WHERE key = ?', (key,)).fetchone()
                    new_index = data['order_index']
                    
                    # Shift other areas to make space
                    if current_area and current_area['order_index'] != new_index:
                        if new_index > current_area['order_index']:
                            conn.execute('''
                                UPDATE areas 
                                SET order_index = order_index - 1
                                WHERE order_index > ? AND order_index <= ?
                            ''', (current_area['order_index'], new_index))
                        else:
                            conn.execute('''
                                UPDATE areas 
                                SET order_index = order_index + 1
                                WHERE order_index >= ? AND order_index < ?
                            ''', (new_index, current_area['order_index']))
                        
                        updates.append('order_index = ?')
                        values.append(new_index)
                
                if updates:
                    values.append(key)
                    query = f'UPDATE areas SET {", ".join(updates)} WHERE key = ?'
                    conn.execute(query, values)
                    conn.commit()
                return jsonify({'status': 'success'})
        except Exception as e:
            print(f"Error updating area: {e}")
            return jsonify({"error": str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            with get_db() as conn:
                # Log current state of area and its children for undo
                area = conn.execute('SELECT * FROM areas WHERE key = ?', (key,)).fetchone()
                if area:
                    log_action_for_undo(conn, 'DELETE', 'areas', key, dict(area))
                    
                objectives = conn.execute('SELECT * FROM objectives WHERE area_key = ?', (key,)).fetchall()
                for obj in objectives:
                    log_action_for_undo(conn, 'DELETE', 'objectives', obj['key'], dict(obj))
                    tasks = conn.execute('SELECT * FROM tasks WHERE objective_key = ?', (obj['key'],)).fetchall()
                    for task in tasks:
                        log_action_for_undo(conn, 'DELETE', 'tasks', task['key'], dict(task))

                area_tasks = conn.execute('SELECT * FROM tasks WHERE area_key = ?', (key,)).fetchall()
                for task in area_tasks:
                    log_action_for_undo(conn, 'DELETE', 'tasks', task['key'], dict(task))

                conn.execute('DELETE FROM areas WHERE key = ?', (key,))
                conn.commit()
                return jsonify({'status': 'success'})
        except Exception as e:
            print(f"Error deleting area: {e}")
            return jsonify({"error": str(e)}), 500

@app.route('/api/objectives', methods=['GET', 'POST'])
def handle_objectives():
    if request.method == 'GET':
        try:
            with get_db() as conn:
                objectives = conn.execute('SELECT * FROM objectives ORDER BY order_index').fetchall()
                result = [dict(objective) for objective in objectives]
                return jsonify(result)
        except Exception as e:
            print(f"Error getting objectives: {e}")
            return jsonify({"error": str(e)}), 500
    
    if request.method == 'POST':
        try:
            data, error = parse_json(['key', 'area_key', 'text'])
            if error:
                return error
            
            with get_db() as conn:
                # Get max order_index for this area
                max_order = conn.execute(
                    'SELECT MAX(order_index) FROM objectives WHERE area_key = ?',
                    (data['area_key'],)
                ).fetchone()[0]
                next_order = (max_order or -1) + 1
                
                conn.execute(
                    'INSERT INTO objectives (key, area_key, text, date_time_created, status, order_index) VALUES (?, ?, ?, ?, ?, ?)',
                    (data['key'], data['area_key'], data['text'], get_pacific_time(), 'open', next_order)
                )
                conn.commit()
                return jsonify({'status': 'success'})
        except Exception as e:
            print(f"Error creating objective: {e}")
            return jsonify({"error": str(e)}), 500

@app.route('/api/objectives/<key>', methods=['PUT', 'PATCH', 'DELETE'])
def handle_objective(key):
    if request.method in ['PUT', 'PATCH']:
        try:
            data = request.json
            with get_db() as conn:
                # Get current state for undo
                current = conn.execute('SELECT * FROM objectives WHERE key = ?', (key,)).fetchone()
                if current:
                    log_action_for_undo(conn, 'UPDATE', 'objectives', key, dict(current))

                updates = []
                values = []
                if 'text' in data:
                    updates.append('text = ?')
                    values.append(data['text'])
                
                # Handle reordering and area changes together
                if 'order_index' in data or 'area_key' in data:
                    current_area = current['area_key']
                    new_area = data.get('area_key', current_area)
                    new_index = data.get('order_index', current['order_index'])
                    
                    # If moving to new area
                    if new_area != current_area:
                        # Shift down items in old area
                        conn.execute('''
                            UPDATE objectives 
                            SET order_index = order_index - 1
                            WHERE area_key = ? AND order_index > ?
                        ''', (current_area, current['order_index']))
                        
                        # Shift up items in new area
                        conn.execute('''
                            UPDATE objectives 
                            SET order_index = order_index + 1
                            WHERE area_key = ? AND order_index >= ?
                        ''', (new_area, new_index))
                        
                        updates.extend(['area_key = ?', 'order_index = ?'])
                        values.extend([new_area, new_index])
                    
                    # If just reordering within same area
                    elif new_index != current['order_index']:
                        if new_index > current['order_index']:
                            conn.execute('''
                                UPDATE objectives 
                                SET order_index = order_index - 1
                                WHERE area_key = ? 
                                AND order_index > ? 
                                AND order_index <= ?
                            ''', (current_area, current['order_index'], new_index))
                        else:
                            conn.execute('''
                                UPDATE objectives 
                                SET order_index = order_index + 1
                                WHERE area_key = ? 
                                AND order_index >= ? 
                                AND order_index < ?
                            ''', (current_area, new_index, current['order_index']))
                        
                        updates.append('order_index = ?')
                        values.append(new_index)
                if 'status' in data:
                    updates.append('status = ?')
                    values.append(data['status'])
                    if data['status'] == 'complete':
                        updates.append('date_time_completed = ?')
                        values.append(get_pacific_time())
                        
                        # Also complete all child tasks
                        conn.execute('''
                            UPDATE tasks 
                            SET status = 'complete', 
                                date_time_completed = ? 
                            WHERE objective_key = ? AND status != 'complete'
                        ''', (get_pacific_time(), key))
                    else:
                        updates.append('date_time_completed = ?')
                        values.append(None)
                
                # Execute the main update
                if updates:
                    values.append(key)
                    query = f'UPDATE objectives SET {", ".join(updates)} WHERE key = ?'
                    conn.execute(query, values)
                    conn.commit()
                    
                    # Return the updated objective with all fields
                    updated = conn.execute(
                        'SELECT * FROM objectives WHERE key = ?',
                        (key,)
                    ).fetchone()
                    return jsonify(dict(updated))
                return jsonify({"error": "No updates provided"}), 400
        except Exception as e:
            print(f"Error patching objective: {e}")
            return jsonify({"error": str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            with get_db() as conn:
                # Log current state for undo
                objective = conn.execute('SELECT * FROM objectives WHERE key = ?', (key,)).fetchone()
                if objective:
                    log_action_for_undo(conn, 'DELETE', 'objectives', key, dict(objective))
                    # Log child tasks
                    tasks = conn.execute('SELECT * FROM tasks WHERE objective_key = ?', (key,)).fetchall()
                    for task in tasks:
                        log_action_for_undo(conn, 'DELETE', 'tasks', task['key'], dict(task))

                conn.execute('DELETE FROM objectives WHERE key = ?', (key,))
                conn.commit()
                return jsonify({'status': 'success'})
        except Exception as e:
            print(f"Error deleting objective: {e}")
            return jsonify({"error": str(e)}), 500
@app.route('/api/tasks', methods=['GET', 'POST'])
def handle_tasks():
    if request.method == 'GET':
        try:
            with get_db() as conn:
                tasks = conn.execute('''
                    SELECT t.*, o.status as parent_status
                    FROM tasks t 
                    LEFT JOIN objectives o ON t.objective_key = o.key
                    ORDER BY t.order_index
                ''').fetchall()
                result = [dict(task) for task in tasks]
                return jsonify(result)
        except Exception as e:
            print(f"Error getting tasks:", e)
            return jsonify({"error": str(e)}), 500
    
    if request.method == 'POST':
        try:
            data, error = parse_json(['key', 'text'])
            if error:
                return error
            
            with get_db() as conn:
                # Validate parent references
                area_key = data.get('area_key')
                objective_key = data.get('objective_key')
                
                # Convert empty strings and null to None
                if not area_key or area_key == '':
                    area_key = None
                if not objective_key or objective_key == '':
                    objective_key = None
                
                # Check that exactly one parent is specified
                if (area_key is None) == (objective_key is None):  # XNOR check
                    return jsonify({"error": "Exactly one of area_key or objective_key must be specified"}), 400

                # If parent is objective, check if objective is complete
                if objective_key is not None:
                    objective = conn.execute(
                        'SELECT status FROM objectives WHERE key = ?', 
                        (objective_key,)
                    ).fetchone()
                    initial_status = 'complete' if objective and objective['status'] == 'complete' else 'open'
                    initial_completed = get_pacific_time() if initial_status == 'complete' else None
                else:
                    initial_status = 'open'
                    initial_completed = None

                # Get max order_index for the parent (area or objective)
                parent_key = data.get('area_key') or data.get('objective_key')
                parent_type = 'area_key' if data.get('area_key') else 'objective_key'
                max_order = conn.execute(
                    f'SELECT MAX(order_index) FROM tasks WHERE {parent_type} = ?',
                    (parent_key,)
                ).fetchone()[0]
                next_order = (max_order or -1) + 1
                
                conn.execute(
                    '''INSERT INTO tasks (
                        key, area_key, objective_key, text,
                        date_time_created, status, date_time_completed, order_index
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                    (data['key'], 
                     data.get('area_key'), 
                     data.get('objective_key'), 
                     data['text'],
                     get_pacific_time(),
                     initial_status,
                     initial_completed,
                     next_order)
                )
                result = conn.execute('SELECT * FROM tasks WHERE key = ?', (data['key'],)).fetchone()
                conn.commit()
                return jsonify(dict(result))
        except Exception as e:
            print(f"Error creating task:", e)
            return jsonify({"error": str(e)}), 500

@app.route('/api/tasks/<key>', methods=['PUT', 'PATCH', 'DELETE'])
def handle_task(key):
    if request.method == 'DELETE':
        try:
            with get_db() as conn:
                task = conn.execute('SELECT * FROM tasks WHERE key = ?', (key,)).fetchone()
                if not task:
                    return jsonify({"error": "Task not found"}), 404
                
                # Log for undo
                log_action_for_undo(conn, 'DELETE', 'tasks', key, dict(task))
                
                # Update order indices for remaining tasks
                task_dict = dict(task)
                parent_key = task_dict['area_key'] if task_dict['area_key'] else task_dict['objective_key']
                parent_type = 'area_key' if task_dict['area_key'] else 'objective_key'
                
                conn.execute(f'''
                    UPDATE tasks 
                    SET order_index = order_index - 1
                    WHERE {parent_type} = ? 
                    AND order_index > ?
                ''', (parent_key, task_dict['order_index']))
                
                # Delete the task
                conn.execute('DELETE FROM tasks WHERE key = ?', (key,))
                conn.commit()
                return jsonify({'status': 'success'})
        except Exception as e:
            print(f"Error deleting task: {e}")
            return jsonify({"error": str(e)}), 500

    if request.method in ['PUT', 'PATCH']:
        try:
            data = request.json
            with get_db() as conn:
                # Get current state
                current = conn.execute('SELECT * FROM tasks WHERE key = ?', (key,)).fetchone()
                if not current:
                    return jsonify({"error": f"Task {key} not found"}), 404
                
                current_dict = dict(current)
                
                # Log current state for undo
                log_action_for_undo(conn, 'UPDATE', 'tasks', key, current_dict)
                
                # Handle basic updates (text and status)
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
                        values.append(get_pacific_time())
                    else:
                        updates.append('date_time_completed = ?')
                        values.append(None)
                
                # Handle parent and order changes
                new_area_key = data.get('area_key')
                new_objective_key = data.get('objective_key')
                new_order = data.get('order_index')

                # Keep existing order if not specified
                if new_order is None:
                    new_order = current_dict['order_index']

                # If neither parent is specified in the update, keep existing parents
                if new_area_key is None and new_objective_key is None:
                    new_area_key = current_dict['area_key']
                    new_objective_key = current_dict['objective_key']
                else:
                    # Normalize parent keys
                    new_area_key = None if not new_area_key or new_area_key in ('', 'null') else new_area_key
                    new_objective_key = None if not new_objective_key or new_objective_key in ('', 'null') else new_objective_key
                    
                    # Validate parent references
                    if new_area_key and new_objective_key:
                        return jsonify({"error": "Task cannot have both area and objective parent"}), 400
                    if not new_area_key and not new_objective_key:
                        return jsonify({"error": "Task must have either area or objective parent"}), 400
                
                # Verify parent exists
                if new_area_key:
                    area = conn.execute('SELECT key FROM areas WHERE key = ?', (new_area_key,)).fetchone()
                    if not area:
                        return jsonify({"error": f"Area {new_area_key} not found"}), 400
                if new_objective_key:
                    objective = conn.execute('SELECT key FROM objectives WHERE key = ?', (new_objective_key,)).fetchone()
                    if not objective:
                        return jsonify({"error": f"Objective {new_objective_key} not found"}), 400
                
                # Determine if we're changing parents
                current_parent = current_dict['area_key'] if current_dict['area_key'] else current_dict['objective_key']
                new_parent = new_area_key if new_area_key else new_objective_key
                changing_parent = current_parent != new_parent
                
                # Handle reordering
                if changing_parent:
                    # When moving to a new parent, first shift down tasks in the old parent
                    if current_dict['area_key']:
                        conn.execute('''
                            UPDATE tasks 
                            SET order_index = order_index - 1
                            WHERE area_key = ? AND order_index > ?
                        ''', (current_dict['area_key'], current_dict['order_index']))
                    else:
                        conn.execute('''
                            UPDATE tasks 
                            SET order_index = order_index - 1
                            WHERE objective_key = ? AND order_index > ?
                        ''', (current_dict['objective_key'], current_dict['order_index']))

                    # Then shift up tasks in the new parent to make space
                    if new_area_key:
                        conn.execute('''
                            UPDATE tasks 
                            SET order_index = order_index + 1
                            WHERE area_key = ? AND order_index >= ?
                        ''', (new_area_key, new_order))
                    else:
                        conn.execute('''
                            UPDATE tasks 
                            SET order_index = order_index + 1
                            WHERE objective_key = ? AND order_index >= ?
                        ''', (new_objective_key, new_order))
                else:
                    # Reordering within the same parent
                    current_order = current_dict['order_index']
                    if new_order > current_order:
                        # Moving down: shift tasks up
                        if new_area_key:
                            conn.execute('''
                                UPDATE tasks 
                                SET order_index = order_index - 1
                                WHERE area_key = ? 
                                AND order_index > ? 
                                AND order_index <= ?
                            ''', (new_area_key, current_order, new_order))
                        else:
                            conn.execute('''
                                UPDATE tasks 
                                SET order_index = order_index - 1
                                WHERE objective_key = ? 
                                AND order_index > ? 
                                AND order_index <= ?
                            ''', (new_objective_key, current_order, new_order))
                    else:
                        # Moving up: shift tasks down
                        if new_area_key:
                            conn.execute('''
                                UPDATE tasks 
                                SET order_index = order_index + 1
                                WHERE area_key = ? 
                                AND order_index >= ? 
                                AND order_index < ?
                            ''', (new_area_key, new_order, current_order))
                        else:
                            conn.execute('''
                                UPDATE tasks 
                                SET order_index = order_index + 1
                                WHERE objective_key = ? 
                                AND order_index >= ? 
                                AND order_index < ?
                            ''', (new_objective_key, new_order, current_order))
                
                # Create updated task with new parent and order
                updated_task = {
                    **current_dict,
                    'area_key': new_area_key,
                    'objective_key': new_objective_key,
                    'order_index': new_order
                }
                
                # Update the task with new parent and order
                updates.extend(['area_key = ?', 'objective_key = ?', 'order_index = ?'])
                values.extend([new_area_key, new_objective_key, new_order])
                
                # Execute update
                values.append(key)
                query = f'UPDATE tasks SET {", ".join(updates)} WHERE key = ?'
                conn.execute(query, values)
                
                # Return updated task
                conn.commit()
                return jsonify(updated_task)
                
        except Exception as e:
            print(f"Error updating task: {e}")
            return jsonify({"error": str(e)}), 500

@app.route('/api/undo', methods=['POST'])
def undo_last_action():
    try:
        with get_db() as conn:
            # Get the last action from the undo log
            last_action = conn.execute('''
                SELECT * FROM undo_log 
                ORDER BY id DESC 
                LIMIT 1
            ''').fetchone()
            
            if not last_action:
                return jsonify({"error": "No actions to undo"}), 404

            action_data = dict(last_action)
            old_data = json.loads(action_data['old_data'])

            # Restore the data based on action type
            if action_data['action_type'] == 'DELETE':
                if action_data['table_name'] == 'areas':
                    conn.execute(
                        'INSERT INTO areas (key, text, order_index, date_time_created) VALUES (?, ?, ?, ?)',
                        (old_data['key'], old_data['text'], old_data['order_index'], old_data['date_time_created'])
                    )
                elif action_data['table_name'] == 'objectives':
                    conn.execute('''
                        INSERT INTO objectives (
                            key, area_key, text, order_index, date_time_created, 
                            date_time_completed, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        old_data['key'], old_data['area_key'], old_data['text'],
                        old_data['order_index'], old_data['date_time_created'],
                        old_data['date_time_completed'], old_data['status']
                    ))
                elif action_data['table_name'] == 'tasks':
                    conn.execute('''
                        INSERT INTO tasks (
                            key, area_key, objective_key, text, order_index,
                            date_time_created, date_time_completed, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        old_data['key'], old_data['area_key'], old_data['objective_key'],
                        old_data['text'], old_data['order_index'], old_data['date_time_created'],
                        old_data['date_time_completed'], old_data['status']
                    ))
            
            elif action_data['action_type'] == 'UPDATE':
                if action_data['table_name'] == 'areas':
                    conn.execute(
                        'UPDATE areas SET text = ?, order_index = ? WHERE key = ?',
                        (old_data['text'], old_data['order_index'], old_data['key'])
                    )
                elif action_data['table_name'] == 'objectives':
                    conn.execute('''
                        UPDATE objectives 
                        SET text = ?, area_key = ?, order_index = ?, 
                            status = ?, date_time_completed = ?
                        WHERE key = ?
                    ''', (
                        old_data['text'], old_data['area_key'], old_data['order_index'],
                        old_data['status'], old_data['date_time_completed'], old_data['key']
                    ))
                elif action_data['table_name'] == 'tasks':
                    conn.execute('''
                        UPDATE tasks 
                        SET text = ?, area_key = ?, objective_key = ?, 
                            order_index = ?, status = ?, date_time_completed = ?
                        WHERE key = ?
                    ''', (
                        old_data['text'], old_data['area_key'], old_data['objective_key'],
                        old_data['order_index'], old_data['status'], old_data['date_time_completed'],
                        old_data['key']
                    ))

            # Remove this action from the undo log
            conn.execute('DELETE FROM undo_log WHERE id = ?', (action_data['id'],))
            conn.commit()

            return jsonify({'status': 'success'})
    except Exception as e:
        print(f"Error during undo:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
