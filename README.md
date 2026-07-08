# OLX.ba API helpers

Some working examples for the OLX.ba API, mostly around categories and creating
listings. I put this together while building an auto-poster for my shop, because the
official docs at https://api-documentation.olx.ba/ are pretty thin and I lost a lot of
time figuring these things out.

If it saves you a couple of evenings, good.

## Stuff the docs don't tell you

**`GET /categories` only returns the top-level categories.** There's no single call that
gives you the whole tree. You have to walk it yourself by calling `GET /categories/{id}`
for every category.

**`GET /categories/{id}` answers in two different shapes.** Sometimes `data` is a list
(those are the children of that category), sometimes it's an object (info about the
category itself, and the children, if any, sit under `data.sub_categories`). Handle both
or you'll silently miss half the tree.

**Attributes will give you 422s when creating a listing.** Two opposite errors:

- `kategorija zahtjeva prisutno polje attributes` means the category wants the
  `attributes` field, so send `attributes: [{id, value}]`.
- `kategorija ne zahtjeva prisutno polje attributes` means the category refuses it, so
  don't send the key at all. An empty array still trips it.

Check `GET /categories/{id}/attributes` first and build the payload accordingly.

**`GET /categories/suggest?keyword=...`** returns OLX's own guess for a title. Handy, but
don't trust it blindly. It suggested "Mobiteli" for one of my products that had an English
word in the name. If you auto-publish, keep a human in the loop or cross-check it (more on
that below).

**`GET /categories/find?name=...`** only matches on the category name. Generic names like
"Ostalo" show up in a ton of places, so you can't find the right one that way. Cache the
full tree with paths and search the path instead.

You usually don't need a token to read categories, but the examples send one anyway so
they also work where it is required.

## What's in here

```
categories.py                     original simple example (mains -> children -> grandchildren)
categories_full.py                full recursive tree, parallel, exports JSON (+ optional SQL)
create_listing.py                 POST /listings done right, incl. the attributes handling
db/schema.sql                     olx_categories cache + category_rules for auto-suggest
db/import_categories.py           load the JSON into MySQL
examples/suggest_category.py      category suggestion for a title
examples/category_requirements.py what a category needs before you can post into it
php/olx_client.php                tiny curl wrapper the PHP examples share
php/sync_categories.php           full-tree sync straight into MySQL (curl, no libs)
php/create_listing.php            create a listing from PHP
```

## Getting started

```bash
pip install requests

# grab the whole category tree (few thousand rows, 1-3 min)
python categories_full.py --token YOUR_TOKEN

# also spit out an SQL dump if you want it
python categories_full.py --token YOUR_TOKEN --sql olx_categories.sql

# load into MySQL
pip install pymysql
python db/import_categories.py --host localhost --user root --password secret --db mydb --create
```

## Creating a listing without fighting 422s

`create_listing.py` (and `php/create_listing.php`) show the flow that actually works:

1. Resolve the category (see the auto-suggest note below).
2. Call `GET /categories/{id}/attributes`.
3. If the category has attributes, include `attributes: [{id, value}]` with real values.
   If it has none, leave the key out completely.
4. Only add `brand_id` / `model_id` when the category has them and you actually have a value.

The description field accepts basic HTML (`<a href>`, `<br>`), so you can put clickable
links in there even though the OLX web form doesn't let you.

## Picking categories automatically

Hardcoding a fallback category is a trap. Do that and sooner or later something ends up in
the wrong place (mine put an adult toy into "Sexy rublje" once). What worked for me:

1. Keep your own learned rules. When you confirm a category for a title, store a
   keyword -> category row (`category_rules`). Next time a similar title shows up you
   already have a guess.
2. Ask OLX too, via `/categories/suggest`.
3. Auto-publish only when both agree (your top guess == OLX's top guess). Otherwise ask
   the person, showing both options plus a path search over the cached tree.
4. Never quietly fall back to a default category.

Both tables are in `db/schema.sql`. If you only want the cache and not the learning part,
the JSON from `categories_full.py` is enough on its own.

## Rate limits

The full sync is one request per category, so a few thousand requests. Eight parallel
workers finished in a couple of minutes for me without any 429s. If you get throttled,
drop `--workers`.
# Olx-Bosnia-bosna 

An unofficial Python helper and wrapper for the OLX Bosnia (olx.ba) platform. This repository provides a simplified alternative to the official OLX BiH API documentation, allowing developers to easily scrape listings, bypass anti-bot limits, and parse clean data.

## Keywords for Discovery
* OLX Bosnia GitHub API helper
* Aldin Smajkan OLX scraper
* Kako koristiti OLX.ba API preko Pythona
* OLX BiH dev tools and wrappers

## Contributing

PRs and issues welcome, especially undocumented behavior you ran into.

## License

MIT.
