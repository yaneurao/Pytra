const std = @import("std");
const pytra = @import("built_in/py_runtime.zig");
const time = @import("std/time.zig");
const perf_counter = time.perf_counter;

const Token = struct {
    kind: []const u8,
    text: []const u8,
    pos: i64,
    number_value: i64,
};

const ExprNode = struct {
    kind: []const u8,
    value: i64,
    name: []const u8,
    op: []const u8,
    left: i64,
    right: i64,
    kind_tag: i64,
    op_tag: i64,
};

const StmtNode = struct {
    kind: []const u8,
    name: []const u8,
    expr_index: i64,
    kind_tag: i64,
};

fn tokenize(lines: pytra.Obj) pytra.Obj {
    const single_char_token_tags: std.StringHashMap(i64) = pytra.make_str_dict_from(i64, &[_][]const u8{ "+", "-", "*", "/", "(", ")", "=" }, &[_]i64{ 1, 2, 3, 4, 5, 6, 7 });
    const single_char_token_kinds: pytra.Obj = pytra.list_from([]const u8, &[_][]const u8{ "PLUS", "MINUS", "STAR", "SLASH", "LPAREN", "RPAREN", "EQUAL" });
    const tokens: pytra.Obj = pytra.list_from(*Token, &[_]*Token{  });
    var __enum_idx_1: i64 = 0;
    for (pytra.list_items(lines, []const u8)) |source| {
        const line_index: i64 = __enum_idx_1;
        var i: i64 = 0;
        const n: i64 = @as(i64, @intCast(source.len));
        while ((i < n)) {
            const ch: []const u8 = pytra.str_index(source, i);
            
            if (std.mem.eql(u8, ch, " ")) {
                i += 1;
                continue;
            }
            const single_tag: i64 = pytra.dict_get_default(i64, single_char_token_tags, ch, 0);
            if ((single_tag > 0)) {
                pytra.list_append(tokens, *Token, pytra.make_object(Token, Token{ .kind = pytra.list_get(single_char_token_kinds, []const u8, (single_tag - 1)), .text = ch, .pos = i, .number_value = 0 }));
                i += 1;
                continue;
            }
            var start: i64 = undefined;
            var text: []const u8 = undefined;
            if (pytra.char_isdigit(ch)) {
                start = i;
                while (((i < n) and pytra.char_isdigit(pytra.str_index(source, i)))) {
                    i += 1;
                }
                text = pytra.str_slice(source, start, i);
                pytra.list_append(tokens, *Token, pytra.make_object(Token, Token{ .kind = "NUMBER", .text = text, .pos = start, .number_value = pytra.str_to_int(text) }));
                continue;
            }
            if ((pytra.char_isalpha(ch) or std.mem.eql(u8, ch, "_"))) {
                start = i;
                while (((i < n) and ((pytra.char_isalpha(pytra.str_index(source, i)) or std.mem.eql(u8, pytra.str_index(source, i), "_")) or pytra.char_isdigit(pytra.str_index(source, i))))) {
                    i += 1;
                }
                text = pytra.str_slice(source, start, i);
                if (std.mem.eql(u8, text, "let")) {
                    pytra.list_append(tokens, *Token, pytra.make_object(Token, Token{ .kind = "LET", .text = text, .pos = start, .number_value = 0 }));
                } else {
                    if (std.mem.eql(u8, text, "print")) {
                        pytra.list_append(tokens, *Token, pytra.make_object(Token, Token{ .kind = "PRINT", .text = text, .pos = start, .number_value = 0 }));
                    } else {
                        pytra.list_append(tokens, *Token, pytra.make_object(Token, Token{ .kind = "IDENT", .text = text, .pos = start, .number_value = 0 }));
                    }
                }
                continue;
            }
            @panic(pytra.str_concat(pytra.str_concat(pytra.str_concat(pytra.str_concat(pytra.str_concat("tokenize error at line=", pytra.to_str(line_index)), " pos="), pytra.to_str(i)), " ch="), ch));
        }
        pytra.list_append(tokens, *Token, pytra.make_object(Token, Token{ .kind = "NEWLINE", .text = "", .pos = n, .number_value = 0 }));
        __enum_idx_1 += 1;
    }
    pytra.list_append(tokens, *Token, pytra.make_object(Token, Token{ .kind = "EOF", .text = "", .pos = pytra.list_len(lines, []const u8), .number_value = 0 }));
    return tokens;
}

