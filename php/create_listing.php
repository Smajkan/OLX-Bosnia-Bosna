<?php
/**
 * Create a listing (POST /listings) from PHP without hitting the attribute 422s.
 *
 * The catch: some categories require the `attributes` field and some reject it.
 * Sending [] to a category that doesn't want attributes fails too. So look up the
 * category attributes first and only include the key when there are any.
 *
 *   php create_listing.php
 */
require __DIR__ . '/olx_client.php';

// config
const TOKEN = 'YOUR_TOKEN';

$olx = new OlxClient(TOKEN);

/**
 * Build the attributes array for a category.
 * Returns [array $attributes, bool $sendKey]. When $sendKey is false the category
 * has no attributes and you must leave the key out of the payload entirely.
 */
function build_attributes(OlxClient $olx, int $categoryId, array $values): array
{
    $attrs = $olx->get("/categories/{$categoryId}/attributes") ?: [];
    if (!$attrs) {
        return [[], false];
    }
    $filled = [];
    foreach ($attrs as $a) {
        $id  = (int)$a['id'];
        $key = $a['name'] ?? (string)$id;               // map however your data is keyed
        $val = $values[$key] ?? $values[$id] ?? null;   // by attribute name or id
        if ($val !== null && $val !== '') {
            $filled[] = ['id' => $id, 'value' => (string)$val];
        }
    }
    return [$filled, true];
}

function create_listing(OlxClient $olx, array $product, int $categoryId, array $attributeValues = []): ?int
{
    $payload = [
        'type'              => 'single',
        'title'             => $product['title'],
        'short_description' => $product['short_description'] ?? $product['title'],
        'description'       => $product['description'],   // basic HTML ok: <a href>, <br>
        'price'             => $product['price'],
        'listing_type'      => 'sell',
        'state'             => 'new',
        'available'         => true,
        'category_id'       => $categoryId,
        'sku_number'        => $product['sku'] ?? '',
    ];

    [$attributes, $sendKey] = build_attributes($olx, $categoryId, $attributeValues);
    if ($sendKey) {
        $payload['attributes'] = $attributes;   // include only when the category has attributes
    }
    if (!empty($product['brand_id'])) {
        $payload['brand_id'] = (int)$product['brand_id'];
    }
    if (!empty($product['model_id'])) {
        $payload['model_id'] = (int)$product['model_id'];
    }

    $res = $olx->post('/listings', $payload);
    if ($res['status'] >= 400) {
        echo "HTTP {$res['status']}\n";
        // OLX returns the exact failing field under body.errors
        echo json_encode($res['body'], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE) . "\n";
        return null;
    }
    $data = $res['body']['data'] ?? $res['body'];
    $id   = $data['id'] ?? null;
    echo "created listing id {$id}\n";
    return $id ? (int)$id : null;
}

// demo
$product = [
    'title'       => 'Example product',
    'description' => "Line one.<br>Line two with a <a href=\"https://example.com\">link</a>.",
    'price'       => 25,
    'sku'         => 'EXAMPLE-1',
];

// after this you'd upload images via the image endpoints and publish; left out to stay focused
create_listing($olx, $product, 2369, ['Stanje' => 'Novo']);
