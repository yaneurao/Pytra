-- from dataclasses import dataclass as dataclass (not yet mapped)
-- from time import perf_counter as perf_counter (not yet mapped)

local function __pytra_isinstance(obj, class_tbl)
    if type(obj) ~= "table" then
        return false
    end
    local mt = getmetatable(obj)
    while mt do
        if mt == class_tbl then
            return true
        end
        local parent = getmetatable(mt)
        if type(parent) == "table" and type(parent.__index) == "table" then
            mt = parent.__index
        else
            mt = nil
        end
    end
    return false
end

Token = {}
Token.__index = Token

function Token.new()
    return setmetatable({}, Token)
end

ExprNode = {}
ExprNode.__index = ExprNode

function ExprNode.new()
    return setmetatable({}, ExprNode)
end

StmtNode = {}
StmtNode.__index = StmtNode

function StmtNode.new()
    return setmetatable({}, StmtNode)
end

function tokenize(lines)
    local single_char_token_tags = { ["+"] = 1, ["-"] = 2, ["*"] = 3, ["/"] = 4, ["("] = 5, [")"] = 6, ["="] = 7 }
    local single_char_token_kinds = { "PLUS", "MINUS", "STAR", "SLASH", "LPAREN", "RPAREN", "EQUAL" }
    local tokens = {  }
    for _, it in ipairs(enumerate(lines)) do
        local i = 0
        local n = len(source)
        while (i < n) do
            local ch = source[(i) + 1]
            
            if (ch == " ") then
                i = i + 1
                continue
            end
            local single_tag = single_char_token_tags:get(ch, 0)
            if (single_tag > 0) then
                tokens:append(Token.new(single_char_token_kinds[((single_tag - 1)) + 1], ch, i, 0))
                i = i + 1
                continue
            end
            if ch:isdigit() then
                local start = i
                while ((i < n) and source[(i) + 1]:isdigit()) do
                    i = i + 1
                end
                local text = string.sub(source, (start) + 1, i)
                tokens:append(Token.new("NUMBER", text, start, int(text)))
                continue
            end
            if (ch:isalpha() or (ch == "_")) then
                start = i
                while ((i < n) and ((source[(i) + 1]:isalpha() or (source[(i) + 1] == "_")) or source[(i) + 1]:isdigit())) do
                    i = i + 1
                end
                text = string.sub(source, (start) + 1, i)
                if (text == "let") then
                    tokens:append(Token.new("LET", text, start, 0))
                else
                    if (text == "print") then
                        tokens:append(Token.new("PRINT", text, start, 0))
                    else
                        tokens:append(Token.new("IDENT", text, start, 0))
                    end
                end
                continue
            end
            error(((((("tokenize error at line=" + str(line_index)) + " pos=") + str(i)) + " ch=") + ch))
        end
        tokens:append(Token.new("NEWLINE", "", n, 0))
    end
    tokens:append(Token.new("EOF", "", len(lines), 0))
    return tokens
end

Parser = {}
Parser.__index = Parser

function Parser:new_expr_nodes()
    return {  }
end

function Parser.new(tokens)
    local self = setmetatable({}, Parser)
    local self.tokens = tokens
    local self.pos = 0
    local self.expr_nodes = self:new_expr_nodes()
    return self
end

function Parser:current_token()
    return self.tokens[(self.pos) + 1]
end

function Parser:previous_token()
    return self.tokens[((self.pos - 1)) + 1]
end

function Parser:peek_kind()
    return self:current_token().kind
end

function Parser:match(kind)
    if (self:peek_kind() == kind) then
        self.pos = self.pos + 1
        return true
    end
    return false
end

function Parser:expect(kind)
    local token = self:current_token()
    if (token.kind ~= kind) then
        error(((((("parse error at pos=" + tostring(token.pos)) + ", expected=") + kind) + ", got=") + token.kind))
    end
    self.pos = self.pos + 1
    return token
end

function Parser:skip_newlines()
    while self:match("NEWLINE") do
        do end
    end
end

function Parser:add_expr(node)
    self.expr_nodes:append(node)
    return (len(self.expr_nodes) - 1)
end

function Parser:parse_program()
    local stmts = {  }
    self:skip_newlines()
    while (self:peek_kind() ~= "EOF") do
        local stmt = self:parse_stmt()
        stmts:append(stmt)
        self:skip_newlines()
    end
    return stmts
end

function Parser:parse_stmt()
    if self:match("LET") then
        local let_name = self:expect("IDENT").text
        self:expect("EQUAL")
        local let_expr_index = self:parse_expr()
        return StmtNode.new("let", let_name, let_expr_index, 1)
    end
    if self:match("PRINT") then
        local print_expr_index = self:parse_expr()
        return StmtNode.new("print", "", print_expr_index, 3)
    end
    local assign_name = self:expect("IDENT").text
    self:expect("EQUAL")
    local assign_expr_index = self:parse_expr()
    return StmtNode.new("assign", assign_name, assign_expr_index, 2)
end

function Parser:parse_expr()
    return self:parse_add()
end

function Parser:parse_add()
    local left = self:parse_mul()
    while true do
        if self:match("PLUS") then
            local right = self:parse_mul()
            left = self:add_expr(ExprNode.new("bin", 0, "", "+", left, right, 3, 1))
            continue
        end
        if self:match("MINUS") then
            right = self:parse_mul()
            left = self:add_expr(ExprNode.new("bin", 0, "", "-", left, right, 3, 2))
            continue
        end
        _break
    end
    return left
