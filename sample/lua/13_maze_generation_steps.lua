-- from __future__ import annotations as annotations (not yet mapped)
-- from time import perf_counter as perf_counter (not yet mapped)
-- from pytra.runtime.gif import grayscale_palette as grayscale_palette (not yet mapped)
-- from pytra.runtime.gif import save_gif as save_gif (not yet mapped)

-- 13: Sample that outputs DFS maze-generation progress as a GIF.

function capture(grid, w, h, scale)
    width = (w * scale)
    height = (h * scale)
    frame = bytearray((width * height))
    for y = 0, (h) - 1, 1 do
        for x = 0, (w) - 1, 1 do
            v = (((grid[(y) + 1][(x) + 1] == 0)) and (255) or (40))
            for yy = 0, (scale) - 1, 1 do
                base = ((((y * scale) + yy) * width) + (x * scale))
                for xx = 0, (scale) - 1, 1 do
                    frame[((base + xx)) + 1] = v
                end
            end
        end
    end
    return bytes(frame)
end

function run_13_maze_generation_steps()
    -- Increase maze size and render resolution to ensure sufficient runtime.
    cell_w = 89
    cell_h = 67
    scale = 5
    capture_every = 20
    out_path = "sample/out/13_maze_generation_steps.gif"
    
    start = perf_counter()
    local grid = (function() local __lc_out_2 = {}; for __lc_i_1 = 0, (cell_h) - 1, 1 do table.insert(__lc_out_2, ({ 1 } * cell_w)) end; return __lc_out_2 end)()
    local stack = { { 1, 1 } }
    grid[(1) + 1][(1) + 1] = 0
    
    local dirs = { { 2, 0 }, { (-2), 0 }, { 0, 2 }, { 0, (-2) } }
    local frames = {  }
    step = 0
    
    while stack do
        local __pytra_tuple_3 = stack[((-1)) + 1]
        x = __pytra_tuple_3[1]
        y = __pytra_tuple_3[2]
        local candidates = {  }
        for k = 0, (4) - 1, 1 do
            local __pytra_tuple_4 = dirs[(k) + 1]
            dx = __pytra_tuple_4[1]
            dy = __pytra_tuple_4[2]
            nx = (x + dx)
            ny = (y + dy)
            if ((nx >= 1) and (nx < (cell_w - 1)) and (ny >= 1) and (ny < (cell_h - 1)) and (grid[(ny) + 1][(nx) + 1] == 1)) then
                if (dx == 2) then
                    candidates:append({ nx, ny, (x + 1), y })
                else
                    if (dx == (-2)) then
                        candidates:append({ nx, ny, (x - 1), y })
                    else
                        if (dy == 2) then
                            candidates:append({ nx, ny, x, (y + 1) })
                        else
                            candidates:append({ nx, ny, x, (y - 1) })
                        end
                    end
                end
            end
        end
        if (len(candidates) == 0) then
            stack:pop()
        else
            sel = candidates[(((((x * 17) + (y * 29)) + (len(stack) * 13)) % len(candidates))) + 1]
            local __pytra_tuple_5 = sel
            nx = __pytra_tuple_5[1]
            ny = __pytra_tuple_5[2]
            wx = __pytra_tuple_5[3]
            wy = __pytra_tuple_5[4]
            grid[(wy) + 1][(wx) + 1] = 0
            grid[(ny) + 1][(nx) + 1] = 0
            stack:append({ nx, ny })
        end
        if ((step % capture_every) == 0) then
            frames:append(capture(grid, cell_w, cell_h, scale))
        end
        step = step + 1
    end
    frames:append(capture(grid, cell_w, cell_h, scale))
    save_gif(out_path, (cell_w * scale), (cell_h * scale), frames, grayscale_palette())
    elapsed = (perf_counter() - start)
    print("output:", out_path)
    print("frames:", len(frames))
    print("elapsed_sec:", elapsed)
end


run_13_maze_generation_steps()
