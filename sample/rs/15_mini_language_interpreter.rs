#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{math_cos, math_exp, math_sin, math_sqrt, perf_counter, py_bool, py_grayscale_palette, py_in, py_len, py_print, py_save_gif, py_slice, py_write_rgb_png};

// このファイルは自動生成です（native Rust mode）。

#[derive(Clone)]
struct Token {
    kind: String,
    text: String,
    pos: i64,
}

impl Token {
    fn new(kind: String, text: String, pos: i64) -> Self {
        let mut self_obj = Self {
            kind: String::new(),
            text: String::new(),
            pos: 0,
        };
        self_obj.kind = kind;
        self_obj.text = text;
        self_obj.pos = pos;
        self_obj
    }
}

#[derive(Clone)]
struct ExprNode {
    kind: String,
    value: i64,
    name: String,
    op: String,
    left: i64,
    right: i64,
}

impl ExprNode {
    fn new(kind: String, value: i64, name: String, op: String, left: i64, right: i64) -> Self {
        let mut self_obj = Self {
            kind: String::new(),
            value: 0,
            name: String::new(),
            op: String::new(),
            left: 0,
            right: 0,
        };
        self_obj.kind = kind;
        self_obj.value = value;
        self_obj.name = name;
        self_obj.op = op;
        self_obj.left = left;
        self_obj.right = right;
        self_obj
    }
}

#[derive(Clone)]
struct StmtNode {
    kind: String,
    name: String,
    expr_index: i64,
}

impl StmtNode {
    fn new(kind: String, name: String, expr_index: i64) -> Self {
        let mut self_obj = Self {
            kind: String::new(),
            name: String::new(),
            expr_index: 0,
        };
        self_obj.kind = kind;
        self_obj.name = name;
        self_obj.expr_index = expr_index;
        self_obj
    }
}

#[derive(Clone)]
struct Parser {
    tokens: Vec<Token>,
    pos: i64,
    expr_nodes: Vec<ExprNode>,
}

impl Parser {
    fn new(tokens: Vec<Token>) -> Self {
        let mut self_obj = Self {
            tokens: Vec::new(),
            pos: 0,
            expr_nodes: Vec::new(),
        };
        self_obj.tokens = tokens;
        self_obj.pos = 0;
        self_obj.expr_nodes = self_obj.new_expr_nodes();
        self_obj
    }

    fn new_expr_nodes(&self) -> Vec<ExprNode> {
        let mut nodes: Vec<ExprNode> = vec![];
        return nodes;
    }

    fn peek_kind(&self) -> String {
        return (self.tokens)[self.pos as usize].kind;
    }

