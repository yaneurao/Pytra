import { PYTRA_TYPE_ID, PY_TYPE_MAP, PY_TYPE_OBJECT, pyRegisterClassType, pyLen, pyStr } from "./pytra/py_runtime.js";
import { perf_counter } from "./pytra/std/time.js";

class Token {
    static PYTRA_TYPE_ID = pyRegisterClassType([PY_TYPE_OBJECT]);
    
    constructor(kind, text, pos, number_value) {
    this[PYTRA_TYPE_ID] = Token.PYTRA_TYPE_ID;
    this.kind = kind;
    this.text = text;
    this.pos = pos;
    this.number_value = number_value;
    }
}

class ExprNode {
    static PYTRA_TYPE_ID = pyRegisterClassType([PY_TYPE_OBJECT]);
    
    constructor(kind, value, name, op, left, right, kind_tag, op_tag) {
    this[PYTRA_TYPE_ID] = ExprNode.PYTRA_TYPE_ID;
    this.kind = kind;
    this.value = value;
    this.name = name;
    this.op = op;
    this.left = left;
    this.right = right;
    this.kind_tag = kind_tag;
    this.op_tag = op_tag;
    }
}

class StmtNode {
    static PYTRA_TYPE_ID = pyRegisterClassType([PY_TYPE_OBJECT]);
    
    constructor(kind, name, expr_index, kind_tag) {
    this[PYTRA_TYPE_ID] = StmtNode.PYTRA_TYPE_ID;
    this.kind = kind;
    this.name = name;
    this.expr_index = expr_index;
    this.kind_tag = kind_tag;
    }
}

function tokenize(lines) {
    let single_char_token_tags = ({[PYTRA_TYPE_ID]: PY_TYPE_MAP, "+": 1, "-": 2, "*": 3, "/": 4, "(": 5, ")": 6, "=": 7});
    let single_char_token_kinds = ["PLUS", "MINUS", "STAR", "SLASH", "LPAREN", "RPAREN", "EQUAL"];
    let tokens = [];
    for (const [line_index, source] of lines.map((__v, __i) => [__i, __v])) {
        let i = 0;
        let n = (source).length;
        while (i < n) {
            let ch = source[(((i) < 0) ? ((source).length + (i)) : (i))];
            
            if (ch === " ") {
                i += 1;
                continue;
            }
            let single_tag = (Object.prototype.hasOwnProperty.call(single_char_token_tags, ch) ? single_char_token_tags[ch] : 0);
            if (single_tag > 0) {
                tokens.push(new Token(single_char_token_kinds[(((single_tag - 1) < 0) ? ((single_char_token_kinds).length + (single_tag - 1)) : (single_tag - 1))], ch, i, 0));
                i += 1;
                continue;
            }
            if ((typeof ch === "string") && (ch).length > 0 && (/^[0-9]+$/.test(ch))) {
                let start = i;
                while (i < n && ((typeof source[(((i) < 0) ? ((source).length + (i)) : (i))] === "string") && (source[(((i) < 0) ? ((source).length + (i)) : (i))]).length > 0 && (/^[0-9]+$/.test(source[(((i) < 0) ? ((source).length + (i)) : (i))])))) {
                    i += 1;
                }
                let text = source.slice(start, i);
                tokens.push(new Token("NUMBER", text, start, Math.trunc(Number(text))));
                continue;
            }
            if (((typeof ch === "string") && (ch).length > 0 && (/^[A-Za-z]+$/.test(ch))) || ch === "_") {
                let start = i;
                while (i < n && ((typeof source[(((i) < 0) ? ((source).length + (i)) : (i))] === "string") && (source[(((i) < 0) ? ((source).length + (i)) : (i))]).length > 0 && (/^[A-Za-z]+$/.test(source[(((i) < 0) ? ((source).length + (i)) : (i))]))) || source[(((i) < 0) ? ((source).length + (i)) : (i))] === "_" || ((typeof source[(((i) < 0) ? ((source).length + (i)) : (i))] === "string") && (source[(((i) < 0) ? ((source).length + (i)) : (i))]).length > 0 && (/^[0-9]+$/.test(source[(((i) < 0) ? ((source).length + (i)) : (i))])))) {
                    i += 1;
                }
                let text = source.slice(start, i);
                if (text === "let") {
                    tokens.push(new Token("LET", text, start, 0));
                } else {
                    if (text === "print") {
                        tokens.push(new Token("PRINT", text, start, 0));
                    } else {
                        tokens.push(new Token("IDENT", text, start, 0));
                    }
                }
                continue;
            }
            throw new Error("tokenize error at line=" + String(line_index) + " pos=" + String(i) + " ch=" + ch);
        }
        tokens.push(new Token("NEWLINE", "", n, 0));
    }
    tokens.push(new Token("EOF", "", (lines).length, 0));
    return tokens;
}

