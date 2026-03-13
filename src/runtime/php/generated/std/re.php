<?php
// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/re.py
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

class Match_ {
    public function __construct($text, $groups) {
        $this->_text = $text;
        $this->_groups = $groups;
    }

    public function group($idx) {
        if (($idx == 0)) {
            return $this->_text;
        }
        if ((($idx < 0) || ($idx > __pytra_len($this->_groups)))) {
            throw new Exception(strval(IndexError("group index out of range")));
        }
        return $this->_groups[__pytra_index($this->_groups, ($idx - 1))];
    }
}

function group($m, $idx) {
    if (($m == null)) {
        return "";
    }
    $mm = $m;
    return $mm->group($idx);
}

function strip_group($m, $idx) {
    return group($m, $idx)->strip();
}

function _is_ident($s) {
    if (($s == "")) {
        return false;
    }
    $h = __pytra_str_slice($s, 0, 1);
    $is_head_alpha = ((("a" <= $h) && ($h <= "z")) || (("A" <= $h) && ($h <= "Z")));
    if ((!($is_head_alpha || ($h == "_")))) {
        return false;
    }
    foreach (__pytra_str_slice($s, 1, __pytra_len($s)) as $ch) {
        $is_alpha = ((("a" <= $ch) && ($ch <= "z")) || (("A" <= $ch) && ($ch <= "Z")));
        $is_digit = (("0" <= $ch) && ($ch <= "9"));
        if ((!($is_alpha || $is_digit || ($ch == "_")))) {
            return false;
        }
    }
    return true;
}

function _is_dotted_ident($s) {
    if (($s == "")) {
        return false;
    }
    $part = "";
    foreach ($s as $ch) {
        if (($ch == ".")) {
            if ((!_is_ident($part))) {
                return false;
            }
            $part = "";
            continue;
        }
        $part .= $ch;
    }
    if ((!_is_ident($part))) {
        return false;
    }
    if (($part == "")) {
        return false;
    }
    return true;
}

function _strip_suffix_colon($s) {
    $t = $s->rstrip();
    if ((__pytra_len($t) == 0)) {
        return "";
    }
    if ((__pytra_str_slice($t, (-1), __pytra_len($t)) != ":")) {
        return "";
    }
    return __pytra_str_slice($t, 0, (-1));
}

function _is_space_ch($ch) {
    if (($ch == " ")) {
        return true;
    }
    if (($ch == "	")) {
        return true;
    }
    if (($ch == "\r")) {
        return true;
    }
    if (($ch == "\n")) {
        return true;
    }
    return false;
}

function _is_alnum_or_underscore($ch) {
    $is_alpha = ((("a" <= $ch) && ($ch <= "z")) || (("A" <= $ch) && ($ch <= "Z")));
    $is_digit = (("0" <= $ch) && ($ch <= "9"));
    if (($is_alpha || $is_digit)) {
        return true;
    }
    return ($ch == "_");
}

function _skip_spaces($t, $i) {
    while (($i < __pytra_len($t))) {
        if ((!_is_space_ch(__pytra_str_slice($t, $i, ($i + 1))))) {
            return $i;
        }
        $i += 1;
    }
    return $i;
}

