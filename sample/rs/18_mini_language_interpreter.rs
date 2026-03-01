mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::time::perf_counter;

#[derive(Clone, Debug)]
struct Token {
    kind: String,
    text: String,
    pos: i64,
    number_value: i64,
}
impl Token {
    fn new(kind: String, text: String, pos: i64, number_value: i64) -> Self {
        Self {
            kind: kind,
            text: text,
            pos: pos,
            number_value: number_value,
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
    kind_tag: i64,
    op_tag: i64,
}
impl ExprNode {
    fn new(kind: String, value: i64, name: String, op: String, left: i64, right: i64, kind_tag: i64, op_tag: i64) -> Self {
        Self {
            kind: kind,
            value: value,
            name: name,
            op: op,
            left: left,
            right: right,
            kind_tag: kind_tag,
            op_tag: op_tag,
        }
    }
}


#[derive(Clone, Debug)]
struct StmtNode {
    kind: String,
    name: String,
    expr_index: i64,
    kind_tag: i64,
}
impl StmtNode {
    fn new(kind: String, name: String, expr_index: i64, kind_tag: i64) -> Self {
        Self {
            kind: kind,
            name: name,
            expr_index: expr_index,
            kind_tag: kind_tag,
        }
    }
}


fn tokenize(lines: &Vec<String>) -> Vec<Token> {
    let single_char_token_tags: ::std::collections::BTreeMap<String, i64> = ::std::collections::BTreeMap::from([(("+").to_string(), 1), (("-").to_string(), 2), (("*").to_string(), 3), (("/").to_string(), 4), (("(").to_string(), 5), ((")").to_string(), 6), (("=").to_string(), 7)]);
    let single_char_token_kinds: Vec<String> = vec![("PLUS").to_string(), ("MINUS").to_string(), ("STAR").to_string(), ("SLASH").to_string(), ("LPAREN").to_string(), ("RPAREN").to_string(), ("EQUAL").to_string()];
    let mut tokens: Vec<Token> = vec![];
    for (line_index, source) in (lines).iter().enumerate().map(|(i, v)| (i as i64, v)) {
        let mut i: i64 = 0;
        let n: i64 = source.len() as i64;
        while i < n {
            let ch: String = ((py_str_at(&source, ((i) as i64))).to_string());
            
            if ch == " " {
                i += 1;
                continue;
            }
            let single_tag: i64 = py_any_to_i64(&single_char_token_tags.get(&ch).cloned().unwrap_or(0));
            if single_tag > 0 {
                tokens.push(Token::new((((single_char_token_kinds[((if ((single_tag - 1) as i64) < 0 { (single_char_token_kinds.len() as i64 + ((single_tag - 1) as i64)) } else { ((single_tag - 1) as i64) }) as usize)]).clone()).to_string()), ((ch).to_string()), i, 0));
                i += 1;
                continue;
            }
            if py_isdigit(&ch) {
                let mut start: i64 = i;
                while (i < n) && py_isdigit(&py_str_at(&source, ((i) as i64))) {
                    i += 1;
                }
                let mut text: String = ((py_slice_str(&source, Some((start) as i64), Some((i) as i64))).to_string());
                tokens.push(Token::new(("NUMBER").to_string(), ((text).to_string()), start, ((text).parse::<i64>().unwrap_or(0))));
                continue;
            }
            if py_isalpha(&ch) || (ch == "_") {
                let mut start = i;
                while (i < n) && ((py_isalpha(&py_str_at(&source, ((i) as i64))) || (py_str_at(&source, ((i) as i64)) == "_")) || py_isdigit(&py_str_at(&source, ((i) as i64)))) {
                    i += 1;
                }
                let mut text = py_slice_str(&source, Some((start) as i64), Some((i) as i64));
                if text == "let" {
                    tokens.push(Token::new(("LET").to_string(), ((text).to_string()), start, 0));
                } else {
                    if text == "print" {
                        tokens.push(Token::new(("PRINT").to_string(), ((text).to_string()), start, 0));
                    } else {
                        tokens.push(Token::new(("IDENT").to_string(), ((text).to_string()), start, 0));
                    }
                }
                continue;
            }
            panic!("{}", format!("{}{}", format!("{}{}", format!("{}{}", format!("{}{}", format!("{}{}", ("tokenize error at line=").to_string(), (line_index).to_string()), (" pos=").to_string()), (i).to_string()), (" ch=").to_string()), ch));
        }
        tokens.push(Token::new(("NEWLINE").to_string(), ("").to_string(), n, 0));
    }
    tokens.push(Token::new(("EOF").to_string(), ("").to_string(), lines.len() as i64, 0));
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
            tokens: tokens,
            pos: 0,
            expr_nodes: Vec::new(),
        }
    }
    
