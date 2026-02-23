const __pytra_root = process.cwd();
const py_runtime = require(__pytra_root + '/src/js_module/py_runtime.js');
const { PYTRA_TYPE_ID, PY_TYPE_BOOL, PY_TYPE_NUMBER, PY_TYPE_STRING, PY_TYPE_ARRAY, PY_TYPE_MAP, PY_TYPE_SET, PY_TYPE_OBJECT, pyRegisterClassType, pyIsInstance } = py_runtime;

import { dataclass } from "./dataclasses.js";
import { perf_counter } from "./time.js";

class Token {
    static PYTRA_TYPE_ID = pyRegisterClassType([PY_TYPE_OBJECT]);
    
    constructor() {
    this[PYTRA_TYPE_ID] = Token.PYTRA_TYPE_ID;
    }
}

class ExprNode {
    static PYTRA_TYPE_ID = pyRegisterClassType([PY_TYPE_OBJECT]);
    
    constructor() {
    this[PYTRA_TYPE_ID] = ExprNode.PYTRA_TYPE_ID;
    }
}

class StmtNode {
    static PYTRA_TYPE_ID = pyRegisterClassType([PY_TYPE_OBJECT]);
    
    constructor() {
    this[PYTRA_TYPE_ID] = StmtNode.PYTRA_TYPE_ID;
    }
}

function tokenize(lines) {
    let tokens = [];
    for (const [line_index, source] of lines.map((__v, __i) => [__i, __v])) {
        let i = 0;
        let n = (source).length;
        while (i < n) {
            let ch = source[i];
            
            if (ch === " ") {
                i += 1;
                py_continue;
            }
            if (ch === "+") {
                tokens.push(new Token("PLUS", ch, i));
                i += 1;
                py_continue;
            }
            if (ch === "-") {
                tokens.push(new Token("MINUS", ch, i));
                i += 1;
                py_continue;
            }
            if (ch === "*") {
                tokens.push(new Token("STAR", ch, i));
                i += 1;
                py_continue;
            }
            if (ch === "/") {
                tokens.push(new Token("SLASH", ch, i));
                i += 1;
                py_continue;
            }
            if (ch === "(") {
                tokens.push(new Token("LPAREN", ch, i));
                i += 1;
                py_continue;
            }
            if (ch === ")") {
                tokens.push(new Token("RPAREN", ch, i));
                i += 1;
                py_continue;
            }
            if (ch === "=") {
                tokens.push(new Token("EQUAL", ch, i));
                i += 1;
                py_continue;
            }
            if (ch.isdigit()) {
                let start = i;
                while ((i < n) && source[i].isdigit()) {
                    i += 1;
                }
                let text = source[];
                tokens.push(new Token("NUMBER", text, start));
                py_continue;
            }
            if (ch.isalpha() || (ch === "_")) {
                let start = i;
                while ((i < n) && ((source[i].isalpha() || (source[i] === "_")) || source[i].isdigit())) {
                    i += 1;
                }
                let text = source[];
                if (text === "let") {
                    tokens.push(new Token("LET", text, start));
                } else {
                    if (text === "print") {
                        tokens.push(new Token("PRINT", text, start));
                    } else {
                        tokens.push(new Token("IDENT", text, start));
                    }
                }
                py_continue;
            }
            throw RuntimeError(((((("tokenize error at line=" + String(line_index)) + " pos=") + String(i)) + " ch=") + ch));
        }
        tokens.push(new Token("NEWLINE", "", n));
    }
    tokens.push(new Token("EOF", "", (lines).length));
    return tokens;
}

class Parser {
    static PYTRA_TYPE_ID = pyRegisterClassType([PY_TYPE_OBJECT]);
    
    constructor(tokens) {
    this[PYTRA_TYPE_ID] = Parser.PYTRA_TYPE_ID;
        this.tokens = tokens;
        this.pos = 0;
        this.expr_nodes = this.new_expr_nodes();
    }
    
