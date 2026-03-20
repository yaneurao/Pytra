#Requires -Version 5.1

$pytra_runtime = Join-Path $PSScriptRoot "py_runtime.ps1"
if (Test-Path $pytra_runtime) { . $pytra_runtime }

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# import: pytra.std.time

# class Token
$kind = $null
$text = $null
$pos = $null
$number_value = $null

# class ExprNode
$kind = $null
$value = $null
$name = $null
$op = $null
$left = $null
$right = $null
$kind_tag = $null
$op_tag = $null

# class StmtNode
$kind = $null
$name = $null
$expr_index = $null
$kind_tag = $null

function tokenize {
    param($lines)
    $single_char_token_tags = @{"+" = 1; "-" = 2; "*" = 3; "/" = 4; "(" = 5; ")" = 6; "=" = 7}
    $single_char_token_kinds = @("PLUS", "MINUS", "STAR", "SLASH", "LPAREN", "RPAREN", "EQUAL")
    $tokens = @()
    for ($_i = $null; $_i -lt $null; $_i += 1) {
        $i = 0
        $n = __pytra_len $source
        while (($i -lt $n)) {
            $ch = $source[$i]
            if (($ch -eq " ")) {
                $i += 1
                continue
            }
            $single_tag = $(if ($single_char_token_tags.ContainsKey($ch)) { $single_char_token_tags[$ch] } else { 0 })
            if (($single_tag -gt 0)) {
                $tokens += @(& { $__obj = @{}; (Token $__obj $single_char_token_kinds[($single_tag - 1)] $ch $i 0); $__obj })
                $i += 1
                continue
            }
            if ($ch.isdigit()) {
                $start = $i
                while ((($i -lt $n) -and $source[$i].isdigit())) {
                    $i += 1
                }
                $text = $source[$start..($i - 1)]
                $tokens += @(& { $__obj = @{}; (Token $__obj "NUMBER" $text $start __pytra_int $text); $__obj })
                continue
            }
            if (($ch.isalpha() -or ($ch -eq "_"))) {
                $start = $i
                while ((($i -lt $n) -and (($source[$i].isalpha() -or ($source[$i] -eq "_")) -or $source[$i].isdigit()))) {
                    $i += 1
                }
                $text = $source[$start..($i - 1)]
                if (($text -eq "let")) {
                    $tokens += @(& { $__obj = @{}; (Token $__obj "LET" $text $start 0); $__obj })
                } elseif (($text -eq "print")) {
                    $tokens += @(& { $__obj = @{}; (Token $__obj "PRINT" $text $start 0); $__obj })
                } else {
                    $tokens += @(& { $__obj = @{}; (Token $__obj "IDENT" $text $start 0); $__obj })
                }
                continue
            }
            throw (RuntimeError ((((("tokenize error at line=" + __pytra_str $line_index) + " pos=") + __pytra_str $i) + " ch=") + $ch))
        }
        $tokens += @(& { $__obj = @{}; (Token $__obj "NEWLINE" "" $n 0); $__obj })
    }
    $tokens += @(& { $__obj = @{}; (Token $__obj "EOF" "" __pytra_len $lines 0); $__obj })
    return $tokens
}

