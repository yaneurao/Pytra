<?php
// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/json.py
// generated-by: tools/gen_runtime_from_manifest.py

declare(strict_types=1);

$__pytra_runtime_candidates = [
    dirname(__DIR__) . '/py_runtime.php',
    dirname(__DIR__, 2) . '/native/built_in/py_runtime.php',
];
foreach ($__pytra_runtime_candidates as $__pytra_runtime_path) {
    if (is_file($__pytra_runtime_path)) {
        require_once $__pytra_runtime_path;
        break;
    }
}
if (!function_exists('__pytra_len')) {
    throw new RuntimeException('py_runtime.php not found for generated PHP runtime lane');
}

function _pytra_json_is_object_value($value): bool {
    if (is_object($value)) {
        return true;
    }
    return is_array($value) && !__pytra_array_is_list_like($value);
}

function _pytra_json_is_array_value($value): bool {
    return is_array($value) && __pytra_array_is_list_like($value);
}

function _pytra_json_object_raw($value): object {
    if (is_object($value)) {
        return $value;
    }
    if (is_array($value) && !__pytra_array_is_list_like($value)) {
        return (object)$value;
    }
    return (object)[];
}

function _pytra_json_object_props($value): array {
    $props = get_object_vars(_pytra_json_object_raw($value));
    return is_array($props) ? $props : [];
}

function _pytra_json_array_raw($value): array {
    if (is_array($value) && __pytra_array_is_list_like($value)) {
        return array_values($value);
    }
    return [];
}

function _pytra_json_unwrap($value) {
    if ($value instanceof JsonValue || $value instanceof JsonObj || $value instanceof JsonArr) {
        return $value->raw;
    }
    return $value;
}

function _pytra_json_normalize_indent($indent): ?int {
    if ($indent === null) {
        return null;
    }
    $value = (int)$indent;
    return $value < 0 ? 0 : $value;
}

function _pytra_json_repeat_indent(int $indent, int $level): string {
    return str_repeat(" ", $indent * $level);
}

function _pytra_json_escape_string(string $text, bool $ensure_ascii): string {
    $flags = JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR;
    if (!$ensure_ascii) {
        $flags |= JSON_UNESCAPED_UNICODE;
    }
    $encoded = json_encode($text, $flags);
    if (!is_string($encoded)) {
        throw new RuntimeException('json string encoding failed');
    }
    return $encoded;
}

function _pytra_json_number_text($value): string {
    if (is_int($value)) {
        return (string)$value;
    }
    $encoded = json_encode($value, JSON_PRESERVE_ZERO_FRACTION | JSON_THROW_ON_ERROR);
    if (!is_string($encoded)) {
        throw new RuntimeException('json number encoding failed');
    }
    return $encoded;
}

class JsonObj {
    public object $raw;

    public function __construct($raw) {
        $this->raw = _pytra_json_object_raw($raw);
    }

    public function get(string $key): ?JsonValue {
        $props = _pytra_json_object_props($this->raw);
        if (!array_key_exists($key, $props)) {
            return null;
        }
        return new JsonValue($props[$key]);
    }

    public function get_obj(string $key): ?JsonObj {
        $value = $this->get($key);
        return $value === null ? null : $value->as_obj();
    }

    public function get_arr(string $key): ?JsonArr {
        $value = $this->get($key);
        return $value === null ? null : $value->as_arr();
    }

    public function get_str(string $key): ?string {
        $value = $this->get($key);
        return $value === null ? null : $value->as_str();
    }

    public function get_int(string $key): ?int {
        $value = $this->get($key);
        return $value === null ? null : $value->as_int();
    }

    public function get_float(string $key): ?float {
        $value = $this->get($key);
        return $value === null ? null : $value->as_float();
    }

    public function get_bool(string $key): ?bool {
        $value = $this->get($key);
        return $value === null ? null : $value->as_bool();
    }
}

class JsonArr {
    public array $raw;

    public function __construct($raw) {
        $this->raw = _pytra_json_array_raw($raw);
    }

    public function get(int $index): ?JsonValue {
        if ($index < 0 || !array_key_exists($index, $this->raw)) {
            return null;
        }
        return new JsonValue($this->raw[$index]);
    }

    public function get_obj(int $index): ?JsonObj {
        $value = $this->get($index);
        return $value === null ? null : $value->as_obj();
    }

    public function get_arr(int $index): ?JsonArr {
        $value = $this->get($index);
        return $value === null ? null : $value->as_arr();
    }

    public function get_str(int $index): ?string {
        $value = $this->get($index);
        return $value === null ? null : $value->as_str();
    }

    public function get_int(int $index): ?int {
        $value = $this->get($index);
        return $value === null ? null : $value->as_int();
    }

    public function get_float(int $index): ?float {
        $value = $this->get($index);
        return $value === null ? null : $value->as_float();
    }

    public function get_bool(int $index): ?bool {
        $value = $this->get($index);
        return $value === null ? null : $value->as_bool();
    }
}

