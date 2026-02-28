-- from __future__ import annotations as annotations (not yet mapped)
-- from time import perf_counter as perf_counter (not yet mapped)
local png = { write_rgb_png = function(...) end, write_gif = function(...) end }

-- 04: Sample that renders an orbit-trap Julia set and writes a PNG image.

function render_orbit_trap_julia(width, height, max_iter, cx, cy)
    local pixels = bytearray()
    local __hoisted_cast_1 = float((height - 1))
    local __hoisted_cast_2 = float((width - 1))
    local __hoisted_cast_3 = float(max_iter)
    
    for y = 0, (height) - 1, 1 do
        local zy0 = ((-1.3) + (2.6 * (y / __hoisted_cast_1)))
        for x = 0, (width) - 1, 1 do
            local zx = ((-1.9) + (3.8 * (x / __hoisted_cast_2)))
            local zy = zy0
            
            local trap = 1000000000.0
            local i = 0
            while (i < max_iter) do
                local ax = zx
                if (ax < 0.0) then
                    ax = (-ax)
                end
                local ay = zy
                if (ay < 0.0) then
                    ay = (-ay)
                end
                local dxy = (zx - zy)
                if (dxy < 0.0) then
                    dxy = (-dxy)
                end
                if (ax < trap) then
                    trap = ax
                end
                if (ay < trap) then
                    trap = ay
                end
                if (dxy < trap) then
                    trap = dxy
                end
                local zx2 = (zx * zx)
                local zy2 = (zy * zy)
                if ((zx2 + zy2) > 4.0) then
                    _break
                end
                zy = (((2.0 * zx) * zy) + cy)
                zx = ((zx2 - zy2) + cx)
                i = i + 1
            end
            local r = 0
            local g = 0
            local b = 0
            if (i >= max_iter) then
                r = 0
                g = 0
                b = 0
            else
                local trap_scaled = (trap * 3.2)
                if (trap_scaled > 1.0) then
                    trap_scaled = 1.0
                end
                if (trap_scaled < 0.0) then
                    trap_scaled = 0.0
                end
                local t = (i / __hoisted_cast_3)
                local tone = int((255.0 * (1.0 - trap_scaled)))
                r = int((tone * (0.35 + (0.65 * t))))
                g = int((tone * (0.15 + (0.85 * (1.0 - t)))))
                b = int((255.0 * (0.25 + (0.75 * t))))
                if (r > 255) then
                    r = 255
                end
                if (g > 255) then
                    g = 255
                end
                if (b > 255) then
                    b = 255
                end
            end
            pixels:append(r)
            pixels:append(g)
            pixels:append(b)
        end
    end
    return pixels
end

function run_04_orbit_trap_julia()
    local width = 1920
    local height = 1080
    local max_iter = 1400
    local out_path = "sample/out/04_orbit_trap_julia.png"
    
    local start = perf_counter()
    local pixels = render_orbit_trap_julia(width, height, max_iter, (-0.7269), 0.1889)
    png:write_rgb_png(out_path, width, height, pixels)
    local elapsed = (perf_counter() - start)
    
    print("output:", out_path)
    print("size:", width, "x", height)
    print("max_iter:", max_iter)
    print("elapsed_sec:", elapsed)
end


run_04_orbit_trap_julia()
