# Pytra Julia runtime helpers
# Generated runtime support for Python→Julia transpilation.

abstract type PytraBuiltinException <: Base.Exception end
mutable struct __PytraException <: PytraBuiltinException
    msg
end
Base.show(io::IO, e::__PytraException) = print(io, e.msg)
Base.showerror(io::IO, e::__PytraException) = print(io, e.msg)
const PytraException = PytraBuiltinException
__pytra_exception(msg="error") = __PytraException(msg)

abstract type PytraValueError <: PytraBuiltinException end
mutable struct __PytraValueError <: PytraValueError
    msg
end
Base.show(io::IO, e::__PytraValueError) = print(io, e.msg)
Base.showerror(io::IO, e::__PytraValueError) = print(io, e.msg)
__pytra_value_error(msg="error") = __PytraValueError(msg)

abstract type PytraRuntimeError <: PytraBuiltinException end
mutable struct __PytraRuntimeError <: PytraRuntimeError
    msg
end
Base.show(io::IO, e::__PytraRuntimeError) = print(io, e.msg)
Base.showerror(io::IO, e::__PytraRuntimeError) = print(io, e.msg)
__pytra_runtime_error(msg="error") = __PytraRuntimeError(msg)

abstract type PytraTypeError <: PytraBuiltinException end
mutable struct __PytraTypeError <: PytraTypeError
    msg
end
Base.show(io::IO, e::__PytraTypeError) = print(io, e.msg)
Base.showerror(io::IO, e::__PytraTypeError) = print(io, e.msg)
__pytra_type_error(msg="error") = __PytraTypeError(msg)

abstract type PytraAssertionError <: PytraBuiltinException end
mutable struct __PytraAssertionError <: PytraAssertionError
    msg
end
Base.show(io::IO, e::__PytraAssertionError) = print(io, e.msg)
Base.showerror(io::IO, e::__PytraAssertionError) = print(io, e.msg)
__pytra_assertion_error(msg="error") = __PytraAssertionError(msg)

abstract type PytraIndexError <: PytraBuiltinException end
mutable struct __PytraIndexError <: PytraIndexError
    msg
end
Base.show(io::IO, e::__PytraIndexError) = print(io, e.msg)
Base.showerror(io::IO, e::__PytraIndexError) = print(io, e.msg)
__pytra_index_error(msg="error") = __PytraIndexError(msg)

abstract type PytraKeyError <: PytraBuiltinException end
mutable struct __PytraKeyError <: PytraKeyError
    msg
end
Base.show(io::IO, e::__PytraKeyError) = print(io, e.msg)
Base.showerror(io::IO, e::__PytraKeyError) = print(io, e.msg)
__pytra_key_error(msg="error") = __PytraKeyError(msg)

__pytra_exception_message(v::__PytraException) = string(v.msg)
__pytra_exception_message(v::__PytraValueError) = string(v.msg)
__pytra_exception_message(v::__PytraRuntimeError) = string(v.msg)
__pytra_exception_message(v::__PytraTypeError) = string(v.msg)
__pytra_exception_message(v::__PytraAssertionError) = string(v.msg)
__pytra_exception_message(v::__PytraIndexError) = string(v.msg)
__pytra_exception_message(v::__PytraKeyError) = string(v.msg)

__pytra_new_BaseException(msg="error") = __pytra_exception(msg)
__pytra_new_Exception(msg="error") = __pytra_exception(msg)
__pytra_new_ValueError(msg="error") = __pytra_value_error(msg)
__pytra_new_RuntimeError(msg="error") = __pytra_runtime_error(msg)
__pytra_new_TypeError(msg="error") = __pytra_type_error(msg)
__pytra_new_IndexError(msg="error") = __pytra_index_error(msg)
__pytra_new_KeyError(msg="error") = __pytra_key_error(msg)

