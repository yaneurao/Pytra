-- from __future__ import annotations as annotations (not yet mapped)
local math = math
-- from time import perf_counter as perf_counter (not yet mapped)
-- from pytra.runtime.gif import save_gif as save_gif (not yet mapped)

-- 11: Sample that outputs Lissajous-motion particles as a GIF.

function color_palette()
    p = bytearray()
    for i = 0, (256) - 1, 1 do
        r = i
        g = ((i * 3) % 256)
        b = (255 - i)
        p:append(r)
        p:append(g)
        p:append(b)
    end
    return bytes(p)
end

function run_11_lissajous_particles()
    w = 320
    h = 240
    frames_n = 360
    particles = 48
    out_path = "sample/out/11_lissajous_particles.gif"
    
    start = perf_counter()
    local frames = {  }
    
    for t = 0, (frames_n) - 1, 1 do
        frame = bytearray((w * h))
        local __hoisted_cast_1 = float(t)
        
        for p = 0, (particles) - 1, 1 do
            phase = (p * 0.261799)
            x = int(((w * 0.5) + ((w * 0.38) * math.sin(((0.11 * __hoisted_cast_1) + (phase * 2.0))))))
            y = int(((h * 0.5) + ((h * 0.38) * math.sin(((0.17 * __hoisted_cast_1) + (phase * 3.0))))))
            color = (30 + ((p * 9) % 220))
            
            for dy = (-2), (3) - 1, 1 do
                for dx = (-2), (3) - 1, 1 do
                    xx = (x + dx)
                    yy = (y + dy)
                    if ((xx >= 0) and (xx < w) and (yy >= 0) and (yy < h)) then
                        d2 = ((dx * dx) + (dy * dy))
                        if (d2 <= 4) then
                            idx = ((yy * w) + xx)
                            v = (color - (d2 * 20))
                            v = max(0, v)
                            if (v > frame[(idx) + 1]) then
                                frame[(idx) + 1] = v
                            end
                        end
                    end
                end
            end
        end
        frames:append(bytes(frame))
    end
    save_gif(out_path, w, h, frames, color_palette())
    elapsed = (perf_counter() - start)
    print("output:", out_path)
    print("frames:", frames_n)
    print("elapsed_sec:", elapsed)
end


run_11_lissajous_particles()
