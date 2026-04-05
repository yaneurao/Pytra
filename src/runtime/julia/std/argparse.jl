mutable struct ArgumentParser
    prog
    specs
end

function ArgumentParser(prog)
    return ArgumentParser(prog, Any[])
end

function add_argument(parser, args...)
    push!(parser.specs, collect(args))
    return nothing
end

function add_argument(parser, args...; action=nothing, choices=nothing, default=nothing)
    push!(parser.specs, (collect(args), (action=action, choices=choices, default=default)))
    return nothing
end

function parse_args(parser, argv)
    out = Dict{Any,Any}()
    positional = Any[]
    i = 1
    while i <= length(argv)
        token = argv[i]
        if token == "--pretty"
            out["pretty"] = true
            i += 1
            continue
        end
        if token == "-o" || token == "--output"
            out["output"] = argv[i + 1]
            i += 2
            continue
        end
        if token == "-m" || token == "--mode"
            out["mode"] = argv[i + 1]
            i += 2
            continue
        end
        push!(positional, token)
        i += 1
    end
    if length(positional) > 0
        out["input"] = positional[1]
    end
    if !haskey(out, "pretty")
        out["pretty"] = false
    end
    if !haskey(out, "mode")
        out["mode"] = "a"
    end
    return out
end
