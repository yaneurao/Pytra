<?php
// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/string_ops.py
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

function _is_space($ch) {
    return (($ch == " ") || ($ch == "	") || ($ch == "\n") || ($ch == "\r"));
}

function _contains_char($chars, $ch) {
    $i = 0;
    $n = __pytra_len($chars);
    while (($i < $n)) {
        if (($chars[$i] == $ch)) {
            return true;
        }
        $i += 1;
    }
    return false;
}

function _normalize_index($idx, $n) {
    $out = $idx;
    if (($out < 0)) {
        $out += $n;
    }
    if (($out < 0)) {
        $out = 0;
    }
    if (($out > $n)) {
        $out = $n;
    }
    return $out;
}

function py_join($sep, $parts) {
    $n = __pytra_len($parts);
    if (($n == 0)) {
        return "";
    }
    $out = "";
    $i = 0;
    while (($i < $n)) {
        if (($i > 0)) {
            $out .= $sep;
        }
        $out .= $parts[__pytra_index($parts, $i)];
        $i += 1;
    }
    return $out;
}

function py_split($s, $sep, $maxsplit) {
    $out = [];
    if (($sep == "")) {
        $out[] = $s;
        return $out;
    }
    $pos = 0;
    $splits = 0;
    $n = __pytra_len($s);
    $m = __pytra_len($sep);
    $unlimited = ($maxsplit < 0);
    while (true) {
        if (((!$unlimited) && ($splits >= $maxsplit))) {
            break;
        }
        $at = py_find_window($s, $sep, $pos, $n);
        if (($at < 0)) {
            break;
        }
        $out[] = __pytra_str_slice($s, $pos, $at);
        $pos = ($at + $m);
        $splits += 1;
    }
    $out[] = __pytra_str_slice($s, $pos, $n);
    return $out;
}

function py_splitlines($s) {
    $out = [];
    $n = __pytra_len($s);
    $start = 0;
    $i = 0;
    while (($i < $n)) {
        $ch = $s[$i];
        if ((($ch == "\n") || ($ch == "\r"))) {
            $out[] = __pytra_str_slice($s, $start, $i);
            if ((($ch == "\r") && (($i + 1) < $n) && ($s[($i + 1)] == "\n"))) {
                $i += 1;
            }
            $i += 1;
            $start = $i;
            continue;
        }
        $i += 1;
    }
    if (($start < $n)) {
        $out[] = __pytra_str_slice($s, $start, $n);
    } else {
        if (($n > 0)) {
            $last = $s[($n - 1)];
            if ((($last == "\n") || ($last == "\r"))) {
                $out[] = "";
            }
        }
    }
    return $out;
}

function py_count($s, $needle) {
    if (($needle == "")) {
        return (__pytra_len($s) + 1);
    }
    $out = 0;
    $pos = 0;
    $n = __pytra_len($s);
    $m = __pytra_len($needle);
    while (true) {
        $at = py_find_window($s, $needle, $pos, $n);
        if (($at < 0)) {
            return $out;
        }
        $out += 1;
        $pos = ($at + $m);
    }
}

function py_lstrip($s) {
    $i = 0;
    $n = __pytra_len($s);
    while ((($i < $n) && _is_space($s[$i]))) {
        $i += 1;
    }
    return __pytra_str_slice($s, $i, $n);
}

function py_lstrip_chars($s, $chars) {
    $i = 0;
    $n = __pytra_len($s);
    while ((($i < $n) && _contains_char($chars, $s[$i]))) {
        $i += 1;
    }
    return __pytra_str_slice($s, $i, $n);
}

function py_rstrip($s) {
    $n = __pytra_len($s);
    $i = ($n - 1);
    while ((($i >= 0) && _is_space($s[$i]))) {
        $i -= 1;
    }
    return __pytra_str_slice($s, 0, ($i + 1));
}

function py_rstrip_chars($s, $chars) {
    $n = __pytra_len($s);
    $i = ($n - 1);
    while ((($i >= 0) && _contains_char($chars, $s[$i]))) {
        $i -= 1;
    }
    return __pytra_str_slice($s, 0, ($i + 1));
}

function py_strip($s) {
    return py_rstrip(py_lstrip($s));
}

function py_strip_chars($s, $chars) {
    return py_rstrip_chars(py_lstrip_chars($s, $chars), $chars);
}

function py_startswith($s, $prefix) {
    $n = __pytra_len($s);
    $m = __pytra_len($prefix);
    if (($m > $n)) {
        return false;
    }
    $i = 0;
    while (($i < $m)) {
        if (($s[$i] != $prefix[$i])) {
            return false;
        }
        $i += 1;
    }
    return true;
}

function py_endswith($s, $suffix) {
    $n = __pytra_len($s);
    $m = __pytra_len($suffix);
    if (($m > $n)) {
        return false;
    }
    $i = 0;
    $base = ($n - $m);
    while (($i < $m)) {
        if (($s[($base + $i)] != $suffix[$i])) {
            return false;
        }
        $i += 1;
    }
    return true;
}

function py_find($s, $needle) {
    return py_find_window($s, $needle, 0, __pytra_len($s));
}

function py_find_window($s, $needle, $start, $end) {
    $n = __pytra_len($s);
    $m = __pytra_len($needle);
    $lo = _normalize_index($start, $n);
    $up = _normalize_index($end, $n);
    if (($up < $lo)) {
        return (-1);
    }
    if (($m == 0)) {
        return $lo;
    }
    $i = $lo;
    $last = ($up - $m);
    while (($i <= $last)) {
        $j = 0;
        $ok = true;
        while (($j < $m)) {
            if (($s[($i + $j)] != $needle[$j])) {
                $ok = false;
                break;
            }
            $j += 1;
        }
        if ($ok) {
            return $i;
        }
        $i += 1;
    }
    return (-1);
}

function py_rfind($s, $needle) {
    return py_rfind_window($s, $needle, 0, __pytra_len($s));
}

function py_rfind_window($s, $needle, $start, $end) {
    $n = __pytra_len($s);
    $m = __pytra_len($needle);
    $lo = _normalize_index($start, $n);
    $up = _normalize_index($end, $n);
    if (($up < $lo)) {
        return (-1);
    }
    if (($m == 0)) {
        return $up;
    }
    $i = ($up - $m);
    while (($i >= $lo)) {
        $j = 0;
        $ok = true;
        while (($j < $m)) {
            if (($s[($i + $j)] != $needle[$j])) {
                $ok = false;
                break;
            }
            $j += 1;
        }
        if ($ok) {
            return $i;
        }
        $i -= 1;
    }
    return (-1);
}

function py_replace($s, $oldv, $newv) {
    if (($oldv == "")) {
        return $s;
    }
    $out = "";
    $n = __pytra_len($s);
    $m = __pytra_len($oldv);
    $i = 0;
    while (($i < $n)) {
        if (((($i + $m) <= $n) && (py_find_window($s, $oldv, $i, ($i + $m)) == $i))) {
            $out .= $newv;
            $i += $m;
        } else {
            $out .= $s[$i];
            $i += 1;
        }
    }
    return $out;
}
