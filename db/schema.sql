-- Tables for the category cache and the auto-suggest learning.
--
-- olx_categories : the full OLX category tree, cached locally. Same for everyone,
--                  so no per-user column. Fill it from categories_full.py --sql,
--                  db/import_categories.py, or php/sync_categories.php.
-- category_rules : learned keyword -> category rules. When someone confirms a
--                  category for a product title, upsert a row and bump hits.
--                  If you run a single shop, just leave tenant_id at 1.

CREATE TABLE IF NOT EXISTS olx_categories (
  id         INT NOT NULL,
  parent_id  INT DEFAULT NULL,
  name       VARCHAR(200) NOT NULL,
  path       VARCHAR(600) DEFAULT NULL,   -- e.g. "Sve ostalo > Seksualna pomagala > Seksualne igracke > Ostalo"
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_olxcat_parent (parent_id),
  KEY idx_olxcat_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS category_rules (
  id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
  tenant_id     INT UNSIGNED NOT NULL DEFAULT 1,
  keyword       VARCHAR(80) NOT NULL,
  category_id   INT NOT NULL,
  category_name VARCHAR(150) DEFAULT NULL,
  hits          INT NOT NULL DEFAULT 1,
  updated_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_rule (tenant_id, keyword, category_id),
  KEY idx_rule_lookup (tenant_id, keyword)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- The whole point of caching the tree: you can search the path, which
-- /categories/find can't do (it only matches the name).
--   SELECT id, name, path FROM olx_categories
--   WHERE path LIKE '%igracke%' AND path LIKE '%ostalo%'
--   ORDER BY CHAR_LENGTH(path) ASC LIMIT 20;
