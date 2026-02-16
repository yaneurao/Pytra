// このファイルは自動生成です（Python -> TypeScript native mode）。

const __pytra_root = process.cwd();
const py_runtime = require(__pytra_root + '/src/ts_module/py_runtime.ts');
const py_math = require(__pytra_root + '/src/ts_module/math.ts');
const py_time = require(__pytra_root + '/src/ts_module/time.ts');
const { pyPrint, pyLen, pyBool, pyRange, pyFloorDiv, pyMod, pyIn, pySlice, pyOrd, pyChr, pyBytearray, pyBytes, pyIsDigit, pyIsAlpha } = py_runtime;
const { perfCounter } = py_time;
const perf_counter = perfCounter;

class Token {
    constructor(kind, text, pos) {
        this.kind = kind;
        this.text = text;
        this.pos = pos;
    }
}
class ExprNode {
    constructor(kind, value, name, op, left, right) {
        this.kind = kind;
        this.value = value;
        this.name = name;
        this.op = op;
        this.left = left;
        this.right = right;
    }
}
class StmtNode {
    constructor(kind, name, expr_index) {
        this.kind = kind;
        this.name = name;
        this.expr_index = expr_index;
    }
}
function tokenize(lines) {
    let tokens = [];
    let line_index = 0;
    while (pyBool(((line_index) < (pyLen(lines))))) {
        let source = lines[line_index];
        let i = 0;
        let n = pyLen(source);
        while (pyBool(((i) < (n)))) {
            let ch = pySlice(source, i, ((i) + (1)));
            if (pyBool(((ch) === (' ')))) {
                i = i + 1;
                continue;
            }
            if (pyBool(((ch) === ('+')))) {
                tokens.push(new Token('PLUS', ch, i));
                i = i + 1;
                continue;
            }
            if (pyBool(((ch) === ('-')))) {
                tokens.push(new Token('MINUS', ch, i));
                i = i + 1;
                continue;
            }
            if (pyBool(((ch) === ('*')))) {
                tokens.push(new Token('STAR', ch, i));
                i = i + 1;
                continue;
            }
            if (pyBool(((ch) === ('/')))) {
                tokens.push(new Token('SLASH', ch, i));
                i = i + 1;
                continue;
            }
            if (pyBool(((ch) === ('(')))) {
                tokens.push(new Token('LPAREN', ch, i));
                i = i + 1;
                continue;
            }
            if (pyBool(((ch) === (')')))) {
                tokens.push(new Token('RPAREN', ch, i));
                i = i + 1;
                continue;
            }
            if (pyBool(((ch) === ('=')))) {
                tokens.push(new Token('EQUAL', ch, i));
                i = i + 1;
                continue;
            }
            if (pyBool(pyIsDigit(ch))) {
                let start = i;
                while (pyBool((((i) < (n)) && pyIsDigit(pySlice(source, i, ((i) + (1))))))) {
                    i = i + 1;
                }
                let text = pySlice(source, start, i);
                tokens.push(new Token('NUMBER', text, start));
                continue;
            }
            if (pyBool((pyIsAlpha(ch) || ((ch) === ('_'))))) {
                let start = i;
                while (pyBool((((i) < (n)) && ((pyIsAlpha(pySlice(source, i, ((i) + (1)))) || ((pySlice(source, i, ((i) + (1)))) === ('_'))) || pyIsDigit(pySlice(source, i, ((i) + (1)))))))) {
                    i = i + 1;
                }
                let text = pySlice(source, start, i);
                if (pyBool(((text) === ('let')))) {
                    tokens.push(new Token('LET', text, start));
                } else {
                    if (pyBool(((text) === ('print')))) {
                        tokens.push(new Token('PRINT', text, start));
                    } else {
                        tokens.push(new Token('IDENT', text, start));
                    }
                }
                continue;
            }
            throw new Error((((((((((('tokenize error at line=') + (String(line_index)))) + (' pos='))) + (String(i)))) + (' ch='))) + (ch)));
        }
        tokens.push(new Token('NEWLINE', '', n));
        line_index = line_index + 1;
    }
    tokens.push(new Token('EOF', '', pyLen(lines)));
    return tokens;
}
class Parser {
    constructor(tokens) {
        this.tokens = tokens;
        this.pos = 0;
        this.expr_nodes = this.new_expr_nodes();
    }

    new_expr_nodes() {
        let nodes = [];
        return nodes;
    }

    peek_kind() {
        return this.tokens[this.pos].kind;
    }

    match(kind) {
        if (pyBool(((this.peek_kind()) === (kind)))) {
            this.pos = this.pos + 1;
            return true;
        }
        return false;
    }

