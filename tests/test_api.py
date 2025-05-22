import os
import sqlite3
import tempfile
import unittest

import backend.app as app

class APITestCase(unittest.TestCase):
    def setUp(self):
        # create a temporary database file
        self.db_fd, self.db_path = tempfile.mkstemp()
        # create tables required for the tests
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE areas (
                key TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                date_time_created TEXT NOT NULL,
                order_index INTEGER NOT NULL DEFAULT 0
            )
        ''')
        conn.execute('''
            CREATE TABLE objectives (
                key TEXT PRIMARY KEY,
                area_key TEXT NOT NULL,
                text TEXT NOT NULL,
                date_time_created TEXT NOT NULL,
                date_time_completed TEXT,
                status TEXT DEFAULT 'open' CHECK(status IN ('open', 'complete', 'secondary')),
                order_index INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (area_key) REFERENCES areas (key) ON DELETE CASCADE
            )
        ''')
        conn.execute('''
            CREATE TABLE tasks (
                key TEXT PRIMARY KEY,
                area_key TEXT,
                objective_key TEXT,
                text TEXT NOT NULL,
                date_time_created TEXT NOT NULL,
                date_time_completed TEXT,
                status TEXT DEFAULT 'open' CHECK(status IN ('open', 'complete', 'secondary')),
                order_index INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (area_key) REFERENCES areas (key) ON DELETE CASCADE,
                FOREIGN KEY (objective_key) REFERENCES objectives (key) ON DELETE CASCADE,
                CHECK ((area_key IS NOT NULL AND objective_key IS NULL) OR
                       (area_key IS NULL AND objective_key IS NOT NULL))
            )
        ''')
        conn.execute('''
            CREATE TABLE undo_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_type TEXT NOT NULL,
                table_name TEXT NOT NULL,
                record_key TEXT NOT NULL,
                old_data TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

        def get_test_db():
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        app.get_db = get_test_db

        # patch timestamp function for determinism
        self.original_get_pacific_time = app.get_pacific_time
        app.get_pacific_time = lambda: "2021-01-01T00:00:00"

        self.client = app.app.test_client()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)
        app.get_pacific_time = self.original_get_pacific_time

    def test_test_endpoint(self):
        resp = self.client.get('/api/test')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json(), {"status": "ok", "message": "API is working"})

    def test_create_and_get_area(self):
        resp = self.client.post('/api/areas', json={"key": "area1", "text": "Area 1"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json(), {"status": "success"})

        resp = self.client.get('/api/areas')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['key'], 'area1')
        self.assertEqual(data[0]['text'], 'Area 1')
        self.assertEqual(data[0]['order_index'], 0)

    def test_objectives_update_delete_and_undo(self):
        # create area and objectives
        self.client.post('/api/areas', json={"key": "area1", "text": "Area 1"})
        self.client.post('/api/objectives', json={"key": "obj1", "area_key": "area1", "text": "Obj 1"})
        self.client.post('/api/objectives', json={"key": "obj2", "area_key": "area1", "text": "Obj 2"})

        resp = self.client.get('/api/objectives')
        data = resp.get_json()
        self.assertEqual([o['key'] for o in data], ['obj1', 'obj2'])

        # reorder objective
        resp = self.client.patch('/api/objectives/obj1', json={"order_index": 1})
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get('/api/objectives')
        data = resp.get_json()
        self.assertEqual([(o['key'], o['order_index']) for o in data], [('obj2', 0), ('obj1', 1)])

        # delete and undo
        resp = self.client.delete('/api/objectives/obj1')
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get('/api/objectives')
        self.assertEqual([o['key'] for o in resp.get_json()], ['obj2'])

        resp = self.client.post('/api/undo')
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get('/api/objectives')
        self.assertEqual([o['key'] for o in resp.get_json()], ['obj2', 'obj1'])

    def test_tasks_update_delete_and_undo(self):
        # setup area, objective and tasks
        self.client.post('/api/areas', json={"key": "area1", "text": "Area 1"})
        self.client.post('/api/objectives', json={"key": "obj1", "area_key": "area1", "text": "Objective"})
        self.client.post('/api/tasks', json={"key": "task1", "text": "Task 1", "objective_key": "obj1"})
        self.client.post('/api/tasks', json={"key": "task2", "text": "Task 2", "objective_key": "obj1"})

        tasks = self.client.get('/api/tasks').get_json()
        obj_tasks = [t for t in tasks if t['objective_key'] == 'obj1']
        self.assertEqual([t['key'] for t in obj_tasks], ['task1', 'task2'])

        # reorder task
        resp = self.client.patch('/api/tasks/task1', json={"order_index": 1})
        self.assertEqual(resp.status_code, 200)
        tasks = self.client.get('/api/tasks').get_json()
        obj_tasks = sorted([t for t in tasks if t['objective_key'] == 'obj1'], key=lambda x: x['order_index'])
        self.assertEqual([(t['key'], t['order_index']) for t in obj_tasks], [('task2', 0), ('task1', 1)])

        # delete and undo
        resp = self.client.delete('/api/tasks/task1')
        self.assertEqual(resp.status_code, 200)
        tasks = self.client.get('/api/tasks').get_json()
        self.assertEqual([t['key'] for t in tasks if t['objective_key'] == 'obj1'], ['task2'])

        resp = self.client.post('/api/undo')
        self.assertEqual(resp.status_code, 200)
        tasks = self.client.get('/api/tasks').get_json()
        obj_tasks = sorted([t for t in tasks if t['objective_key'] == 'obj1'], key=lambda x: x['order_index'])
        self.assertEqual([t['key'] for t in obj_tasks], ['task2', 'task1'])

if __name__ == '__main__':
    unittest.main()
