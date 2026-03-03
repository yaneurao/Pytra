dofile((debug.getinfo(1, "S").source:sub(2):match("^(.*[\\/])") or "") .. "py_runtime.lua")

-- from __future__ import annotations as annotations (not yet mapped)
local math = __pytra_math_module()
local perf_counter = __pytra_perf_counter
local save_gif = __pytra_save_gif

-- 11: Sample that outputs Lissajous-motion particles as a GIF.

function color_palette()
    p = __pytra_bytearray()
    for i = 0, 256 - 1 do
        r = i
        g = ((i * 3) % 256)
        b = (255 - i)
        table.move({r, g, b}, 1, 3, #(p) + 1, p)
    end
    return __pytra_bytes(p)
end

function run_11_lissajous_particles()
    w = 320
    h = 240
    frames_n = 360
    particles = 48
    out_path = "sample/out/11_lissajous_particles.gif"
    
    start = perf_counter()
    local frames = {  }
    
    for t = 0, frames_n - 1 do
        frame = __pytra_bytearray((w * h))
        local __hoisted_cast_1 = __pytra_float(t)
        
        for p = 0, particles - 1 do
            phase = (p * 0.261799)
            x = __pytra_int(((w * 0.5) + ((w * 0.38) * math.sin(((0.11 * __hoisted_cast_1) + (phase * 2.0))))))
            y = __pytra_int(((h * 0.5) + ((h * 0.38) * math.sin(((0.17 * __hoisted_cast_1) + (phase * 3.0))))))
            color = (30 + ((p * 9) % 220))
            
            for dy = (-2), 3 - 1 do
                for dx = (-2), 3 - 1 do
                    xx = (x + dx)
                    yy = (y + dy)
                    if ((xx >= 0) and (xx < w) and (yy >= 0) and (yy < h)) then
                        d2 = ((dx * dx) + (dy * dy))
                        if (d2 <= 4) then
                            idx = ((yy * w) + xx)
                            v = (color - (d2 * 20))
                            v = math.max(0, v)
                            if (v > frame[(((idx) < 0) and (#(frame) + (idx) + 1) or ((idx) + 1))]) then
                                frame[(((idx) < 0) and (#(frame) + (idx) + 1) or ((idx) + 1))] = v
                            end
                        end
                    end
                end
            end
        end
        table.insert(frames, __pytra_bytes(frame))
    end
    save_gif(out_path, w, h, frames, color_palette())
    elapsed = (perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frames_n)
    __pytra_print("elapsed_sec:", elapsed)
end


run_11_lissajous_particles()
