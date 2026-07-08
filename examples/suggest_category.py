"""
Ask OLX for a category suggestion given a product title.

  GET /categories/suggest?keyword={title}

Useful, but not something to trust on its own. It once suggested "Mobiteli" for a
product of mine that just had an English word in the name. If you auto-publish, cross
check it against your own rules and confirm with a human when they disagree.

  python suggest_category.py --token YOUR_TOKEN "Zeko Vibrator Good Vibrations"
"""
import argparse

import requests

API = "https://api.olx.ba"


def suggest(token, title, limit=5):
    r = requests.get(
        API + "/categories/suggest",
        params={"keyword": title},
        headers={"Accept": "application/json", "Authorization": "Bearer " + token},
        timeout=20,
    )
    data = r.json().get("data") or []
    out = []
    for c in data[:limit]:
        parents = c.get("parent_categories") or []
        path = " > ".join(parents + [c.get("name", "")]) if parents else c.get("name", "")
        out.append({"id": c["id"], "path": path, "count": c.get("count", 0)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", required=True)
    ap.add_argument("title")
    args = ap.parse_args()

    results = suggest(args.token, args.title)
    if not results:
        print("no suggestions")
        return
    print("suggestions for: %s\n" % args.title)
    for i, c in enumerate(results, 1):
        print("%d. [%s] %s  (%d active)" % (i, c["id"], c["path"], c["count"]))


if __name__ == "__main__":
    main()
