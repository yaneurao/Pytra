use crate::dataclasses::dataclass;
use crate::time::perf_counter;

#[derive(Clone, Debug)]
struct Token {
    kind: String,
    text: String,
    pos: i64,
}
impl Token {
    fn new() -> Self {
        Self {
            kind: String::new(),
            text: String::new(),
            pos: 0,
        }
    }
}

#[derive(Clone, Debug)]
struct ExprNode {
    kind: String,
    value: i64,
    name: String,
    op: String,
    left: i64,
    right: i64,
}
impl ExprNode {
    fn new() -> Self {
        Self {
            kind: String::new(),
            value: 0,
            name: String::new(),
            op: String::new(),
            left: 0,
            right: 0,
        }
    }
}

#[derive(Clone, Debug)]
struct StmtNode {
    kind: String,
    name: String,
    expr_index: i64,
}
impl StmtNode {
    fn new() -> Self {
        Self {
            kind: String::new(),
            name: String::new(),
            expr_index: 0,
        }
    }
}

fn tokenize(lines: Vec<String>) -> Vec<Token> {
    let mut tokens: Vec<Token> = vec![];
    for (line_index, source) in enumerate(lines) {
        let mut i: i64 = 0;
        let n: i64 = source.len() as i64;
        while i < n {
            let ch: String = source[i as usize];
            
            if ch == " " {
                i += 1;
                py_continue;
            }
            if ch == "+" {
                tokens.push(Token::new("PLUS", ch, i));
                i += 1;
                py_continue;
            }
            if ch == "-" {
                tokens.push(Token::new("MINUS", ch, i));
                i += 1;
                py_continue;
            }
            if ch == "*" {
                tokens.push(Token::new("STAR", ch, i));
                i += 1;
                py_continue;
            }
            if ch == "/" {
                tokens.push(Token::new("SLASH", ch, i));
                i += 1;
                py_continue;
            }
            if ch == "(" {
                tokens.push(Token::new("LPAREN", ch, i));
                i += 1;
                py_continue;
            }
            if ch == ")" {
                tokens.push(Token::new("RPAREN", ch, i));
                i += 1;
                py_continue;
            }
            if ch == "=" {
                tokens.push(Token::new("EQUAL", ch, i));
                i += 1;
                py_continue;
            }
            if ch.isdigit() {
                let mut start: i64 = i;
                while (i < n) && source[i as usize].isdigit() {
                    i += 1;
                }
                let mut text: String = source[ as usize];
                tokens.push(Token::new("NUMBER", text, start));
                py_continue;
            }
            if ch.isalpha() || (ch == "_") {
                let mut start = i;
                while (i < n) && ((source[i as usize].isalpha() || (source[i as usize] == "_")) || source[i as usize].isdigit()) {
                    i += 1;
                }
                let mut text = source[ as usize];
                if text == "let" {
                    tokens.push(Token::new("LET", text, start));
                } else {
                    if text == "print" {
                        tokens.push(Token::new("PRINT", text, start));
                    } else {
                        tokens.push(Token::new("IDENT", text, start));
                    }
                }
                py_continue;
            }
            // unsupported stmt: Raise
        }
        tokens.push(Token::new("NEWLINE", "", n));
    }
    tokens.push(Token::new("EOF", "", lines.len() as i64));
    return tokens;
}

#[derive(Clone, Debug)]
struct Parser {
    tokens: Vec<Token>,
    pos: i64,
    expr_nodes: Vec<ExprNode>,
}
impl Parser {
    fn new(tokens: Vec<Token>) -> Self {
        Self {
            tokens: Vec::new(),
            pos: 0,
            expr_nodes: Vec::new(),
        }
    }
    
    fn new_expr_nodes(&self) -> Vec<ExprNode> {
        return vec![];
    }
    
    fn peek_kind(&self) -> String {
        return py_self.tokens[py_self.pos as usize].kind;
    }
    
    fn py_match(&self, kind: String) -> bool {
        if py_self.peek_kind() == kind {
            py_self.pos += 1;
            return true;
        }
        return false;
    }
    
    fn expect(&self, kind: String) -> Token {
        if py_self.peek_kind() != kind {
            let t: Token = py_self.tokens[py_self.pos as usize];
            // unsupported stmt: Raise
        }
        let token: Token = py_self.tokens[py_self.pos as usize];
        py_self.pos += 1;
        return token;
    }
    
