-- Auto-generated Pytra Lua native source from EAST3.

-- from time import perf_counter as perf_counter (not yet mapped)

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
        end
        acc = ((acc + (row_sum * (y + 1))) % mod_out)
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
    
    print("pixels:", (width * height))
    print("checksum:", checksum)
    print("elapsed_sec:", elapsed)
end


-- __main__ guard
run_integer_benchmark()
