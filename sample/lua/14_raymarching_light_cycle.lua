-- from __future__ import annotations as annotations (not yet mapped)
local math = math
-- from time import perf_counter as perf_counter (not yet mapped)
-- from pytra.runtime.gif import save_gif as save_gif (not yet mapped)

-- 14: Sample that outputs a moving-light scene in a simple raymarching style as a GIF.

function palette()
    p = bytearray()
    for i = 0, (256) - 1, 1 do
        r = min(255, int((20 + (i * 0.9))))
        g = min(255, int((10 + (i * 0.7))))
        b = min(255, (30 + i))
        p:append(r)
        p:append(g)
        p:append(b)
    end
    return bytes(p)
end

function scene(x, y, light_x, light_y)
    x1 = (x + 0.45)
    y1 = (y + 0.2)
    x2 = (x - 0.35)
    y2 = (y - 0.15)
    r1 = math.sqrt(((x1 * x1) + (y1 * y1)))
    r2 = math.sqrt(((x2 * x2) + (y2 * y2)))
    blob = (math.exp((((-7.0) * r1) * r1)) + math.exp((((-8.0) * r2) * r2)))
    
    lx = (x - light_x)
    ly = (y - light_y)
    l = math.sqrt(((lx * lx) + (ly * ly)))
    lit = (1.0 / (1.0 + ((3.5 * l) * l)))
    
    v = int((((255.0 * blob) * lit) * 5.0))
    return min(255, max(0, v))
end

function run_14_raymarching_light_cycle()
    w = 320
    h = 240
    frames_n = 84
    out_path = "sample/out/14_raymarching_light_cycle.gif"
    
    start = perf_counter()
    local frames = {  }
    local __hoisted_cast_1 = float(frames_n)
    local __hoisted_cast_2 = float((h - 1))
    local __hoisted_cast_3 = float((w - 1))
    
    for t = 0, (frames_n) - 1, 1 do
        frame = bytearray((w * h))
        a = (((t / __hoisted_cast_1) * math.pi) * 2.0)
        light_x = (0.75 * math.cos(a))
        light_y = (0.55 * math.sin((a * 1.2)))
        
        for y = 0, (h) - 1, 1 do
            row_base = (y * w)
            py = (((y / __hoisted_cast_2) * 2.0) - 1.0)
            for x = 0, (w) - 1, 1 do
                px = (((x / __hoisted_cast_3) * 2.0) - 1.0)
                frame[((row_base + x)) + 1] = scene(px, py, light_x, light_y)
            end
        end
        frames:append(bytes(frame))
    end
    save_gif(out_path, w, h, frames, palette())
    elapsed = (perf_counter() - start)
    print("output:", out_path)
    print("frames:", frames_n)
    print("elapsed_sec:", elapsed)
end


run_14_raymarching_light_cycle()
