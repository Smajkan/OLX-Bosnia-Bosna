"""
Show what a category needs before you can post into it.

  GET /categories/{id}/attributes              -> [{id, name, display_name, input_type, options, required}]
  GET /categories/{id}/brands                  -> [{id, name}]
  GET /categories/{id}/brands/{brand}/models   -> [{id, name}]
  GET /category/{id}   (singular!)             -> info: brand_required, has_models, ...

The 422 trap on POST /listings, straight from the API:
  "kategorija zahtjeva prisutno polje attributes"     -> send attributes: [{id, value}]
  "kategorija ne zahtjeva prisutno polje attributes"  -> don't send the key at all (even [] fails)

So call this first and build the payload based on what you see.

  python category_requirements.py --token YOUR_TOKEN 2369
"""
import argparse

import requests

API = "https://api.olx.ba"


def get(token, path):
    r = requests.get(API + path,
                     headers={"Accept": "application/json", "Authorization": "Bearer " + token},
                     timeout=20)
    return r.json().get("data")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", required=True)
    ap.add_argument("category_id", type=int)
    args = ap.parse_args()

    info = get(args.token, "/category/%d" % args.category_id)  # singular endpoint
    if isinstance(info, dict):
        print("category: %s (id %d)" % (info.get("name"), args.category_id))
        print("  brand_required: %s" % info.get("brand_required"))
        print("  has_models:     %s" % info.get("has_models"))

    attrs = get(args.token, "/categories/%d/attributes" % args.category_id) or []
    if not attrs:
        print("\nno attributes. do NOT send the 'attributes' key on POST /listings.")
    else:
        print("\nattributes (%d). send attributes: [{id, value}, ...]:" % len(attrs))
        for a in attrs:
            req = " *required*" if a.get("required") else ""
            opts = a.get("options") or []
            opts_txt = (" options: %s%s" % (opts[:8], "..." if len(opts) > 8 else "")) if opts else ""
            print("  [%s] %s (%s)%s%s" % (a["id"], a.get("display_name") or a.get("name"),
                                          a.get("input_type", "text"), req, opts_txt))
        print("\nheads up: the 'required' flag isn't always accurate. some categories return")
        print("required=false on everything yet still demand the attributes field on publish.")

    brands = get(args.token, "/categories/%d/brands" % args.category_id) or []
    if brands:
        names = [b["name"] for b in brands[:10]]
        print("\nbrands (%d): %s%s" % (len(brands), names, "..." if len(brands) > 10 else ""))


if __name__ == "__main__":
    main()
