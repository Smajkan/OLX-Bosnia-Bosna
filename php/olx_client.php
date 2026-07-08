<?php
/**
 * Tiny curl wrapper shared by the PHP examples. No dependencies.
 *
 *   $olx = new OlxClient('YOUR_TOKEN');   // token optional for reads
 *   $data = $olx->get('/categories');
 *   $res  = $olx->post('/listings', $payload);
 */
class OlxClient
{
    private string $base;
    private string $token;

    public function __construct(string $token = '', string $base = 'https://api.olx.ba')
    {
        $this->token = $token;
        $this->base  = rtrim($base, '/');
    }

    private function headers(bool $json = false): array
    {
        $h = ['Accept: application/json'];
        if ($this->token !== '') {
            $h[] = 'Authorization: Bearer ' . $this->token;
        }
        if ($json) {
            $h[] = 'Content-Type: application/json';
        }
        return $h;
    }

    /** GET, returns decoded 'data' (or the whole body if there's no data key). */
    public function get(string $path)
    {
        $ch = curl_init($this->base . $path);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT        => 20,
            CURLOPT_CONNECTTIMEOUT => 6,
            CURLOPT_HTTPHEADER     => $this->headers(),
        ]);
        $raw = curl_exec($ch);
        curl_close($ch);
        $j = json_decode((string)$raw, true);
        if (!is_array($j)) {
            return null;
        }
        return array_key_exists('data', $j) ? $j['data'] : $j;
    }

    /** POST JSON, returns ['status' => int, 'body' => array|null]. */
    public function post(string $path, array $payload): array
    {
        $ch = curl_init($this->base . $path);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT        => 30,
            CURLOPT_CONNECTTIMEOUT => 6,
            CURLOPT_POST           => true,
            CURLOPT_POSTFIELDS     => json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES),
            CURLOPT_HTTPHEADER     => $this->headers(true),
        ]);
        $raw    = curl_exec($ch);
        $status = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        return ['status' => $status, 'body' => json_decode((string)$raw, true)];
    }
}
