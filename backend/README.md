# Local database and API demonstration

This is a working SQLite backend example for fictional internship demonstration data. It is separate from the GitHub Pages website. The live website still saves data in each browser and its Backend & data tab is a browser-based record explorer.

Run with Python 3.10 or newer, without installing packages:

```sh
python3 backend/server.py
```

It creates `backend/demo.sqlite3` once and serves only on `127.0.0.1:8787`.

Open these links on the same computer:

- <http://127.0.0.1:8787/api/health>
- <http://127.0.0.1:8787/api/summary?period=2025-2026>
- <http://127.0.0.1:8787/api/alumni>
- <http://127.0.0.1:8787/api/contacts>
- <http://127.0.0.1:8787/api/gifts>
- <http://127.0.0.1:8787/api/goals>
- <http://127.0.0.1:8787/api/audit>

The summary also accepts `period=2026-2027`, `period=all`, and an optional `staff=James%20Carter` filter. Dates come from the database's goal records and include both boundaries. Initial records are a snapshot of the fictional sample dataset; later browser edits do not synchronize to SQLite.

Example contact write:

```sh
curl http://127.0.0.1:8787/api/contacts \
  -H 'Content-Type: application/json' \
  -d '{"alumnus_id":1,"date":"2026-10-18","type":"Phone","outcome":"Connected","logged_by":"James Carter","notes":"Fictional demonstration contact."}'
```

The write validates inputs, checks foreign keys, and creates an audit record in one transaction. Unknown alumni/staff cannot be inserted. SQL parameters protect values from injection. The schema and example aggregation queries illustrate relational storage, joins, date filtering, and reporting.

This is not production authentication or a deployment-ready university system. The API does not enforce real staff roles. It stays local, rejects cross-origin browser writes, and must use fictional data only. A production service needs identity, role checks, secure shared hosting, migrations, backups, monitoring, and a privacy-reviewed data model.

Run the backend checks with `python3 -m unittest discover -s backend -p "test_*.py"`. They verify totals, admin date filters, foreign keys, and transactional audit writes.

Donation timing: `GET /api/donation-timing?period=all` (also accepts goal period and staff filters). It measures earliest logged contact to the first-ever payment, excludes missing prior contacts, and returns the average plus per-alumnus dates/days. Sample outreach history is fictional. The period filter applies to first payment, not contact date.