    fn skip_newlines(&self) {
        while py_self.py_match("NEWLINE") {
            // pass
        }
    }
    
    fn add_expr(&self, node: ExprNode) -> i64 {
        py_self.expr_nodes.push(node);
        return (py_self.expr_nodes.len() as i64 - 1);
    }
    
    fn parse_program(&self) -> Vec<StmtNode> {
        let mut stmts: Vec<StmtNode> = vec![];
        py_self.skip_newlines();
        while py_self.peek_kind() != "EOF" {
            let stmt: StmtNode = py_self.parse_stmt();
            stmts.push(stmt);
            py_self.skip_newlines();
        }
        return stmts;
    }
    
    fn parse_stmt(&self) -> StmtNode {
        if py_self.py_match("LET") {
            let let_name: String = py_self.expect("IDENT").text;
            py_self.expect("EQUAL");
            let let_expr_index: i64 = py_self.parse_expr();
            return StmtNode::new("let", let_name, let_expr_index);
        }
        if py_self.py_match("PRINT") {
            let print_expr_index: i64 = py_self.parse_expr();
            return StmtNode::new("print", "", print_expr_index);
        }
        let assign_name: String = py_self.expect("IDENT").text;
        py_self.expect("EQUAL");
        let assign_expr_index: i64 = py_self.parse_expr();
        return StmtNode::new("assign", assign_name, assign_expr_index);
    }
    
    fn parse_expr(&self) -> i64 {
        return py_self.parse_add();
    }
    
    fn parse_add(&self) -> i64 {
        let mut left: i64 = py_self.parse_mul();
        while true {
            if py_self.py_match("PLUS") {
                let mut right: i64 = py_self.parse_mul();
                left = py_self.add_expr(ExprNode::new("bin", 0, "", "+", left, right));
                py_continue;
            }
            if py_self.py_match("MINUS") {
                let mut right = py_self.parse_mul();
                left = py_self.add_expr(ExprNode::new("bin", 0, "", "-", left, right));
                py_continue;
            }
            py_break;
        }
        return left;
    }
    
    fn parse_mul(&self) -> i64 {
        let mut left: i64 = py_self.parse_unary();
        while true {
            if py_self.py_match("STAR") {
                let mut right: i64 = py_self.parse_unary();
                left = py_self.add_expr(ExprNode::new("bin", 0, "", "*", left, right));
                py_continue;
            }
            if py_self.py_match("SLASH") {
                let mut right = py_self.parse_unary();
                left = py_self.add_expr(ExprNode::new("bin", 0, "", "/", left, right));
                py_continue;
            }
            py_break;
        }
        return left;
    }
    
    fn parse_unary(&self) -> i64 {
        if py_self.py_match("MINUS") {
            let child: i64 = py_self.parse_unary();
            return py_self.add_expr(ExprNode::new("neg", 0, "", "", child, (-1)));
        }
        return py_self.parse_primary();
    }
    
    fn parse_primary(&self) -> i64 {
        if py_self.py_match("NUMBER") {
            let token_num: Token = py_self.tokens[(py_self.pos - 1) as usize];
            return py_self.add_expr(ExprNode::new("lit", token_num.text as i64, "", "", (-1), (-1)));
        }
        if py_self.py_match("IDENT") {
            let token_ident: Token = py_self.tokens[(py_self.pos - 1) as usize];
            return py_self.add_expr(ExprNode::new("var", 0, token_ident.text, "", (-1), (-1)));
        }
        if py_self.py_match("LPAREN") {
            let expr_index: i64 = py_self.parse_expr();
            py_self.expect("RPAREN");
            return expr_index;
        }
        let t = py_self.tokens[py_self.pos as usize];
        // unsupported stmt: Raise
    }
}

fn eval_expr(expr_index: i64, expr_nodes: Vec<ExprNode>, env: ::std::collections::BTreeMap<String, i64>) -> i64 {
    let node: ExprNode = expr_nodes[expr_index as usize];
    
    if node.kind == "lit" {
        return node.value;
    }
    if node.kind == "var" {
        if !(node.name == env) {
            // unsupported stmt: Raise
        }
        return env[node.name as usize];
    }
    if node.kind == "neg" {
        return (-eval_expr(node.left, expr_nodes, env));
    }
    if node.kind == "bin" {
        let lhs: i64 = eval_expr(node.left, expr_nodes, env);
        let rhs: i64 = eval_expr(node.right, expr_nodes, env);
        if node.op == "+" {
            return (lhs + rhs);
        }
        if node.op == "-" {
            return (lhs - rhs);
        }
        if node.op == "*" {
            return (lhs * rhs);
        }
        if node.op == "/" {
            if rhs == 0 {
                // unsupported stmt: Raise
            }
            return (lhs / rhs);
        }
        // unsupported stmt: Raise
    }
    // unsupported stmt: Raise
}