function match_($pattern, $text, $flags) {
    if (($pattern == "^([A-Za-z_][A-Za-z0-9_]*)\\[(.*)\\]$")) {
        if ((!$text->endswith("]"))) {
            return null;
        }
        $i = $text->find("[");
        if (($i <= 0)) {
            return null;
        }
        $head = __pytra_str_slice($text, 0, $i);
        if ((!_is_ident($head))) {
            return null;
        }
        return new Match_($text, [$head, __pytra_str_slice($text, ($i + 1), (-1))]);
    }
    if (($pattern == "^def\\s+([A-Za-z_][A-Za-z0-9_]*)\\((.*)\\)\\s*(?:->\\s*(.+)\\s*)?:\\s*$")) {
        $t = _strip_suffix_colon($text);
        if (($t == "")) {
            return null;
        }
        $i = 0;
        if ((!$t->startswith("def"))) {
            return null;
        }
        $i = 3;
        if ((($i >= __pytra_len($t)) || (!_is_space_ch(__pytra_str_slice($t, $i, ($i + 1)))))) {
            return null;
        }
        $i = _skip_spaces($t, $i);
        $j = $i;
        while ((($j < __pytra_len($t)) && _is_alnum_or_underscore(__pytra_str_slice($t, $j, ($j + 1))))) {
            $j += 1;
        }
        $name = __pytra_str_slice($t, $i, $j);
        if ((!_is_ident($name))) {
            return null;
        }
        $k = $j;
        $k = _skip_spaces($t, $k);
        if ((($k >= __pytra_len($t)) || (__pytra_str_slice($t, $k, ($k + 1)) != "("))) {
            return null;
        }
        $r = $t->rfind(")");
        if (($r <= $k)) {
            return null;
        }
        $args = __pytra_str_slice($t, ($k + 1), $r);
        $tail = __pytra_str_slice($t, ($r + 1), __pytra_len($t))->strip();
        if (($tail == "")) {
            return new Match_($text, [$name, $args, ""]);
        }
        if ((!$tail->startswith("->"))) {
            return null;
        }
        $ret = __pytra_str_slice($tail, 2, __pytra_len($tail))->strip();
        if (($ret == "")) {
            return null;
        }
        return new Match_($text, [$name, $args, $ret]);
    }
    if (($pattern == "^([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*([^=]+?)(?:\\s*=\\s*(.+))?$")) {
        $c = $text->find(":");
        if (($c <= 0)) {
            return null;
        }
        $name = __pytra_str_slice($text, 0, $c)->strip();
        if ((!_is_ident($name))) {
            return null;
        }
        $rhs = __pytra_str_slice($text, ($c + 1), __pytra_len($text));
        $eq = $rhs->find("=");
        if (($eq < 0)) {
            $ann = $rhs->strip();
            if (($ann == "")) {
                return null;
            }
            return new Match_($text, [$name, $ann, ""]);
        }
        $ann = __pytra_str_slice($rhs, 0, $eq)->strip();
        $val = __pytra_str_slice($rhs, ($eq + 1), __pytra_len($rhs))->strip();
        if ((($ann == "") || ($val == ""))) {
            return null;
        }
        return new Match_($text, [$name, $ann, $val]);
    }
    if (($pattern == "^[A-Za-z_][A-Za-z0-9_]*$")) {
        if (_is_ident($text)) {
            return new Match_($text, []);
        }
        return null;
    }
    if (($pattern == "^class\\s+([A-Za-z_][A-Za-z0-9_]*)(?:\\(([A-Za-z_][A-Za-z0-9_]*)\\))?\\s*:\\s*$")) {
        $t = _strip_suffix_colon($text);
        if (($t == "")) {
            return null;
        }
        if ((!$t->startswith("class"))) {
            return null;
        }
        $i = 5;
        if ((($i >= __pytra_len($t)) || (!_is_space_ch(__pytra_str_slice($t, $i, ($i + 1)))))) {
            return null;
        }
        $i = _skip_spaces($t, $i);
        $j = $i;
        while ((($j < __pytra_len($t)) && _is_alnum_or_underscore(__pytra_str_slice($t, $j, ($j + 1))))) {
            $j += 1;
        }
        $name = __pytra_str_slice($t, $i, $j);
        if ((!_is_ident($name))) {
            return null;
        }
        $tail = __pytra_str_slice($t, $j, __pytra_len($t))->strip();
        if (($tail == "")) {
            return new Match_($text, [$name, ""]);
        }
        if ((!($tail->startswith("(") && $tail->endswith(")")))) {
            return null;
        }
        $base = __pytra_str_slice($tail, 1, (-1))->strip();
        if ((!_is_ident($base))) {
            return null;
        }
        return new Match_($text, [$name, $base]);
    }
    if (($pattern == "^(any|all)\\((.+)\\)$")) {
        if (($text->startswith("any(") && $text->endswith(")") && (__pytra_len($text) > 5))) {
            return new Match_($text, ["any", __pytra_str_slice($text, 4, (-1))]);
        }
        if (($text->startswith("all(") && $text->endswith(")") && (__pytra_len($text) > 5))) {
            return new Match_($text, ["all", __pytra_str_slice($text, 4, (-1))]);
        }
        return null;
    }
    if (($pattern == "^\\[\\s*([A-Za-z_][A-Za-z0-9_]*)\\s+for\\s+([A-Za-z_][A-Za-z0-9_]*)\\s+in\\s+(.+)\\]$")) {
        if ((!($text->startswith("[") && $text->endswith("]")))) {
            return null;
        }
        $inner = __pytra_str_slice($text, 1, (-1))->strip();
        $m1 = " for ";
        $m2 = " in ";
        $i = $inner->find($m1);
        if (($i < 0)) {
            return null;
        }
        $expr = __pytra_str_slice($inner, 0, $i)->strip();
        $rest = __pytra_str_slice($inner, ($i + __pytra_len($m1)), __pytra_len($inner));
        $j = $rest->find($m2);
        if (($j < 0)) {
            return null;
        }
        $var_ = __pytra_str_slice($rest, 0, $j)->strip();
        $it = __pytra_str_slice($rest, ($j + __pytra_len($m2)), __pytra_len($rest))->strip();
        if (((!_is_ident($expr)) || (!_is_ident($var_)) || ($it == ""))) {
            return null;
        }
        return new Match_($text, [$expr, $var_, $it]);
    }
    if (($pattern == "^for\\s+(.+)\\s+in\\s+(.+):$")) {
        $t = _strip_suffix_colon($text);
        if ((($t == "") || (!$t->startswith("for")))) {
            return null;
        }
        $rest = __pytra_str_slice($t, 3, __pytra_len($t))->strip();
        $i = $rest->find(" in ");
        if (($i < 0)) {
            return null;
        }
        $left = __pytra_str_slice($rest, 0, $i)->strip();
        $right = __pytra_str_slice($rest, ($i + 4), __pytra_len($rest))->strip();
        if ((($left == "") || ($right == ""))) {
            return null;
        }
        return new Match_($text, [$left, $right]);
    }
    if (($pattern == "^with\\s+(.+)\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*$")) {
        $t = _strip_suffix_colon($text);
        if ((($t == "") || (!$t->startswith("with")))) {
            return null;
        }
        $rest = __pytra_str_slice($t, 4, __pytra_len($t))->strip();
        $i = $rest->rfind(" as ");
        if (($i < 0)) {
            return null;
        }
        $expr = __pytra_str_slice($rest, 0, $i)->strip();
        $name = __pytra_str_slice($rest, ($i + 4), __pytra_len($rest))->strip();
        if ((($expr == "") || (!_is_ident($name)))) {
            return null;
        }
        return new Match_($text, [$expr, $name]);
    }
    if (($pattern == "^except\\s+(.+?)\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*$")) {
        $t = _strip_suffix_colon($text);
        if ((($t == "") || (!$t->startswith("except")))) {
            return null;
        }
        $rest = __pytra_str_slice($t, 6, __pytra_len($t))->strip();
        $i = $rest->rfind(" as ");
        if (($i < 0)) {
            return null;
        }
        $exc = __pytra_str_slice($rest, 0, $i)->strip();
        $name = __pytra_str_slice($rest, ($i + 4), __pytra_len($rest))->strip();
        if ((($exc == "") || (!_is_ident($name)))) {
            return null;
        }
        return new Match_($text, [$exc, $name]);
    }
    if (($pattern == "^except\\s+(.+?)\\s*:\\s*$")) {
        $t = _strip_suffix_colon($text);
        if ((($t == "") || (!$t->startswith("except")))) {
            return null;
        }
        $rest = __pytra_str_slice($t, 6, __pytra_len($t))->strip();
        if (($rest == "")) {
            return null;
        }
        return new Match_($text, [$rest]);
    }
    if (($pattern == "^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*:\\s*(.+)$")) {
        $c = $text->find(":");
        if (($c <= 0)) {
            return null;
        }
        $target = __pytra_str_slice($text, 0, $c)->strip();
        $ann = __pytra_str_slice($text, ($c + 1), __pytra_len($text))->strip();
        if ((($ann == "") || (!_is_dotted_ident($target)))) {
            return null;
        }
        return new Match_($text, [$target, $ann]);
    }
    if (($pattern == "^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*:\\s*([^=]+?)\\s*=\\s*(.+)$")) {
        $c = $text->find(":");
        if (($c <= 0)) {
            return null;
        }
        $target = __pytra_str_slice($text, 0, $c)->strip();
        $rhs = __pytra_str_slice($text, ($c + 1), __pytra_len($text));
        $eq = $rhs->find("=");
        if (($eq < 0)) {
            return null;
        }
        $ann = __pytra_str_slice($rhs, 0, $eq)->strip();
        $expr = __pytra_str_slice($rhs, ($eq + 1), __pytra_len($rhs))->strip();
        if (((!_is_dotted_ident($target)) || ($ann == "") || ($expr == ""))) {
            return null;
        }
        return new Match_($text, [$target, $ann, $expr]);
    }
    if (($pattern == "^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*(\\+=|-=|\\*=|/=|//=|%=|&=|\\|=|\\^=|<<=|>>=)\\s*(.+)$")) {
        $ops = ["<<=", ">>=", "+=", "-=", "*=", "/=", "//=", "%=", "&=", "|=", "^="];
        $op_pos = (-1);
        $op_txt = "";
        foreach ($ops as $op) {
            $p = $text->find($op);
            if ((($p >= 0) && (($op_pos < 0) || ($p < $op_pos)))) {
                $op_pos = $p;
                $op_txt = $op;
            }
        }
        if (($op_pos < 0)) {
            return null;
        }
        $left = __pytra_str_slice($text, 0, $op_pos)->strip();
        $right = __pytra_str_slice($text, ($op_pos + __pytra_len($op_txt)), __pytra_len($text))->strip();
        if ((($right == "") || (!_is_dotted_ident($left)))) {
            return null;
        }
        return new Match_($text, [$left, $op_txt, $right]);
    }
    if (($pattern == "^([A-Za-z_][A-Za-z0-9_]*)\\s*,\\s*([A-Za-z_][A-Za-z0-9_]*)\\s*=\\s*(.+)$")) {
        $eq = $text->find("=");
        if (($eq < 0)) {
            return null;
        }
        $left = __pytra_str_slice($text, 0, $eq);
        $right = __pytra_str_slice($text, ($eq + 1), __pytra_len($text))->strip();
        if (($right == "")) {
            return null;
        }
        $c = $left->find(",");
        if (($c < 0)) {
            return null;
        }
        $a = __pytra_str_slice($left, 0, $c)->strip();
        $b = __pytra_str_slice($left, ($c + 1), __pytra_len($left))->strip();
        if (((!_is_ident($a)) || (!_is_ident($b)))) {
            return null;
        }
        return new Match_($text, [$a, $b, $right]);
    }
    if (($pattern == "^if\\s+__name__\\s*==\\s*[\\\"']__main__[\\\"']\\s*:\\s*$")) {
        $t = _strip_suffix_colon($text);
        if (($t == "")) {
            return null;
        }
        $rest = $t->strip();
        if ((!$rest->startswith("if"))) {
            return null;
        }
        $rest = __pytra_str_slice($rest, 2, __pytra_len($rest))->strip();
        if ((!$rest->startswith("__name__"))) {
            return null;
        }
        $rest = __pytra_str_slice($rest, __pytra_len("__name__"), __pytra_len($rest))->strip();
        if ((!$rest->startswith("=="))) {
            return null;
        }
        $rest = __pytra_str_slice($rest, 2, __pytra_len($rest))->strip();
        if ((in_array($rest, null, true))) {
            return new Match_($text, []);
        }
        return null;
    }
    if (($pattern == "^import\\s+(.+)$")) {
        if ((!$text->startswith("import"))) {
            return null;
        }
        if ((__pytra_len($text) <= 6)) {
            return null;
        }
        if ((!_is_space_ch(__pytra_str_slice($text, 6, 7)))) {
            return null;
        }
        $rest = __pytra_str_slice($text, 7, __pytra_len($text))->strip();
        if (($rest == "")) {
            return null;
        }
        return new Match_($text, [$rest]);
    }
    if (($pattern == "^([A-Za-z_][A-Za-z0-9_\\.]*)(?:\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*))?$")) {
        $parts = $text->split(" as ");
        if ((__pytra_len($parts) == 1)) {
            $name = $parts[__pytra_index($parts, 0)]->strip();
            if ((!_is_dotted_ident($name))) {
                return null;
            }
            return new Match_($text, [$name, ""]);
        }
        if ((__pytra_len($parts) == 2)) {
            $name = $parts[__pytra_index($parts, 0)]->strip();
            $alias = $parts[__pytra_index($parts, 1)]->strip();
            if (((!_is_dotted_ident($name)) || (!_is_ident($alias)))) {
                return null;
            }
            return new Match_($text, [$name, $alias]);
        }
        return null;
    }
    if (($pattern == "^from\\s+([A-Za-z_][A-Za-z0-9_\\.]*)\\s+import\\s+(.+)$")) {
        if ((!$text->startswith("from "))) {
            return null;
        }
        $rest = __pytra_str_slice($text, 5, __pytra_len($text));
        $i = $rest->find(" import ");
        if (($i < 0)) {
            return null;
        }
        $mod = __pytra_str_slice($rest, 0, $i)->strip();
        $sym = __pytra_str_slice($rest, ($i + 8), __pytra_len($rest))->strip();
        if (((!_is_dotted_ident($mod)) || ($sym == ""))) {
            return null;
        }
        return new Match_($text, [$mod, $sym]);
    }
    if (($pattern == "^([A-Za-z_][A-Za-z0-9_]*)(?:\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*))?$")) {
        $parts = $text->split(" as ");
        if ((__pytra_len($parts) == 1)) {
            $name = $parts[__pytra_index($parts, 0)]->strip();
            if ((!_is_ident($name))) {
                return null;
            }
            return new Match_($text, [$name, ""]);
        }
        if ((__pytra_len($parts) == 2)) {
            $name = $parts[__pytra_index($parts, 0)]->strip();
            $alias = $parts[__pytra_index($parts, 1)]->strip();
            if (((!_is_ident($name)) || (!_is_ident($alias)))) {
                return null;
            }
            return new Match_($text, [$name, $alias]);
        }
        return null;
    }
    if (($pattern == "^([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*([^=]+?)\\s*=\\s*(.+)$")) {
        $c = $text->find(":");
        if (($c <= 0)) {
            return null;
        }
        $name = __pytra_str_slice($text, 0, $c)->strip();
        $rhs = __pytra_str_slice($text, ($c + 1), __pytra_len($text));
        $eq = $rhs->find("=");
        if (($eq < 0)) {
            return null;
        }
        $ann = __pytra_str_slice($rhs, 0, $eq)->strip();
        $expr = __pytra_str_slice($rhs, ($eq + 1), __pytra_len($rhs))->strip();
        if (((!_is_ident($name)) || ($ann == "") || ($expr == ""))) {
            return null;
        }
        return new Match_($text, [$name, $ann, $expr]);
    }
    if (($pattern == "^([A-Za-z_][A-Za-z0-9_]*)\\s*=\\s*(.+)$")) {
        $eq = $text->find("=");
        if (($eq < 0)) {
            return null;
        }
        $name = __pytra_str_slice($text, 0, $eq)->strip();
        $expr = __pytra_str_slice($text, ($eq + 1), __pytra_len($text))->strip();
        if (((!_is_ident($name)) || ($expr == ""))) {
            return null;
        }
        return new Match_($text, [$name, $expr]);
    }
    throw new Exception(strval(ValueError(null)));
}

