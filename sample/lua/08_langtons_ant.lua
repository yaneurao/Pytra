-- from __future__ import annotations as annotations (not yet mapped)
-- from time import perf_counter as perf_counter (not yet mapped)
-- from pytra.runtime.gif import grayscale_palette as grayscale_palette (not yet mapped)
-- from pytra.runtime.gif import save_gif as save_gif (not yet mapped)

-- 08: Sample that outputs Langton's Ant trajectories as a GIF.

function capture(grid, w, h)
    frame = bytearray((w * h))
    for y = 0, (h) - 1, 1 do
        row_base = (y * w)
        for x = 0, (w) - 1, 1 do
            frame[((row_base + x)) + 1] = ((grid[(y) + 1][(x) + 1]) and (255) or (0))
        end
    end
    return bytes(frame)
end

function run_08_langtons_ant()
    w = 420
    h = 420
    out_path = "sample/out/08_langtons_ant.gif"
    
    start = perf_counter()
    
    local grid = (function() local __lc_out_2 = {}; for __lc_i_1 = 0, (h) - 1, 1 do table.insert(__lc_out_2, ({ 0 } * w)) end; return __lc_out_2 end)()
    x = (w // 2)
    y = (h // 2)
    d = 0
    
    steps_total = 600000
    capture_every = 3000
    local frames = {  }
    
    for i = 0, (steps_total) - 1, 1 do
        if (grid[(y) + 1][(x) + 1] == 0) then
            d = ((d + 1) % 4)
            grid[(y) + 1][(x) + 1] = 1
        else
            d = ((d + 3) % 4)
            grid[(y) + 1][(x) + 1] = 0
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
            frames:append(capture(grid, w, h))
        end
    end
    save_gif(out_path, w, h, frames, grayscale_palette())
    elapsed = (perf_counter() - start)
    print("output:", out_path)
    print("frames:", len(frames))
    print("elapsed_sec:", elapsed)
end


run_08_langtons_ant()