    new_expr_nodes() {
        return [];
    }
    
    peek_kind() {
        return this.tokens[this.pos].kind;
    }
    
    match(kind) {
        if (this.peek_kind() === kind) {
            this.pos += 1;
            return true;
        }
        return false;
    }
    
    expect(kind) {
        if (this.peek_kind() !== kind) {
            let t = this.tokens[this.pos];
            throw RuntimeError(((((("parse error at pos=" + String(t.pos)) + ", expected=") + kind) + ", got=") + t.kind));
        }
        let token = this.tokens[this.pos];
        this.pos += 1;
        return token;
    }
    
    skip_newlines() {
        while (this.match("NEWLINE")) {
            // pass
        }
    }
    
    add_expr(node) {
        this.expr_nodes.push(node);
        return ((this.expr_nodes).length - 1);
    }
    
    parse_program() {
        let stmts = [];
        this.skip_newlines();
        while (this.peek_kind() !== "EOF") {
            let stmt = this.parse_stmt();
            stmts.push(stmt);
            this.skip_newlines();
        }
        return stmts;
    }
    
    parse_stmt() {
        if (this.match("LET")) {
            let let_name = this.expect("IDENT").text;
            this.expect("EQUAL");
            let let_expr_index = this.parse_expr();
            return new StmtNode("let", let_name, let_expr_index);
        }
        if (this.match("PRINT")) {
            let print_expr_index = this.parse_expr();
            return new StmtNode("print", "", print_expr_index);
        }
        let assign_name = this.expect("IDENT").text;
        this.expect("EQUAL");
        let assign_expr_index = this.parse_expr();
        return new StmtNode("assign", assign_name, assign_expr_index);
    }
    
    parse_expr() {
        return this.parse_add();
    }
    
    parse_add() {
        let left = this.parse_mul();
        while (true) {
            if (this.match("PLUS")) {
                let right = this.parse_mul();
                left = this.add_expr(new ExprNode("bin", 0, "", "+", left, right));
                py_continue;
            }
            if (this.match("MINUS")) {
                let right = this.parse_mul();
                left = this.add_expr(new ExprNode("bin", 0, "", "-", left, right));
                py_continue;
            }
            py_break;
        }
        return left;
    }
    
    parse_mul() {
        let left = this.parse_unary();
        while (true) {
            if (this.match("STAR")) {
                let right = this.parse_unary();
                left = this.add_expr(new ExprNode("bin", 0, "", "*", left, right));
                py_continue;
            }
            if (this.match("SLASH")) {
                let right = this.parse_unary();
                left = this.add_expr(new ExprNode("bin", 0, "", "/", left, right));
                py_continue;
            }
            py_break;
        }
        return left;
    }
    
    parse_unary() {
        if (this.match("MINUS")) {
            let child = this.parse_unary();
            return this.add_expr(new ExprNode("neg", 0, "", "", child, (-1)));
        }
        return this.parse_primary();
    }
    
    parse_primary() {
        if (this.match("NUMBER")) {
            let token_num = this.tokens[(this.pos - 1)];
            return this.add_expr(new ExprNode("lit", Math.trunc(Number(token_num.text)), "", "", (-1), (-1)));
        }
        if (this.match("IDENT")) {
            let token_ident = this.tokens[(this.pos - 1)];
            return this.add_expr(new ExprNode("var", 0, token_ident.text, "", (-1), (-1)));
        }
        if (this.match("LPAREN")) {
            let expr_index = this.parse_expr();
            this.expect("RPAREN");
            return expr_index;
        }
        let t = this.tokens[this.pos];
        throw RuntimeError(((("primary parse error at pos=" + String(t.pos)) + " got=") + t.kind));
    }
}