    fn new_expr_nodes(&self) -> Vec<ExprNode> {
        return vec![];
    }
    
    fn current_token(&self) -> Token {
        return (self.tokens[((if ((self.pos) as i64) < 0 { (self.tokens.len() as i64 + ((self.pos) as i64)) } else { ((self.pos) as i64) }) as usize)]).clone();
    }
    
    fn previous_token(&self) -> Token {
        return (self.tokens[((if ((self.pos - 1) as i64) < 0 { (self.tokens.len() as i64 + ((self.pos - 1) as i64)) } else { ((self.pos - 1) as i64) }) as usize)]).clone();
    }
    
    fn peek_kind(&self) -> String {
        return self.current_token().kind;
    }
    
    fn py_match(&mut self, kind: &str) -> bool {
        if self.peek_kind() == kind {
            self.pos += 1;
            return true;
        }
        return false;
    }
    
    fn expect(&mut self, kind: &str) -> Token {
        let token: Token = self.current_token();
        if token.kind != kind {
            panic!("{}", format!("{}{}", format!("{}{}", format!("{}{}", format!("{}{}", format!("{}{}", ("parse error at pos=").to_string(), py_any_to_string(&token.pos)), (", expected=").to_string()), kind), (", got=").to_string()), token.kind));
        }
        self.pos += 1;
        return token;
    }
    
    fn skip_newlines(&mut self) {
        while self.py_match("NEWLINE") {
            ();
        }
    }
    
    fn add_expr(&mut self, node: ExprNode) -> i64 {
        self.expr_nodes.push(node);
        return self.expr_nodes.len() as i64 - 1;
    }
    
    fn parse_program(&mut self) -> Vec<StmtNode> {
        let mut stmts: Vec<StmtNode> = vec![];
        self.skip_newlines();
        while self.peek_kind() != "EOF" {
            let stmt: StmtNode = self.parse_stmt();
            stmts.push(stmt);
            self.skip_newlines();
        }
        return stmts;
    }
    
    fn parse_stmt(&mut self) -> StmtNode {
        if self.py_match("LET") {
            let let_name: String = ((py_any_to_string(&self.expect("IDENT").text)).to_string());
            self.expect("EQUAL");
            let let_expr_index: i64 = self.parse_expr();
            return StmtNode::new(("let").to_string(), ((let_name).to_string()), let_expr_index, 1);
        }
        if self.py_match("PRINT") {
            let print_expr_index: i64 = self.parse_expr();
            return StmtNode::new(("print").to_string(), ("").to_string(), print_expr_index, 3);
        }
        let assign_name: String = ((py_any_to_string(&self.expect("IDENT").text)).to_string());
        self.expect("EQUAL");
        let assign_expr_index: i64 = self.parse_expr();
        return StmtNode::new(("assign").to_string(), ((assign_name).to_string()), assign_expr_index, 2);
    }
    
    fn parse_expr(&mut self) -> i64 {
        return self.parse_add();
    }
    
    fn parse_add(&mut self) -> i64 {
        let mut left: i64 = self.parse_mul();
        while true {
            if self.py_match("PLUS") {
                let mut right: i64 = self.parse_mul();
                left = self.add_expr(ExprNode::new(("bin").to_string(), 0, ("").to_string(), ("+").to_string(), left, right, 3, 1));
                continue;
            }
            if self.py_match("MINUS") {
                let mut right = self.parse_mul();
                left = self.add_expr(ExprNode::new(("bin").to_string(), 0, ("").to_string(), ("-").to_string(), left, right, 3, 2));
                continue;
            }
            break;
        }
        return left;
    }
    
