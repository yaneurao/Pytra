dofile((debug.getinfo(1, "S").source:sub(2):match("^(.*[\\/])") or "") .. "py_runtime.lua")

local math = __pytra_math_module()
local png = __pytra_png_module()
local perf_counter = __pytra_perf_counter

-- 02: Sample that runs a mini sphere-only ray tracer and outputs a PNG image.
-- Dependencies are kept minimal (time only) for transpilation compatibility.

function clamp01(v)
    if (v < 0.0) then
        return 0.0
    end
    if (v > 1.0) then
        return 1.0
    end
    return v
end

function hit_sphere(ox, oy, oz, dx, dy, dz, cx, cy, cz, r)
    local lx = (ox - cx)
    local ly = (oy - cy)
    local lz = (oz - cz)
    
    local a = (((dx * dx) + (dy * dy)) + (dz * dz))
    local b = (2.0 * (((lx * dx) + (ly * dy)) + (lz * dz)))
    local c = ((((lx * lx) + (ly * ly)) + (lz * lz)) - (r * r))
    
    local d = ((b * b) - ((4.0 * a) * c))
    if (d < 0.0) then
        return (-1.0)
    end
    local sd = math.sqrt(d)
    local t0 = (((-b) - sd) / (2.0 * a))
    local t1 = (((-b) + sd) / (2.0 * a))
    
    if (t0 > 0.001) then
        return t0
    end
    if (t1 > 0.001) then
        return t1
    end
    return (-1.0)
end

function render(width, height, aa)
    local pixels = __pytra_bytearray()
    
    -- Camera origin
    local ox = 0.0
    local oy = 0.0
    local oz = (-3.0)
    
    -- Light direction (normalized)
    local lx = (-0.4)
    local ly = 0.8
    local lz = (-0.45)
    local __hoisted_cast_1 = __pytra_float(aa)
    local __hoisted_cast_2 = __pytra_float((height - 1))
    local __hoisted_cast_3 = __pytra_float((width - 1))
    local __hoisted_cast_4 = __pytra_float(height)
    
    for y = 0, height - 1 do
        for x = 0, width - 1 do
            local ar = 0
            local ag = 0
            local ab = 0
            
            for ay = 0, aa - 1 do
                for ax = 0, aa - 1 do
                    fy = ((y + ((ay + 0.5) / __hoisted_cast_1)) / __hoisted_cast_2)
                    fx = ((x + ((ax + 0.5) / __hoisted_cast_1)) / __hoisted_cast_3)
                    local sy = (1.0 - (2.0 * fy))
                    local sx = (((2.0 * fx) - 1.0) * (width / __hoisted_cast_4))
                    
                    local dx = sx
                    local dy = sy
                    local dz = 1.0
                    local inv_len = (1.0 / math.sqrt((((dx * dx) + (dy * dy)) + (dz * dz))))
                    dx = dx * inv_len
                    dy = dy * inv_len
                    dz = dz * inv_len
                    
                    local t_min = 1e+30
                    local hit_id = (-1)
                    
                    local t = hit_sphere(ox, oy, oz, dx, dy, dz, (-0.8), (-0.2), 2.2, 0.8)
                    if ((t > 0.0) and (t < t_min)) then
                        t_min = t
                        hit_id = 0
                    end
                    t = hit_sphere(ox, oy, oz, dx, dy, dz, 0.9, 0.1, 2.9, 0.95)
                    if ((t > 0.0) and (t < t_min)) then
                        t_min = t
                        hit_id = 1
                    end
                    t = hit_sphere(ox, oy, oz, dx, dy, dz, 0.0, (-1001.0), 3.0, 1000.0)
                    if ((t > 0.0) and (t < t_min)) then
                        t_min = t
                        hit_id = 2
                    end
                    local r = 0
                    local g = 0
                    local b = 0
                    
                    if (hit_id >= 0) then
                        local px = (ox + (dx * t_min))
                        local py = (oy + (dy * t_min))
                        local pz = (oz + (dz * t_min))
                        
                        local nx = 0.0
                        local ny = 0.0
                        local nz = 0.0
                        
                        if (hit_id == 0) then
                            nx = ((px + 0.8) / 0.8)
                            ny = ((py + 0.2) / 0.8)
                            nz = ((pz - 2.2) / 0.8)
                        else
                            if (hit_id == 1) then
                                nx = ((px - 0.9) / 0.95)
                                ny = ((py - 0.1) / 0.95)
                                nz = ((pz - 2.9) / 0.95)
                            else
                                nx = 0.0
                                ny = 1.0
                                nz = 0.0
                            end
                        end
                        local diff = (((nx * (-lx)) + (ny * (-ly))) + (nz * (-lz)))
                        diff = clamp01(diff)
                        
                        local base_r = 0.0
                        local base_g = 0.0
                        local base_b = 0.0
                        
                        if (hit_id == 0) then
                            base_r = 0.95
                            base_g = 0.35
                            base_b = 0.25
                        else
                            if (hit_id == 1) then
                                base_r = 0.25
                                base_g = 0.55
                                base_b = 0.95
                            else
                                local checker = (__pytra_int(((px + 50.0) * 0.8)) + __pytra_int(((pz + 50.0) * 0.8)))
                                if ((checker % 2) == 0) then
                                    base_r = 0.85
                                    base_g = 0.85
                                    base_b = 0.85
                                else
                                    base_r = 0.2
                                    base_g = 0.2
                                    base_b = 0.2
                                end
                            end
                        end
                        local shade = (0.12 + (0.88 * diff))
                        r = __pytra_int((255.0 * clamp01((base_r * shade))))
                        g = __pytra_int((255.0 * clamp01((base_g * shade))))
                        b = __pytra_int((255.0 * clamp01((base_b * shade))))
                    else
                        local tsky = (0.5 * (dy + 1.0))
                        r = __pytra_int((255.0 * (0.65 + (0.2 * tsky))))
                        g = __pytra_int((255.0 * (0.75 + (0.18 * tsky))))
                        b = __pytra_int((255.0 * (0.9 + (0.08 * tsky))))
                    end
                    ar = ar + r
                    ag = ag + g
                    ab = ab + b
                end
            end
            samples = (aa * aa)
            table.insert(pixels, (ar // samples))
            table.insert(pixels, (ag // samples))
            table.insert(pixels, (ab // samples))
        end
    end
    return pixels
end

function run_raytrace()
    local width = 1600
    local height = 900
    local aa = 2
    local out_path = "sample/out/02_raytrace_spheres.png"
    
    local start = perf_counter()
    local pixels = render(width, height, aa)
    png.write_rgb_png(out_path, width, height, pixels)
    local elapsed = (perf_counter() - start)
    
    __pytra_print("output:", out_path)
    __pytra_print("size:", width, "x", height)
    __pytra_print("elapsed_sec:", elapsed)
end


run_raytrace()