function eval_expr(expr_index, expr_nodes, env) {
    let node = expr_nodes[expr_index];
    
    if (node.kind === "lit") {
        return node.value;
    }
    if (node.kind === "var") {
        if (!(node.name == env)) {
            throw RuntimeError(("undefined variable: " + node.name));
        }
        return env[node.name];
    }
    if (node.kind === "neg") {
        return (-eval_expr(node.left, expr_nodes, env));
    }
    if (node.kind === "bin") {
        let lhs = eval_expr(node.left, expr_nodes, env);
        let rhs = eval_expr(node.right, expr_nodes, env);
        if (node.op === "+") {
            return (lhs + rhs);
        }
        if (node.op === "-") {
            return (lhs - rhs);
        }
        if (node.op === "*") {
            return (lhs * rhs);
        }
        if (node.op === "/") {
            if (rhs === 0) {
                throw RuntimeError("division by zero");
            }
            return Math.floor((lhs) / (rhs));
        }
        throw RuntimeError(("unknown operator: " + node.op));
    }
    throw RuntimeError(("unknown node kind: " + node.kind));
}

function execute(stmts, expr_nodes, trace) {
    let env = ({[PYTRA_TYPE_ID]: PY_TYPE_MAP});
    let checksum = 0;
    let printed = 0;
    
    for (const stmt of stmts) {
        if (stmt.kind === "let") {
            env[stmt.name] = eval_expr(stmt.expr_index, expr_nodes, env);
            py_continue;
        }
        if (stmt.kind === "assign") {
            if (!(stmt.name == env)) {
                throw RuntimeError(("assign to undefined variable: " + stmt.name));
            }
            env[stmt.name] = eval_expr(stmt.expr_index, expr_nodes, env);
            py_continue;
        }
        let value = eval_expr(stmt.expr_index, expr_nodes, env);
        if (trace) {
            console.log(value);
        }
        let norm = (value % 1000000007);
        if (norm < 0) {
            norm += 1000000007;
        }
        checksum = ((((checksum * 131) + norm)) % 1000000007);
        printed += 1;
    }
    if (trace) {
        console.log("printed:", printed);
    }
    return checksum;
}

function build_benchmark_source(var_count, loops) {
    let lines = [];
    
    // Declare initial variables.
    for (let i = 0; i < var_count; i += 1) {
        lines.push(((("let v" + String(i)) + " = ") + String((i + 1))));
    }
    // Force evaluation of many arithmetic expressions.
    for (let i = 0; i < loops; i += 1) {
        let x = (i % var_count);
        let y = (((i + 3)) % var_count);
        let c1 = ((i % 7) + 1);
        let c2 = ((i % 11) + 2);
        lines.push(((((((((("v" + String(x)) + " = (v") + String(x)) + " * ") + String(c1)) + " + v") + String(y)) + " + 10000) / ") + String(c2)));
        if ((i % 97) === 0) {
            lines.push(("print v" + String(x)));
        }
    }
    // Print final values together.
    lines.push("print (v0 + v1 + v2 + v3)");
    return lines;
}

function run_demo() {
    let demo_lines = [];
    demo_lines.push("let a = 10");
    demo_lines.push("let b = 3");
    demo_lines.push("a = (a + b) * 2");
    demo_lines.push("print a");
    demo_lines.push("print a / b");
    
    let tokens = tokenize(demo_lines);
    let parser = new Parser(tokens);
    let stmts = parser.parse_program();
    let checksum = execute(stmts, parser.expr_nodes, true);
    console.log("demo_checksum:", checksum);
}

function run_benchmark() {
    let source_lines = build_benchmark_source(32, 120000);
    let start = perf_counter();
    let tokens = tokenize(source_lines);
    let parser = new Parser(tokens);
    let stmts = parser.parse_program();
    let checksum = execute(stmts, parser.expr_nodes, false);
    let elapsed = (perf_counter() - start);
    
    console.log("token_count:", (tokens).length);
    console.log("expr_count:", (parser.expr_nodes).length);
    console.log("stmt_count:", (stmts).length);
    console.log("checksum:", checksum);
    console.log("elapsed_sec:", elapsed);
}

function __pytra_main() {
    run_demo();
    run_benchmark();
}

// __main__ guard
main();
