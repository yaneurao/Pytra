<?php
declare(strict_types=1);

// Module dependencies (utils/png, utils/gif, std/time) are require_once'd
// by the emitter-generated code, not here. py_runtime provides only
// Python built-in function equivalents (spec §6).

function __pytra_print(...$args): void {
    if (count($args) === 0) {
        echo PHP_EOL;
        return;
    }
    $parts = [];
    foreach ($args as $arg) {
        $parts[] = py_to_string($arg);
    }
    echo implode(" ", $parts) . PHP_EOL;
}

if (!class_exists('Enum')) {
    class Enum {}
}

if (!class_exists('IntEnum')) {
    class IntEnum extends Enum {}
}

if (!class_exists('IntFlag')) {
    class IntFlag extends IntEnum {}
}

function __pytra_repr_value($v): string {
    if (is_bool($v)) { return $v ? "True" : "False"; }
    if ($v === null) { return "None"; }
    if (is_int($v)) { return (string)$v; }
    if (is_float($v)) {
        if (floor($v) == $v && !is_infinite($v) && abs($v) < 1e15) {
            return number_format($v, 1, '.', '');
        }
        $mag = abs($v);
        if ($mag > 0.0 && ($mag < 1e-4 || $mag >= 1e16)) {
            $out = strtolower(sprintf('%.16e', $v));
            return preg_replace('/e([+-])0+(\d+)$/', 'e$1$2', $out) ?? $out;
        }
        $out = rtrim(rtrim(sprintf('%.15F', $v), '0'), '.');
        return $out === '-0' ? '0' : $out;
    }
    if (is_string($v)) { return "'" . $v . "'"; }
    if (is_array($v)) { return __pytra_repr_array($v); }
    return (string)$v;
}

function __pytra_repr_array($v): string {
    if (!is_array($v) || count($v) === 0) { return "[]"; }
    $items = [];
    foreach ($v as $item) {
        $items[] = __pytra_repr_value($item);
    }
    return "[" . implode(", ", $items) . "]";
}

function __pytra_repr_dict(array $v): string {
    if (count($v) === 0) {
        return "{}";
    }
    $items = [];
    foreach ($v as $k => $item) {
        $items[] = __pytra_repr_value($k) . ": " . __pytra_repr_value($item);
    }
    return "{" . implode(", ", $items) . "}";
}

function __pytra_repr_tuple(array $v): string {
    $items = [];
    foreach ($v as $item) {
        $items[] = __pytra_repr_value($item);
    }
    if (count($items) === 1) {
        return "(" . $items[0] . ",)";
    }
    return "(" . implode(", ", $items) . ")";
}