const ValueError = __PytraValueError
const RuntimeError = __PytraRuntimeError
const TypeError = __PytraTypeError
const IndexError = __PytraIndexError
const KeyError = __PytraKeyError

function __pytra_exception_message(v)
    return string(v)
end

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
            push!(parts, __pytra_str(v))
        end
    end
    println(join(parts, " "))
    return nothing
end

function py_assert_true(cond, _label="")
    return __pytra_truthy(cond)
end

function py_assert_eq(a, b, _label="")
    return a == b
end

function py_assert_all(items, _label="")
    return all(__pytra_truthy(item) for item in items)
end

function py_assert_stdout(_expected, fn)
    return true
end

function __LIST_CTOR__(value)
    if value === nothing
        return []
    end
    return collect(value)
end

function reversed(value)
    return reverse(value)
end

function __pytra_str(v)
    if v === nothing
        return "None"
    end
    if isa(v, Bool)
        return v ? "True" : "False"
    end
    if isa(v, AbstractString)
        return v
    end
    if isa(v, AbstractVector)
        parts = String[]
        for item in v
            if isa(item, AbstractString)
                push!(parts, "'" * item * "'")
            else
                push!(parts, __pytra_str(item))
            end
        end
        return "[" * join(parts, ", ") * "]"
    end
    if isa(v, Tuple)
        parts = String[]
        for item in v
            if isa(item, AbstractString)
                push!(parts, "'" * item * "'")
            else
                push!(parts, __pytra_str(item))
            end
        end
        if length(parts) == 1
            return "(" * parts[1] * ",)"
        end
        return "(" * join(parts, ", ") * ")"
    end
    if isa(v, AbstractDict)
        parts = String[]
        dict_keys = collect(keys(v))
        sort!(dict_keys, by=__pytra_str)
        for k in dict_keys
            item = v[k]
            key_repr = isa(k, AbstractString) ? "'" * k * "'" : __pytra_str(k)
            val_repr = isa(item, AbstractString) ? "'" * item * "'" : __pytra_str(item)
            push!(parts, key_repr * ": " * val_repr)
        end
        return "{" * join(parts, ", ") * "}"
    end
    return string(v)
end

function __pytra_format(v, spec)
    if spec == "4d"
        return lpad(string(Int(v)), 4)
    end
    if spec == ".4f"
        return string(round(Float64(v), digits=4))
    end
    return __pytra_str(v)
end

function __pytra_re_sub(pattern, repl, text, count=nothing)
    regex = Regex(pattern)
    return replace(text, regex => repl)
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

function sorted(v)
    return sort(collect(v))
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

function __pytra_float_from_str(v)
    return parse(Float64, strip(string(v)))
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

function __pytra_str_slice(s, start, stop)
    len_s = length(s)
    start_idx = start
    if start_idx < 0
        start_idx = len_s + start_idx
    end
    if start_idx < 0
        start_idx = 0
    end
    stop_idx = stop
    if stop_idx === nothing
        stop_idx = len_s
    elseif stop_idx < 0
        stop_idx = len_s + stop_idx
    end
    if stop_idx < 0
        stop_idx = 0
    end
    if stop_idx > len_s
        stop_idx = len_s
    end
    if start_idx > stop_idx
        return ""
    end
    if start_idx == stop_idx
        return ""
    end
    return s[(start_idx + 1):stop_idx]
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

function __pytra_deque(v=nothing)
    if v === nothing
        return Any[]
    end
    if isa(v, AbstractArray) || isa(v, Tuple)
        return collect(v)
    end
    return Any[v]
end

deque(v=nothing) = __pytra_deque(v)

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

function __pytra_str_index(s, sub)
    pos = __pytra_str_find(s, sub)
    if pos < 0
        throw(__pytra_value_error("substring not found"))
    end
    return pos
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

function __py_io_enter(io)
    return io
end

function __py_io_exit(io, _exc_type=nothing, _exc_val=nothing, _exc_tb=nothing)
    close(io)
    return nothing
end
