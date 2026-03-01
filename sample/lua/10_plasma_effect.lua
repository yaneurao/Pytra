-- from __future__ import annotations as annotations (not yet mapped)
local math = math
-- from time import perf_counter as perf_counter (not yet mapped)
-- from pytra.runtime.gif import grayscale_palette as grayscale_palette (not yet mapped)
-- from pytra.runtime.gif import save_gif as save_gif (not yet mapped)

-- 10: Sample that outputs a plasma effect as a GIF.

function run_10_plasma_effect()
    w = 320
    h = 240
    frames_n = 216
    out_path = "sample/out/10_plasma_effect.gif"
    
    start = perf_counter()
    local frames = {  }
    
    for t = 0, (frames_n) - 1, 1 do
        frame = bytearray((w * h))
        for y = 0, (h) - 1, 1 do
            row_base = (y * w)
            for x = 0, (w) - 1, 1 do
                dx = (x - 160)
                dy = (y - 120)
                v = (((math.sin(((x + (t * 2.0)) * 0.045)) + math.sin(((y - (t * 1.2)) * 0.05))) + math.sin((((x + y) + (t * 1.7)) * 0.03))) + math.sin(((math.sqrt(((dx * dx) + (dy * dy))) * 0.07) - (t * 0.18))))
                c = int(((v + 4.0) * (255.0 / 8.0)))
                if (c < 0) then
                    c = 0
                end
                if (c > 255) then
                    c = 255
                end
                frame[((row_base + x)) + 1] = c
            end
        end
        frames:append(bytes(frame))
    end
    save_gif(out_path, w, h, frames, grayscale_palette())
    elapsed = (perf_counter() - start)
    print("output:", out_path)
    print("frames:", frames_n)
    print("elapsed_sec:", elapsed)
end


run_10_plasma_effect()
