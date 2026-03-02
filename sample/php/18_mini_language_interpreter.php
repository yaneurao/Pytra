<?php
declare(strict_types=1);

require_once __DIR__ . '/pytra/py_runtime.php';

class Token {
    public $kind;
    public $text;
    public $pos;
    public $number_value;
    public function __construct($kind, $text, $pos, $number_value) {
        $this->kind = $kind;
        $this->text = $text;
        $this->pos = $pos;
        $this->number_value = $number_value;
    }
}

class ExprNode {
    public $kind;
    public $value;
    public $name;
    public $op;
    public $left;
    public $right;
    public $kind_tag;
    public $op_tag;
    public function __construct($kind, $value, $name, $op, $left, $right, $kind_tag, $op_tag) {
        $this->kind = $kind;
        $this->value = $value;
        $this->name = $name;
        $this->op = $op;
        $this->left = $left;
        $this->right = $right;
        $this->kind_tag = $kind_tag;
        $this->op_tag = $op_tag;
    }
}

class StmtNode {
    public $kind;
    public $name;
    public $expr_index;
    public $kind_tag;
    public function __construct($kind, $name, $expr_index, $kind_tag) {
        $this->kind = $kind;
        $this->name = $name;
        $this->expr_index = $expr_index;
        $this->kind_tag = $kind_tag;
    }
}

class Parser {
    public function new_expr_nodes() {
        return [];
    }

    public function __construct($tokens) {
        $this->tokens = $tokens;
        $this->pos = 0;
        $this->expr_nodes = $this->new_expr_nodes();
    }

    public function current_token() {
        return $this->tokens[$this->pos];
    }

    public function previous_token() {
        return $this->tokens[($this->pos - 1)];
    }

    public function peek_kind() {
        return $this->current_token()->kind;
    }

    public function match_($kind) {
        if (($this->peek_kind() == $kind)) {
            $this->pos += 1;
            return true;
        }
        return false;
    }

    public function expect($kind) {
        $token = $this->current_token();
        if (($token->kind != $kind)) {
            throw new Exception(strval(((((("parse error at pos=" . strval($token->pos)) . ", expected=") . $kind) . ", got=") . $token->kind)));
        }
        $this->pos += 1;
        return $token;
    }

    public function skip_newlines() {
        while ($this->match_("NEWLINE")) {
            ;
        }
    }

    public function add_expr($node) {
        $this->expr_nodes[] = $node;
        return (__pytra_len($this->expr_nodes) - 1);
    }

    public function parse_program() {
        $stmts = [];
        $this->skip_newlines();
        while (($this->peek_kind() != "EOF")) {
            $stmt = $this->parse_stmt();
            $stmts[] = $stmt;
            $this->skip_newlines();
        }
        return $stmts;
    }

    public function parse_stmt() {
        if ($this->match_("LET")) {
            $let_name = $this->expect("IDENT")->text;
            $this->expect("EQUAL");
            $let_expr_index = $this->parse_expr();
            return new StmtNode("let", $let_name, $let_expr_index, 1);
        }
        if ($this->match_("PRINT")) {
            $print_expr_index = $this->parse_expr();
            return new StmtNode("print", "", $print_expr_index, 3);
        }
        $assign_name = $this->expect("IDENT")->text;
        $this->expect("EQUAL");
        $assign_expr_index = $this->parse_expr();
        return new StmtNode("assign", $assign_name, $assign_expr_index, 2);
    }

    public function parse_expr() {
        return $this->parse_add();
    }

    public function parse_add() {
        $left = $this->parse_mul();
        while (true) {
            if ($this->match_("PLUS")) {
                $right = $this->parse_mul();
                $left = $this->add_expr(new ExprNode("bin", 0, "", "+", $left, $right, 3, 1));
                continue;
            }
            if ($this->match_("MINUS")) {
                $right = $this->parse_mul();
                $left = $this->add_expr(new ExprNode("bin", 0, "", "-", $left, $right, 3, 2));
                continue;
            }
            break;
        }
        return $left;
    }