# class Parser
function Parser_new_expr_nodes {
    param($self)
    return @()
}
function Parser {
    param($self, $tokens)
    $self.tokens = $tokens
    $self.pos = 0
    $self.expr_nodes = $self.new_expr_nodes()
}
function Parser_current_token {
    param($self)
    return $self.tokens[$self.pos]
}
function Parser_previous_token {
    param($self)
    return $self.tokens[($self.pos - 1)]
}
function Parser_peek_kind {
    param($self)
    return $self.current_token().kind
}
function Parser_match {
    param($self, $kind)
    if (($self.peek_kind() -eq $kind)) {
        $self.pos += 1
        return $true
    }
    return $false
}
function Parser_expect {
    param($self, $kind)
    $token = $self.current_token()
    if (($token.kind -ne $kind)) {
        throw (RuntimeError ((((("parse error at pos=" + __pytra_str $token.pos) + ", expected=") + $kind) + ", got=") + $token.kind))
    }
    $self.pos += 1
    return $token
}
function Parser_skip_newlines {
    param($self)
    while ($self.match("NEWLINE")) {
        # pass
    }
}
function Parser_add_expr {
    param($self, $node)
    $self.expr_nodes += @($node)
    return (__pytra_len $self.expr_nodes - 1)
}
function Parser_parse_program {
    param($self)
    $stmts = @()
    $self.skip_newlines()
    while (($self.peek_kind() -ne "EOF")) {
        $stmt = $self.parse_stmt()
        $stmts += @($stmt)
        $self.skip_newlines()
    }
    return $stmts
}
function Parser_parse_stmt {
    param($self)
    if ($self.match("LET")) {
        $let_name = $self.expect("IDENT").text
        $self.expect("EQUAL")
        $let_expr_index = $self.parse_expr()
        return & { $__obj = @{}; (StmtNode $__obj "let" $let_name $let_expr_index 1); $__obj }
    }
    if ($self.match("PRINT")) {
        $print_expr_index = $self.parse_expr()
        return & { $__obj = @{}; (StmtNode $__obj "print" "" $print_expr_index 3); $__obj }
    }
    $assign_name = $self.expect("IDENT").text
    $self.expect("EQUAL")
    $assign_expr_index = $self.parse_expr()
    return & { $__obj = @{}; (StmtNode $__obj "assign" $assign_name $assign_expr_index 2); $__obj }
}
function Parser_parse_expr {
    param($self)
    return $self.parse_add()
}
function Parser_parse_add {
    param($self)
    $left = $self.parse_mul()
    while ($true) {
        if ($self.match("PLUS")) {
            $right = $self.parse_mul()
            $left = $self.add_expr(& { $__obj = @{}; (ExprNode $__obj "bin" 0 "" "+" $left $right 3 1); $__obj })
            continue
        }
        if ($self.match("MINUS")) {
            $right = $self.parse_mul()
            $left = $self.add_expr(& { $__obj = @{}; (ExprNode $__obj "bin" 0 "" "-" $left $right 3 2); $__obj })
            continue
        }
        break
    }
    return $left
}
function Parser_parse_mul {
    param($self)
    $left = $self.parse_unary()
    while ($true) {
        if ($self.match("STAR")) {
            $right = $self.parse_unary()
            $left = $self.add_expr(& { $__obj = @{}; (ExprNode $__obj "bin" 0 "" "*" $left $right 3 3); $__obj })
            continue
        }
        if ($self.match("SLASH")) {
            $right = $self.parse_unary()
            $left = $self.add_expr(& { $__obj = @{}; (ExprNode $__obj "bin" 0 "" "/" $left $right 3 4); $__obj })
            continue
        }
        break
    }
    return $left
}
function Parser_parse_unary {
    param($self)
    if ($self.match("MINUS")) {
        $child = $self.parse_unary()
        return $self.add_expr(& { $__obj = @{}; (ExprNode $__obj "neg" 0 "" "" $child (-1) 4 0); $__obj })
    }
    return $self.parse_primary()
}
function Parser_parse_primary {
    param($self)
    if ($self.match("NUMBER")) {
        $token_num = $self.previous_token()
        return $self.add_expr(& { $__obj = @{}; (ExprNode $__obj "lit" $token_num.number_value "" "" (-1) (-1) 1 0); $__obj })
    }
    if ($self.match("IDENT")) {
        $token_ident = $self.previous_token()
        return $self.add_expr(& { $__obj = @{}; (ExprNode $__obj "var" 0 $token_ident.text "" (-1) (-1) 2 0); $__obj })
    }
    if ($self.match("LPAREN")) {
        $expr_index = $self.parse_expr()
        $self.expect("RPAREN")
        return $expr_index
    }
    $t = $self.current_token()
    throw (RuntimeError ((("primary parse error at pos=" + __pytra_str $t.pos) + " got=") + $t.kind))
}