class Parser {
    static PYTRA_TYPE_ID = pyRegisterClassType([PY_TYPE_OBJECT]);
    
    constructor(tokens) {
        this.tokens = (Array.isArray(tokens) ? tokens.slice() : Array.from(tokens));
        this.pos = 0;
        this.expr_nodes = this.new_expr_nodes();
    this[PYTRA_TYPE_ID] = Parser.PYTRA_TYPE_ID;
    }
    
    new_expr_nodes() {
        return [];
    }
    
    current_token() {
        return this.tokens[(((this.pos) < 0) ? ((this.tokens).length + (this.pos)) : (this.pos))];
    }
    
    previous_token() {
        return this.tokens[(((this.pos - 1) < 0) ? ((this.tokens).length + (this.pos - 1)) : (this.pos - 1))];
    }
    
    peek_kind() {
        return this.current_token().kind;
    }
    
    match(kind) {
        if (this.peek_kind() === kind) {
            this.pos += 1;
            return true;
        }
        return false;
    }
    
    expect(kind) {
        let token = this.current_token();
        if (token.kind !== kind) {
            throw new Error("parse error at pos=" + pyStr(token.pos) + ", expected=" + kind + ", got=" + token.kind);
        }
        this.pos += 1;
        return token;
    }
    
    skip_newlines() {
        while (this.match("NEWLINE")) {
            ;
        }
    }
    
    add_expr(node) {
        this.expr_nodes.push(node);
        return (this.expr_nodes).length - 1;
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
            return new StmtNode("let", let_name, let_expr_index, 1);
        }
        if (this.match("PRINT")) {
            let print_expr_index = this.parse_expr();
            return new StmtNode("print", "", print_expr_index, 3);
        }
        let assign_name = this.expect("IDENT").text;
        this.expect("EQUAL");
        let assign_expr_index = this.parse_expr();
        return new StmtNode("assign", assign_name, assign_expr_index, 2);
    }
    
    parse_expr() {
        return this.parse_add();
    }
    
    parse_add() {
        let left = this.parse_mul();
        while (true) {
            if (this.match("PLUS")) {
                let right = this.parse_mul();
                left = this.add_expr(new ExprNode("bin", 0, "", "+", left, right, 3, 1));
                continue;
            }
            if (this.match("MINUS")) {
                let right = this.parse_mul();
                left = this.add_expr(new ExprNode("bin", 0, "", "-", left, right, 3, 2));
                continue;
            }
            break;
        }
        return left;
    }
    
    parse_mul() {
        let left = this.parse_unary();
        while (true) {
            if (this.match("STAR")) {
                let right = this.parse_unary();
                left = this.add_expr(new ExprNode("bin", 0, "", "*", left, right, 3, 3));
                continue;
            }
            if (this.match("SLASH")) {
                let right = this.parse_unary();
                left = this.add_expr(new ExprNode("bin", 0, "", "/", left, right, 3, 4));
                continue;
            }
            break;
        }
        return left;
    }
    
    parse_unary() {
        if (this.match("MINUS")) {
            let child = this.parse_unary();
            return this.add_expr(new ExprNode("neg", 0, "", "", child, -1, 4, 0));
        }
        return this.parse_primary();
    }
    
    parse_primary() {
        if (this.match("NUMBER")) {
            let token_num = this.previous_token();
            return this.add_expr(new ExprNode("lit", token_num.number_value, "", "", -1, -1, 1, 0));
        }
        if (this.match("IDENT")) {
            let token_ident = this.previous_token();
            return this.add_expr(new ExprNode("var", 0, token_ident.text, "", -1, -1, 2, 0));
        }
        if (this.match("LPAREN")) {
            let expr_index = this.parse_expr();
            this.expect("RPAREN");
            return expr_index;
        }
        let t = this.current_token();
        throw new Error("primary parse error at pos=" + pyStr(t.pos) + " got=" + t.kind);
    }
}

