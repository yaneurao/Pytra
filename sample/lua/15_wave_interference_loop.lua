-- from __future__ import annotations as annotations (not yet mapped)
local math = math
-- from time import perf_counter as perf_counter (not yet mapped)
-- from pytra.utils.gif import grayscale_palette as grayscale_palette (not yet mapped)
-- from pytra.utils.gif import save_gif as save_gif (not yet mapped)

-- 15: Sample that renders wave interference animation and writes a GIF.

function run_15_wave_interference_loop()
    w = 320
    h = 240
    frames_n = 96
    out_path = "sample/out/15_wave_interference_loop.gif"
    
    start = perf_counter()
    local frames = {  }
    
    for t = 0, (frames_n) - 1, 1 do
        frame = bytearray((w * h))
        phase = (t * 0.12)
        for y = 0, (h) - 1, 1 do
            row_base = (y * w)
            for x = 0, (w) - 1, 1 do
                dx = (x - 160)
                dy = (y - 120)
                v = (((math.sin(((x + (t * 1.5)) * 0.045)) + math.sin(((y - (t * 1.2)) * 0.04))) + math.sin((((x + y) * 0.02) + phase))) + math.sin(((math.sqrt(((dx * dx) + (dy * dy))) * 0.08) - (phase * 1.3))))
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


run_15_wave_interference_loop()
