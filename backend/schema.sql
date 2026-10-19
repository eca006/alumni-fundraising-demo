PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS staff (name TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS alumni (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, graduation_year TEXT, college TEXT,
 email TEXT, phone TEXT, preferred_contact TEXT, relationship_source TEXT,
 origin_staff TEXT REFERENCES staff(name), assigned_staff TEXT REFERENCES staff(name), added TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS contacts (
 id INTEGER PRIMARY KEY AUTOINCREMENT, alumnus_id INTEGER NOT NULL REFERENCES alumni(id),
 date TEXT NOT NULL, type TEXT NOT NULL, outcome TEXT NOT NULL,
 logged_by TEXT NOT NULL REFERENCES staff(name), notes TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS gifts (
 id INTEGER PRIMARY KEY AUTOINCREMENT, alumnus_id INTEGER NOT NULL REFERENCES alumni(id),
 kind TEXT NOT NULL CHECK(kind IN ('Request','Pledge','Payment','Estimate')),
 amount REAL NOT NULL CHECK(amount>0), date TEXT NOT NULL,
 credited_to TEXT NOT NULL REFERENCES staff(name), status TEXT, purpose TEXT, frequency TEXT
);
CREATE TABLE IF NOT EXISTS followups (
 id INTEGER PRIMARY KEY AUTOINCREMENT, alumnus_id INTEGER NOT NULL REFERENCES alumni(id),
 action TEXT NOT NULL, due TEXT NOT NULL, assigned_to TEXT NOT NULL REFERENCES staff(name)
);
CREATE TABLE IF NOT EXISTS referrals (
 id INTEGER PRIMARY KEY AUTOINCREMENT, from_alumnus INTEGER NOT NULL REFERENCES alumni(id),
 to_alumnus INTEGER REFERENCES alumni(id), referred_name TEXT NOT NULL,
 assigned_to TEXT NOT NULL REFERENCES staff(name), status TEXT
);
CREATE TABLE IF NOT EXISTS events (
 id INTEGER PRIMARY KEY, title TEXT NOT NULL, type TEXT, date TEXT NOT NULL,
 start_time TEXT, end_time TEXT, location TEXT, host TEXT REFERENCES staff(name), status TEXT
);
CREATE TABLE IF NOT EXISTS goals (
 period TEXT PRIMARY KEY, amount REAL NOT NULL CHECK(amount>0), start TEXT NOT NULL,
 end TEXT NOT NULL, CHECK(start<=end)
);
CREATE TABLE IF NOT EXISTS audit_log (
 id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 action TEXT NOT NULL, table_name TEXT NOT NULL, record_id INTEGER NOT NULL, actor TEXT NOT NULL REFERENCES staff(name)
);
CREATE INDEX IF NOT EXISTS gifts_period ON gifts(kind,date);
CREATE INDEX IF NOT EXISTS contacts_alumni ON contacts(alumnus_id,date);
