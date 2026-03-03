dofile((debug.getinfo(1, "S").source:sub(2):match("^(.*[\\/])") or "") .. "py_runtime.lua")

-- from __future__ import annotations as annotations (not yet mapped)
local perf_counter = __pytra_perf_counter
local grayscale_palette = __pytra_grayscale_palette
local save_gif = __pytra_save_gif

-- 05: Sample that outputs a Mandelbrot zoom as an animated GIF.

function render_frame(width, height, center_x, center_y, scale, max_iter)
    frame = __pytra_bytearray((width * height))
    local __hoisted_cast_1 = __pytra_float(max_iter)
    for y = 0, height - 1 do
        row_base = (y * width)
        cy = (center_y + ((y - (height * 0.5)) * scale))
        for x = 0, width - 1 do
            cx = (center_x + ((x - (width * 0.5)) * scale))
            zx = 0.0
            zy = 0.0
            i = 0
            while (i < max_iter) do
                zx2 = (zx * zx)
                zy2 = (zy * zy)
                if ((zx2 + zy2) > 4.0) then
                    break
                end
                zy = (((2.0 * zx) * zy) + cy)
                zx = ((zx2 - zy2) + cx)
                i = i + 1
            end
            frame[((((row_base + x)) < 0) and (#(frame) + ((row_base + x)) + 1) or (((row_base + x)) + 1))] = __pytra_int(((255.0 * i) / __hoisted_cast_1))
        end
    end
    return __pytra_bytes(frame)
end

function run_05_mandelbrot_zoom()
    width = 320
    height = 240
    frame_count = 48
    max_iter = 110
    center_x = (-0.743643887037151)
    center_y = 0.13182590420533
    base_scale = (3.2 / width)
    zoom_per_frame = 0.93
    out_path = "sample/out/05_mandelbrot_zoom.gif"
    
    start = perf_counter()
    local frames = {  }
    scale = base_scale
    for _ = 0, frame_count - 1 do
        table.insert(frames, render_frame(width, height, center_x, center_y, scale, max_iter))
        scale = scale * zoom_per_frame
    end
    save_gif(out_path, width, height, frames, grayscale_palette())
    elapsed = (perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", frame_count)
    __pytra_print("elapsed_sec:", elapsed)
end


run_05_mandelbrot_zoom()
