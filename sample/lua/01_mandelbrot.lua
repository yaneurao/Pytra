dofile((debug.getinfo(1, "S").source:sub(2):match("^(.*[\\/])") or "") .. "py_runtime.lua")

local perf_counter = __pytra_perf_counter
local png = __pytra_png_module()

-- 01: Sample that outputs the Mandelbrot set as a PNG image.
-- Syntax is kept straightforward with future transpilation in mind.

function escape_count(cx, cy, max_iter)
    local x = 0.0
    local y = 0.0
    for i = 0, max_iter - 1 do
        local x2 = (x * x)
        local y2 = (y * y)
        if ((x2 + y2) > 4.0) then
            return i
        end
        y = (((2.0 * x) * y) + cy)
        x = ((x2 - y2) + cx)
    end
    return max_iter
end

function color_map(iter_count, max_iter)
    if (iter_count >= max_iter) then
        return { 0, 0, 0 }
    end
    local t = (iter_count / max_iter)
    local r = __pytra_int((255.0 * (t * t)))
    local g = __pytra_int((255.0 * t))
    local b = __pytra_int((255.0 * (1.0 - t)))
    return { r, g, b }
end

function render_mandelbrot(width, height, max_iter, x_min, x_max, y_min, y_max)
    local pixels = __pytra_bytearray()
    local __hoisted_cast_1 = __pytra_float((height - 1))
    local __hoisted_cast_2 = __pytra_float((width - 1))
    local __hoisted_cast_3 = __pytra_float(max_iter)
    
    for y = 0, height - 1 do
        local py = (y_min + ((y_max - y_min) * (y / __hoisted_cast_1)))
        
        for x = 0, width - 1 do
            local px = (x_min + ((x_max - x_min) * (x / __hoisted_cast_2)))
            local it = escape_count(px, py, max_iter)
            local r
            local g
            local b
            if (it >= max_iter) then
                r = 0
                g = 0
                b = 0
            else
                local t = (it / __hoisted_cast_3)
                r = __pytra_int((255.0 * (t * t)))
                g = __pytra_int((255.0 * t))
                b = __pytra_int((255.0 * (1.0 - t)))
            end
            table.insert(pixels, r)
            table.insert(pixels, g)
            table.insert(pixels, b)
        end
    end
    return pixels
end

function run_mandelbrot()
    local width = 1600
    local height = 1200
    local max_iter = 1000
    local out_path = "sample/out/01_mandelbrot.png"
    
    local start = perf_counter()
    
    local pixels = render_mandelbrot(width, height, max_iter, (-2.2), 1.0, (-1.2), 1.2)
    png.write_rgb_png(out_path, width, height, pixels)
    
    local elapsed = (perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("size:", width, "x", height)
    __pytra_print("max_iter:", max_iter)
    __pytra_print("elapsed_sec:", elapsed)
end


run_mandelbrot()