fn execute(stmts: Vec<StmtNode>, expr_nodes: Vec<ExprNode>, trace: bool) -> i64 {
    let mut env: ::std::collections::BTreeMap<String, i64> = ::std::collections::BTreeMap::from([]);
    let mut checksum: i64 = 0;
    let mut printed: i64 = 0;
    
    for stmt in (stmts).clone() {
        if stmt.kind == "let" {
            env[stmt.name as usize] = eval_expr(stmt.expr_index, expr_nodes, env);
            py_continue;
        }
        if stmt.kind == "assign" {
            if !(stmt.name == env) {
                // unsupported stmt: Raise
            }
            env[stmt.name as usize] = eval_expr(stmt.expr_index, expr_nodes, env);
            py_continue;
        }
        let value: i64 = eval_expr(stmt.expr_index, expr_nodes, env);
        if trace {
            println!("{}", value);
        }
        let mut norm: i64 = (value % 1000000007);
        if norm < 0 {
            norm += 1000000007;
        }
        checksum = ((((checksum * 131) + norm)) % 1000000007);
        printed += 1;
    }
    if trace {
        println!("{:?}", ("printed:", printed));
    }
    return checksum;
}

fn build_benchmark_source(var_count: i64, loops: i64) -> Vec<String> {
    let mut lines: Vec<String> = vec![];
    
    // Declare initial variables.
    let mut i: i64 = 0;
    while i < var_count {
        lines.push(((("let v" + i.to_string()) + " = ") + (i + 1).to_string()));
        i += 1;
    }
    // Force evaluation of many arithmetic expressions.
    let mut i: i64 = 0;
    while i < loops {
        let x: i64 = (i % var_count);
        let y: i64 = (((i + 3)) % var_count);
        let c1: i64 = ((i % 7) + 1);
        let c2: i64 = ((i % 11) + 2);
        lines.push(((((((((("v" + x.to_string()) + " = (v") + x.to_string()) + " * ") + c1.to_string()) + " + v") + y.to_string()) + " + 10000) / ") + c2.to_string()));
        if (i % 97) == 0 {
            lines.push(("print v" + x.to_string()));
        }
        i += 1;
    }
    // Print final values together.
    lines.push("print (v0 + v1 + v2 + v3)");
    return lines;
}

fn run_demo() {
    let mut demo_lines: Vec<String> = vec![];
    demo_lines.push("let a = 10");
    demo_lines.push("let b = 3");
    demo_lines.push("a = (a + b) * 2");
    demo_lines.push("print a");
    demo_lines.push("print a / b");
    
    let tokens: Vec<Token> = tokenize(demo_lines);
    let parser: Parser = Parser::new(tokens);
    let stmts: Vec<StmtNode> = parser.parse_program();
    let checksum: i64 = execute(stmts, parser.expr_nodes, true);
    println!("{:?}", ("demo_checksum:", checksum));
}

fn run_benchmark() {
    let source_lines: Vec<String> = build_benchmark_source(32, 120000);
    let start: f64 = perf_counter();
    let tokens: Vec<Token> = tokenize(source_lines);
    let parser: Parser = Parser::new(tokens);
    let stmts: Vec<StmtNode> = parser.parse_program();
    let checksum: i64 = execute(stmts, parser.expr_nodes, false);
    let elapsed: f64 = (perf_counter() - start);
    
    println!("{:?}", ("token_count:", tokens.len() as i64));
    println!("{:?}", ("expr_count:", parser.expr_nodes.len() as i64));
    println!("{:?}", ("stmt_count:", stmts.len() as i64));
    println!("{:?}", ("checksum:", checksum));
    println!("{:?}", ("elapsed_sec:", elapsed));
}

fn __pytra_main() {
    run_demo();
    run_benchmark();
}

fn main() {
    main();
}
