"""Local-only fictional-data backend demo. Standard library; no dependencies."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from datetime import date
import json
import sqlite3
import argparse

ROOT = Path(__file__).resolve().parent

def connect(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    return conn

def initialize(path):
    conn = connect(path)
    conn.executescript((ROOT / 'schema.sql').read_text())
    if conn.execute('SELECT count(*) FROM staff').fetchone()[0]:
        conn.close()
        return
    db = json.loads((ROOT / 'seed.json').read_text())
    with conn:
        conn.executemany('INSERT INTO staff VALUES (?)', [(x,) for x in ['James Carter', 'Sarah Miller']])
        conn.executemany('INSERT INTO alumni VALUES (?,?,?,?,?,?,?,?,?,?,?)', [
            (x['id'], x['name'], x.get('year'), x.get('college'), x.get('email'), x.get('phone'),
             x.get('pref'), x.get('source'), x['origin'], x['owner'], x['added']) for x in db['alumni']])
        conn.executemany('INSERT INTO contacts(alumnus_id,date,type,outcome,logged_by,notes) VALUES (?,?,?,?,?,?)', [
            (x['alumnus'],x['date'],x['type'],x['outcome'],x['by'],x.get('notes','')) for x in db['contacts']])
        conn.executemany('INSERT INTO gifts(alumnus_id,kind,amount,date,credited_to,status,purpose,frequency) VALUES (?,?,?,?,?,?,?,?)', [
            (x['alumnus'],x['kind'],x['amount'],x['date'],x['by'],x.get('status'),x.get('purpose'),x.get('frequency')) for x in db['gifts']])
        conn.executemany('INSERT INTO followups(alumnus_id,action,due,assigned_to) VALUES (?,?,?,?)', [
            (x['alumnus'],x['action'],x['due'],x['by']) for x in db['tasks']])
        conn.executemany('INSERT INTO referrals(from_alumnus,to_alumnus,referred_name,assigned_to,status) VALUES (?,?,?,?,?)', [
            (x['from'],x.get('to'),x['name'],x['by'],x['status']) for x in db['refs']])
        conn.executemany('INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?)', [
            (x['id'],x['title'],x['type'],x['date'],x['time'],x['endTime'],x['location'],x['host'],x['status']) for x in db['events']])
        conn.executemany('INSERT INTO goals VALUES (?,?,?,?)', [(k,x['amount'],x['start'],x['end']) for k,x in db['goals'].items()])
    conn.close()

def read_summary(conn,period='all',staff=None):
    params=[]
    clause='1=1'
    bounds=None
    if period!='all':
        g=conn.execute('SELECT start,end FROM goals WHERE period=?',(period,)).fetchone()
        if not g:
            raise ValueError('Unknown goal period')
        bounds=dict(g)
        clause+=' AND date BETWEEN ? AND ?'
        params.extend([g['start'],g['end']])
    gift_clause=clause
    contact_clause=clause
    if staff:
        if not conn.execute('SELECT 1 FROM staff WHERE name=?',(staff,)).fetchone():
            raise ValueError('Unknown fundraiser')
        gift_clause+=' AND credited_to=?'
        contact_clause+=' AND logged_by=?'
        params.append(staff)
    payments=conn.execute(f"SELECT COALESCE(SUM(amount),0) received, COUNT(DISTINCT alumnus_id) donors FROM gifts WHERE kind='Payment' AND {gift_clause}",params).fetchone()
    requests=conn.execute(f"SELECT status,COUNT(*) n FROM gifts WHERE kind='Request' AND {gift_clause} GROUP BY status",params).fetchall()
    outcomes={x['status']:x['n'] for x in requests}
    decided=outcomes.get('Accepted',0)+outcomes.get('Declined',0)
    contacts=conn.execute(f"SELECT COUNT(*) entries,COALESCE(SUM(outcome IN ('Connected','Meeting held')),0) connected FROM contacts WHERE {contact_clause}",params).fetchone()
    return {'period':period,'dates':bounds,'fundraiser':staff or 'All staff','received':payments['received'],'unique_donors':payments['donors'],
            'request_outcomes':outcomes,'acceptance_rate':outcomes.get('Accepted',0)/decided if decided else None,
            'contacts':dict(contacts),'connection_rate':contacts['connected']/contacts['entries'] if contacts['entries'] else None}

def read_timing(conn,period='all',staff=None):
    bounds=None
    if period!='all':
        bounds=conn.execute('SELECT start,end FROM goals WHERE period=?',(period,)).fetchone()
        if not bounds:
            raise ValueError('Unknown goal period')
    if staff and not conn.execute('SELECT 1 FROM staff WHERE name=?',(staff,)).fetchone():
        raise ValueError('Unknown fundraiser')
    firsts=conn.execute("""WITH ranked AS (
       SELECT *,ROW_NUMBER() OVER(PARTITION BY alumnus_id ORDER BY date,id) AS rn
       FROM gifts WHERE kind='Payment')
       SELECT r.alumnus_id,a.name,r.date first_payment,r.credited_to,
          (SELECT MIN(c.date) FROM contacts c WHERE c.alumnus_id=r.alumnus_id AND c.date<=r.date) first_contact
       FROM ranked r JOIN alumni a ON a.id=r.alumnus_id WHERE rn=1 ORDER BY a.name""").fetchall()
    records=[]
    for row in firsts:
        item=dict(row)
        if bounds and not(bounds['start']<=item['first_payment']<=bounds['end']):continue
        if staff and item['credited_to']!=staff:continue
        item['days']=(date.fromisoformat(item['first_payment'])-date.fromisoformat(item['first_contact'])).days if item['first_contact'] else None
        records.append(item)
    measured=[r['days'] for r in records if r['days'] is not None]
    return {'average_days':sum(measured)/len(measured) if measured else None,
            'measured_alumni':len(measured),'excluded_alumni':len(records)-len(measured),'records':records}

def add_contact(conn,data):
    required=['alumnus_id','date','type','outcome','logged_by']
    if not isinstance(data,dict) or any(not data.get(k) for k in required):
        raise ValueError('Required: alumnus_id, date, type, outcome, logged_by')
    if not isinstance(data['alumnus_id'],int) or isinstance(data['alumnus_id'],bool):
        raise ValueError('alumnus_id must be an integer')
    date.fromisoformat(data['date'])
    if data['type'] not in ['Email','Phone','Meeting','Video meeting','Text','Event interaction']:
        raise ValueError('Invalid contact type')
    if data['outcome'] not in ['Attempted—no response','Voicemail left','Connected','Meeting held']:
        raise ValueError('Invalid contact outcome')
    notes=data.get('notes','')
    if not isinstance(notes,str) or len(notes)>5000:
        raise ValueError('Notes must be text, at most 5000 characters')
    with conn:
        result=conn.execute('INSERT INTO contacts(alumnus_id,date,type,outcome,logged_by,notes) VALUES (?,?,?,?,?,?)',
           (data['alumnus_id'],data['date'],data['type'],data['outcome'],data['logged_by'],notes))
        record_id=result.lastrowid
        conn.execute("INSERT INTO audit_log(action,table_name,record_id,actor) VALUES ('create','contacts',?,?)",(record_id,data['logged_by']))
    return {'id':record_id,'saved':True,'audit_logged':True}

class Handler(BaseHTTPRequestHandler):
    def send_json(self,payload,status=200):
        raw=json.dumps(payload).encode()
        self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(raw)))
        self.send_header('Cache-Control','no-store')
        self.end_headers()
        self.wfile.write(raw)
    def do_GET(self):
        parsed=urlparse(self.path)
        params=parse_qs(parsed.query)
        conn=connect(self.server.database)
        try:
            if parsed.path=='/api/summary':
                self.send_json(read_summary(conn,params.get('period',['all'])[0],params.get('staff',[None])[0]))
            elif parsed.path=='/api/donation-timing':
                self.send_json(read_timing(conn,params.get('period',['all'])[0],params.get('staff',[None])[0]))
            elif parsed.path=='/api/health':
                self.send_json({'status':'ok','storage':'SQLite','mode':'local fictional-data demo'})
            else:
                queries={'/api/alumni':'SELECT * FROM alumni ORDER BY name','/api/contacts':
                  'SELECT c.*, a.name alumnus_name FROM contacts c JOIN alumni a ON a.id=c.alumnus_id ORDER BY c.date DESC,c.id DESC',
                  '/api/gifts':'SELECT * FROM gifts ORDER BY date DESC,id DESC','/api/goals':'SELECT * FROM goals',
                  '/api/audit':'SELECT * FROM audit_log ORDER BY id DESC LIMIT 100'}
                query=queries.get(parsed.path)
                if not query:
                    self.send_json({'error':'Not found'},404)
                else:
                    self.send_json([dict(x) for x in conn.execute(query)])
        except ValueError as error:
            self.send_json({'error':str(error)},400)
        finally:
            conn.close()
    def do_POST(self):
        if urlparse(self.path).path!='/api/contacts':
            self.send_json({'error':'Not found'},404)
            return
        # Browser cross-origin writes are refused. No authentication is implied.
        if self.headers.get('Origin') not in [None,'http://127.0.0.1:'+str(self.server.server_port),'http://localhost:'+str(self.server.server_port)]:
            self.send_json({'error':'Cross-origin writes are not supported'},403)
            return
        conn=connect(self.server.database)
        try:
            size=int(self.headers.get('Content-Length','0'))
            if size<=0 or size>16384:
                raise ValueError('Invalid request size')
            if 'application/json' not in self.headers.get('Content-Type',''):
                raise ValueError('Use Content-Type: application/json')
            payload=json.loads(self.rfile.read(size))
            self.send_json(add_contact(conn,payload),201)
        except (ValueError,TypeError,sqlite3.IntegrityError) as error:
            self.send_json({'error':str(error)},400)
        finally:
            conn.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=8787)
    parser.add_argument('--database',type=Path,default=ROOT/'demo.sqlite3')
    args=parser.parse_args()
    initialize(args.database)
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    server.database=args.database
    print(f'Local backend: http://127.0.0.1:{args.port}/api/summary?period=all',flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: server.server_close()
