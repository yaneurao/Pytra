-- from __future__ import annotations as annotations (not yet mapped)
local math = math
-- from time import perf_counter as perf_counter (not yet mapped)
-- from pytra.runtime.gif import save_gif as save_gif (not yet mapped)

-- 06: Sample that sweeps Julia-set parameters and outputs a GIF.

function julia_palette()
    -- Keep index 0 black for points inside the set; build a high-saturation gradient for the rest.
    palette = bytearray((256 * 3))
    palette[(0) + 1] = 0
    palette[(1) + 1] = 0
    palette[(2) + 1] = 0
    for i = 1, (256) - 1, 1 do
        t = ((i - 1) / 254.0)
        r = int((255.0 * ((((9.0 * (1.0 - t)) * t) * t) * t)))
        g = int((255.0 * ((((15.0 * (1.0 - t)) * (1.0 - t)) * t) * t)))
        b = int((255.0 * ((((8.5 * (1.0 - t)) * (1.0 - t)) * (1.0 - t)) * t)))
        palette[(((i * 3) + 0)) + 1] = r
        palette[(((i * 3) + 1)) + 1] = g
        palette[(((i * 3) + 2)) + 1] = b
    end
    return bytes(palette)
end

function render_frame(width, height, cr, ci, max_iter, phase)
    frame = bytearray((width * height))
    local __hoisted_cast_1 = float((height - 1))
    local __hoisted_cast_2 = float((width - 1))
    for y = 0, (height) - 1, 1 do
        row_base = (y * width)
        zy0 = ((-1.2) + (2.4 * (y / __hoisted_cast_1)))
        for x = 0, (width) - 1, 1 do
            zx = ((-1.8) + (3.6 * (x / __hoisted_cast_2)))
            zy = zy0
            i = 0
            while (i < max_iter) do
                zx2 = (zx * zx)
                zy2 = (zy * zy)
                if ((zx2 + zy2) > 4.0) then
                    _break
                end
                zy = (((2.0 * zx) * zy) + ci)
                zx = ((zx2 - zy2) + cr)
                i = i + 1
            end
            if (i >= max_iter) then
                frame[((row_base + x)) + 1] = 0
            else
                -- Add a small frame phase so colors flow smoothly.
                color_index = (1 + ((((i * 224) // max_iter) + phase) % 255))
                frame[((row_base + x)) + 1] = color_index
            end
        end
    end
    return bytes(frame)
end

function run_06_julia_parameter_sweep()
    width = 320
    height = 240
    frames_n = 72
    max_iter = 180
    out_path = "sample/out/06_julia_parameter_sweep.gif"
    
    start = perf_counter()
    local frames = {  }
    -- Orbit an ellipse around a known visually good region to reduce flat blown highlights.
    center_cr = (-0.745)
    center_ci = 0.186
    radius_cr = 0.12
    radius_ci = 0.1
    -- Add start and phase offsets so GitHub thumbnails do not appear too dark.
    -- Tune it to start in a red-leaning color range.
    start_offset = 20
    phase_offset = 180
    local __hoisted_cast_3 = float(frames_n)
    for i = 0, (frames_n) - 1, 1 do
        t = (((i + start_offset) % frames_n) / __hoisted_cast_3)
        angle = ((2.0 * math.pi) * t)
        cr = (center_cr + (radius_cr * math.cos(angle)))
        ci = (center_ci + (radius_ci * math.sin(angle)))
        phase = ((phase_offset + (i * 5)) % 255)
        frames:append(render_frame(width, height, cr, ci, max_iter, phase))
    end
    save_gif(out_path, width, height, frames, julia_palette())
    elapsed = (perf_counter() - start)
    print("output:", out_path)
    print("frames:", frames_n)
    print("elapsed_sec:", elapsed)
end


run_06_julia_parameter_sweep()
