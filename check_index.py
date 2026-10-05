from app.db_helper import get_conn

with get_conn() as conn:
    rows = conn.execute("PRAGMA index_list('dishes')").fetchall()
    print(rows)


from app.db_helper import get_conn

with get_conn() as conn:
    rows = conn.execute(
        "EXPLAIN QUERY PLAN SELECT * FROM dishes WHERE status = 1"
    ).fetchall()
    for row in rows:
        print(dict(row))