dofile((debug.getinfo(1, "S").source:sub(2):match("^(.*[\\/])") or "") .. "py_runtime.lua")

-- from __future__ import annotations as annotations (not yet mapped)
local math = __pytra_math_module()
local perf_counter = __pytra_perf_counter
local grayscale_palette = __pytra_grayscale_palette
local save_gif = __pytra_save_gif

-- 10: Sample that outputs a plasma effect as a GIF.

function run_10_plasma_effect()
    w = 320
    h = 240
    frames_n = 216
    out_path = "sample/out/10_plasma_effect.gif"
    
    start = perf_counter()
    local frames = {  }
    
    for t = 0, frames_n - 1 do
        frame = __pytra_bytearray((w * h))
        for y = 0, h - 1 do
            row_base = (y * w)
            for x = 0, w - 1 do
                dx = (x - 160)
                dy = (y - 120)
                v = (((math.sin(((x + (t * 2.0)) * 0.045)) + math.sin(((y - (t * 1.2)) * 0.05))) + math.sin((((x + y) + (t * 1.7)) * 0.03))) + math.sin(((math.sqrt(((dx * dx) + (dy * dy))) * 0.07) - (t * 0.18))))
                c = __pytra_int(((v + 4.0) * (255.0 / 8.0)))
                if (c < 0) then
                    c = 0
                end
                if (c > 255) then
                    c = 255
                end
                frame[((((row_base + x)) < 0) and (#(frame) + ((row_base + x)) + 1) or (((row_base + x)) + 1))] = c
            end
        end
        table.insert(frames, __pytra_bytes(frame))
    end
    save_gif(out_path, w, h, frames, grayscale_palette())
    elapsed = (perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
end


run_10_plasma_effect()
