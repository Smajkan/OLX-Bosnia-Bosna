"""
Fetch the complete OLX.ba category tree.

Why this exists: GET /categories only gives you the top level. To get everything
you have to call GET /categories/{id} for every category and walk down. That call
returns either a list (children) or an object (info + sub_categories), so both
shapes are handled here.

Outputs:
  olx_categories_full.json   flat list of {id, parent_id, name, path, depth}
  olx_categories_tree.json   nested tree
  --sql FILE                 optional SQL dump matching db/schema.sql

Run:
  python categories_full.py --token YOUR_TOKEN [--workers 8] [--sql out.sql]
"""
import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor

import requests

API = "https://api.olx.ba"


def headers(token):
    h = {"Accept": "application/json"}
    if token:
        h["Authorization"] = "Bearer " + token
    return h


def get_children(session, token, node):
    """Return the children of one category. Deals with both response shapes."""
    try:
        r = session.get(API + "/categories/%d" % node["id"], headers=headers(token), timeout=20)
        data = r.json().get("data")
    except Exception as e:
        # one flaky request shouldn't kill the whole run
        print("  skip %d (%s): %s" % (node["id"], node["name"], e), file=sys.stderr)
        return []

    if isinstance(data, list):
        children = data
    elif isinstance(data, dict):
        children = data.get("sub_categories") or data.get("children") or []
    else:
        children = []

    out = []
    for c in children:
        if not isinstance(c, dict) or "id" not in c:
            continue
        name = str(c.get("name", "")).strip()
        if not name:
            continue
        out.append({
            "id": int(c["id"]),
            "parent_id": node["id"],
            "name": name,
            "path": node["path"] + " > " + name,
            "depth": node["depth"] + 1,
        })
    return out


def fetch_tree(token, workers=8, max_depth=8):
    session = requests.Session()
    r = session.get(API + "/categories", headers=headers(token), timeout=20)
    mains = r.json().get("data") or []

    seen = {}
    frontier = []
    for c in mains:
        if "id" not in c:
            continue
        name = str(c.get("name", "")).strip()
        if not name:
            continue
        node = {"id": int(c["id"]), "parent_id": None, "name": name, "path": name, "depth": 0}
        seen[node["id"]] = node
        frontier.append(node)

    depth = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        while frontier and depth < max_depth:
            print("depth %d: expanding %d (total %d)" % (depth, len(frontier), len(seen)))
            results = pool.map(lambda n: get_children(session, token, n), frontier)
            nxt = []
            for children in results:
                for child in children:
                    if child["id"] in seen:  # guard against loops / dupes
                        continue
                    seen[child["id"]] = child
                    nxt.append(child)
            frontier = nxt
            depth += 1

    return sorted(seen.values(), key=lambda x: x["path"].lower())


def build_tree(flat):
    by_id = {c["id"]: dict(c, children=[]) for c in flat}
    roots = []
    for c in by_id.values():
        pid = c["parent_id"]
        if pid is not None and pid in by_id:
            by_id[pid]["children"].append(c)
        else:
            roots.append(c)
    return roots


def sql_escape(s):
    return s.replace("\\", "\\\\").replace("'", "\\'")


def dump_sql(flat, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("-- OLX.ba categories dump. Schema in db/schema.sql. Safe to re-run.\n\n")
        for c in flat:
            pid = "NULL" if c["parent_id"] is None else str(c["parent_id"])
            f.write(
                "INSERT INTO olx_categories (id, parent_id, name, path) VALUES "
                "(%d, %s, '%s', '%s') "
                "ON DUPLICATE KEY UPDATE parent_id=VALUES(parent_id), name=VALUES(name), path=VALUES(path);\n"
                % (c["id"], pid, sql_escape(c["name"]), sql_escape(c["path"]))
            )


def main():
    ap = argparse.ArgumentParser(description="Fetch the full OLX.ba category tree.")
    ap.add_argument("--token", default="", help="OLX.ba token (often not needed for reads)")
    ap.add_argument("--workers", type=int, default=8, help="parallel requests (default 8)")
    ap.add_argument("--sql", default="", help="also write an SQL dump here")
    args = ap.parse_args()

    flat = fetch_tree(args.token, workers=args.workers)
    print("\ntotal categories: %d" % len(flat))

    with open("olx_categories_full.json", "w", encoding="utf-8") as f:
        json.dump(flat, f, ensure_ascii=False, indent=2)
    print("wrote olx_categories_full.json")

    with open("olx_categories_tree.json", "w", encoding="utf-8") as f:
        json.dump(build_tree(flat), f, ensure_ascii=False, indent=2)
    print("wrote olx_categories_tree.json")

    if args.sql:
        dump_sql(flat, args.sql)
        print("wrote %s" % args.sql)


if __name__ == "__main__":
    main()