    public function parse_mul() {
        $left = $this->parse_unary();
        while (true) {
            if ($this->match_("STAR")) {
                $right = $this->parse_unary();
                $left = $this->add_expr(new ExprNode("bin", 0, "", "*", $left, $right, 3, 3));
                continue;
            }
            if ($this->match_("SLASH")) {
                $right = $this->parse_unary();
                $left = $this->add_expr(new ExprNode("bin", 0, "", "/", $left, $right, 3, 4));
                continue;
            }
            break;
        }
        return $left;
    }

    public function parse_unary() {
        if ($this->match_("MINUS")) {
            $child = $this->parse_unary();
            return $this->add_expr(new ExprNode("neg", 0, "", "", $child, (-1), 4, 0));
        }
        return $this->parse_primary();
    }

    public function parse_primary() {
        if ($this->match_("NUMBER")) {
            $token_num = $this->previous_token();
            return $this->add_expr(new ExprNode("lit", $token_num->number_value, "", "", (-1), (-1), 1, 0));
        }
        if ($this->match_("IDENT")) {
            $token_ident = $this->previous_token();
            return $this->add_expr(new ExprNode("var", 0, $token_ident->text, "", (-1), (-1), 2, 0));
        }
        if ($this->match_("LPAREN")) {
            $expr_index = $this->parse_expr();
            $this->expect("RPAREN");
            return $expr_index;
        }
        $t = $this->current_token();
        throw new Exception(strval(((("primary parse error at pos=" . strval($t->pos)) . " got=") . $t->kind)));
    }
}

function tokenize($lines) {
    $single_char_token_tags = ["+" => 1, "-" => 2, "*" => 3, "/" => 4, "(" => 5, ")" => 6, "=" => 7];
    $single_char_token_kinds = ["PLUS", "MINUS", "STAR", "SLASH", "LPAREN", "RPAREN", "EQUAL"];
    $tokens = [];
    for ($__i = 0; $__i < count($lines); $__i += 1) {
        $line_index = $__i;
        $source = $lines[$__i];
        $i = 0;
        $n = __pytra_len($source);
        while (($i < $n)) {
            $ch = $source[$i];
            if (($ch == " ")) {
                $i += 1;
                continue;
            }
            $single_tag = ($single_char_token_tags[$ch] ?? 0);
            if (($single_tag > 0)) {
                $tokens[] = new Token($single_char_token_kinds[($single_tag - 1)], $ch, $i, 0);
                $i += 1;
                continue;
            }
            if (__pytra_str_isdigit($ch)) {
                $start = $i;
                while ((($i < $n) && __pytra_str_isdigit($source[$i]))) {
                    $i += 1;
                }
                $text = __pytra_str_slice($source, $start, $i);
                $tokens[] = new Token("NUMBER", $text, $start, ((int)($text)));
                continue;
            }
            if ((__pytra_str_isalpha($ch) || ($ch == "_"))) {
                $start = $i;
                while ((($i < $n) && ((__pytra_str_isalpha($source[$i]) || ($source[$i] == "_")) || __pytra_str_isdigit($source[$i])))) {
                    $i += 1;
                }
                $text = __pytra_str_slice($source, $start, $i);
                if (($text == "let")) {
                    $tokens[] = new Token("LET", $text, $start, 0);
                } else {
                    if (($text == "print")) {
                        $tokens[] = new Token("PRINT", $text, $start, 0);
                    } else {
                        $tokens[] = new Token("IDENT", $text, $start, 0);
                    }
                }
                continue;
            }
            throw new Exception(strval(((((("tokenize error at line=" . strval($line_index)) . " pos=") . strval($i)) . " ch=") . $ch)));
        }
        $tokens[] = new Token("NEWLINE", "", $n, 0);
    }
    $tokens[] = new Token("EOF", "", __pytra_len($lines), 0);
    return $tokens;
}

