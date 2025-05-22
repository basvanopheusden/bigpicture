import os
import sqlite3
import tempfile
import unittest

import backend.app as app

class APITestCase(unittest.TestCase):
    def setUp(self):
        # create a temporary database file
        self.db_fd, self.db_path = tempfile.mkstemp()
        # create areas table required for the tests
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE areas (
                key TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                date_time_created TEXT NOT NULL,
                order_index INTEGER NOT NULL DEFAULT 0
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

if __name__ == '__main__':
    unittest.main()
