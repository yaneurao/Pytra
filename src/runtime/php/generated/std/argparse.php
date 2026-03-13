<?php
// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/argparse.py
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

class Namespace_ {
    public function __construct($values) {
        if (($values == null)) {
            $this->values = [];
            return;
        }
        $this->values = $values;
    }
}

class _ArgSpec {
    public function __construct($names, $action, $choices, $default_, $help_text) {
        $this->names = $names;
        $this->action = $action;
        $this->choices = $choices;
        $this->default_ = $default_;
        $this->help_text = $help_text;
        $this->is_optional = ((__pytra_len($names) > 0) && $names[__pytra_index($names, 0)]->startswith("-"));
        if ($this->is_optional) {
            $base = $names[__pytra_index($names, (-1))]->lstrip("-")->replace("-", "_");
            $this->dest = $base;
        } else {
            $this->dest = $names[__pytra_index($names, 0)];
        }
    }
}

class ArgumentParser {
    public function __construct($description) {
        $this->description = $description;
        $this->_specs = [];
    }

    public function add_argument($name0, $name1, $name2, $name3, $help, $action, $choices, $default_) {
        $names = [];
        if (($name0 != "")) {
            $names[] = $name0;
        }
        if (($name1 != "")) {
            $names[] = $name1;
        }
        if (($name2 != "")) {
            $names[] = $name2;
        }
        if (($name3 != "")) {
            $names[] = $name3;
        }
        if ((__pytra_len($names) == 0)) {
            throw new Exception(strval(ValueError("add_argument requires at least one name")));
        }
        $spec = new _ArgSpec($names);
        $this->_specs[] = $spec;
    }

    public function _fail($msg) {
        if (($msg != "")) {
            $sys->write_stderr(null);
        }
        throw new Exception(strval(SystemExit(2)));
    }

    public function parse_args($argv) {
        $args = null;
        if (($argv == null)) {
            $args = __pytra_str_slice($sys->argv, 1, __pytra_len($sys->argv));
        } else {
            $args = list_($argv);
        }
        $specs_pos = [];
        $specs_opt = [];
        foreach ($this->_specs as $s) {
            if ($s->is_optional) {
                $specs_opt[] = $s;
            } else {
                $specs_pos[] = $s;
            }
        }
        $by_name = [];
        $spec_i = 0;
        foreach ($specs_opt as $s) {
            foreach ($s->names as $n) {
                $by_name[$n] = $spec_i;
            }
            $spec_i += 1;
        }
        $values = [];
        foreach ($this->_specs as $s) {
            if (($s->action == "store_true")) {
                $values[$s->dest] = (($s->default_ == null) ? ((bool)($s->default_)) : false);
            } else {
                if (($s->default_ == null)) {
                    $values[$s->dest] = $s->default_;
                } else {
                    $values[$s->dest] = null;
                }
            }
        }
        $pos_i = 0;
        $i = 0;
        while (($i < __pytra_len($args))) {
            $tok = $args[__pytra_index($args, $i)];
            if ($tok->startswith("-")) {
                if ((!array_key_exists($tok, $by_name))) {
                    $this->_fail(null);
                }
                $spec = $specs_opt[__pytra_index($specs_opt, $by_name[$tok])];
                if (($spec->action == "store_true")) {
                    $values[$spec->dest] = true;
                    $i += 1;
                    continue;
                }
                if ((($i + 1) >= __pytra_len($args))) {
                    $this->_fail(null);
                }
                $val = $args[__pytra_index($args, ($i + 1))];
                if (((__pytra_len($spec->choices) > 0) && (!__pytra_contains($spec->choices, $val)))) {
                    $this->_fail(null);
                }
                $values[$spec->dest] = $val;
                $i += 2;
                continue;
            }
            if (($pos_i >= __pytra_len($specs_pos))) {
                $this->_fail(null);
            }
            $spec = $specs_pos[__pytra_index($specs_pos, $pos_i)];
            $values[$spec->dest] = $tok;
            $pos_i += 1;
            $i += 1;
        }
        if (($pos_i < __pytra_len($specs_pos))) {
            $this->_fail(null);
        }
        return $values;
    }
}