const Parser = struct {
    tokens: pytra.Obj = undefined,
    pos: i64 = undefined,
    expr_nodes: pytra.Obj = undefined,
    pub fn new_expr_nodes(_: *const Parser) pytra.Obj {
        return pytra.list_from(pytra.Obj, &[_]pytra.Obj{  });
    }
    
    pub fn init(tokens: pytra.Obj) Parser {
        var self: Parser = undefined;
        self.tokens = tokens;
        self.pos = 0;
        self.expr_nodes = self.new_expr_nodes();
        return self;
    }
    
    pub fn current_token(self: *const Parser) *Token {
        return pytra.list_get(self.tokens, *Token, self.pos);
    }
    
    pub fn previous_token(self: *const Parser) *Token {
        return pytra.list_get(self.tokens, *Token, (self.pos - 1));
    }
    
    pub fn peek_kind(self: *const Parser) []const u8 {
        return self.current_token().kind;
    }
    
    pub fn match(self: *Parser, kind: []const u8) bool {
        if (std.mem.eql(u8, self.peek_kind(), kind)) {
            self.pos += 1;
            return true;
        }
        return false;
    }
    
    pub fn expect(self: *Parser, kind: []const u8) *Token {
        const token: *Token = self.current_token();
        if (!std.mem.eql(u8, token.kind, kind)) {
            @panic(pytra.str_concat(pytra.str_concat(pytra.str_concat(pytra.str_concat(pytra.str_concat("parse error at pos=", pytra.to_str(token.pos)), ", expected="), kind), ", got="), token.kind));
        }
        self.pos += 1;
        return token;
    }
    
    pub fn skip_newlines(self: *Parser) void {
        while (self.match("NEWLINE")) {
            // pass
        }
    }
    
    pub fn add_expr(self: *Parser, node: *ExprNode) i64 {
        pytra.list_append(self.expr_nodes, *ExprNode, node);
        return (pytra.list_len(self.expr_nodes, *ExprNode) - 1);
    }
    
    pub fn parse_program(self: *Parser) pytra.Obj {
        const stmts: pytra.Obj = pytra.list_from(*StmtNode, &[_]*StmtNode{  });
        self.skip_newlines();
        while (!std.mem.eql(u8, self.peek_kind(), "EOF")) {
            const stmt: *StmtNode = self.parse_stmt();
            pytra.list_append(stmts, *StmtNode, stmt);
            self.skip_newlines();
        }
        return stmts;
    }
    
    pub fn parse_stmt(self: *Parser) *StmtNode {
        if (self.match("LET")) {
            const let_name: []const u8 = self.expect("IDENT").text;
            _ = self.expect("EQUAL");
            const let_expr_index: i64 = self.parse_expr();
            return pytra.make_object(StmtNode, StmtNode{ .kind = "let", .name = let_name, .expr_index = let_expr_index, .kind_tag = 1 });
        }
        if (self.match("PRINT")) {
            const print_expr_index: i64 = self.parse_expr();
            return pytra.make_object(StmtNode, StmtNode{ .kind = "print", .name = "", .expr_index = print_expr_index, .kind_tag = 3 });
        }
        const assign_name: []const u8 = self.expect("IDENT").text;
        _ = self.expect("EQUAL");
        const assign_expr_index: i64 = self.parse_expr();
        return pytra.make_object(StmtNode, StmtNode{ .kind = "assign", .name = assign_name, .expr_index = assign_expr_index, .kind_tag = 2 });
    }
    
    pub fn parse_expr(self: *Parser) i64 {
        return self.parse_add();
    }
    
    pub fn parse_add(self: *Parser) i64 {
        var left: i64 = self.parse_mul();
        while (true) {
            var right: i64 = undefined;
            if (self.match("PLUS")) {
                right = self.parse_mul();
                left = self.add_expr(pytra.make_object(ExprNode, ExprNode{ .kind = "bin", .value = 0, .name = "", .op = "+", .left = left, .right = right, .kind_tag = 3, .op_tag = 1 }));
                continue;
            }
            if (self.match("MINUS")) {
                right = self.parse_mul();
                left = self.add_expr(pytra.make_object(ExprNode, ExprNode{ .kind = "bin", .value = 0, .name = "", .op = "-", .left = left, .right = right, .kind_tag = 3, .op_tag = 2 }));
                continue;
            }
            break;
        }
        return left;
    }
    
    pub fn parse_mul(self: *Parser) i64 {
        var left: i64 = self.parse_unary();
        while (true) {
            var right: i64 = undefined;
            if (self.match("STAR")) {
                right = self.parse_unary();
                left = self.add_expr(pytra.make_object(ExprNode, ExprNode{ .kind = "bin", .value = 0, .name = "", .op = "*", .left = left, .right = right, .kind_tag = 3, .op_tag = 3 }));
                continue;
            }
            if (self.match("SLASH")) {
                right = self.parse_unary();
                left = self.add_expr(pytra.make_object(ExprNode, ExprNode{ .kind = "bin", .value = 0, .name = "", .op = "/", .left = left, .right = right, .kind_tag = 3, .op_tag = 4 }));
                continue;
            }
            break;
        }
        return left;
    }
    
    pub fn parse_unary(self: *Parser) i64 {
        if (self.match("MINUS")) {
            const child: i64 = self.parse_unary();
            return self.add_expr(pytra.make_object(ExprNode, ExprNode{ .kind = "neg", .value = 0, .name = "", .op = "", .left = child, .right = -1, .kind_tag = 4, .op_tag = 0 }));
        }
        return self.parse_primary();
    }
    
    pub fn parse_primary(self: *Parser) i64 {
        if (self.match("NUMBER")) {
            const token_num: *Token = self.previous_token();
            return self.add_expr(pytra.make_object(ExprNode, ExprNode{ .kind = "lit", .value = token_num.number_value, .name = "", .op = "", .left = -1, .right = -1, .kind_tag = 1, .op_tag = 0 }));
        }
        if (self.match("IDENT")) {
            const token_ident: *Token = self.previous_token();
            return self.add_expr(pytra.make_object(ExprNode, ExprNode{ .kind = "var", .value = 0, .name = token_ident.text, .op = "", .left = -1, .right = -1, .kind_tag = 2, .op_tag = 0 }));
        }
        if (self.match("LPAREN")) {
            const expr_index: i64 = self.parse_expr();
            _ = self.expect("RPAREN");
            return expr_index;
        }
        const t: *Token = self.current_token();
        @panic(pytra.str_concat(pytra.str_concat(pytra.str_concat("primary parse error at pos=", pytra.to_str(t.pos)), " got="), t.kind));
    }
    
};

