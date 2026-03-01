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

local perf_counter = __pytra_perf_counter

-- 17: Sample that scans a large grid using integer arithmetic only and computes a checksum.
-- It avoids floating-point error effects, making cross-language comparisons easier.

function run_integer_grid_checksum(width, height, seed)
    local mod_main = 2147483647
    local mod_out = 1000000007
    local acc = (seed % mod_out)
    
    for y = 0, (height) - 1, 1 do
        local row_sum = 0
        for x = 0, (width) - 1, 1 do
            local v = ((((x * 37) + (y * 73)) + seed) % mod_main)
            v = (((v * 48271) + 1) % mod_main)
            row_sum = row_sum + (v % 256)
            ::__pytra_continue_2::
        end
        acc = ((acc + (row_sum * (y + 1))) % mod_out)
        ::__pytra_continue_1::
    end
    return acc
end

function run_integer_benchmark()
    -- Previous baseline: 2400 x 1600 (= 3,840,000 cells).
    -- 7600 x 5000 (= 38,000,000 cells) is ~9.9x larger to make this case
    -- meaningful in runtime benchmarks.
    local width = 7600
    local height = 5000
    
    local start = perf_counter()
    local checksum = run_integer_grid_checksum(width, height, 123456789)
    local elapsed = (perf_counter() - start)
    
    __pytra_print("pixels:", (width * height))
    __pytra_print("checksum:", checksum)
    __pytra_print("elapsed_sec:", elapsed)
end


run_integer_benchmark()
