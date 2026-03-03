dofile((debug.getinfo(1, "S").source:sub(2):match("^(.*[\\/])") or "") .. "py_runtime.lua")

-- from __future__ import annotations as annotations (not yet mapped)
local perf_counter = __pytra_perf_counter
local grayscale_palette = __pytra_grayscale_palette
local save_gif = __pytra_save_gif

-- 12: Sample that outputs intermediate states of bubble sort as a GIF.

function render(values, w, h)
    frame = __pytra_bytearray((w * h))
    n = #(values)
    bar_w = (w / n)
    local __hoisted_cast_1 = __pytra_float(n)
    local __hoisted_cast_2 = __pytra_float(h)
    for i = 0, n - 1 do
        x0 = __pytra_int((i * bar_w))
        x1 = __pytra_int(((i + 1) * bar_w))
        if (x1 <= x0) then
            x1 = (x0 + 1)
        end
        bh = __pytra_int(((values[(((i) < 0) and (#(values) + (i) + 1) or ((i) + 1))] / __hoisted_cast_1) * __hoisted_cast_2))
        y = (h - bh)
        for y = y, h - 1 do
            for x = x0, x1 - 1 do
                frame[(((((y * w) + x)) < 0) and (#(frame) + (((y * w) + x)) + 1) or ((((y * w) + x)) + 1))] = 255
            end
        end
    end
    return __pytra_bytes(frame)
end

function run_12_sort_visualizer()
    w = 320
    h = 180
    n = 124
    out_path = "sample/out/12_sort_visualizer.gif"
    
    start = perf_counter()
    local values = {  }
    for i = 0, n - 1 do
        table.insert(values, (((i * 37) + 19) % n))
    end
    local frames = { render(values, w, h) }
    frame_stride = 16
    
    op = 0
    for i = 0, n - 1 do
        swapped = false
        for j = 0, (((n - i) - 1)) - 1 do
            if (values[(((j) < 0) and (#(values) + (j) + 1) or ((j) + 1))] > values[((((j + 1)) < 0) and (#(values) + ((j + 1)) + 1) or (((j + 1)) + 1))]) then
                local __pytra_tuple_7 = { values[((((j + 1)) < 0) and (#(values) + ((j + 1)) + 1) or (((j + 1)) + 1))], values[(((j) < 0) and (#(values) + (j) + 1) or ((j) + 1))] }
                values[(((j) < 0) and (#(values) + (j) + 1) or ((j) + 1))] = __pytra_tuple_7[1]
                values[((((j + 1)) < 0) and (#(values) + ((j + 1)) + 1) or (((j + 1)) + 1))] = __pytra_tuple_7[2]
                swapped = true
            end
            if ((op % frame_stride) == 0) then
                table.insert(frames, render(values, w, h))
            end
            op = op + 1
        end
        if (not swapped) then
            break
        end
    end
    save_gif(out_path, w, h, frames, grayscale_palette())
    elapsed = (perf_counter() - start)
    __pytra_print("output:", out_path)
    __pytra_print("frames:", #(frames))
    __pytra_print("elapsed_sec:", elapsed)
end


run_12_sort_visualizer()
