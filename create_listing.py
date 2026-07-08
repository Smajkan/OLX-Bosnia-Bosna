"""
Create a listing on OLX.ba (POST /listings) without running into the attribute 422s.

The gotcha: some categories require the `attributes` field and some reject it outright.
Sending an empty [] to a category that doesn't want attributes still fails. So the flow
is: look up the category's attributes first, then include the key only if it has any.

This example fills required attributes interactively for demo purposes. In a real
integration you'd map them from your own product data.

Run:
  python create_listing.py --token YOUR_TOKEN
"""
import argparse

import requests

API = "https://api.olx.ba"


def api(token):
    s = requests.Session()
    s.headers.update({"Accept": "application/json", "Authorization": "Bearer " + token})
    return s


def category_attributes(s, category_id):
    r = s.get(API + "/categories/%d/attributes" % category_id, timeout=20)
    return r.json().get("data") or []


def build_attributes(s, category_id):
    """
    Return (attributes_list, send_key).
    send_key is False when the category has no attributes, meaning you must NOT
    put the key in the payload at all.
    """
    attrs = category_attributes(s, category_id)
    if not attrs:
        return [], False

    filled = []
    for a in attrs:
        label = a.get("display_name") or a.get("name")
        options = a.get("options") or []
        if options:
            print("%s options: %s" % (label, options[:10]))
        value = input("value for '%s'%s: " % (label, " *" if a.get("required") else "")).strip()
        if value:
            filled.append({"id": int(a["id"]), "value": value})
    return filled, True


def create_listing(s, product, category_id):
    payload = {
        "type": "single",
        "title": product["title"],
        "short_description": product.get("short_description", product["title"]),
        "description": product["description"],  # basic HTML ok: <a href>, <br>
        "price": product["price"],
        "listing_type": "sell",
        "state": "new",
        "available": True,
        "category_id": category_id,
        "sku_number": product.get("sku", ""),
    }

    attributes, send_key = build_attributes(s, category_id)
    if send_key:
        payload["attributes"] = attributes  # only include when the category has attributes

    # brand / model only when present and known
    if product.get("brand_id"):
        payload["brand_id"] = product["brand_id"]
    if product.get("model_id"):
        payload["model_id"] = product["model_id"]

    r = s.post(API + "/listings", json=payload, timeout=30)
    if r.status_code >= 400:
        print("HTTP %d" % r.status_code)
        print(r.text)  # OLX puts the exact failing field in the errors object
        return None
    data = r.json().get("data") or r.json()
    listing_id = data.get("id")
    print("created listing id %s" % listing_id)
    return listing_id


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", required=True)
    args = ap.parse_args()

    s = api(args.token)

    product = {
        "title": "Example product",
        "description": "Line one.<br>Line two with a <a href=\"https://example.com\">link</a>.",
        "price": 25,
        "sku": "EXAMPLE-1",
    }
    category_id = int(input("category id to post into: ").strip())

    # after creating, you upload images separately via the image endpoints,
    # then publish. Left out here to keep the example focused.
    create_listing(s, product, category_id)


if __name__ == "__main__":
    main()
