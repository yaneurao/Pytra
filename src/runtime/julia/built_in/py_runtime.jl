# Pytra Julia runtime helpers
# Generated runtime support for Python→Julia transpilation.

function __pytra_print(args...)
    if length(args) == 0
        println()
        return nothing
    end
    parts = String[]
    for v in args
        if v === true
            push!(parts, "True")
        elseif v === false
            push!(parts, "False")
        elseif v === nothing
            push!(parts, "None")
        else
            push!(parts, string(v))
        end
    end
    println(join(parts, " "))
    return nothing
end

function __pytra_truthy(v)
    if v === nothing
        return false
    end
    if isa(v, Bool)
        return v
    end
    if isa(v, Number)
        return v != 0
    end
    if isa(v, AbstractString)
        return length(v) != 0
    end
    if isa(v, AbstractArray) || isa(v, AbstractDict) || isa(v, AbstractSet) || isa(v, Tuple)
        return !isempty(v)
    end
    return true
end

function __pytra_contains(container, value)
    if isa(container, AbstractDict)
        return haskey(container, value)
    end
    if isa(container, AbstractString)
        return occursin(string(value), container)
    end
    if isa(container, AbstractSet)
        return value in container
    end
    if isa(container, AbstractArray) || isa(container, Tuple)
        return value in container
    end
    return false
end

function __pytra_int(v)
    if isa(v, AbstractString)
        return parse(Int, strip(v))
    end
    return Int(floor(v))
end

function __pytra_idx(index::Integer, len::Integer)
    if index < 0
        return len + index + 1
    end
    return index + 1
end

function __pytra_range(start, stop, step)
    if step > 0
        return start:step:(stop - 1)
    elseif step < 0
        return start:step:(stop + 1)
    else
        return Int[]
    end
end

function __pytra_repeat_seq(a, b)
    seq = a
    count_val = b
    if isa(a, Number) && !isa(b, Number)
        seq = b
        count_val = a
    end
    n = Int(floor(count_val))
    if n <= 0
        if isa(seq, AbstractString)
            return ""
        end
        return Any[]
    end
    if isa(seq, AbstractString)
        return repeat(seq, n)
    end
    if isa(seq, AbstractArray)
        out = Any[]
        for _ in 1:n
            append!(out, seq)
        end
        return out
    end
    return a * b
end

function __pytra_enumerate(iterable)
    out = Any[]
    for (i, v) in enumerate(iterable)
        push!(out, (i - 1, v))
    end
    return out
end

function __pytra_slice(arr, start, stop)
    s = start + 1
    if stop === nothing
        return arr[s:end]
    end
    return arr[s:stop]
end

function __pytra_bytearray(v=nothing)
    if v === nothing
        return UInt8[]
    end
    if isa(v, Integer)
        return zeros(UInt8, v)
    end
    if isa(v, AbstractArray)
        return UInt8.(v)
    end
    return UInt8[]
end

function __pytra_bytes(v=nothing)
    if v === nothing
        return UInt8[]
    end
    if isa(v, AbstractArray)
        return UInt8.(v)
    end
    if isa(v, AbstractString)
        return Vector{UInt8}(codeunits(v))
    end
    return UInt8[]
end

# Python の bytes イテレーションは int を返す。
# Julia の UInt8 はビット演算でオーバーフローするため、
# bytes/bytearray のイテレーション時に Int に昇格させる。
function __pytra_iter_ints(data)
    return Int.(data)
end

function __pytra_str_find(s, sub)
    r = findfirst(sub, s)
    if r === nothing
        return -1
    end
    return first(r) - 1
end

function __pytra_str_rfind(s, sub)
    r = findlast(sub, s)
    if r === nothing
        return -1
    end
    return first(r) - 1
end

function __pytra_str_isdigit(s)
    if length(s) == 0
        return false
    end
    return all(isdigit, s)
end

function __pytra_str_isalpha(s)
    if length(s) == 0
        return false
    end
    return all(isletter, s)
end

function __pytra_str_isalnum(s)
    if length(s) == 0
        return false
    end
    return all(c -> isdigit(c) || isletter(c), s)
end

function __pytra_perf_counter()
    return time()
end

function __pytra_noop()
    return nothing
end

function py_open(path, mode="r")
    if mode == "wb"
        return open(path, "w")
    elseif mode == "rb"
        return open(path, "r")
    end
    return open(path, mode)
end
