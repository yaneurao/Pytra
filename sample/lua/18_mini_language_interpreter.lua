local function __pytra_print(...)
    local argc = select("#", ...)
    if argc == 0 then
        io.write("\n")
        return
    end
    local parts = {}
    for i = 1, argc do
        local v = select(i, ...)
        if v == true then
            parts[i] = "True"
        elseif v == false then
            parts[i] = "False"
        elseif v == nil then
            parts[i] = "None"
        else
            parts[i] = tostring(v)
        end
    end
    io.write(table.concat(parts, " ") .. "\n")
end

local function __pytra_repeat_seq(a, b)
    local seq = a
    local count = b
    if type(a) == "number" and type(b) ~= "number" then
        seq = b
        count = a
    end
    local n = math.floor(tonumber(count) or 0)
    if n <= 0 then
        if type(seq) == "string" then return "" end
        return {}
    end
    if type(seq) == "string" then
        return string.rep(seq, n)
    end
    if type(seq) ~= "table" then
        return (tonumber(a) or 0) * (tonumber(b) or 0)
    end
    local out = {}
    for _ = 1, n do
        for i = 1, #seq do
            out[#out + 1] = seq[i]
        end
    end
    return out
end

local function __pytra_truthy(v)
    if v == nil then return false end
    local t = type(v)
    if t == "boolean" then return v end
    if t == "number" then return v ~= 0 end
    if t == "string" then return #v ~= 0 end
    if t == "table" then return next(v) ~= nil end
    return true
end

local function __pytra_contains(container, value)
    local t = type(container)
    if t == "table" then
        if container[value] ~= nil then return true end
        for i = 1, #container do
            if container[i] == value then return true end
        end
        return false
    end
    if t == "string" then
        if type(value) ~= "string" then value = tostring(value) end
        return string.find(container, value, 1, true) ~= nil
    end
    return false
end

local function __pytra_str_isdigit(s)
    if type(s) ~= "string" or #s == 0 then return false end
    for i = 1, #s do
        local b = string.byte(s, i)
        if b < 48 or b > 57 then return false end
    end
    return true
end

local function __pytra_str_isalpha(s)
    if type(s) ~= "string" or #s == 0 then return false end
    for i = 1, #s do
        local b = string.byte(s, i)
        local is_upper = (b >= 65 and b <= 90)
        local is_lower = (b >= 97 and b <= 122)
        if not (is_upper or is_lower) then return false end
    end
    return true
end

local function __pytra_str_isalnum(s)
    if type(s) ~= "string" or #s == 0 then return false end
    for i = 1, #s do
        local b = string.byte(s, i)
        local is_digit = (b >= 48 and b <= 57)
        local is_upper = (b >= 65 and b <= 90)
        local is_lower = (b >= 97 and b <= 122)
        if not (is_digit or is_upper or is_lower) then return false end
    end
    return true
end

local function __pytra_perf_counter()
    return os.clock()
end

-- from dataclasses import dataclass as dataclass (not yet mapped)
local perf_counter = __pytra_perf_counter

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

function Token.new(kind, text, pos, number_value)
    local self = setmetatable({}, Token)
    self.kind = kind
    self.text = text
    self.pos = pos
    self.number_value = number_value
    return self
end

ExprNode = {}
ExprNode.__index = ExprNode

function ExprNode.new(kind, value, name, op, left, right, kind_tag, op_tag)
    local self = setmetatable({}, ExprNode)
    self.kind = kind
    self.value = value
    self.name = name
    self.op = op
    self.left = left
    self.right = right
    self.kind_tag = kind_tag
    self.op_tag = op_tag
    return self
end

StmtNode = {}
StmtNode.__index = StmtNode

function StmtNode.new(kind, name, expr_index, kind_tag)
    local self = setmetatable({}, StmtNode)
    self.kind = kind
    self.name = name
    self.expr_index = expr_index
    self.kind_tag = kind_tag
    return self
end

function tokenize(lines)
    local single_char_token_tags = { ["+"] = 1, ["-"] = 2, ["*"] = 3, ["/"] = 4, ["("] = 5, [")"] = 6, ["="] = 7 }
    local single_char_token_kinds = { "PLUS", "MINUS", "STAR", "SLASH", "LPAREN", "RPAREN", "EQUAL" }
    local tokens = {  }
    for _, __it_2 in ipairs((function(__v) local __out = {}; for __i = 1, #__v do table.insert(__out, { __i - 1, __v[__i] }) end; return __out end)(lines)) do
        local line_index = __it_2[1]
        local source = __it_2[2]
        local i = 0
        local n = #(source)
        while (i < n) do
            local ch = string.sub(source, (((i) < 0) and (#(source) + (i) + 1) or ((i) + 1)), (((i) < 0) and (#(source) + (i) + 1) or ((i) + 1)))
            
            if (ch == " ") then
                i = i + 1
                goto __pytra_continue_3
            end
            local single_tag = (function(__tbl, __key, __default) local __val = __tbl[__key]; if __val == nil then return __default end; return __val end)(single_char_token_tags, ch, 0)
            if (single_tag > 0) then
                table.insert(tokens, Token.new(single_char_token_kinds[((((single_tag - 1)) < 0) and (#(single_char_token_kinds) + ((single_tag - 1)) + 1) or (((single_tag - 1)) + 1))], ch, i, 0))
                i = i + 1
                goto __pytra_continue_3
            end
            if __pytra_str_isdigit(ch) then
                local start = i
                while ((i < n) and __pytra_str_isdigit(string.sub(source, (((i) < 0) and (#(source) + (i) + 1) or ((i) + 1)), (((i) < 0) and (#(source) + (i) + 1) or ((i) + 1))))) do
                    i = i + 1
                    ::__pytra_continue_4::
                end
                local text = string.sub(source, (start) + 1, i)
                table.insert(tokens, Token.new("NUMBER", text, start, (math.floor(tonumber(text) or 0))))
                goto __pytra_continue_3
            end
            if (__pytra_str_isalpha(ch) or (ch == "_")) then
                start = i
                while ((i < n) and ((__pytra_str_isalpha(string.sub(source, (((i) < 0) and (#(source) + (i) + 1) or ((i) + 1)), (((i) < 0) and (#(source) + (i) + 1) or ((i) + 1)))) or (string.sub(source, (((i) < 0) and (#(source) + (i) + 1) or ((i) + 1)), (((i) < 0) and (#(source) + (i) + 1) or ((i) + 1))) == "_")) or __pytra_str_isdigit(string.sub(source, (((i) < 0) and (#(source) + (i) + 1) or ((i) + 1)), (((i) < 0) and (#(source) + (i) + 1) or ((i) + 1)))))) do
                    i = i + 1
                    ::__pytra_continue_5::
                end
                text = string.sub(source, (start) + 1, i)
                if (text == "let") then
                    table.insert(tokens, Token.new("LET", text, start, 0))
                else
                    if (text == "print") then
                        table.insert(tokens, Token.new("PRINT", text, start, 0))
                    else
                        table.insert(tokens, Token.new("IDENT", text, start, 0))
                    end
                end
                goto __pytra_continue_3
            end
            error(((((("tokenize error at line=" .. tostring(line_index)) .. " pos=") .. tostring(i)) .. " ch=") .. ch))
            ::__pytra_continue_3::
        end
        table.insert(tokens, Token.new("NEWLINE", "", n, 0))
        ::__pytra_continue_1::
    end
    table.insert(tokens, Token.new("EOF", "", #(lines), 0))
    return tokens
end

Parser = {}
Parser.__index = Parser

function Parser:new_expr_nodes()
    return {  }
end

function Parser.new(tokens)
    local self = setmetatable({}, Parser)
    self.tokens = tokens
    self.pos = 0
    self.expr_nodes = self:new_expr_nodes()
    return self
end

function Parser:current_token()
    return self.tokens[(((self.pos) < 0) and (#(self.tokens) + (self.pos) + 1) or ((self.pos) + 1))]
end

function Parser:previous_token()
    return self.tokens[((((self.pos - 1)) < 0) and (#(self.tokens) + ((self.pos - 1)) + 1) or (((self.pos - 1)) + 1))]
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
        error(((((("parse error at pos=" .. tostring(token.pos)) .. ", expected=") .. kind) .. ", got=") .. token.kind))
    end
    self.pos = self.pos + 1
    return token
end

function Parser:skip_newlines()
    while self:match("NEWLINE") do
        do end
        ::__pytra_continue_6::
    end
end

function Parser:add_expr(node)
    table.insert(self.expr_nodes, node)
    return (#(self.expr_nodes) - 1)
end

function Parser:parse_program()
    local stmts = {  }
    self:skip_newlines()
    while (self:peek_kind() ~= "EOF") do
        local stmt = self:parse_stmt()
        table.insert(stmts, stmt)
        self:skip_newlines()
        ::__pytra_continue_7::
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
            goto __pytra_continue_8
        end
        if self:match("MINUS") then
            right = self:parse_mul()
            left = self:add_expr(ExprNode.new("bin", 0, "", "-", left, right, 3, 2))
            goto __pytra_continue_8
        end
        break
        ::__pytra_continue_8::
    end
    return left
end

function Parser:parse_mul()
    local left = self:parse_unary()
    while true do
        if self:match("STAR") then
            local right = self:parse_unary()
            left = self:add_expr(ExprNode.new("bin", 0, "", "*", left, right, 3, 3))
            goto __pytra_continue_9
        end
        if self:match("SLASH") then
            right = self:parse_unary()
            left = self:add_expr(ExprNode.new("bin", 0, "", "/", left, right, 3, 4))
            goto __pytra_continue_9
        end
        break
        ::__pytra_continue_9::
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
    error(((("primary parse error at pos=" .. tostring(t.pos)) .. " got=") .. t.kind))
end

function eval_expr(expr_index, expr_nodes, env)
    local node = expr_nodes[(((expr_index) < 0) and (#(expr_nodes) + (expr_index) + 1) or ((expr_index) + 1))]
    
    if (node.kind_tag == 1) then
        return node.value
    end
    if (node.kind_tag == 2) then
        if (not __pytra_contains(env, node.name)) then
            error(("undefined variable: " .. node.name))
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
        error(("unknown operator: " .. node.op))
    end
    error(("unknown node kind: " .. node.kind))
end

function execute(stmts, expr_nodes, trace)
    local env = {}
    local checksum = 0
    local printed = 0
    
    for _, stmt in ipairs(stmts) do
        if (stmt.kind_tag == 1) then
            env[stmt.name] = eval_expr(stmt.expr_index, expr_nodes, env)
            goto __pytra_continue_10
        end
        if (stmt.kind_tag == 2) then
            if (not __pytra_contains(env, stmt.name)) then
                error(("assign to undefined variable: " .. stmt.name))
            end
            env[stmt.name] = eval_expr(stmt.expr_index, expr_nodes, env)
            goto __pytra_continue_10
        end
        local value = eval_expr(stmt.expr_index, expr_nodes, env)
        if trace then
            __pytra_print(value)
        end
        local norm = (value % 1000000007)
        if (norm < 0) then
            norm = norm + 1000000007
        end
        checksum = (((checksum * 131) + norm) % 1000000007)
        printed = printed + 1
        ::__pytra_continue_10::
    end
    if trace then
        __pytra_print("printed:", printed)
    end
    return checksum
end

function build_benchmark_source(var_count, loops)
    local lines = {  }
    
    -- Declare initial variables.
    for i = 0, (var_count) - 1, 1 do
        table.insert(lines, ((("let v" .. tostring(i)) .. " = ") .. tostring((i + 1))))
        ::__pytra_continue_11::
    end
    -- Force evaluation of many arithmetic expressions.
    for i = 0, (loops) - 1, 1 do
        local x = (i % var_count)
        local y = ((i + 3) % var_count)
        local c1 = ((i % 7) + 1)
        local c2 = ((i % 11) + 2)
        table.insert(lines, ((((((((("v" .. tostring(x)) .. " = (v") .. tostring(x)) .. " * ") .. tostring(c1)) .. " + v") .. tostring(y)) .. " + 10000) / ") .. tostring(c2)))
        if ((i % 97) == 0) then
            table.insert(lines, ("print v" .. tostring(x)))
        end
        ::__pytra_continue_12::
    end
    -- Print final values together.
    table.insert(lines, "print (v0 + v1 + v2 + v3)")
    return lines
end

function run_demo()
    local demo_lines = {  }
    table.insert(demo_lines, "let a = 10")
    table.insert(demo_lines, "let b = 3")
    table.insert(demo_lines, "a = (a + b) * 2")
    table.insert(demo_lines, "print a")
    table.insert(demo_lines, "print a / b")
    
    local tokens = tokenize(demo_lines)
    local parser = Parser.new(tokens)
    local stmts = parser:parse_program()
    local checksum = execute(stmts, parser.expr_nodes, true)
    __pytra_print("demo_checksum:", checksum)
end

function run_benchmark()
    local source_lines = build_benchmark_source(32, 120000)
    local start = perf_counter()
    local tokens = tokenize(source_lines)
    local parser = Parser.new(tokens)
    local stmts = parser:parse_program()
    local checksum = execute(stmts, parser.expr_nodes, false)
    local elapsed = (perf_counter() - start)
    
    __pytra_print("token_count:", #(tokens))
    __pytra_print("expr_count:", #(parser.expr_nodes))
    __pytra_print("stmt_count:", #(stmts))
    __pytra_print("checksum:", checksum)
    __pytra_print("elapsed_sec:", elapsed)
end

function __pytra_main()
    run_demo()
    run_benchmark()
end


__pytra_main()
