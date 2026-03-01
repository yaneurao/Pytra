-- from __future__ import annotations as annotations (not yet mapped)
-- from time import perf_counter as perf_counter (not yet mapped)
-- from pytra.utils.gif import grayscale_palette as grayscale_palette (not yet mapped)
-- from pytra.utils.gif import save_gif as save_gif (not yet mapped)

-- 12: Sample that outputs intermediate states of bubble sort as a GIF.

function render(values, w, h)
    frame = bytearray((w * h))
    n = len(values)
    bar_w = (w / n)
    local __hoisted_cast_1 = float(n)
    local __hoisted_cast_2 = float(h)
    for i = 0, (n) - 1, 1 do
        x0 = int((i * bar_w))
        x1 = int(((i + 1) * bar_w))
        if (x1 <= x0) then
            x1 = (x0 + 1)
        end
        bh = int(((values[(i) + 1] / __hoisted_cast_1) * __hoisted_cast_2))
        y = (h - bh)
        for y = y, (h) - 1, 1 do
            for x = x0, (x1) - 1, 1 do
                frame[(((y * w) + x)) + 1] = 255
            end
        end
    end
    return bytes(frame)
end

function run_12_sort_visualizer()
    w = 320
    h = 180
    n = 124
    out_path = "sample/out/12_sort_visualizer.gif"
    
    start = perf_counter()
    local values = {  }
    for i = 0, (n) - 1, 1 do
        values:append((((i * 37) + 19) % n))
    end
    local frames = { render(values, w, h) }
    frame_stride = 16
    
    op = 0
    for i = 0, (n) - 1, 1 do
        swapped = false
        for j = 0, (((n - i) - 1)) - 1, 1 do
            if (values[(j) + 1] > values[((j + 1)) + 1]) then
                local __pytra_tuple_1 = { values[((j + 1)) + 1], values[(j) + 1] }
                values[(j) + 1] = __pytra_tuple_1[1]
                values[((j + 1)) + 1] = __pytra_tuple_1[2]
                swapped = true
            end
            if ((op % frame_stride) == 0) then
                frames:append(render(values, w, h))
            end
            op = op + 1
        end
        if (not swapped) then
            _break
        end
    end
    save_gif(out_path, w, h, frames, grayscale_palette())
    elapsed = (perf_counter() - start)
    print("output:", out_path)
    print("frames:", len(frames))
    print("elapsed_sec:", elapsed)
end


run_12_sort_visualizer()