    fn r#match(&mut self, kind: String) -> bool {
        if py_bool(&(((self.peek_kind()) == (kind)))) {
            self.pos = self.pos + 1;
            return true;
        }
        return false;
    }

    fn expect(&mut self, kind: String) -> Token {
        if py_bool(&(((self.peek_kind()) != (kind)))) {
            let mut t: Token = (self.tokens)[self.pos as usize];
            panic!("{}", RuntimeError((format!("{}{}", format!("{}{}", format!("{}{}", format!("{}{}", format!("{}{}", "parse error at pos=".to_string(), format!("{}", t.pos)), ", expected=".to_string()), kind), ", got=".to_string()), t.kind)).clone()));
        }
        let mut token: Token = (self.tokens)[self.pos as usize];
        self.pos = self.pos + 1;
        return token;
    }

    fn skip_newlines(&self) -> () {
        while py_bool(&(self.r#match("NEWLINE".to_string()))) {
        }
    }

    fn add_expr(&self, node: ExprNode) -> i64 {
        self.expr_nodes.push(node);
        return (((py_len(&self.expr_nodes) as i64)) - (1));
    }

    fn parse_program(&self) -> Vec<StmtNode> {
        let mut stmts: Vec<StmtNode> = vec![];
        self.skip_newlines();
        while py_bool(&(((self.peek_kind()) != ("EOF".to_string())))) {
            let mut stmt: StmtNode = self.parse_stmt();
            stmts.push(stmt);
            self.skip_newlines();
        }
        return stmts;
    }

    fn parse_stmt(&self) -> StmtNode {
        if py_bool(&(self.r#match("LET".to_string()))) {
            let mut let_name: String = self.expect("IDENT".to_string()).text;
            self.expect("EQUAL".to_string());
            let mut let_expr_index: i64 = self.parse_expr();
            return StmtNode::new("let".to_string(), let_name, let_expr_index);
        }
        if py_bool(&(self.r#match("PRINT".to_string()))) {
            let mut print_expr_index: i64 = self.parse_expr();
            return StmtNode::new("print".to_string(), "".to_string(), print_expr_index);
        }
        let mut assign_name: String = self.expect("IDENT".to_string()).text;
        self.expect("EQUAL".to_string());
        let mut assign_expr_index: i64 = self.parse_expr();
        return StmtNode::new("assign".to_string(), assign_name, assign_expr_index);
    }

    fn parse_expr(&self) -> i64 {
        return self.parse_add();
    }

    fn parse_add(&self) -> i64 {
        let mut left: i64 = self.parse_mul();
        let mut done: bool = false;
        while py_bool(&((!done))) {
            if py_bool(&(self.r#match("PLUS".to_string()))) {
                let mut right: i64 = self.parse_mul();
                left = self.add_expr(ExprNode::new("bin".to_string(), 0, "".to_string(), "+".to_string(), left, right));
                continue;
            }
            if py_bool(&(self.r#match("MINUS".to_string()))) {
                let mut right = self.parse_mul();
                left = self.add_expr(ExprNode::new("bin".to_string(), 0, "".to_string(), "-".to_string(), left, right));
                continue;
            }
            done = true;
        }
        return left;
    }

    fn parse_mul(&self) -> i64 {
        let mut left: i64 = self.parse_unary();
        let mut done: bool = false;
        while py_bool(&((!done))) {
            if py_bool(&(self.r#match("STAR".to_string()))) {
                let mut right: i64 = self.parse_unary();
                left = self.add_expr(ExprNode::new("bin".to_string(), 0, "".to_string(), "*".to_string(), left, right));
                continue;
            }
            if py_bool(&(self.r#match("SLASH".to_string()))) {
                let mut right = self.parse_unary();
                left = self.add_expr(ExprNode::new("bin".to_string(), 0, "".to_string(), "/".to_string(), left, right));
                continue;
            }
            done = true;
        }
        return left;
    }

    fn parse_unary(&self) -> i64 {
        if py_bool(&(self.r#match("MINUS".to_string()))) {
            let mut child: i64 = self.parse_unary();
            return self.add_expr(ExprNode::new("neg".to_string(), 0, "".to_string(), "".to_string(), child, (-1)));
        }
        return self.parse_primary();
    }

    fn parse_primary(&self) -> i64 {
        if py_bool(&(self.r#match("NUMBER".to_string()))) {
            let mut token_num: Token = (self.tokens)[((self.pos) - (1)) as usize];
            let mut parsed_value: i64 = 0;
            let mut idx: i64 = 0;
            while py_bool(&(((idx) < ((py_len(&token_num.text) as i64))))) {
                let mut ch: String = py_slice(&(token_num.text), Some(idx), Some(((idx) + (1))));
                parsed_value = ((((((parsed_value) * (10))) + (((ch).chars().next().unwrap() as i64)))) - ((("0".to_string()).chars().next().unwrap() as i64)));
                idx = idx + 1;
            }
            return self.add_expr(ExprNode::new("lit".to_string(), parsed_value, "".to_string(), "".to_string(), (-1), (-1)));
        }
        if py_bool(&(self.r#match("IDENT".to_string()))) {
            let mut token_ident: Token = (self.tokens)[((self.pos) - (1)) as usize];
            return self.add_expr(ExprNode::new("var".to_string(), 0, token_ident.text, "".to_string(), (-1), (-1)));
        }
        if py_bool(&(self.r#match("LPAREN".to_string()))) {
            let mut expr_index: i64 = self.parse_expr();
            self.expect("RPAREN".to_string());
            return expr_index;
        }
        let mut t = (self.tokens)[self.pos as usize];
        panic!("{}", RuntimeError((format!("{}{}", format!("{}{}", format!("{}{}", "primary parse error at pos=".to_string(), format!("{}", t.pos)), " got=".to_string()), t.kind)).clone()));
    }
}

fn tokenize(lines: Vec<String>) -> Vec<Token> {
    let mut tokens: Vec<Token> = vec![];
    let mut line_index: i64 = 0;
    while py_bool(&(((line_index) < ((py_len(&lines) as i64))))) {
        let mut source: String = (lines)[line_index as usize];
        let mut i: i64 = 0;
        let mut n: i64 = (py_len(&source) as i64);
        while py_bool(&(((i) < (n)))) {
            let mut ch: String = py_slice(&(source), Some(i), Some(((i) + (1))));
            if py_bool(&(((ch) == (" ".to_string())))) {
                i = i + 1;
                continue;
            }
            if py_bool(&(((ch) == ("+".to_string())))) {
                tokens.push(Token::new("PLUS".to_string(), ch, i));
                i = i + 1;
                continue;
            }
            if py_bool(&(((ch) == ("-".to_string())))) {
                tokens.push(Token::new("MINUS".to_string(), ch, i));
                i = i + 1;
                continue;
            }
            if py_bool(&(((ch) == ("*".to_string())))) {
                tokens.push(Token::new("STAR".to_string(), ch, i));
                i = i + 1;
                continue;
            }
            if py_bool(&(((ch) == ("/".to_string())))) {
                tokens.push(Token::new("SLASH".to_string(), ch, i));
                i = i + 1;
                continue;
            }
            if py_bool(&(((ch) == ("(".to_string())))) {
                tokens.push(Token::new("LPAREN".to_string(), ch, i));
                i = i + 1;
                continue;
            }
            if py_bool(&(((ch) == (")".to_string())))) {
                tokens.push(Token::new("RPAREN".to_string(), ch, i));
                i = i + 1;
                continue;
            }
            if py_bool(&(((ch) == ("=".to_string())))) {
                tokens.push(Token::new("EQUAL".to_string(), ch, i));
                i = i + 1;
                continue;
            }
            if py_bool(&(ch.isdigit())) {
                let mut start: i64 = i;
                while py_bool(&((((i) < (n)) && py_slice(&(source), Some(i), Some(((i) + (1)))).isdigit()))) {
                    i = i + 1;
                }
                let mut text: String = py_slice(&(source), Some(start), Some(i));
                tokens.push(Token::new("NUMBER".to_string(), text, start));
                continue;
            }
            if py_bool(&((ch.isalpha() || ((ch) == ("_".to_string()))))) {
                let mut start = i;
                while py_bool(&((((i) < (n)) && ((py_slice(&(source), Some(i), Some(((i) + (1)))).isalpha() || ((py_slice(&(source), Some(i), Some(((i) + (1))))) == ("_".to_string()))) || py_slice(&(source), Some(i), Some(((i) + (1)))).isdigit())))) {
                    i = i + 1;
                }
                let mut text = py_slice(&(source), Some(start), Some(i));
                if py_bool(&(((text) == ("let".to_string())))) {
                    tokens.push(Token::new("LET".to_string(), text, start));
                } else {
                    if py_bool(&(((text) == ("print".to_string())))) {
                        tokens.push(Token::new("PRINT".to_string(), text, start));
                    } else {
                        tokens.push(Token::new("IDENT".to_string(), text, start));
                    }
                }
                continue;
            }
            panic!("{}", RuntimeError((format!("{}{}", format!("{}{}", format!("{}{}", format!("{}{}", format!("{}{}", "tokenize error at line=".to_string(), format!("{}", line_index)), " pos=".to_string()), format!("{}", i)), " ch=".to_string()), ch)).clone()));
        }
        tokens.push(Token::new("NEWLINE".to_string(), "".to_string(), n));
        line_index = line_index + 1;
    }
    tokens.push(Token::new("EOF".to_string(), "".to_string(), (py_len(&lines) as i64)));
    return tokens;
}

fn eval_expr(expr_index: i64, expr_nodes: Vec<ExprNode>, env: std::collections::HashMap<String, i64>) -> i64 {
    if py_bool(&(false)) {
        (env)["__dummy__".to_string() as usize] = 0;
    }
    let mut node: ExprNode = (expr_nodes)[expr_index as usize];
    if py_bool(&(((node.kind) == ("lit".to_string())))) {
        return node.value;
    }
    if py_bool(&(((node.kind) == ("var".to_string())))) {
        if py_bool(&((!py_in(&(env), &(node.name))))) {
            panic!("{}", RuntimeError((format!("{}{}", "undefined variable: ".to_string(), node.name)).clone()));
        }
        return (env)[node.name as usize];
    }
    if py_bool(&(((node.kind) == ("neg".to_string())))) {
        return (-eval_expr(node.left, (expr_nodes).clone(), (env).clone()));
    }
    if py_bool(&(((node.kind) == ("bin".to_string())))) {
        let mut lhs: i64 = eval_expr(node.left, (expr_nodes).clone(), (env).clone());
        let mut rhs: i64 = eval_expr(node.right, (expr_nodes).clone(), (env).clone());
        if py_bool(&(((node.op) == ("+".to_string())))) {
            return ((lhs) + (rhs));
        }
        if py_bool(&(((node.op) == ("-".to_string())))) {
            return ((lhs) - (rhs));
        }
        if py_bool(&(((node.op) == ("*".to_string())))) {
            return ((lhs) * (rhs));
        }
        if py_bool(&(((node.op) == ("/".to_string())))) {
            if py_bool(&(((rhs) == (0)))) {
                panic!("{}", RuntimeError(("division by zero".to_string()).clone()));
            }
            return ((lhs) / (rhs));
        }
        panic!("{}", RuntimeError((format!("{}{}", "unknown operator: ".to_string(), node.op)).clone()));
    }
    panic!("{}", RuntimeError((format!("{}{}", "unknown node kind: ".to_string(), node.kind)).clone()));
}

fn execute(stmts: Vec<StmtNode>, expr_nodes: Vec<ExprNode>, trace: bool) -> i64 {
    let mut env: std::collections::HashMap<String, i64> = std::collections::HashMap::from([]);
    let mut checksum: i64 = 0;
    let mut printed: i64 = 0;
    for stmt in (stmts).clone() {
        if py_bool(&(((stmt.kind) == ("let".to_string())))) {
            (env)[stmt.name as usize] = eval_expr(stmt.expr_index, (expr_nodes).clone(), (env).clone());
            continue;
        }
        if py_bool(&(((stmt.kind) == ("assign".to_string())))) {
            if py_bool(&((!py_in(&(env), &(stmt.name))))) {
                panic!("{}", RuntimeError((format!("{}{}", "assign to undefined variable: ".to_string(), stmt.name)).clone()));
            }
            (env)[stmt.name as usize] = eval_expr(stmt.expr_index, (expr_nodes).clone(), (env).clone());
            continue;
        }
        let mut value: i64 = eval_expr(stmt.expr_index, (expr_nodes).clone(), (env).clone());
        if py_bool(&(trace)) {
            py_print(value);
        }
        let mut norm: i64 = ((value) % (1000000007));
        if py_bool(&(((norm) < (0)))) {
            norm = norm + 1000000007;
        }
        checksum = ((((((checksum) * (131))) + (norm))) % (1000000007));
        printed = printed + 1;
    }
    if py_bool(&(trace)) {
        println!("{} {}", "printed:".to_string(), printed);
    }
    return checksum;
}

fn build_benchmark_source(var_count: i64, loops: i64) -> Vec<String> {
    let mut lines: Vec<String> = vec![];
    for i in (0)..(var_count) {
        lines.push(format!("{}{}", format!("{}{}", format!("{}{}", "let v".to_string(), format!("{}", i)), " = ".to_string()), format!("{}", ((i) + (1)))));
    }
    for i in (0)..(loops) {
        let mut x: i64 = ((i) % (var_count));
        let mut y: i64 = ((((i) + (3))) % (var_count));
        let mut c1: i64 = ((((i) % (7))) + (1));
        let mut c2: i64 = ((((i) % (11))) + (2));
        lines.push(format!("{}{}", format!("{}{}", format!("{}{}", format!("{}{}", format!("{}{}", format!("{}{}", format!("{}{}", format!("{}{}", format!("{}{}", "v".to_string(), format!("{}", x)), " = (v".to_string()), format!("{}", x)), " * ".to_string()), format!("{}", c1)), " + v".to_string()), format!("{}", y)), " + 10000) / ".to_string()), format!("{}", c2)));
        if py_bool(&(((((i) % (97))) == (0)))) {
            lines.push(format!("{}{}", "print v".to_string(), format!("{}", x)));
        }
    }
    lines.push("print (v0 + v1 + v2 + v3)".to_string());
    return lines;
}

fn run_demo() -> () {
    let mut demo_lines: Vec<String> = vec![];
    demo_lines.push("let a = 10".to_string());
    demo_lines.push("let b = 3".to_string());
    demo_lines.push("a = (a + b) * 2".to_string());
    demo_lines.push("print a".to_string());
    demo_lines.push("print a / b".to_string());
    let mut tokens: Vec<Token> = tokenize((demo_lines).clone());
    let mut parser: Parser = Parser::new(tokens);
    let mut stmts: Vec<StmtNode> = parser.parse_program();
    let mut checksum: i64 = execute((stmts).clone(), parser.expr_nodes, true);
    println!("{} {}", "demo_checksum:".to_string(), checksum);
}

fn run_benchmark() -> () {
    let mut source_lines: Vec<String> = build_benchmark_source(32, 120000);
    let mut start: f64 = perf_counter();
    let mut tokens: Vec<Token> = tokenize((source_lines).clone());
    let mut parser: Parser = Parser::new(tokens);
    let mut stmts: Vec<StmtNode> = parser.parse_program();
    let mut checksum: i64 = execute((stmts).clone(), parser.expr_nodes, false);
    let mut elapsed: f64 = ((perf_counter()) - (start));
    println!("{} {}", "token_count:".to_string(), (py_len(&tokens) as i64));
    println!("{} {}", "expr_count:".to_string(), (py_len(&parser.expr_nodes) as i64));
    println!("{} {}", "stmt_count:".to_string(), (py_len(&stmts) as i64));
    println!("{} {}", "checksum:".to_string(), checksum);
    println!("{} {}", "elapsed_sec:".to_string(), elapsed);
}

fn main() -> () {
    run_demo();
    run_benchmark();
}
