dofile((debug.getinfo(1, "S").source:sub(2):match("^(.*[\\/])") or "") .. "py_runtime.lua")

-- from __future__ import annotations as annotations (not yet mapped)
local perf_counter = __pytra_perf_counter
local save_gif = __pytra_save_gif

-- 09: Sample that outputs a simple fire effect as a GIF.

function fire_palette()
    p = __pytra_bytearray()
    for i = 0, 256 - 1 do
        r = 0
        g = 0
        b = 0
        if (i < 85) then
            r = (i * 3)
            g = 0
            b = 0
        else
            if (i < 170) then
                r = 255
                g = ((i - 85) * 3)
                b = 0
            else
                r = 255
                g = 255
                b = ((i - 170) * 3)
            end
        end
        table.move({r, g, b}, 1, 3, #(p) + 1, p)
    end
    return __pytra_bytes(p)
end

function run_09_fire_simulation()
    w = 380
    h = 260
    steps = 420
    out_path = "sample/out/09_fire_simulation.gif"
    
    start = perf_counter()
    local heat = (function() local __lc_out_3 = {}; for __lc_i_2 = 0, (h) - 1, 1 do table.insert(__lc_out_3, __pytra_repeat_seq({ 0 }, w)) end; return __lc_out_3 end)()
    local frames = {  }
    
    for t = 0, steps - 1 do
        for x = 0, w - 1 do
            val = (170 + (((x * 13) + (t * 17)) % 86))
            heat[((((h - 1)) < 0) and (#(heat) + ((h - 1)) + 1) or (((h - 1)) + 1))][(((x) < 0) and (#(heat[((((h - 1)) < 0) and (#(heat) + ((h - 1)) + 1) or (((h - 1)) + 1))]) + (x) + 1) or ((x) + 1))] = val
        end
        for y = 1, h - 1 do
            for x = 0, w - 1 do
                a = heat[(((y) < 0) and (#(heat) + (y) + 1) or ((y) + 1))][(((x) < 0) and (#(heat[(((y) < 0) and (#(heat) + (y) + 1) or ((y) + 1))]) + (x) + 1) or ((x) + 1))]
                b = heat[(((y) < 0) and (#(heat) + (y) + 1) or ((y) + 1))][((((((x - 1) + w) % w)) < 0) and (#(heat[(((y) < 0) and (#(heat) + (y) + 1) or ((y) + 1))]) + ((((x - 1) + w) % w)) + 1) or (((((x - 1) + w) % w)) + 1))]
                c = heat[(((y) < 0) and (#(heat) + (y) + 1) or ((y) + 1))][(((((x + 1) % w)) < 0) and (#(heat[(((y) < 0) and (#(heat) + (y) + 1) or ((y) + 1))]) + (((x + 1) % w)) + 1) or ((((x + 1) % w)) + 1))]
                d = heat[(((((y + 1) % h)) < 0) and (#(heat) + (((y + 1) % h)) + 1) or ((((y + 1) % h)) + 1))][(((x) < 0) and (#(heat[(((((y + 1) % h)) < 0) and (#(heat) + (((y + 1) % h)) + 1) or ((((y + 1) % h)) + 1))]) + (x) + 1) or ((x) + 1))]
                v = ((((a + b) + c) + d) // 4)
                cool = (1 + (((x + y) + t) % 3))
                nv = (v - cool)
                heat[((((y - 1)) < 0) and (#(heat) + ((y - 1)) + 1) or (((y - 1)) + 1))][(((x) < 0) and (#(heat[((((y - 1)) < 0) and (#(heat) + ((y - 1)) + 1) or (((y - 1)) + 1))]) + (x) + 1) or ((x) + 1))] = (((nv > 0)) and (nv) or (0))
            end
        end
        frame = __pytra_bytearray((w * h))
        for yy = 0, h - 1 do
            row_base = (yy * w)
            for xx = 0, w - 1 do
                frame[((((row_base + xx)) < 0) and (#(frame) + ((row_base + xx)) + 1) or (((row_base + xx)) + 1))] = heat[(((yy) < 0) and (#(heat) + (yy) + 1) or ((yy) + 1))][(((xx) < 0) and (#(heat[(((yy) < 0) and (#(heat) + (yy) + 1) or ((yy) + 1))]) + (xx) + 1) or ((xx) + 1))]
            end
        end
        table.insert(frames, __pytra_bytes(frame))
    end
    save_gif(out_path, w, h, frames, fire_palette())
    elapsed = (perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", steps)
    __pytra_print("elapsed_sec:", elapsed)
end


run_09_fire_simulation()