function eval_expr($expr_index, $expr_nodes, $env) {
    $node = $expr_nodes[$expr_index];
    if (($node->kind_tag == 1)) {
        return $node->value;
    }
    if (($node->kind_tag == 2)) {
        if ((!(array_key_exists($node->name, $env)))) {
            throw new Exception(strval(("undefined variable: " . $node->name)));
        }
        return $env[$node->name];
    }
    if (($node->kind_tag == 4)) {
        return (-eval_expr($node->left, $expr_nodes, $env));
    }
    if (($node->kind_tag == 3)) {
        $lhs = eval_expr($node->left, $expr_nodes, $env);
        $rhs = eval_expr($node->right, $expr_nodes, $env);
        if (($node->op_tag == 1)) {
            return ($lhs + $rhs);
        }
        if (($node->op_tag == 2)) {
            return ($lhs - $rhs);
        }
        if (($node->op_tag == 3)) {
            return ($lhs * $rhs);
        }
        if (($node->op_tag == 4)) {
            if (($rhs == 0)) {
                throw new Exception(strval("division by zero"));
            }
            return intdiv($lhs, $rhs);
        }
        throw new Exception(strval(("unknown operator: " . $node->op)));
    }
    throw new Exception(strval(("unknown node kind: " . $node->kind)));
}

function execute($stmts, $expr_nodes, $trace) {
    $env = [];
    $checksum = 0;
    $printed = 0;
    foreach ($stmts as $stmt) {
        if (($stmt->kind_tag == 1)) {
            $env[$stmt->name] = eval_expr($stmt->expr_index, $expr_nodes, $env);
            continue;
        }
        if (($stmt->kind_tag == 2)) {
            if ((!(array_key_exists($stmt->name, $env)))) {
                throw new Exception(strval(("assign to undefined variable: " . $stmt->name)));
            }
            $env[$stmt->name] = eval_expr($stmt->expr_index, $expr_nodes, $env);
            continue;
        }
        $value = eval_expr($stmt->expr_index, $expr_nodes, $env);
        if ($trace) {
            __pytra_print($value);
        }
        $norm = ($value % 1000000007);
        if (($norm < 0)) {
            $norm += 1000000007;
        }
        $checksum = ((($checksum * 131) + $norm) % 1000000007);
        $printed += 1;
    }
    if ($trace) {
        __pytra_print("printed:", $printed);
    }
    return $checksum;
}

function build_benchmark_source($var_count, $loops) {
    $lines = [];
    for ($i = 0; $i < $var_count; $i += 1) {
        $lines[] = ((("let v" . strval($i)) . " = ") . strval(($i + 1)));
    }
    for ($i = 0; $i < $loops; $i += 1) {
        $x = ($i % $var_count);
        $y = (($i + 3) % $var_count);
        $c1 = (($i % 7) + 1);
        $c2 = (($i % 11) + 2);
        $lines[] = ((((((((("v" . strval($x)) . " = (v") . strval($x)) . " * ") . strval($c1)) . " + v") . strval($y)) . " + 10000) / ") . strval($c2));
        if ((($i % 97) == 0)) {
            $lines[] = ("print v" . strval($x));
        }
    }
    $lines[] = "print (v0 + v1 + v2 + v3)";
    return $lines;
}

function run_demo() {
    $demo_lines = [];
    $demo_lines[] = "let a = 10";
    $demo_lines[] = "let b = 3";
    $demo_lines[] = "a = (a + b) * 2";
    $demo_lines[] = "print a";
    $demo_lines[] = "print a / b";
    $tokens = tokenize($demo_lines);
    $parser = new Parser($tokens);
    $stmts = $parser->parse_program();
    $checksum = execute($stmts, $parser->expr_nodes, true);
    __pytra_print("demo_checksum:", $checksum);
}

function run_benchmark() {
    $source_lines = build_benchmark_source(32, 120000);
    $start = __pytra_perf_counter();
    $tokens = tokenize($source_lines);
    $parser = new Parser($tokens);
    $stmts = $parser->parse_program();
    $checksum = execute($stmts, $parser->expr_nodes, false);
    $elapsed = (__pytra_perf_counter() - $start);
    __pytra_print("token_count:", __pytra_len($tokens));
    __pytra_print("expr_count:", __pytra_len($parser->expr_nodes));
    __pytra_print("stmt_count:", __pytra_len($stmts));
    __pytra_print("checksum:", $checksum);
    __pytra_print("elapsed_sec:", $elapsed);
}

function __pytra_main() {
    run_demo();
    run_benchmark();
}

function main(): void {
    __pytra_main();
}

function __pytra_entry_main(): void {
    main();
}

__pytra_entry_main();
