"""
Load olx_categories_full.json into MySQL. Upsert, so re-running is fine.

  pip install pymysql
  python import_categories.py --host localhost --user root --password secret --db mydb --create

--create also applies schema.sql first.
"""
import argparse
import json
import os
import sys

try:
    import pymysql
except ImportError:
    sys.exit("pymysql not installed. run: pip install pymysql")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", type=int, default=3306)
    ap.add_argument("--user", required=True)
    ap.add_argument("--password", required=True)
    ap.add_argument("--db", required=True)
    ap.add_argument("--json", default="olx_categories_full.json")
    ap.add_argument("--create", action="store_true", help="apply schema.sql first")
    args = ap.parse_args()

    if not os.path.exists(args.json):
        sys.exit("%s not found. run categories_full.py first." % args.json)

    with open(args.json, encoding="utf-8") as f:
        cats = json.load(f)
    if not cats:
        sys.exit("json is empty")

    conn = pymysql.connect(host=args.host, port=args.port, user=args.user,
                           password=args.password, database=args.db, charset="utf8mb4")
    cur = conn.cursor()

    if args.create:
        schema = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
        with open(schema, encoding="utf-8") as f:
            for stmt in f.read().split(";"):
                if stmt.strip() and not stmt.strip().startswith("--"):
                    cur.execute(stmt)
        print("schema applied")

    sql = ("INSERT INTO olx_categories (id, parent_id, name, path) VALUES (%s,%s,%s,%s) "
           "ON DUPLICATE KEY UPDATE parent_id=VALUES(parent_id), name=VALUES(name), path=VALUES(path)")
    rows = [(c["id"], c.get("parent_id"), c["name"], c.get("path")) for c in cats]
    cur.executemany(sql, rows)
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM olx_categories")
    print("imported %d, table now holds %d" % (len(rows), cur.fetchone()[0]))
    conn.close()


if __name__ == "__main__":
    main()
