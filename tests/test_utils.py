import unittest
import sqlite3
from flask import Flask

import backend.utils as utils

class ParseJsonTestCase(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)

    def test_invalid_json(self):
        with self.app.test_request_context('/api', data='{', content_type='application/json'):
            data, error = utils.parse_json(['key'])
            self.assertIsNone(data)
            resp, status = error
            self.assertEqual(status, 400)
            self.assertIn('Invalid JSON', resp.get_json()['error'])

    def test_valid_json(self):
        with self.app.test_request_context('/api', json={'key': 'val'}):
            data, error = utils.parse_json(['key'])
            self.assertEqual(data, {'key': 'val'})
            self.assertIsNone(error)

class ShiftOrderTestCase(unittest.TestCase):
    def test_shift_after_delete(self):
        conn = sqlite3.connect(':memory:')
        conn.execute('CREATE TABLE tasks (key TEXT, area_key TEXT, objective_key TEXT, order_index INTEGER)')
        tasks = [
            ('t1', 'a1', None, 0),
            ('t2', 'a1', None, 1),
            ('t3', 'a1', None, 2)
        ]
        conn.executemany('INSERT INTO tasks VALUES (?, ?, ?, ?)', tasks)
        utils.shift_tasks_after_delete(conn, 'area_key', 'a1', 0)
        conn.execute('DELETE FROM tasks WHERE key = ?', ('t1',))
        rows = conn.execute('SELECT key, order_index FROM tasks ORDER BY order_index').fetchall()
        self.assertEqual([(r[0], r[1]) for r in rows], [('t2', 0), ('t3', 1)])
        conn.close()

if __name__ == '__main__':
    unittest.main()