function eval_expr(expr_index, expr_nodes, env) {
    let node = expr_nodes[(((expr_index) < 0) ? ((expr_nodes).length + (expr_index)) : (expr_index))];
    
    if (node.kind_tag === 1) {
        return node.value;
    }
    if (node.kind_tag === 2) {
        if (!(Object.prototype.hasOwnProperty.call(env, node.name))) {
            throw new Error("undefined variable: " + node.name);
        }
        return env[node.name];
    }
    if (node.kind_tag === 4) {
        return -eval_expr(node.left, expr_nodes, env);
    }
    if (node.kind_tag === 3) {
        let lhs = eval_expr(node.left, expr_nodes, env);
        let rhs = eval_expr(node.right, expr_nodes, env);
        if (node.op_tag === 1) {
            return lhs + rhs;
        }
        if (node.op_tag === 2) {
            return lhs - rhs;
        }
        if (node.op_tag === 3) {
            return lhs * rhs;
        }
        if (node.op_tag === 4) {
            if (rhs === 0) {
                throw new Error("division by zero");
            }
            return Math.floor(lhs / rhs);
        }
        throw new Error("unknown operator: " + node.op);
    }
    throw new Error("unknown node kind: " + node.kind);
}

function execute(stmts, expr_nodes, trace) {
    let env = ({[PYTRA_TYPE_ID]: PY_TYPE_MAP});
    let checksum = 0;
    let printed = 0;
    
    for (const stmt of stmts) {
        if (stmt.kind_tag === 1) {
            env[stmt.name] = eval_expr(stmt.expr_index, expr_nodes, env);
            continue;
        }
        if (stmt.kind_tag === 2) {
            if (!(Object.prototype.hasOwnProperty.call(env, stmt.name))) {
                throw new Error("assign to undefined variable: " + stmt.name);
            }
            env[stmt.name] = eval_expr(stmt.expr_index, expr_nodes, env);
            continue;
        }
        let value = eval_expr(stmt.expr_index, expr_nodes, env);
        if (trace) {
            console.log(value);
        }
        let norm = value % 1000000007;
        if (norm < 0) {
            norm += 1000000007;
        }
        checksum = (checksum * 131 + norm) % 1000000007;
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
        lines.push("let v" + String(i) + " = " + String(i + 1));
    }
    // Force evaluation of many arithmetic expressions.
    for (let i = 0; i < loops; i += 1) {
        let x = i % var_count;
        let y = (i + 3) % var_count;
        let c1 = i % 7 + 1;
        let c2 = i % 11 + 2;
        lines.push("v" + String(x) + " = (v" + String(x) + " * " + String(c1) + " + v" + String(y) + " + 10000) / " + String(c2));
        if (i % 97 === 0) {
            lines.push("print v" + String(x));
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
    let elapsed = perf_counter() - start;
    
    console.log("token_count:", (tokens).length);
    console.log("expr_count:", pyLen(parser.expr_nodes));
    console.log("stmt_count:", (stmts).length);
    console.log("checksum:", checksum);
    console.log("elapsed_sec:", elapsed);
}

function __pytra_main() {
    run_demo();
    run_benchmark();
}

__pytra_main();
