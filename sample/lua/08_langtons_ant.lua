dofile((debug.getinfo(1, "S").source:sub(2):match("^(.*[\\/])") or "") .. "py_runtime.lua")

-- from __future__ import annotations as annotations (not yet mapped)
local perf_counter = __pytra_perf_counter
local grayscale_palette = __pytra_grayscale_palette
local save_gif = __pytra_save_gif

-- 08: Sample that outputs Langton's Ant trajectories as a GIF.

function capture(grid, w, h)
    frame = __pytra_bytearray((w * h))
    for y = 0, h - 1 do
        row_base = (y * w)
        for x = 0, w - 1 do
            frame[((((row_base + x)) < 0) and (#(frame) + ((row_base + x)) + 1) or (((row_base + x)) + 1))] = ((grid[(((y) < 0) and (#(grid) + (y) + 1) or ((y) + 1))][(((x) < 0) and (#(grid[(((y) < 0) and (#(grid) + (y) + 1) or ((y) + 1))]) + (x) + 1) or ((x) + 1))]) and (255) or (0))
        end
    end
    return __pytra_bytes(frame)
end

function run_08_langtons_ant()
    w = 420
    h = 420
    out_path = "sample/out/08_langtons_ant.gif"
    
    start = perf_counter()
    
    local grid = (function() local __lc_out_4 = {}; for __lc_i_3 = 0, (h) - 1, 1 do table.insert(__lc_out_4, __pytra_repeat_seq({ 0 }, w)) end; return __lc_out_4 end)()
    x = (w // 2)
    y = (h // 2)
    d = 0
    
    steps_total = 600000
    capture_every = 3000
    local frames = {  }
    
    for i = 0, steps_total - 1 do
        if (grid[(((y) < 0) and (#(grid) + (y) + 1) or ((y) + 1))][(((x) < 0) and (#(grid[(((y) < 0) and (#(grid) + (y) + 1) or ((y) + 1))]) + (x) + 1) or ((x) + 1))] == 0) then
            d = ((d + 1) % 4)
            grid[(((y) < 0) and (#(grid) + (y) + 1) or ((y) + 1))][(((x) < 0) and (#(grid[(((y) < 0) and (#(grid) + (y) + 1) or ((y) + 1))]) + (x) + 1) or ((x) + 1))] = 1
        else
            d = ((d + 3) % 4)
            grid[(((y) < 0) and (#(grid) + (y) + 1) or ((y) + 1))][(((x) < 0) and (#(grid[(((y) < 0) and (#(grid) + (y) + 1) or ((y) + 1))]) + (x) + 1) or ((x) + 1))] = 0
        end
        if (d == 0) then
            y = (((y - 1) + h) % h)
        else
            if (d == 1) then
                x = ((x + 1) % w)
            else
                if (d == 2) then
                    y = ((y + 1) % h)
                else
                    x = (((x - 1) + w) % w)
                end
            end
        end
        if ((i % capture_every) == 0) then
            table.insert(frames, capture(grid, w, h))
        end
    end
    save_gif(out_path, w, h, frames, grayscale_palette())
    elapsed = (perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", #(frames))
    __pytra_print("elapsed_sec:", elapsed)
end


run_08_langtons_ant()
