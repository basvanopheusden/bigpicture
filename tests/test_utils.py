import sqlite3
import unittest

from backend.utils import next_order_index, rows_to_dicts


class UtilsTestCase(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.execute('CREATE TABLE t (id INTEGER PRIMARY KEY, order_index INTEGER)')

    def tearDown(self):
        self.conn.close()

    def test_next_order_index_empty(self):
        self.assertEqual(next_order_index(self.conn, 't'), 0)

    def test_next_order_index_existing(self):
        self.conn.execute('INSERT INTO t (order_index) VALUES (0), (1)')
        self.assertEqual(next_order_index(self.conn, 't'), 2)

    def test_rows_to_dicts(self):
        self.conn.row_factory = sqlite3.Row
        self.conn.execute('INSERT INTO t (order_index) VALUES (5)')
        rows = self.conn.execute('SELECT * FROM t').fetchall()
        result = rows_to_dicts(rows)
        self.assertEqual(result[0]['order_index'], 5)


if __name__ == '__main__':
    unittest.main()