class JsonValue {
    public $raw;

    public function __construct($raw) {
        $this->raw = $raw;
    }

    public function as_obj(): ?JsonObj {
        return _pytra_json_is_object_value($this->raw) ? new JsonObj($this->raw) : null;
    }

    public function as_arr(): ?JsonArr {
        return _pytra_json_is_array_value($this->raw) ? new JsonArr($this->raw) : null;
    }

    public function as_str(): ?string {
        return is_string($this->raw) ? $this->raw : null;
    }

    public function as_int(): ?int {
        if (is_bool($this->raw)) {
            return null;
        }
        return is_int($this->raw) ? $this->raw : null;
    }

    public function as_float(): ?float {
        return is_float($this->raw) ? $this->raw : null;
    }

    public function as_bool(): ?bool {
        return is_bool($this->raw) ? $this->raw : null;
    }
}

function loads(string $text) {
    return json_decode((string)$text, false, 512, JSON_THROW_ON_ERROR);
}

function loads_obj(string $text): ?JsonObj {
    $value = loads($text);
    return _pytra_json_is_object_value($value) ? new JsonObj($value) : null;
}

function loads_arr(string $text): ?JsonArr {
    $value = loads($text);
    return _pytra_json_is_array_value($value) ? new JsonArr($value) : null;
}

function _pytra_json_dump_list(array $values, bool $ensure_ascii, ?int $indent, string $item_sep, string $key_sep, int $level): string {
    if (count($values) === 0) {
        return '[]';
    }
    if ($indent === null) {
        $parts = [];
        foreach ($values as $item) {
            $parts[] = _pytra_json_dump_value($item, $ensure_ascii, $indent, $item_sep, $key_sep, $level);
        }
        return '[' . implode($item_sep, $parts) . ']';
    }
    $indent_i = _pytra_json_normalize_indent($indent);
    $parts = [];
    foreach ($values as $item) {
        $parts[] = _pytra_json_repeat_indent($indent_i, $level + 1) . _pytra_json_dump_value($item, $ensure_ascii, $indent_i, $item_sep, $key_sep, $level + 1);
    }
    return "[\n" . implode(",\n", $parts) . "\n" . _pytra_json_repeat_indent($indent_i, $level) . ']';
}

function _pytra_json_dump_dict($values, bool $ensure_ascii, ?int $indent, string $item_sep, string $key_sep, int $level): string {
    $props = _pytra_json_object_props($values);
    if (count($props) === 0) {
        return '{}';
    }
    if ($indent === null) {
        $parts = [];
        foreach ($props as $key => $item) {
            $parts[] = _pytra_json_escape_string((string)$key, $ensure_ascii) . $key_sep . _pytra_json_dump_value($item, $ensure_ascii, $indent, $item_sep, $key_sep, $level);
        }
        return '{' . implode($item_sep, $parts) . '}';
    }
    $indent_i = _pytra_json_normalize_indent($indent);
    $parts = [];
    foreach ($props as $key => $item) {
        $parts[] = _pytra_json_repeat_indent($indent_i, $level + 1) . _pytra_json_escape_string((string)$key, $ensure_ascii) . $key_sep . _pytra_json_dump_value($item, $ensure_ascii, $indent_i, $item_sep, $key_sep, $level + 1);
    }
    return "{\n" . implode(",\n", $parts) . "\n" . _pytra_json_repeat_indent($indent_i, $level) . '}';
}

function _pytra_json_dump_value($value, bool $ensure_ascii, ?int $indent, string $item_sep, string $key_sep, int $level): string {
    $value = _pytra_json_unwrap($value);
    if ($value === null) {
        return 'null';
    }
    if (is_bool($value)) {
        return $value ? 'true' : 'false';
    }
    if (is_int($value) || is_float($value)) {
        return _pytra_json_number_text($value);
    }
    if (is_string($value)) {
        return _pytra_json_escape_string($value, $ensure_ascii);
    }
    if (_pytra_json_is_array_value($value)) {
        return _pytra_json_dump_list(_pytra_json_array_raw($value), $ensure_ascii, $indent, $item_sep, $key_sep, $level);
    }
    if (_pytra_json_is_object_value($value)) {
        return _pytra_json_dump_dict($value, $ensure_ascii, $indent, $item_sep, $key_sep, $level);
    }
    throw new TypeError('json.dumps unsupported type');
}

function dumps($obj, bool $ensure_ascii = true, $indent = null, $separators = null): string {
    $indent_value = _pytra_json_normalize_indent($indent);
    $item_sep = ',';
    $key_sep = $indent_value === null ? ':' : ': ';
    if (is_array($separators) && count($separators) >= 2) {
        $item_sep = (string)$separators[0];
        $key_sep = (string)$separators[1];
    }
    return _pytra_json_dump_value($obj, $ensure_ascii, $indent_value, $item_sep, $key_sep, 0);
}
