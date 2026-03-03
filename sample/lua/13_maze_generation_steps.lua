dofile((debug.getinfo(1, "S").source:sub(2):match("^(.*[\\/])") or "") .. "py_runtime.lua")

-- from __future__ import annotations as annotations (not yet mapped)
local perf_counter = __pytra_perf_counter
local grayscale_palette = __pytra_grayscale_palette
local save_gif = __pytra_save_gif

-- 13: Sample that outputs DFS maze-generation progress as a GIF.

function capture(grid, w, h, scale)
    width = (w * scale)
    height = (h * scale)
    frame = __pytra_bytearray((width * height))
    for y = 0, h - 1 do
        for x = 0, w - 1 do
            v = (((grid[(((y) < 0) and (#(grid) + (y) + 1) or ((y) + 1))][(((x) < 0) and (#(grid[(((y) < 0) and (#(grid) + (y) + 1) or ((y) + 1))]) + (x) + 1) or ((x) + 1))] == 0)) and (255) or (40))
            for yy = 0, scale - 1 do
                base = ((((y * scale) + yy) * width) + (x * scale))
                for xx = 0, scale - 1 do
                    frame[((((base + xx)) < 0) and (#(frame) + ((base + xx)) + 1) or (((base + xx)) + 1))] = v
                end
            end
        end
    end
    return __pytra_bytes(frame)
end

function run_13_maze_generation_steps()
    -- Increase maze size and render resolution to ensure sufficient runtime.
    cell_w = 89
    cell_h = 67
    scale = 5
    capture_every = 20
    out_path = "sample/out/13_maze_generation_steps.gif"
    
    start = perf_counter()
    local grid = (function() local __lc_out_6 = {}; for __lc_i_5 = 0, (cell_h) - 1, 1 do table.insert(__lc_out_6, __pytra_repeat_seq({ 1 }, cell_w)) end; return __lc_out_6 end)()
    local stack = { { 1, 1 } }
    grid[2][2] = 0
    
    local dirs = { { 2, 0 }, { (-2), 0 }, { 0, 2 }, { 0, (-2) } }
    local frames = {  }
    step = 0
    
    while __pytra_truthy(stack) do
        local __pytra_tuple_8 = stack[(#(stack) + (-1) + 1)]
        x = __pytra_tuple_8[1]
        y = __pytra_tuple_8[2]
        local candidates = {  }
        for k = 0, 4 - 1 do
            local __pytra_tuple_10 = dirs[(((k) < 0) and (#(dirs) + (k) + 1) or ((k) + 1))]
            dx = __pytra_tuple_10[1]
            dy = __pytra_tuple_10[2]
            nx = (x + dx)
            ny = (y + dy)
            if ((nx >= 1) and (nx < (cell_w - 1)) and (ny >= 1) and (ny < (cell_h - 1)) and (grid[(((ny) < 0) and (#(grid) + (ny) + 1) or ((ny) + 1))][(((nx) < 0) and (#(grid[(((ny) < 0) and (#(grid) + (ny) + 1) or ((ny) + 1))]) + (nx) + 1) or ((nx) + 1))] == 1)) then
                if (dx == 2) then
                    table.insert(candidates, { nx, ny, (x + 1), y })
                else
                    if (dx == (-2)) then
                        table.insert(candidates, { nx, ny, (x - 1), y })
                    else
                        if (dy == 2) then
                            table.insert(candidates, { nx, ny, x, (y + 1) })
                        else
                            table.insert(candidates, { nx, ny, x, (y - 1) })
                        end
                    end
                end
            end
        end
        if (#(candidates) == 0) then
            table.remove(stack)
        else
            sel = candidates[(((((((x * 17) + (y * 29)) + (#(stack) * 13)) % #(candidates))) < 0) and (#(candidates) + (((((x * 17) + (y * 29)) + (#(stack) * 13)) % #(candidates))) + 1) or ((((((x * 17) + (y * 29)) + (#(stack) * 13)) % #(candidates))) + 1))]
            local __pytra_tuple_11 = sel
            nx = __pytra_tuple_11[1]
            ny = __pytra_tuple_11[2]
            wx = __pytra_tuple_11[3]
            wy = __pytra_tuple_11[4]
            grid[(((wy) < 0) and (#(grid) + (wy) + 1) or ((wy) + 1))][(((wx) < 0) and (#(grid[(((wy) < 0) and (#(grid) + (wy) + 1) or ((wy) + 1))]) + (wx) + 1) or ((wx) + 1))] = 0
            grid[(((ny) < 0) and (#(grid) + (ny) + 1) or ((ny) + 1))][(((nx) < 0) and (#(grid[(((ny) < 0) and (#(grid) + (ny) + 1) or ((ny) + 1))]) + (nx) + 1) or ((nx) + 1))] = 0
            table.insert(stack, { nx, ny })
        end
        if ((step % capture_every) == 0) then
            table.insert(frames, capture(grid, cell_w, cell_h, scale))
        end
        step = step + 1
    end
    table.insert(frames, capture(grid, cell_w, cell_h, scale))
    save_gif(out_path, (cell_w * scale), (cell_h * scale), frames, grayscale_palette())
    elapsed = (perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", #(frames))
    __pytra_print("elapsed_sec:", elapsed)
end


run_13_maze_generation_steps()