    fn parse_mul(&mut self) -> i64 {
        let mut left: i64 = self.parse_unary();
        while true {
            if self.py_match("STAR") {
                let mut right: i64 = self.parse_unary();
                left = self.add_expr(ExprNode::new(("bin").to_string(), 0, ("").to_string(), ("*").to_string(), left, right, 3, 3));
                continue;
            }
            if self.py_match("SLASH") {
                let mut right = self.parse_unary();
                left = self.add_expr(ExprNode::new(("bin").to_string(), 0, ("").to_string(), ("/").to_string(), left, right, 3, 4));
                continue;
            }
            break;
        }
        return left;
    }
    
    fn parse_unary(&mut self) -> i64 {
        if self.py_match("MINUS") {
            let child: i64 = self.parse_unary();
            return self.add_expr(ExprNode::new(("neg").to_string(), 0, ("").to_string(), ("").to_string(), child, -1, 4, 0));
        }
        return self.parse_primary();
    }
    
    fn parse_primary(&mut self) -> i64 {
        if self.py_match("NUMBER") {
            let token_num: Token = self.previous_token();
            return self.add_expr(ExprNode::new(("lit").to_string(), token_num.number_value, ("").to_string(), ("").to_string(), -1, -1, 1, 0));
        }
        if self.py_match("IDENT") {
            let token_ident: Token = self.previous_token();
            return self.add_expr(ExprNode::new(("var").to_string(), 0, ((token_ident.text).to_string()), ("").to_string(), -1, -1, 2, 0));
        }
        if self.py_match("LPAREN") {
            let expr_index: i64 = self.parse_expr();
            self.expect("RPAREN");
            return expr_index;
        }
        let t = self.current_token();
        panic!("{}", format!("{}{}", format!("{}{}", format!("{}{}", ("primary parse error at pos=").to_string(), py_any_to_string(&t.pos)), (" got=").to_string()), t.kind));
    }
}


fn eval_expr(expr_index: i64, expr_nodes: &Vec<ExprNode>, env: &::std::collections::BTreeMap<String, i64>) -> i64 {
    let node: ExprNode = (expr_nodes[((if ((expr_index) as i64) < 0 { (expr_nodes.len() as i64 + ((expr_index) as i64)) } else { ((expr_index) as i64) }) as usize)]).clone();
    
    if node.kind_tag == 1 {
        return node.value;
    }
    if node.kind_tag == 2 {
        if !((env.contains_key(&node.name))) {
            panic!("{}", format!("{}{}", ("undefined variable: ").to_string(), node.name));
        }
        return env.get(&node.name).cloned().expect("dict key not found");
    }
    if node.kind_tag == 4 {
        return -eval_expr(node.left, expr_nodes, env);
    }
    if node.kind_tag == 3 {
        let lhs: i64 = eval_expr(node.left, expr_nodes, env);
        let rhs: i64 = eval_expr(node.right, expr_nodes, env);
        if node.op_tag == 1 {
            return lhs + rhs;
        }
        if node.op_tag == 2 {
            return lhs - rhs;
        }
        if node.op_tag == 3 {
            return lhs * rhs;
        }
        if node.op_tag == 4 {
            if rhs == 0 {
                panic!("{}", ("division by zero").to_string());
            }
            return lhs / rhs;
        }
        panic!("{}", format!("{}{}", ("unknown operator: ").to_string(), node.op));
    }
    panic!("{}", format!("{}{}", ("unknown node kind: ").to_string(), node.kind));
}

