import sqlite3
import tempfile
import unittest
from pathlib import Path
from server import initialize, connect, read_summary, add_contact

class BackendTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/'demo.sqlite3'
        initialize(self.path)
        self.conn=connect(self.path)
    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()
    def test_seed_and_staff_totals(self):
        self.assertEqual(self.conn.execute('PRAGMA foreign_key_check').fetchall(),[])
        self.assertEqual(read_summary(self.conn)['received'],79950)
        self.assertEqual(read_summary(self.conn,staff='James Carter')['received'],37250)
        self.assertEqual(read_summary(self.conn)['unique_donors'],15)
    def test_admin_dates_and_all_time(self):
        self.conn.execute("UPDATE goals SET start='2026-05-01',end='2026-05-01' WHERE period='2026-2027'")
        self.conn.commit()
        self.assertEqual(read_summary(self.conn,'2026-2027')['received'],15000)
        self.assertEqual(read_summary(self.conn,'all')['received'],79950)
        self.conn.execute("UPDATE goals SET start='2027-01-01',end='2027-12-31' WHERE period='2026-2027'")
        self.conn.commit()
        self.assertEqual(read_summary(self.conn,'2026-2027')['received'],0)
    def test_contact_and_audit_transaction(self):
        payload={'alumnus_id':1,'date':'2026-10-18','type':'Phone','outcome':'Connected','logged_by':'James Carter','notes':'Fictional test'}
        result=add_contact(self.conn,payload)
        self.assertTrue(result['audit_logged'])
        before=self.conn.execute('SELECT COUNT(*) FROM contacts').fetchone()[0]
        with self.assertRaises(sqlite3.IntegrityError):
            add_contact(self.conn,{**payload,'alumnus_id':99999})
        self.assertEqual(self.conn.execute('SELECT COUNT(*) FROM contacts').fetchone()[0],before)
        self.assertEqual(self.conn.execute('SELECT COUNT(*) FROM audit_log').fetchone()[0],1)
        with self.assertRaises(ValueError):
            add_contact(self.conn,{**payload,'date':'invalid'})

if __name__=='__main__':
    unittest.main()