    expect(kind) {
        if (pyBool(((this.peek_kind()) !== (kind)))) {
            let t = this.tokens[this.pos];
            throw new Error((((((((((('parse error at pos=') + (String(t.pos)))) + (', expected='))) + (kind))) + (', got='))) + (t.kind)));
        }
        let token = this.tokens[this.pos];
        this.pos = this.pos + 1;
        return token;
    }

    skip_newlines() {
        while (pyBool(this.match('NEWLINE'))) {
        }
    }

    add_expr(node) {
        this.expr_nodes.push(node);
        return ((pyLen(this.expr_nodes)) - (1));
    }

    parse_program() {
        let stmts = [];
        this.skip_newlines();
        while (pyBool(((this.peek_kind()) !== ('EOF')))) {
            let stmt = this.parse_stmt();
            stmts.push(stmt);
            this.skip_newlines();
        }
        return stmts;
    }

    parse_stmt() {
        if (pyBool(this.match('LET'))) {
            let let_name = this.expect('IDENT').text;
            this.expect('EQUAL');
            let let_expr_index = this.parse_expr();
            return new StmtNode('let', let_name, let_expr_index);
        }
        if (pyBool(this.match('PRINT'))) {
            let print_expr_index = this.parse_expr();
            return new StmtNode('print', '', print_expr_index);
        }
        let assign_name = this.expect('IDENT').text;
        this.expect('EQUAL');
        let assign_expr_index = this.parse_expr();
        return new StmtNode('assign', assign_name, assign_expr_index);
    }

    parse_expr() {
        return this.parse_add();
    }

    parse_add() {
        let left = this.parse_mul();
        let done = false;
        while (pyBool((!pyBool(done)))) {
            if (pyBool(this.match('PLUS'))) {
                let right = this.parse_mul();
                left = this.add_expr(new ExprNode('bin', 0, '', '+', left, right));
                continue;
            }
            if (pyBool(this.match('MINUS'))) {
                let right = this.parse_mul();
                left = this.add_expr(new ExprNode('bin', 0, '', '-', left, right));
                continue;
            }
            done = true;
        }
        return left;
    }

    parse_mul() {
        let left = this.parse_unary();
        let done = false;
        while (pyBool((!pyBool(done)))) {
            if (pyBool(this.match('STAR'))) {
                let right = this.parse_unary();
                left = this.add_expr(new ExprNode('bin', 0, '', '*', left, right));
                continue;
            }
            if (pyBool(this.match('SLASH'))) {
                let right = this.parse_unary();
                left = this.add_expr(new ExprNode('bin', 0, '', '/', left, right));
                continue;
            }
            done = true;
        }
        return left;
    }

    parse_unary() {
        if (pyBool(this.match('MINUS'))) {
            let child = this.parse_unary();
            return this.add_expr(new ExprNode('neg', 0, '', '', child, (-(1))));
        }
        return this.parse_primary();
    }

