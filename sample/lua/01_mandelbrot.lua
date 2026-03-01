-- from time import perf_counter as perf_counter (not yet mapped)
local png = { write_rgb_png = function(...) end, write_gif = function(...) end }

-- 01: Sample that outputs the Mandelbrot set as a PNG image.
-- Syntax is kept straightforward with future transpilation in mind.

function escape_count(cx, cy, max_iter)
    local x = 0.0
    local y = 0.0
    for i = 0, (max_iter) - 1, 1 do
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
    local r = int((255.0 * (t * t)))
    local g = int((255.0 * t))
    local b = int((255.0 * (1.0 - t)))
    return { r, g, b }
end

function render_mandelbrot(width, height, max_iter, x_min, x_max, y_min, y_max)
    local pixels = bytearray()
    local __hoisted_cast_1 = float((height - 1))
    local __hoisted_cast_2 = float((width - 1))
    local __hoisted_cast_3 = float(max_iter)
    
    for y = 0, (height) - 1, 1 do
        local py = (y_min + ((y_max - y_min) * (y / __hoisted_cast_1)))
        
        for x = 0, (width) - 1, 1 do
            local px = (x_min + ((x_max - x_min) * (x / __hoisted_cast_2)))
            local it = escape_count(px, py, max_iter)
            local r = nil
            local g = nil
            local b = nil
            if (it >= max_iter) then
                r = 0
                g = 0
                b = 0
            else
                local t = (it / __hoisted_cast_3)
                r = int((255.0 * (t * t)))
                g = int((255.0 * t))
                b = int((255.0 * (1.0 - t)))
            end
            pixels:append(r)
            pixels:append(g)
            pixels:append(b)
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
    png:write_rgb_png(out_path, width, height, pixels)
    
    local elapsed = (perf_counter() - start)
    print("output:", out_path)
    print("size:", width, "x", height)
    print("max_iter:", max_iter)
    print("elapsed_sec:", elapsed)
end


run_mandelbrot()