function sub($pattern, $repl, $text, $flags) {
    if (($pattern == "\\s+")) {
        $out = [];
        $in_ws = false;
        foreach ($text as $ch) {
            if ($ch->isspace()) {
                if ((!$in_ws)) {
                    $out[] = $repl;
                    $in_ws = true;
                }
            } else {
                $out[] = $ch;
                $in_ws = false;
            }
        }
        return ""->join($out);
    }
    if (($pattern == "\\s+#.*$")) {
        $i = 0;
        while (($i < __pytra_len($text))) {
            if ($text[$i]->isspace()) {
                $j = ($i + 1);
                while ((($j < __pytra_len($text)) && $text[$j]->isspace())) {
                    $j += 1;
                }
                if ((($j < __pytra_len($text)) && ($text[$j] == "#"))) {
                    return (__pytra_str_slice($text, 0, $i) . $repl);
                }
            }
            $i += 1;
        }
        return $text;
    }
    if (($pattern == "[^0-9A-Za-z_]")) {
        $out = [];
        foreach ($text as $ch) {
            if (($ch->isalnum() || ($ch == "_"))) {
                $out[] = $ch;
            } else {
                $out[] = $repl;
            }
        }
        return ""->join($out);
    }
    throw new Exception(strval(ValueError(null)));
}
