dofile((debug.getinfo(1, "S").source:sub(2):match("^(.*[\\/])") or "") .. "py_runtime.lua")

local perf_counter = __pytra_perf_counter
local png = __pytra_png_module()

-- 03: Sample that outputs a Julia set as a PNG image.
-- Implemented with simple loop-centric logic for transpilation compatibility.

function render_julia(width, height, max_iter, cx, cy)
    local pixels = __pytra_bytearray()
    local __hoisted_cast_1 = __pytra_float((height - 1))
    local __hoisted_cast_2 = __pytra_float((width - 1))
    local __hoisted_cast_3 = __pytra_float(max_iter)
    
    for y = 0, height - 1 do
        local zy0 = ((-1.2) + (2.4 * (y / __hoisted_cast_1)))
        
        for x = 0, width - 1 do
            local zx = ((-1.8) + (3.6 * (x / __hoisted_cast_2)))
            local zy = zy0
            
            local i = 0
            while (i < max_iter) do
                local zx2 = (zx * zx)
                local zy2 = (zy * zy)
                if ((zx2 + zy2) > 4.0) then
                    break
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
                local t = (i / __hoisted_cast_3)
                r = __pytra_int((255.0 * (0.2 + (0.8 * t))))
                g = __pytra_int((255.0 * (0.1 + (0.9 * (t * t)))))
                b = __pytra_int((255.0 * (1.0 - t)))
            end
            table.move({r, g, b}, 1, 3, #(pixels) + 1, pixels)
        end
    end
    return pixels
end

function run_julia()
    local width = 3840
    local height = 2160
    local max_iter = 20000
    local out_path = "sample/out/03_julia_set.png"
    
    local start = perf_counter()
    local pixels = render_julia(width, height, max_iter, (-0.8), 0.156)
    png.write_rgb_png(out_path, width, height, pixels)
    local elapsed = (perf_counter() - start)
    
    __pytra_print("output:", out_path)
    __pytra_print("size:", width, "x", height)
    __pytra_print("max_iter:", max_iter)
    __pytra_print("elapsed_sec:", elapsed)
end


run_julia()