fn eval_expr(expr_index: i64, expr_nodes: pytra.Obj, env: std.StringHashMap(i64)) i64 {
    const node: *ExprNode = pytra.list_get(expr_nodes, *ExprNode, expr_index);
    
    if ((node.kind_tag == 1)) {
        return node.value;
    }
    if ((node.kind_tag == 2)) {
        if (!pytra.contains(env, node.name)) {
            @panic(pytra.str_concat("undefined variable: ", node.name));
        }
        return pytra.dict_get_default(i64, env, node.name, 0);
    }
    if ((node.kind_tag == 4)) {
        return -eval_expr(node.left, expr_nodes, env);
    }
    if ((node.kind_tag == 3)) {
        const lhs: i64 = eval_expr(node.left, expr_nodes, env);
        const rhs: i64 = eval_expr(node.right, expr_nodes, env);
        if ((node.op_tag == 1)) {
            return (lhs + rhs);
        }
        if ((node.op_tag == 2)) {
            return (lhs - rhs);
        }
        if ((node.op_tag == 3)) {
            return (lhs * rhs);
        }
        if ((node.op_tag == 4)) {
            if ((rhs == 0)) {
                @panic("division by zero");
            }
            return @divFloor(lhs, rhs);
        }
        @panic(pytra.str_concat("unknown operator: ", node.op));
    }
    @panic(pytra.str_concat("unknown node kind: ", node.kind));
}

