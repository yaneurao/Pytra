<?php
declare(strict_types=1);

function __pytra_require_runtime_file(string $staged_rel, string $repo_rel): void {
    $candidates = [
        __DIR__ . '/' . $staged_rel,
        __DIR__ . '/' . $repo_rel,
    ];
    foreach ($candidates as $candidate) {
        if (is_file($candidate)) {
            require_once $candidate;
            return;
        }
    }
    throw new RuntimeException('runtime dependency not found: ' . $repo_rel);
}

__pytra_require_runtime_file('utils/png.php', '../../generated/utils/png.php');
__pytra_require_runtime_file('utils/gif.php', '../../generated/utils/gif.php');
__pytra_require_runtime_file('std/time.php', '../../generated/std/time.php');

function __pytra_print(...$args): void {
    if (count($args) === 0) {
        echo PHP_EOL;
        return;
    }
    $parts = [];
    foreach ($args as $arg) {
        if (is_bool($arg)) {
            $parts[] = $arg ? "True" : "False";
            continue;
        }
        if ($arg === null) {
            $parts[] = "None";
            continue;
        }
        if (is_array($arg)) {
            $parts[] = json_encode($arg, JSON_UNESCAPED_UNICODE);
            continue;
        }
        $parts[] = (string)$arg;
    }
    echo implode(" ", $parts) . PHP_EOL;
}

function __pytra_len($v): int {
    if (is_string($v)) {
        return strlen($v);
    }
    if (is_array($v)) {
        return count($v);
    }
    return 0;
}

function __pytra_truthy($v): bool {
    if (is_bool($v)) {
        return $v;
    }
    if ($v === null) {
        return false;
    }
    if (is_int($v) || is_float($v)) {
        return $v != 0;
    }
    if (is_string($v)) {
        return strlen($v) > 0;
    }
    if (is_array($v)) {
        return count($v) > 0;
    }
    return (bool)$v;
}

function __pytra_int($v): int {
    if (is_int($v)) {
        return $v;
    }
    if (is_bool($v)) {
        return $v ? 1 : 0;
    }
    if (is_float($v)) {
        return (int)$v;
    }
    if (is_string($v) && is_numeric($v)) {
        return (int)$v;
    }
    return 0;
}

function __pytra_float($v): float {
    if (is_float($v)) {
        return $v;
    }
    if (is_int($v) || is_bool($v)) {
        return (float)$v;
    }
    if (is_string($v) && is_numeric($v)) {
        return (float)$v;
    }
    return 0.0;
}

function __pytra_str_isdigit($s): bool {
    if (!is_string($s) || $s === '') {
        return false;
    }
    return preg_match('/^[0-9]+$/', $s) === 1;
}

function __pytra_str_isalpha($s): bool {
    if (!is_string($s) || $s === '') {
        return false;
    }
    return preg_match('/^[A-Za-z]+$/', $s) === 1;
}

function __pytra_str_slice($s, $start, $stop) {
    if (!is_string($s)) {
        return '';
    }
    $n = strlen($s);
    $a = (int)$start;
    $b = (int)$stop;
    if ($a < 0) {
        $a += $n;
    }
    if ($b < 0) {
        $b += $n;
    }
    if ($a < 0) {
        $a = 0;
    }
    if ($b < $a) {
        return '';
    }
    return substr($s, $a, $b - $a);
}

function __pytra_index($container, $index): int {
    $i = __pytra_int($index);
    $n = 0;
    if (is_array($container)) {
        $n = count($container);
    } elseif (is_string($container)) {
        $n = strlen($container);
    }
    if ($i < 0) {
        $i += $n;
    }
    return $i;
}

function __pytra_noop(...$_args) {
    return null;
}

function __pytra_array_is_list_like(array $v): bool {
    $i = 0;
    foreach ($v as $k => $_value) {
        if (!is_int($k) || $k !== $i) {
            return false;
        }
        $i += 1;
    }
    return true;
}

function __pytra_contains($container, $item): bool {
    if (is_array($container)) {
        if (__pytra_array_is_list_like($container)) {
            return in_array($item, $container, true);
        }
        return array_key_exists($item, $container);
    }
    if (is_string($container)) {
        return strpos($container, (string)$item) !== false;
    }
    return false;
}

function bytearray($v = 0): array {
    if (is_int($v) || is_float($v) || is_bool($v)) {
        $n = (int)$v;
        if ($n <= 0) {
            return [];
        }
        return array_fill(0, $n, 0);
    }
    if (is_string($v)) {
        $out = [];
        $n = strlen($v);
        $i = 0;
        while ($i < $n) {
            $out[] = ord($v[$i]);
            $i += 1;
        }
        return $out;
    }
    if (is_array($v)) {
        return array_values($v);
    }
    return [];
}

