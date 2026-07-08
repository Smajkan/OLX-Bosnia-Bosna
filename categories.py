"""
Simple category dump: main categories, their children, and grandchildren,
printed to the console and written to three JSON files.

This is the basic version. If you want the full tree of any depth with parent
ids and full paths, use categories_full.py instead.
"""
import json
import sys

import requests

API = "https://api.olx.ba"
TOKEN = ""  # usually not needed just to read category ids

session = requests.Session()
# Send a normal User-Agent, otherwise the Cloudflare layer in front of the API can
# hand back an HTML challenge instead of JSON and you end up with empty files.
HEADERS = {"Accept": "application/json", "User-Agent": "Mozilla/5.0 (compatible; olx-tools/1.0)"}
if TOKEN:
    HEADERS["Authorization"] = "Bearer " + TOKEN

main_cats = []
children_cats = []
grandchildren_cats = []


def fetch(path):
    r = session.get(API + path, headers=HEADERS, timeout=20)
    try:
        body = r.json()
    except ValueError:
        print("%s did not return JSON (HTTP %d): %s" % (path, r.status_code, r.text[:200]))
        return None
    return body.get("data") if isinstance(body, dict) else None


def walk_grandchildren(category_id):
    data = fetch("/categories/%d" % category_id)
    # object shape = info about this category; children live under sub_categories
    if isinstance(data, dict):
        grandchildren_cats.append({"id": data["id"], "name": data.get("name", "")})
        print("    grandchild %d - %s" % (data["id"], data.get("name", "")))


def walk_children(category_id):
    data = fetch("/categories/%d" % category_id)
    # list shape = the children of this category
    if isinstance(data, list):
        for c in data:
            children_cats.append({"id": c["id"], "name": c.get("name", "")})
            print("  child %d - %s" % (c["id"], c.get("name", "")))
            walk_grandchildren(c["id"])


def main():
    data = fetch("/categories")  # careful: this is ONLY the main categories
    if not data:
        sys.exit("no categories returned, check token / network, not writing empty files")
    for c in data or []:
        main_cats.append({"id": c["id"], "name": c.get("name", "")})
        print("%d - %s" % (c["id"], c.get("name", "")))
        walk_children(c["id"])
        print()

    for name, arr in (("main_cats.json", main_cats),
                      ("children_cats.json", children_cats),
                      ("grandchildren_cats.json", grandchildren_cats)):
        with open(name, "w", encoding="utf-8") as f:
            json.dump(arr, f, ensure_ascii=False, indent=4)
        print("wrote %s (%d items)" % (name, len(arr)))


if __name__ == "__main__":
    main()
