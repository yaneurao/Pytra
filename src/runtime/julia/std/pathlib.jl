include(joinpath(@__DIR__, "os_native.jl"))
include(joinpath(@__DIR__, "os_path_native.jl"))

mutable struct Path
    _value
    Path() = new("")
end

function Path(value)
    p = Path()
    p._value = string(value)
    return p
end

Base.show(io::IO, p::Path) = print(io, p._value)
Base.showerror(io::IO, p::Path) = print(io, p._value)

function Base.getproperty(p::Path, name::Symbol)
    if name === :name
        return __OsPathNative.basename(getfield(p, :_value))
    end
    if name === :stem
        root, _ext = __OsPathNative.splitext(__OsPathNative.basename(getfield(p, :_value)))
        return root
    end
    if name === :parent
        return Path(__OsPathNative.dirname(getfield(p, :_value)))
    end
    return getfield(p, name)
end

function Base.:/(lhs::Path, rhs)
    return Path(__OsPathNative.join(getfield(lhs, :_value), string(rhs)))
end

function Base.joinpath(lhs::Path, rhs...)
    parts = Any[getfield(lhs, :_value)]
    for part in rhs
        push!(parts, string(part))
    end
    return Path(__OsPathNative.join(parts...))
end

function exists(self::Path)
    return __OsPathNative.exists(self._value)
end

function mkdir(self::Path, parents=false, exist_ok=false)
    if parents
        return __OsNative.makedirs(self._value, exist_ok)
    end
    return __OsNative.mkdir(self._value, exist_ok)
end

function mkdir(self::Path; parents=false, exist_ok=false)
    return mkdir(self, parents, exist_ok)
end

function write_text(self::Path, text)
    open(self._value, "w") do io
        write(io, string(text))
    end
    return nothing
end

function read_text(self::Path)
    return read(self._value, String)
end