end

function Parser:parse_mul()
    local left = self:parse_unary()
    while true do
        if self:match("STAR") then
            local right = self:parse_unary()
            left = self:add_expr(ExprNode.new("bin", 0, "", "*", left, right, 3, 3))
            continue
        end
        if self:match("SLASH") then
            right = self:parse_unary()
            left = self:add_expr(ExprNode.new("bin", 0, "", "/", left, right, 3, 4))
            continue
        end
        _break
    end
    return left
end

function Parser:parse_unary()
    if self:match("MINUS") then
        local child = self:parse_unary()
        return self:add_expr(ExprNode.new("neg", 0, "", "", child, (-1), 4, 0))
    end
    return self:parse_primary()
end

function Parser:parse_primary()
    if self:match("NUMBER") then
        local token_num = self:previous_token()
        return self:add_expr(ExprNode.new("lit", token_num.number_value, "", "", (-1), (-1), 1, 0))
    end
    if self:match("IDENT") then
        local token_ident = self:previous_token()
        return self:add_expr(ExprNode.new("var", 0, token_ident.text, "", (-1), (-1), 2, 0))
    end
    if self:match("LPAREN") then
        local expr_index = self:parse_expr()
        self:expect("RPAREN")
        return expr_index
    end
    t = self:current_token()
    error(((("primary parse error at pos=" + tostring(t.pos)) + " got=") + t.kind))
end

function eval_expr(expr_index, expr_nodes, env)
    local node = expr_nodes[(expr_index) + 1]
    
    if (node.kind_tag == 1) then
        return node.value
    end
    if (node.kind_tag == 2) then
        if (not (node.name == env)) then
            error(("undefined variable: " + node.name))
        end
        return env[node.name]
    end
    if (node.kind_tag == 4) then
        return (-eval_expr(node.left, expr_nodes, env))
    end
    if (node.kind_tag == 3) then
        local lhs = eval_expr(node.left, expr_nodes, env)
        local rhs = eval_expr(node.right, expr_nodes, env)
        if (node.op_tag == 1) then
            return (lhs + rhs)
        end
        if (node.op_tag == 2) then
            return (lhs - rhs)
        end
        if (node.op_tag == 3) then
            return (lhs * rhs)
        end
        if (node.op_tag == 4) then
            if (rhs == 0) then
                error("division by zero")
            end
            return (lhs // rhs)
        end
        error(("unknown operator: " + node.op))
    end
    error(("unknown node kind: " + node.kind))
end

function execute(stmts, expr_nodes, trace)
    local env = {}
    local checksum = 0
    local printed = 0
    
    for _, stmt in ipairs(stmts) do
        if (stmt.kind_tag == 1) then
            env[stmt.name] = eval_expr(stmt.expr_index, expr_nodes, env)
            continue
        end
        if (stmt.kind_tag == 2) then
            if (not (stmt.name == env)) then
                error(("assign to undefined variable: " + stmt.name))
            end
            env[stmt.name] = eval_expr(stmt.expr_index, expr_nodes, env)
            continue
        end
        local value = eval_expr(stmt.expr_index, expr_nodes, env)
        if trace then
            print(value)
        end
        local norm = (value % 1000000007)
        if (norm < 0) then
            norm = norm + 1000000007
        end
        checksum = (((checksum * 131) + norm) % 1000000007)
        printed = printed + 1
    end
    if trace then
        print("printed:", printed)
    end
    return checksum
end

function build_benchmark_source(var_count, loops)
    local lines = {  }
    
    -- Declare initial variables.
    for i = 0, (var_count) - 1, 1 do
        lines:append(((("let v" + str(i)) + " = ") + str((i + 1))))
    end
    -- Force evaluation of many arithmetic expressions.
    for i = 0, (loops) - 1, 1 do
        local x = (i % var_count)
        local y = ((i + 3) % var_count)
        local c1 = ((i % 7) + 1)
        local c2 = ((i % 11) + 2)
        lines:append(((((((((("v" + str(x)) + " = (v") + str(x)) + " * ") + str(c1)) + " + v") + str(y)) + " + 10000) / ") + str(c2)))
        if ((i % 97) == 0) then
            lines:append(("print v" + str(x)))
        end
    end
    -- Print final values together.
    lines:append("print (v0 + v1 + v2 + v3)")
    return lines
end

function run_demo()
    local demo_lines = {  }
    demo_lines:append("let a = 10")
    demo_lines:append("let b = 3")
    demo_lines:append("a = (a + b) * 2")
    demo_lines:append("print a")
    demo_lines:append("print a / b")
    
    local tokens = tokenize(demo_lines)
    local parser = Parser.new(tokens)
    local stmts = parser:parse_program()
    local checksum = execute(stmts, parser.expr_nodes, true)
    print("demo_checksum:", checksum)
end

function run_benchmark()
    local source_lines = build_benchmark_source(32, 120000)
    local start = perf_counter()
    local tokens = tokenize(source_lines)
    local parser = Parser.new(tokens)
    local stmts = parser:parse_program()
    local checksum = execute(stmts, parser.expr_nodes, false)
    local elapsed = (perf_counter() - start)
    
    print("token_count:", len(tokens))
    print("expr_count:", #(parser.expr_nodes))
    print("stmt_count:", len(stmts))
    print("checksum:", checksum)
    print("elapsed_sec:", elapsed)
end

function __pytra_main()
    run_demo()
    run_benchmark()
end


main()