fn execute(stmts: &Vec<StmtNode>, expr_nodes: &Vec<ExprNode>, trace: bool) -> i64 {
    let mut env: ::std::collections::BTreeMap<String, i64> = ::std::collections::BTreeMap::from([]);
    let mut checksum: i64 = 0;
    let mut printed: i64 = 0;
    
    for stmt in (stmts).iter() {
        if stmt.kind_tag == 1 {
            env.insert(((stmt.name).to_string()), eval_expr(stmt.expr_index, expr_nodes, &(env)));
            continue;
        }
        if stmt.kind_tag == 2 {
            if !((env.contains_key(&stmt.name))) {
                panic!("{}", format!("{}{}", ("assign to undefined variable: ").to_string(), stmt.name));
            }
            env.insert(((stmt.name).to_string()), eval_expr(stmt.expr_index, expr_nodes, &(env)));
            continue;
        }
        let value: i64 = eval_expr(stmt.expr_index, expr_nodes, &(env));
        if trace {
            println!("{}", value);
        }
        let mut norm: i64 = value % 1000000007;
        if norm < 0 {
            norm += 1000000007;
        }
        checksum = (checksum * 131 + norm) % 1000000007;
        printed += 1;
    }
    if trace {
        println!("{} {}", ("printed:").to_string(), printed);
    }
    return checksum;
}

fn build_benchmark_source(var_count: i64, loops: i64) -> Vec<String> {
    let mut lines: Vec<String> = vec![];
    
    // Declare initial variables.
    let mut i: i64 = 0;
    while i < var_count {
        lines.push(format!("{}{}", format!("{}{}", format!("{}{}", ("let v").to_string(), (i).to_string()), (" = ").to_string()), (i + 1).to_string()));
        i += 1;
    }
    // Force evaluation of many arithmetic expressions.
    let mut i: i64 = 0;
    while i < loops {
        let x: i64 = i % var_count;
        let y: i64 = (i + 3) % var_count;
        let c1: i64 = i % 7 + 1;
        let c2: i64 = i % 11 + 2;
        lines.push(format!("{}{}", format!("{}{}", format!("{}{}", format!("{}{}", format!("{}{}", format!("{}{}", format!("{}{}", format!("{}{}", format!("{}{}", ("v").to_string(), (x).to_string()), (" = (v").to_string()), (x).to_string()), (" * ").to_string()), (c1).to_string()), (" + v").to_string()), (y).to_string()), (" + 10000) / ").to_string()), (c2).to_string()));
        if i % 97 == 0 {
            lines.push(format!("{}{}", ("print v").to_string(), (x).to_string()));
        }
        i += 1;
    }
    // Print final values together.
    lines.push(("print (v0 + v1 + v2 + v3)").to_string());
    return lines;
}

fn run_demo() {
    let mut demo_lines: Vec<String> = vec![];
    demo_lines.push(("let a = 10").to_string());
    demo_lines.push(("let b = 3").to_string());
    demo_lines.push(("a = (a + b) * 2").to_string());
    demo_lines.push(("print a").to_string());
    demo_lines.push(("print a / b").to_string());
    
    let tokens: Vec<Token> = tokenize(&(demo_lines));
    let mut parser: Parser = Parser::new((tokens).clone());
    let stmts: Vec<StmtNode> = parser.parse_program();
    let checksum: i64 = execute(&(stmts), &(parser.expr_nodes), true);
    println!("{} {}", ("demo_checksum:").to_string(), checksum);
}

fn run_benchmark() {
    let source_lines: Vec<String> = build_benchmark_source(32, 120000);
    let start: f64 = perf_counter();
    let tokens: Vec<Token> = tokenize(&(source_lines));
    let mut parser: Parser = Parser::new((tokens).clone());
    let stmts: Vec<StmtNode> = parser.parse_program();
    let checksum: i64 = execute(&(stmts), &(parser.expr_nodes), false);
    let elapsed: f64 = perf_counter() - start;
    
    println!("{} {}", ("token_count:").to_string(), tokens.len() as i64);
    println!("{} {}", ("expr_count:").to_string(), parser.expr_nodes.len() as i64);
    println!("{} {}", ("stmt_count:").to_string(), stmts.len() as i64);
    println!("{} {}", ("checksum:").to_string(), checksum);
    println!("{} {}", ("elapsed_sec:").to_string(), elapsed);
}

fn __pytra_main() {
    run_demo();
    run_benchmark();
}

fn main() {
    __pytra_main();
}