    parse_primary() {
        if (pyBool(this.match('NUMBER'))) {
            let token_num = this.tokens[((this.pos) - (1))];
            let parsed_value = 0;
            let idx = 0;
            while (pyBool(((idx) < (pyLen(token_num.text))))) {
                let ch = pySlice(token_num.text, idx, ((idx) + (1)));
                parsed_value = ((((((parsed_value) * (10))) + (pyOrd(ch)))) - (pyOrd('0')));
                idx = idx + 1;
            }
            return this.add_expr(new ExprNode('lit', parsed_value, '', '', (-(1)), (-(1))));
        }
        if (pyBool(this.match('IDENT'))) {
            let token_ident = this.tokens[((this.pos) - (1))];
            return this.add_expr(new ExprNode('var', 0, token_ident.text, '', (-(1)), (-(1))));
        }
        if (pyBool(this.match('LPAREN'))) {
            let expr_index = this.parse_expr();
            this.expect('RPAREN');
            return expr_index;
        }
        let t = this.tokens[this.pos];
        throw new Error((((((('primary parse error at pos=') + (String(t.pos)))) + (' got='))) + (t.kind)));
    }
}
function eval_expr(expr_index, expr_nodes, env) {
    if (pyBool(false)) {
        env['__dummy__'] = 0;
    }
    let node = expr_nodes[expr_index];
    if (pyBool(((node.kind) === ('lit')))) {
        return node.value;
    }
    if (pyBool(((node.kind) === ('var')))) {
        if (pyBool((!pyBool(pyIn(node.name, env))))) {
            throw new Error((('undefined variable: ') + (node.name)));
        }
        return env[node.name];
    }
    if (pyBool(((node.kind) === ('neg')))) {
        return (-(eval_expr(node.left, expr_nodes, env)));
    }
    if (pyBool(((node.kind) === ('bin')))) {
        let lhs = eval_expr(node.left, expr_nodes, env);
        let rhs = eval_expr(node.right, expr_nodes, env);
        if (pyBool(((node.op) === ('+')))) {
            return ((lhs) + (rhs));
        }
        if (pyBool(((node.op) === ('-')))) {
            return ((lhs) - (rhs));
        }
        if (pyBool(((node.op) === ('*')))) {
            return ((lhs) * (rhs));
        }
        if (pyBool(((node.op) === ('/')))) {
            if (pyBool(((rhs) === (0)))) {
                throw new Error('division by zero');
            }
            return pyFloorDiv(lhs, rhs);
        }
        throw new Error((('unknown operator: ') + (node.op)));
    }
    throw new Error((('unknown node kind: ') + (node.kind)));
}
function execute(stmts, expr_nodes, trace) {
    let env = Object.fromEntries([]);
    let checksum = 0;
    let printed = 0;
    let stmt;
    for (const __pytra_it_1 of stmts) {
        stmt = __pytra_it_1;
        if (pyBool(((stmt.kind) === ('let')))) {
            env[stmt.name] = eval_expr(stmt.expr_index, expr_nodes, env);
            continue;
        }
        if (pyBool(((stmt.kind) === ('assign')))) {
            if (pyBool((!pyBool(pyIn(stmt.name, env))))) {
                throw new Error((('assign to undefined variable: ') + (stmt.name)));
            }
            env[stmt.name] = eval_expr(stmt.expr_index, expr_nodes, env);
            continue;
        }
        let value = eval_expr(stmt.expr_index, expr_nodes, env);
        if (pyBool(trace)) {
            pyPrint(value);
        }
        let norm = pyMod(value, 1000000007);
        if (pyBool(((norm) < (0)))) {
            norm = norm + 1000000007;
        }
        checksum = pyMod(((((checksum) * (131))) + (norm)), 1000000007);
        printed = printed + 1;
    }
    if (pyBool(trace)) {
        pyPrint('printed:', printed);
    }
    return checksum;
}
function build_benchmark_source(var_count, loops) {
    let lines = [];
    let i;
    for (let __pytra_i_2 = 0; __pytra_i_2 < var_count; __pytra_i_2 += 1) {
        i = __pytra_i_2;
        lines.push((((((('let v') + (String(i)))) + (' = '))) + (String(((i) + (1))))));
    }
    for (let __pytra_i_3 = 0; __pytra_i_3 < loops; __pytra_i_3 += 1) {
        i = __pytra_i_3;
        let x = pyMod(i, var_count);
        let y = pyMod(((i) + (3)), var_count);
        let c1 = ((pyMod(i, 7)) + (1));
        let c2 = ((pyMod(i, 11)) + (2));
        lines.push((((((((((((((((((('v') + (String(x)))) + (' = (v'))) + (String(x)))) + (' * '))) + (String(c1)))) + (' + v'))) + (String(y)))) + (' + 10000) / '))) + (String(c2))));
        if (pyBool(((pyMod(i, 97)) === (0)))) {
            lines.push((('print v') + (String(x))));
        }
    }
    lines.push('print (v0 + v1 + v2 + v3)');
    return lines;
}
function run_demo() {
    let demo_lines = [];
    demo_lines.push('let a = 10');
    demo_lines.push('let b = 3');
    demo_lines.push('a = (a + b) * 2');
    demo_lines.push('print a');
    demo_lines.push('print a / b');
    let tokens = tokenize(demo_lines);
    let parser = new Parser(tokens);
    let stmts = parser.parse_program();
    let checksum = execute(stmts, parser.expr_nodes, true);
    pyPrint('demo_checksum:', checksum);
}
function run_benchmark() {
    let source_lines = build_benchmark_source(32, 120000);
    let start = perf_counter();
    let tokens = tokenize(source_lines);
    let parser = new Parser(tokens);
    let stmts = parser.parse_program();
    let checksum = execute(stmts, parser.expr_nodes, false);
    let elapsed = ((perf_counter()) - (start));
    pyPrint('token_count:', pyLen(tokens));
    pyPrint('expr_count:', pyLen(parser.expr_nodes));
    pyPrint('stmt_count:', pyLen(stmts));
    pyPrint('checksum:', checksum);
    pyPrint('elapsed_sec:', elapsed);
}
function main() {
    run_demo();
    run_benchmark();
}
main();