function eval_expr {
    param($expr_index, $expr_nodes, $env)
    $node = $expr_nodes[$expr_index]
    if (($node.kind_tag -eq 1)) {
        return $node.value
    }
    if (($node.kind_tag -eq 2)) {
        if ((-not ($node.name -eq $env))) {
            throw (RuntimeError ("undefined variable: " + $node.name))
        }
        return $env[$node.name]
    }
    if (($node.kind_tag -eq 4)) {
        return (-(eval_expr $node.left $expr_nodes $env))
    }
    if (($node.kind_tag -eq 3)) {
        $lhs = (eval_expr $node.left $expr_nodes $env)
        $rhs = (eval_expr $node.right $expr_nodes $env)
        if (($node.op_tag -eq 1)) {
            return ($lhs + $rhs)
        }
        if (($node.op_tag -eq 2)) {
            return ($lhs - $rhs)
        }
        if (($node.op_tag -eq 3)) {
            return ($lhs * $rhs)
        }
        if (($node.op_tag -eq 4)) {
            if (($rhs -eq 0)) {
                throw (RuntimeError "division by zero")
            }
            return [Math]::Floor($lhs / $rhs)
        }
        throw (RuntimeError ("unknown operator: " + $node.op))
    }
    throw (RuntimeError ("unknown node kind: " + $node.kind))
}

function execute {
    param($stmts, $expr_nodes, $trace)
    $env = @{}
    $checksum = 0
    $printed = 0
    for ($stmt = $null; $stmt -lt $null; $stmt += 1) {
        if (($stmt.kind_tag -eq 1)) {
            $env[$stmt.name] = (eval_expr $stmt.expr_index $expr_nodes $env)
            continue
        }
        if (($stmt.kind_tag -eq 2)) {
            if ((-not ($stmt.name -eq $env))) {
                throw (RuntimeError ("assign to undefined variable: " + $stmt.name))
            }
            $env[$stmt.name] = (eval_expr $stmt.expr_index $expr_nodes $env)
            continue
        }
        $value = (eval_expr $stmt.expr_index $expr_nodes $env)
        if ($trace) {
            __pytra_print $value
        }
        $norm = ($value % 1000000007)
        if (($norm -lt 0)) {
            $norm += 1000000007
        }
        $checksum = ((($checksum * 131) + $norm) % 1000000007)
        $printed += 1
    }
    if ($trace) {
        __pytra_print "printed:" $printed
    }
    return $checksum
}

function build_benchmark_source {
    param($var_count, $loops)
    $lines = @()
    for ($i = 0; ($i -lt $var_count); $i++) {
        $lines += @(((("let v" + __pytra_str $i) + " = ") + __pytra_str ($i + 1)))
    }
    for ($i = 0; ($i -lt $loops); $i++) {
        $x = ($i % $var_count)
        $y = (($i + 3) % $var_count)
        $c1 = (($i % 7) + 1)
        $c2 = (($i % 11) + 2)
        $lines += @(((((((((("v" + __pytra_str $x) + " = (v") + __pytra_str $x) + " * ") + __pytra_str $c1) + " + v") + __pytra_str $y) + " + 10000) / ") + __pytra_str $c2))
        if ((($i % 97) -eq 0)) {
            $lines += @(("print v" + __pytra_str $x))
        }
    }
    $lines += @("print (v0 + v1 + v2 + v3)")
    return $lines
}

function run_demo {
    param()
    $demo_lines = @()
    $demo_lines += @("let a = 10")
    $demo_lines += @("let b = 3")
    $demo_lines += @("a = (a + b) * 2")
    $demo_lines += @("print a")
    $demo_lines += @("print a / b")
    $tokens = (tokenize $demo_lines)
    $parser = & { $__obj = @{}; (Parser $__obj $tokens); $__obj }
    $stmts = $parser.parse_program()
    $checksum = (execute $stmts $parser.expr_nodes $true)
    __pytra_print "demo_checksum:" $checksum
}

function run_benchmark {
    param()
    $source_lines = (build_benchmark_source 32 120000)
    $start = (perf_counter)
    $tokens = (tokenize $source_lines)
    $parser = & { $__obj = @{}; (Parser $__obj $tokens); $__obj }
    $stmts = $parser.parse_program()
    $checksum = (execute $stmts $parser.expr_nodes $false)
    $elapsed = ((perf_counter) - $start)
    __pytra_print "token_count:" __pytra_len $tokens
    __pytra_print "expr_count:" __pytra_len $parser.expr_nodes
    __pytra_print "stmt_count:" __pytra_len $stmts
    __pytra_print "checksum:" $checksum
    __pytra_print "elapsed_sec:" $elapsed
}

function __pytra_main {
    param()
    (run_demo)
    (run_benchmark)
}

(__pytra_main)
