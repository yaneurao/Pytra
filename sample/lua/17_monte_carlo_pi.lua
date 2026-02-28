-- Auto-generated Pytra Lua native source from EAST3.

-- from time import perf_counter as perf_counter (not yet mapped)

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
        end
        acc = ((acc + (row_sum * (y + 1))) % mod_out)
    end
    return acc
end

function run_integer_benchmark()
    local width = 7600
    local height = 5000
    local start = perf_counter()
    local checksum = run_integer_grid_checksum(width, height, 123456789)
    local elapsed = (perf_counter() - start)
    print("pixels:", (width * height))
    print("checksum:", checksum)
    print("elapsed_sec:", elapsed)
end


-- __main__ guard
run_integer_benchmark()