function bytes($v = null): array {
    if ($v === null) {
        return [];
    }
    if (is_array($v)) {
        return array_values($v);
    }
    if (is_string($v)) {
        return bytearray($v);
    }
    return bytearray($v);
}

function __pytra_bytes_to_string($v): string {
    if (is_string($v)) {
        return $v;
    }
    if (is_array($v)) {
        if (count($v) === 0) {
            return '';
        }
        $out = '';
        $chunk = [];
        foreach ($v as $item) {
            $chunk[] = ((int)$item) & 0xFF;
            if (count($chunk) >= 4096) {
                $out .= pack('C*', ...$chunk);
                $chunk = [];
            }
        }
        if (count($chunk) > 0) {
            $out .= pack('C*', ...$chunk);
        }
        return $out;
    }
    return (string)$v;
}

class PyFile {
    private $handle;

    public function __construct(string $path, string $mode = 'r') {
        $h = @fopen($path, $mode);
        if ($h === false) {
            throw new RuntimeException("open failed: " . $path);
        }
        $this->handle = $h;
    }

    public function write($data): int {
        $s = __pytra_bytes_to_string($data);
        $w = fwrite($this->handle, $s);
        if ($w === false) {
            throw new RuntimeException("write failed");
        }
        return $w;
    }

    public function close(): void {
        if ($this->handle !== null) {
            fclose($this->handle);
            $this->handle = null;
        }
    }
}

function open($path, $mode = 'r'): PyFile {
    return new PyFile((string)$path, (string)$mode);
}

function __pytra_list_repeat($v, int $count): array {
    if (!is_array($v) || $count <= 0) {
        return [];
    }
    $out = [];
    $i = 0;
    while ($i < $count) {
        foreach ($v as $item) {
            $out[] = $item;
        }
        $i += 1;
    }
    return $out;
}

function pyMathSqrt($v): float {
    return sqrt(__pytra_float($v));
}

function pyMathSin($v): float {
    return sin(__pytra_float($v));
}

function pyMathCos($v): float {
    return cos(__pytra_float($v));
}

function pyMathTan($v): float {
    return tan(__pytra_float($v));
}

function pyMathExp($v): float {
    return exp(__pytra_float($v));
}

function pyMathLog($v): float {
    return log(__pytra_float($v));
}

function pyMathFabs($v): float {
    return abs(__pytra_float($v));
}

function pyMathFloor($v): float {
    return floor(__pytra_float($v));
}

function pyMathCeil($v): float {
    return ceil(__pytra_float($v));
}

function pyMathPow($a, $b): float {
    return pow(__pytra_float($a), __pytra_float($b));
}

function pyMathPi(): float {
    return M_PI;
}

function pyMathE(): float {
    return M_E;
}

function pyJsonLoads($v) {
    $text = (string)$v;
    return json_decode($text, true, 512, JSON_THROW_ON_ERROR);
}

function pyJsonDumps($v): string {
    return json_encode($v, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR);
}

class Path {
    public string $path;
    public string $name;
    public string $stem;
    public ?Path $parent;

    public function __construct($value) {
        $this->path = (string)$value;
        $this->name = basename($this->path);
        $dot = strrpos($this->name, '.');
        $this->stem = ($dot === false || $dot === 0) ? $this->name : substr($this->name, 0, $dot);
        $parentTxt = dirname($this->path);
        if ($parentTxt === '' || $parentTxt === $this->path) {
            $this->parent = null;
        } else {
            $this->parent = new Path($parentTxt);
        }
    }

    public function __toString(): string {
        return $this->path;
    }

    public function resolve(): Path {
        $resolved = realpath($this->path);
        if ($resolved === false) {
            $resolved = $this->path;
        }
        return new Path($resolved);
    }

    public function exists(): bool {
        return file_exists($this->path);
    }

    public function mkdir($parents = false, $exist_ok = false): void {
        if ($exist_ok && file_exists($this->path)) {
            return;
        }
        if ((bool)$parents) {
            if (@mkdir($this->path, 0777, true)) {
                return;
            }
            if ((bool)$exist_ok && is_dir($this->path)) {
                return;
            }
            throw new RuntimeException("mkdir failed: " . $this->path);
        }
        if (@mkdir($this->path)) {
            return;
        }
        if ((bool)$exist_ok && is_dir($this->path)) {
            return;
        }
        throw new RuntimeException("mkdir failed: " . $this->path);
    }

    public function write_text($text, $encoding = "utf-8"): int {
        $bytes = file_put_contents($this->path, (string)$text);
        if ($bytes === false) {
            throw new RuntimeException("write_text failed: " . $this->path);
        }
        return $bytes;
    }

    public function read_text($encoding = "utf-8"): string {
        $data = file_get_contents($this->path);
        if ($data === false) {
            throw new RuntimeException("read_text failed: " . $this->path);
        }
        return $data;
    }
}
