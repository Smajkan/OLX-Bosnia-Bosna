<?php
/**
 * Full-tree category sync straight into MySQL. Plain curl + mysqli, no libraries.
 *
 * GET /categories       gives only the main categories.
 * GET /categories/{id}   gives either data: [children] (list) or data: {..., sub_categories} (object).
 * This walks the whole thing level by level, in parallel, and upserts into olx_categories.
 *
 * Fill in the config, create the table (db/schema.sql or let this do it), then:
 *   php sync_categories.php
 *
 * Re-running is safe. Cron example (daily at 5am):
 *   0 5 * * * php /path/to/sync_categories.php >/dev/null 2>&1
 */

// config
const OLX_TOKEN   = '';           // usually not required to read categories
const DB_HOST     = 'localhost';
const DB_USER     = 'root';
const DB_PASS     = '';
const DB_NAME     = 'mydb';
const CONCURRENCY = 8;

const API = 'https://api.olx.ba';
set_time_limit(600);

function auth_headers(): array
{
    $h = ['Accept: application/json'];
    if (OLX_TOKEN !== '') {
        $h[] = 'Authorization: Bearer ' . OLX_TOKEN;
    }
    return $h;
}

function olx_get(string $path): ?array
{
    $ch = curl_init(API . $path);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 20,
        CURLOPT_CONNECTTIMEOUT => 6,
        CURLOPT_HTTPHEADER     => auth_headers(),
    ]);
    $raw = curl_exec($ch);
    curl_close($ch);
    $j = json_decode((string)$raw, true);
    return is_array($j) ? $j : null;
}

// 1) main categories
$root  = olx_get('/categories');
$mains = $root['data'] ?? [];
if (!$mains) {
    exit("no main categories, api down or token invalid\n");
}

$all      = [];
$frontier = [];
foreach ($mains as $c) {
    if (!isset($c['id'])) {
        continue;
    }
    $name = trim((string)($c['name'] ?? ''));
    if ($name === '') {
        continue;
    }
    $row = ['id' => (int)$c['id'], 'parent_id' => null, 'name' => $name, 'path' => $name];
    $all[$row['id']] = $row;
    $frontier[] = $row;
}

// 2) walk down with curl_multi
for ($depth = 0; $depth < 8 && $frontier; $depth++) {
    echo "depth {$depth}: expanding " . count($frontier) . ' (total ' . count($all) . ")\n";
    $next = [];
    foreach (array_chunk($frontier, CONCURRENCY) as $batch) {
        $mh  = curl_multi_init();
        $chs = [];
        foreach ($batch as $node) {
            $ch = curl_init(API . '/categories/' . $node['id']);
            curl_setopt_array($ch, [
                CURLOPT_RETURNTRANSFER => true,
                CURLOPT_TIMEOUT        => 20,
                CURLOPT_CONNECTTIMEOUT => 6,
                CURLOPT_HTTPHEADER     => auth_headers(),
            ]);
            curl_multi_add_handle($mh, $ch);
            $chs[] = ['ch' => $ch, 'node' => $node];
        }
        do {
            $mrc = curl_multi_exec($mh, $running);
            if ($running) {
                curl_multi_select($mh, 0.2);
            }
        } while ($running && $mrc === CURLM_OK);

        foreach ($chs as $x) {
            $raw = curl_multi_getcontent($x['ch']);
            curl_multi_remove_handle($mh, $x['ch']);
            curl_close($x['ch']);
            $j = json_decode((string)$raw, true);
            $d = $j['data'] ?? null;

            $children = [];
            if (is_array($d) && array_is_list($d)) {
                $children = $d;                                            // list = children
            } elseif (is_array($d)) {
                $children = $d['sub_categories'] ?? $d['children'] ?? [];  // object = info + sub_categories
                if (!is_array($children)) {
                    $children = [];
                }
            }

            foreach ($children as $c) {
                if (!isset($c['id'])) {
                    continue;
                }
                $cid = (int)$c['id'];
                if (isset($all[$cid])) {   // loop / duplicate guard
                    continue;
                }
                $name = trim((string)($c['name'] ?? ''));
                if ($name === '') {
                    continue;
                }
                $row = [
                    'id'        => $cid,
                    'parent_id' => $x['node']['id'],
                    'name'      => $name,
                    'path'      => $x['node']['path'] . ' > ' . $name,
                ];
                $all[$cid]  = $row;
                $next[]     = $row;
            }
        }
        curl_multi_close($mh);
    }
    $frontier = $next;
}

// 3) upsert
$conn = new mysqli(DB_HOST, DB_USER, DB_PASS, DB_NAME);
if ($conn->connect_error) {
    exit('db: ' . $conn->connect_error . "\n");
}
$conn->set_charset('utf8mb4');
$conn->query(
    "CREATE TABLE IF NOT EXISTS olx_categories (
        id INT NOT NULL, parent_id INT DEFAULT NULL, name VARCHAR(200) NOT NULL,
        path VARCHAR(600) DEFAULT NULL,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (id), KEY idx_olxcat_parent (parent_id), KEY idx_olxcat_name (name)
     ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"
);

$stmt = $conn->prepare(
    "INSERT INTO olx_categories (id, parent_id, name, path) VALUES (?,?,?,?)
     ON DUPLICATE KEY UPDATE parent_id=VALUES(parent_id), name=VALUES(name), path=VALUES(path)"
);
$n = 0;
foreach ($all as $c) {
    $stmt->bind_param('iiss', $c['id'], $c['parent_id'], $c['name'], $c['path']);
    $stmt->execute();
    $n++;
}
echo "done, {$n} categories cached into " . DB_NAME . ".olx_categories\n";
