dofile((debug.getinfo(1, "S").source:sub(2):match("^(.*[\\/])") or "") .. "py_runtime.lua")

-- from __future__ import annotations as annotations (not yet mapped)
local math = __pytra_math_module()
local perf_counter = __pytra_perf_counter
local grayscale_palette = __pytra_grayscale_palette
local save_gif = __pytra_save_gif

-- 15: Sample that renders wave interference animation and writes a GIF.

function run_15_wave_interference_loop()
    w = 320
    h = 240
    frames_n = 96
    out_path = "sample/out/15_wave_interference_loop.gif"
    
    start = perf_counter()
    local frames = {  }
    
    for t = 0, frames_n - 1 do
        frame = __pytra_bytearray((w * h))
        phase = (t * 0.12)
        for y = 0, h - 1 do
            row_base = (y * w)
            for x = 0, w - 1 do
                dx = (x - 160)
                dy = (y - 120)
                v = (((math.sin(((x + (t * 1.5)) * 0.045)) + math.sin(((y - (t * 1.2)) * 0.04))) + math.sin((((x + y) * 0.02) + phase))) + math.sin(((math.sqrt(((dx * dx) + (dy * dy))) * 0.08) - (phase * 1.3))))
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


run_15_wave_interference_loop()