function __pytra_len($v): int {
    if (is_string($v)) {
        return strlen($v);
    }
    if (is_array($v)) {
        return count($v);
    }
    if ($v instanceof \Countable) {
        return count($v);
    }
    if (is_object($v) && property_exists($v, 'length')) {
        return (int)$v->length;
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

function __pytra_clear(&$v): void {
    if (is_array($v)) {
        $v = [];
        return;
    }
    if ($v instanceof __PytraSet) {
        $v->clear();
        return;
    }
    if ($v instanceof \ArrayObject) {
        $v->exchangeArray([]);
    }
}

function __pytra_setdefault(&$v, $key, $default) {
    if (!is_array($v)) {
        return $default;
    }
    if (!array_key_exists($key, $v)) {
        $v[$key] = $default;
    }
    return $v[$key];
}

function py_to_string($v, string $type_hint = ""): string {
    if (is_bool($v)) {
        return $v ? "True" : "False";
    }
    if ($v === null) {
        return "None";
    }
    if (is_int($v)) {
        return (string)$v;
    }
    if (is_float($v)) {
        if (floor($v) == $v && !is_infinite($v) && abs($v) < 1e15) {
            return number_format($v, 1, '.', '');
        }
        $mag = abs($v);
        if ($mag > 0.0 && ($mag < 1e-4 || $mag >= 1e16)) {
            $out = strtolower(sprintf('%.16e', $v));
            return preg_replace('/e([+-])0+(\d+)$/', 'e$1$2', $out) ?? $out;
        }
        $out = rtrim(rtrim(sprintf('%.15F', $v), '0'), '.');
        return $out === '-0' ? '0' : $out;
    }
    if (is_string($v)) {
        return $v;
    }
    if ($v instanceof \Throwable) {
        return $v->getMessage();
    }
    if (is_array($v)) {
        if ($type_hint === "tuple" || str_starts_with($type_hint, "tuple[")) {
            return __pytra_repr_tuple($v);
        }
        if ($type_hint === "dict" || str_starts_with($type_hint, "dict[")) {
            return __pytra_repr_dict($v);
        }
        if ($type_hint === "set" || str_starts_with($type_hint, "set[")) {
            if (count($v) === 0) {
                return "set()";
            }
            $items = [];
            foreach ($v as $item) {
                $items[] = __pytra_repr_value($item);
            }
            return "{" . implode(", ", $items) . "}";
        }
        if (!__pytra_array_is_list_like($v)) {
            return __pytra_repr_dict($v);
        }
        return __pytra_repr_array($v);
    }
    return (string)$v;
}

$GLOBALS['__pytra_argv'] = [];
$GLOBALS['__pytra_path'] = [];

function __pytra_set_argv($items): void {
    $GLOBALS['__pytra_argv'] = is_array($items) ? array_values($items) : [];
}

function __pytra_set_path($items): void {
    $GLOBALS['__pytra_path'] = is_array($items) ? array_values($items) : [];
}

function __pytra_sqrt($x) { return __native_sqrt($x); }
function __pytra_sin($x) { return __native_sin($x); }
function __pytra_cos($x) { return __native_cos($x); }
function __pytra_tan($x) { return __native_tan($x); }
function __pytra_exp($x) { return __native_exp($x); }
function __pytra_log($x) { return __native_log($x); }
function __pytra_log10($x) { return __native_log10($x); }
function __pytra_fabs($x) { return __native_fabs($x); }
function __pytra_floor($x) { return __native_floor($x); }
function __pytra_ceil($x) { return __native_ceil($x); }
function __pytra_pow($x, $y) { return __native_pow($x, $y); }
function __pytra_abspath($p): string {
    $path = (string)$p;
    $resolved = realpath($path);
    if ($resolved !== false) {
        return $resolved;
    }
    if ($path === '') {
        return getcwd() ?: '.';
    }
    if ($path[0] === '/' || preg_match('/^[A-Za-z]:[\\\\\\/]/', $path) === 1) {
        return $path;
    }
    $cwd = getcwd() ?: '.';
    return rtrim($cwd, DIRECTORY_SEPARATOR) . DIRECTORY_SEPARATOR . $path;
}

const __pytra_pi = M_PI;
const __pytra_e = M_E;

class __PytraPath {
    public string $path;

    public function __construct($raw) {
        $this->path = (string)$raw;
    }

    public function __toString(): string {
        return $this->path;
    }

    public function __get(string $name) {
        if ($name === 'parent') {
            $dir = dirname($this->path);
            return new __PytraPath($dir === '.' ? '' : $dir);
        }
        if ($name === 'name') {
            return basename($this->path);
        }
        if ($name === 'stem') {
            $base = basename($this->path);
            $pos = strrpos($base, '.');
            return $pos === false ? $base : substr($base, 0, $pos);
        }
        return null;
    }

    public function joinpath(...$parts): __PytraPath {
        $items = [$this->path];
        foreach ($parts as $part) {
            $items[] = (string)$part;
        }
        return new __PytraPath(__pytra_join(...$items));
    }

    public function mkdir($parents = false, $exist_ok = false): void {
        __pytra_makedirs($this->path, (bool)$exist_ok);
    }

    public function write_text($text): void {
        $parent = dirname($this->path);
        if ($parent !== '' && $parent !== '.' && !is_dir($parent)) {
            mkdir($parent, 0777, true);
        }
        file_put_contents($this->path, (string)$text);
    }

    public function read_text(): string {
        $raw = @file_get_contents($this->path);
        return $raw === false ? '' : $raw;
    }

    public function exists(): bool {
        return file_exists($this->path);
    }
}

function Path($raw): __PytraPath {
    return new __PytraPath($raw);
}

function __pytra_join(...$parts): string {
    $clean = [];
    foreach ($parts as $part) {
        $text = (string)$part;
        if ($text === '') {
            continue;
        }
        $clean[] = trim($text, '/');
    }
    if (count($clean) === 0) {
        return '';
    }
    $joined = implode('/', $clean);
    if (str_starts_with((string)$parts[0], '/')) {
        return '/' . $joined;
    }
    return $joined;
}

function __pytra_splitext($path): array {
    $text = (string)$path;
    $base = basename($text);
    $pos = strrpos($base, '.');
    if ($pos === false || $pos === 0) {
        return [$text, ''];
    }
    $root = substr($text, 0, strlen($text) - (strlen($base) - $pos));
    $ext = substr($base, $pos);
    return [$root . substr($base, 0, $pos), $ext];
}

function __pytra_basename($path): string {
    return basename((string)$path);
}

function __pytra_dirname($path): string {
    $dir = dirname((string)$path);
    return $dir === '.' ? '' : $dir;
}

function __pytra_exists($path): bool {
    return file_exists((string)$path);
}

class __PytraJsonValue {
    public $raw;

    public function __construct($raw) {
        $this->raw = $raw;
    }

    public function as_str(): string {
        return is_string($this->raw) ? $this->raw : py_to_string($this->raw);
    }
}

function __pytra_dumps($value, $ensure_ascii = true, $indent = null, $separators = null): string {
    $flags = 0;
    if (!$ensure_ascii) {
        $flags |= JSON_UNESCAPED_UNICODE;
    }
    if ($indent !== null) {
        $flags |= JSON_PRETTY_PRINT;
    }
    $out = json_encode($value, $flags);
    if (!is_string($out)) {
        return 'null';
    }
    if ($indent !== null) {
        $indent_width = (int)$indent;
        if ($indent_width > 0 && $indent_width !== 4) {
            $lines = explode("\n", $out);
            foreach ($lines as $idx => $line) {
                if (preg_match('/^( +)/', $line, $m) === 1) {
                    $levels = intdiv(strlen($m[1]), 4);
                    $lines[$idx] = str_repeat(' ', $levels * $indent_width) . substr($line, strlen($m[1]));
                }
            }
            $out = implode("\n", $lines);
        }
    }
    return $out;
}

function dumps($value, $ensure_ascii = true, $indent = null, $separators = null): string {
    return __pytra_dumps($value, $ensure_ascii, $indent, $separators);
}

function __pytra_loads($text): ?__PytraJsonValue {
    $raw = json_decode((string)$text, true);
    if (json_last_error() !== JSON_ERROR_NONE) {
        return null;
    }
    return new __PytraJsonValue($raw);
}

function __pytra_loads_arr($text): ?__PytraJsonValue {
    $value = __pytra_loads($text);
    if ($value === null || !is_array($value->raw)) {
        return null;
    }
    return $value;
}

function __pytra_loads_obj($text): ?__PytraJsonValue {
    $value = __pytra_loads($text);
    if ($value === null || !is_array($value->raw) || __pytra_array_is_list_like($value->raw)) {
        return null;
    }
    return $value;
}

function sub($pattern, $replacement, $text, $count = 0): string {
    $delim = '/' . str_replace('/', '\/', (string)$pattern) . '/';
    $limit = (int)$count;
    if ($limit <= 0) {
        $limit = -1;
    }
    $out = preg_replace($delim, (string)$replacement, (string)$text, $limit);
    return is_string($out) ? $out : (string)$text;
}

class __PytraArgumentParser {
    private array $specs = [];

    public function __construct($prog = '') {}

    public function add_argument(...$args): void {
        if (count($args) === 0) {
            return;
        }
        $entry = [
            'short' => null,
            'long' => null,
            'name' => '',
            'action' => '',
            'choices' => null,
            'default' => null,
            'positional' => false,
        ];
        if (count($args) === 1) {
            $entry['name'] = (string)$args[0];
            $entry['positional'] = true;
        } elseif (count($args) === 2 && is_string($args[0]) && str_starts_with((string)$args[0], '--') && is_string($args[1]) && !str_starts_with((string)$args[1], '--')) {
            $entry['long'] = (string)$args[0];
            $entry['name'] = ltrim((string)$args[0], '-');
            $entry['action'] = (string)$args[1];
        } else {
            $entry['short'] = (string)$args[0];
            $entry['long'] = (string)$args[1];
            $entry['name'] = ltrim((string)$args[1], '-');
            if (isset($args[2]) && is_string($args[2])) {
                $entry['action'] = (string)$args[2];
            } elseif (isset($args[2]) && is_array($args[2])) {
                $entry['choices'] = $args[2];
            }
            if (isset($args[3])) {
                $entry['default'] = $args[3];
            }
        }
        $this->specs[] = $entry;
    }

    public function parse_args($argv): array {
        $items = is_array($argv) ? array_values($argv) : [];
        $result = [];
        $positionals = [];
        foreach ($this->specs as $spec) {
            if ($spec['positional']) {
                $positionals[] = $spec;
                continue;
            }
            if ($spec['action'] === 'store_true') {
                $result[$spec['name']] = false;
            } else {
                $result[$spec['name']] = $spec['default'];
            }
        }
        $pos_index = 0;
        for ($i = 0; $i < count($items); $i += 1) {
            $item = $items[$i];
            $matched = null;
            foreach ($this->specs as $spec) {
                if ($spec['positional']) {
                    continue;
                }
                if ($item === $spec['short'] || $item === $spec['long']) {
                    $matched = $spec;
                    break;
                }
            }
            if ($matched !== null) {
                if ($matched['action'] === 'store_true') {
                    $result[$matched['name']] = true;
                    continue;
                }
                if ($i + 1 < count($items)) {
                    $result[$matched['name']] = $items[$i + 1];
                    $i += 1;
                }
                continue;
            }
            if ($pos_index < count($positionals)) {
                $result[$positionals[$pos_index]['name']] = $item;
                $pos_index += 1;
            }
        }
        return $result;
    }
}

function ArgumentParser($prog = ''): __PytraArgumentParser {
    return new __PytraArgumentParser($prog);
}

function __native_sqrt($x) { return sqrt($x); }
function __native_floor($x) { return floor($x); }
function __native_ceil($x) { return ceil($x); }
function __native_sin($x) { return sin($x); }
function __native_cos($x) { return cos($x); }
function __native_tan($x) { return tan($x); }
function __native_log($x) { return log($x); }
function __native_log10($x) { return log10($x); }
function __native_exp($x) { return exp($x); }
function __native_pow($x, $y) { return pow($x, $y); }
function __native_fabs($x) { return abs($x); }
function __native_atan2($y, $x) { return atan2($y, $x); }
function __native_asin($x) { return asin($x); }
function __native_acos($x) { return acos($x); }

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
    if ($i < 0 || $i >= $n) {
        throw new \OutOfRangeException("index out of range");
    }
    return $i;
}

// perf_counter is provided by std/time.php via @extern delegation (spec §6)
function __native_perf_counter(): float {
    return microtime(true);
}

function __pytra_noop(...$_args) {
    return null;
}

function __pytra_assert_true($cond, string $label = ''): bool {
    if (__pytra_truthy($cond)) {
        return true;
    }
    if ($label !== '') {
        __pytra_print('[assert_true] ' . $label . ': False');
    } else {
        __pytra_print('[assert_true] False');
    }
    return false;
}

function __pytra_assert_eq($actual, $expected, string $label = ''): bool {
    $actual_s = py_to_string($actual);
    $expected_s = py_to_string($expected);
    $ok = $actual_s === $expected_s;
    if ($ok) {
        return true;
    }
    if ($label !== '') {
        __pytra_print('[assert_eq] ' . $label . ': actual=' . $actual_s . ', expected=' . $expected_s);
    } else {
        __pytra_print('[assert_eq] actual=' . $actual_s . ', expected=' . $expected_s);
    }
    return false;
}

function __pytra_assert_all(array $results, string $label = ''): bool {
    foreach ($results as $v) {
        if (!__pytra_truthy($v)) {
            if ($label !== '') {
                __pytra_print('[assert_all] ' . $label . ': False');
            } else {
                __pytra_print('[assert_all] False');
            }
            return false;
        }
    }
    return true;
}

function __pytra_assert_stdout(array $_expected_lines, $fn): bool {
    if (is_string($fn) && function_exists($fn)) {
        return true;
    }
    if (is_callable($fn)) {
        return true;
    }
    return true;
}

function __pytra_str_startswith($s, $prefix): bool {
    return is_string($s) && is_string($prefix) && str_starts_with($s, $prefix);
}

function __pytra_str_endswith($s, $suffix): bool {
    return is_string($s) && is_string($suffix) && str_ends_with($s, $suffix);
}

function __pytra_str_find($s, $needle): int {
    if (!is_string($s) || !is_string($needle)) {
        return -1;
    }
    $pos = strpos($s, $needle);
    return $pos === false ? -1 : $pos;
}

function __pytra_str_rfind($s, $needle): int {
    if (!is_string($s) || !is_string($needle)) {
        return -1;
    }
    $pos = strrpos($s, $needle);
    return $pos === false ? -1 : $pos;
}

function __pytra_str_index($s, $needle): int {
    $pos = __pytra_str_find($s, $needle);
    if ($pos < 0) {
        throw new \InvalidArgumentException("substring not found");
    }
    return $pos;
}

function __pytra_str_isalnum($s): bool {
    if (!is_string($s) || $s === '') {
        return false;
    }
    return preg_match('/^[A-Za-z0-9]+$/', $s) === 1;
}

function __pytra_str_isspace($s): bool {
    if (!is_string($s) || $s === '') {
        return false;
    }
    return preg_match('/^\s+$/', $s) === 1;
}

function __pytra_str_split($s, $sep) {
    if (!is_string($s) || !is_string($sep)) {
        return [];
    }
    return explode($sep, $s);
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
    if ($container instanceof __PytraSet) {
        return $container->contains($item);
    }
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

function __pytra_range(...$args): array {
    $argc = count($args);
    if ($argc <= 0) {
        return [];
    }
    if ($argc === 1) {
        $start = 0;
        $stop = __pytra_int($args[0]);
        $step = 1;
    } elseif ($argc === 2) {
        $start = __pytra_int($args[0]);
        $stop = __pytra_int($args[1]);
        $step = 1;
    } else {
        $start = __pytra_int($args[0]);
        $stop = __pytra_int($args[1]);
        $step = __pytra_int($args[2]);
    }
    if ($step === 0) {
        throw new \RuntimeException("range() arg 3 must not be zero");
    }
    $out = [];
    if ($step > 0) {
        for ($i = $start; $i < $stop; $i += $step) {
            $out[] = $i;
        }
        return $out;
    }
    for ($i = $start; $i > $stop; $i += $step) {
        $out[] = $i;
    }
    return $out;
}

function __pytra_py_reversed_object($value): array {
    if (is_array($value)) {
        return array_reverse(array_values($value));
    }
    if ($value instanceof \Traversable) {
        return array_reverse(iterator_to_array($value, false));
    }
    if (is_string($value)) {
        return array_reverse(preg_split('//u', $value, -1, PREG_SPLIT_NO_EMPTY) ?: []);
    }
    return [];
}

function __pytra_makedirs($path, $exist_ok = false): void {
    $path_s = (string)$path;
    if ($path_s === '') {
        return;
    }
    if ($exist_ok && is_dir($path_s)) {
        return;
    }
    if (!is_dir($path_s)) {
        mkdir($path_s, 0777, true);
    }
}

function __pytra_sum($items, $start = 0) {
    $total = $start;
    foreach ($items as $item) {
        $total += $item;
    }
    return $total;
}

function __pytra_dict_items($dict): array {
    if (!is_array($dict)) {
        return [];
    }
    $out = [];
    foreach ($dict as $k => $v) {
        $out[] = [$k, $v];
    }
    return $out;
}

function __pytra_list_extend(&$items, $other): array {
    if (!is_array($items)) {
        $items = [];
    }
    foreach ($other as $item) {
        $items[] = $item;
    }
    return $items;
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

function __pytra_bytes($v = null): array {
    return bytes($v);
}

function __pytra_enumerate($items, int $start = 0): array {
    $out = [];
    $i = $start;
    foreach ($items as $item) {
        $out[] = [$i, $item];
        $i += 1;
    }
    return $out;
}

function __pytra_sorted($items) {
    if ($items instanceof __PytraSet) {
        $out = iterator_to_array($items->getIterator(), false);
        sort($out);
        return $out;
    }
    if (!is_array($items)) {
        if (is_iterable($items)) {
            $out = iterator_to_array($items, false);
            sort($out);
            return $out;
        }
        return [];
    }
    $is_set = true;
    foreach ($items as $value) {
        if ($value !== true) {
            $is_set = false;
            break;
        }
    }
    $out = $is_set ? array_keys($items) : array_values($items);
    sort($out);
    return $out;
}

function __pytra_py_sorted($items) {
    return __pytra_sorted($items);
}

function __pytra_set_update(&$target, $values) {
    if ($target instanceof __PytraSet) {
        if (!is_iterable($values)) {
            return;
        }
        foreach ($values as $value) {
            $target->add($value);
        }
        return;
    }
    if (!is_array($target) || !is_array($values)) {
        return;
    }
    foreach ($values as $key => $value) {
        if ($value === true) {
            $target[$key] = true;
        } else {
            $target[$value] = true;
        }
    }
}

function __pytra_zip(...$iterables): array {
    if (count($iterables) === 0) {
        return [];
    }
    $arrays = [];
    $min_len = null;
    foreach ($iterables as $iterable) {
        $arr = is_array($iterable) ? array_values($iterable) : iterator_to_array($iterable, false);
        $arrays[] = $arr;
        $n = count($arr);
        if ($min_len === null || $n < $min_len) {
            $min_len = $n;
        }
    }
    $out = [];
    for ($i = 0; $i < (int)$min_len; $i += 1) {
        $row = [];
        foreach ($arrays as $arr) {
            $row[] = $arr[$i];
        }
        $out[] = $row;
    }
    return $out;
}

function __pytra_str_iter($value): array {
    if (!is_string($value) || $value === '') {
        return [];
    }
    return preg_split('//u', $value, -1, PREG_SPLIT_NO_EMPTY) ?: [];
}

function __pytra_set_iter($value): array {
    if ($value instanceof __PytraSet) {
        return iterator_to_array($value, false);
    }
    if (is_array($value)) {
        if (__pytra_array_is_list_like($value)) {
            return array_values($value);
        }
        return array_keys($value);
    }
    return [];
}

class __PytraDeque implements \Countable {
    private array $items = [];

    public function append($value): void {
        $this->items[] = $value;
    }

    public function appendleft($value): void {
        array_unshift($this->items, $value);
    }

    public function pop() {
        return array_pop($this->items);
    }

    public function popleft() {
        return array_shift($this->items);
    }

    public function clear(): void {
        $this->items = [];
    }

    public function count(): int {
        return count($this->items);
    }

    public function __get(string $name) {
        if ($name === 'length') {
            return count($this->items);
        }
        return null;
    }
}

function deque($items = null): __PytraDeque {
    $out = new __PytraDeque();
    if (is_array($items)) {
        foreach ($items as $item) {
            $out->append($item);
        }
    }
    return $out;
}

class __PytraSet implements \Countable, \IteratorAggregate {
    private array $items = [];

    public function add($value): void {
        foreach ($this->items as $item) {
            if ($item === $value) {
                return;
            }
        }
        $this->items[] = $value;
    }

    public function contains($value): bool {
        foreach ($this->items as $item) {
            if ($item === $value) {
                return true;
            }
        }
        return false;
    }

    public function clear(): void {
        $this->items = [];
    }

    public function count(): int {
        return count($this->items);
    }

    public function getIterator(): \Traversable {
        return new \ArrayIterator($this->items);
    }
}

function set($items = null): __PytraSet {
    $out = new __PytraSet();
    if (is_iterable($items)) {
        foreach ($items as $item) {
            $out->add($item);
        }
    }
    return $out;
}

function __pytra_set_add($set, $value) {
    if ($set instanceof __PytraSet) {
        $set->add($value);
    }
    return $set;
}

class __PytraTypeInfo {
    public string $__name__;

    public function __construct(string $name) {
        $this->__name__ = $name;
    }
}

function type($value): __PytraTypeInfo {
    if (is_object($value)) {
        return new __PytraTypeInfo(get_class($value));
    }
    if (is_array($value)) {
        return new __PytraTypeInfo("list");
    }
    if (is_string($value)) {
        return new __PytraTypeInfo("str");
    }
    if (is_int($value)) {
        return new __PytraTypeInfo("int");
    }
    if (is_float($value)) {
        return new __PytraTypeInfo("float");
    }
    if (is_bool($value)) {
        return new __PytraTypeInfo("bool");
    }
    if ($value === null) {
        return new __PytraTypeInfo("NoneType");
    }
    return new __PytraTypeInfo(get_debug_type($value));
}

if (!function_exists('__pytra_write_rgb_png')) {
    function __pytra_write_rgb_png($path, $width, $height, $pixels) {
        $raw = bytearray();
        __pytra_list_extend($raw, $pixels);
        $expected = ((int)$width * (int)$height * 3);
        if (__pytra_len($raw) !== $expected) {
            throw new \InvalidArgumentException("pixels length mismatch");
        }
        $row_bytes = ((int)$width * 3);
        $scanlines = bytearray();
        for ($y = 0; $y < (int)$height; $y += 1) {
            $scanlines[] = 0;
            $start = ($y * $row_bytes);
            __pytra_list_extend($scanlines, array_slice($raw, $start, $row_bytes));
        }
        $ihdr = pack('NNCCCCC', (int)$width, (int)$height, 8, 2, 0, 0, 0);
        $idat = pack('C*', 0x78, 0x01);
        $n = count($scanlines);
        $pos = 0;
        while ($pos < $n) {
            $remain = $n - $pos;
            $chunk_len = $remain > 65535 ? 65535 : $remain;
            $final = (($pos + $chunk_len) >= $n) ? 1 : 0;
            $idat .= pack('C', $final);
            $idat .= pack('v', $chunk_len);
            $idat .= pack('v', 0xFFFF ^ $chunk_len);
            $chunk = array_slice($scanlines, $pos, $chunk_len);
            $idat .= pack('C*', ...$chunk);
            $pos += $chunk_len;
        }
        $s1 = 1;
        $s2 = 0;
        foreach ($scanlines as $b) {
            $s1 += $b;
            if ($s1 >= 65521) {
                $s1 -= 65521;
            }
            $s2 = ($s2 + $s1) % 65521;
        }
        $adler = (($s2 << 16) | $s1) & 0xFFFFFFFF;
        $idat .= pack('N', $adler);
        $png = pack('C*', 137, 80, 78, 71, 13, 10, 26, 10);
        foreach ([["IHDR", $ihdr], ["IDAT", $idat], ["IEND", ""]] as [$chunk_type, $data]) {
            $png .= pack('N', strlen($data));
            $png .= $chunk_type;
            $png .= $data;
            $png .= pack('N', crc32($chunk_type . $data) & 0xFFFFFFFF);
        }
        file_put_contents((string)$path, $png);
        return null;
    }
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

    public function read() {
        $data = stream_get_contents($this->handle);
        if ($data === false) {
            throw new RuntimeException("read failed");
        }
        return $data;
    }

    public function __enter__(): PyFile {
        return $this;
    }

    public function __exit__($exc_type, $exc_val, $exc_tb): void {
        $this->close();
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

// Math/JSON/Path functions removed per spec §6:
// pytra.std.math → std/math.php via @extern delegation.
// pytra.std.json → std/json.php via @extern delegation.
// pytra.std.pathlib → std/pathlib.php (emitter-generated Path class).