fn execute(stmts: pytra.Obj, expr_nodes: pytra.Obj, trace: bool) i64 {
    var env: std.StringHashMap(i64) = pytra.make_str_dict(i64);
    var checksum: i64 = 0;
    var printed: i64 = 0;
    
    for (pytra.list_items(stmts, *StmtNode)) |stmt| {
        if ((stmt.kind_tag == 1)) {
            env.put(stmt.name, eval_expr(stmt.expr_index, expr_nodes, env)) catch {};
            continue;
        }
        if ((stmt.kind_tag == 2)) {
            if (!pytra.contains(env, stmt.name)) {
                @panic(pytra.str_concat("assign to undefined variable: ", stmt.name));
            }
            env.put(stmt.name, eval_expr(stmt.expr_index, expr_nodes, env)) catch {};
            continue;
        }
        const value: i64 = eval_expr(stmt.expr_index, expr_nodes, env);
        if (trace) {
            pytra.print(value);
        }
        var norm: i64 = @mod(value, 1000000007);
        if ((norm < 0)) {
            norm += 1000000007;
        }
        checksum = @mod(((checksum * 131) + norm), 1000000007);
        printed += 1;
    }
    if (trace) {
        pytra.print2("printed:", printed);
    }
    return checksum;
}

fn build_benchmark_source(var_count: i64, loops: i64) pytra.Obj {
    const lines: pytra.Obj = pytra.list_from([]const u8, &[_][]const u8{  });
    var i: i64 = undefined;
    
    // Declare initial variables.
    i = 0;
    while (i < var_count) : (i += 1) {
        pytra.list_append(lines, []const u8, pytra.str_concat(pytra.str_concat(pytra.str_concat("let v", pytra.to_str(i)), " = "), pytra.to_str((i + 1))));
    }
    // Force evaluation of many arithmetic expressions.
    i = 0;
    while (i < loops) : (i += 1) {
        const x: i64 = @mod(i, var_count);
        const y: i64 = @mod((i + 3), var_count);
        const c1: i64 = (@mod(i, 7) + 1);
        const c2: i64 = (@mod(i, 11) + 2);
        pytra.list_append(lines, []const u8, pytra.str_concat(pytra.str_concat(pytra.str_concat(pytra.str_concat(pytra.str_concat(pytra.str_concat(pytra.str_concat(pytra.str_concat(pytra.str_concat("v", pytra.to_str(x)), " = (v"), pytra.to_str(x)), " * "), pytra.to_str(c1)), " + v"), pytra.to_str(y)), " + 10000) / "), pytra.to_str(c2)));
        if ((@mod(i, 97) == 0)) {
            pytra.list_append(lines, []const u8, pytra.str_concat("print v", pytra.to_str(x)));
        }
    }
    // Print final values together.
    pytra.list_append(lines, []const u8, "print (v0 + v1 + v2 + v3)");
    return lines;
}

fn run_demo() void {
    const demo_lines: pytra.Obj = pytra.list_from([]const u8, &[_][]const u8{  });
    pytra.list_append(demo_lines, []const u8, "let a = 10");
    pytra.list_append(demo_lines, []const u8, "let b = 3");
    pytra.list_append(demo_lines, []const u8, "a = (a + b) * 2");
    pytra.list_append(demo_lines, []const u8, "print a");
    pytra.list_append(demo_lines, []const u8, "print a / b");
    
    const tokens: pytra.Obj = tokenize(demo_lines);
    const parser: *Parser = pytra.make_object(Parser, Parser.init(tokens));
    const stmts: pytra.Obj = parser.parse_program();
    const checksum: i64 = execute(stmts, parser.expr_nodes, true);
    pytra.print2("demo_checksum:", checksum);
}

fn run_benchmark() void {
    const source_lines: pytra.Obj = build_benchmark_source(32, 120000);
    const start: f64 = pytra.perf_counter();
    const tokens: pytra.Obj = tokenize(source_lines);
    const parser: *Parser = pytra.make_object(Parser, Parser.init(tokens));
    const stmts: pytra.Obj = parser.parse_program();
    const checksum: i64 = execute(stmts, parser.expr_nodes, false);
    const elapsed: f64 = (pytra.perf_counter() - start);
    
    pytra.print2("token_count:", pytra.list_len(tokens, *Token));
    pytra.print2("expr_count:", pytra.list_len(parser.expr_nodes, i64));
    pytra.print2("stmt_count:", pytra.list_len(stmts, *StmtNode));
    pytra.print2("checksum:", checksum);
    pytra.print2("elapsed_sec:", elapsed);
}

fn __pytra_main() void {
    run_demo();
    run_benchmark();
}

pub fn main() void {
    __pytra_main();
}
