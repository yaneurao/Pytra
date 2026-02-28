import { perf_counter } from "./pytra/std/time.js";
import { grayscale_palette } from "./pytra/utils/gif.js";
import { save_gif } from "./pytra/utils/gif.js";

// 12: Sample that outputs intermediate states of bubble sort as a GIF.

function render(values, w, h) {
    let frame = (typeof (w * h) === "number" ? new Array(Math.max(0, Math.trunc(Number((w * h))))).fill(0) : (Array.isArray((w * h)) ? (w * h).slice() : Array.from((w * h))));
    let n = (values).length;
    let bar_w = w / n;
    let __hoisted_cast_1 = Number(n);
    let __hoisted_cast_2 = Number(h);
    const __start_1 = 0;
    for (let i = __start_1; i < n; i += 1) {
        let x0 = Math.trunc(Number(i * bar_w));
        let x1 = Math.trunc(Number((i + 1) * bar_w));
        if (x1 <= x0) {
            x1 = x0 + 1;
        }
        let bh = Math.trunc(Number((values[(((i) < 0) ? ((values).length + (i)) : (i))] / __hoisted_cast_1) * __hoisted_cast_2));
        let y = h - bh;
        const __start_2 = y;
        for (let y = __start_2; y < h; y += 1) {
            const __start_3 = x0;
            for (let x = __start_3; x < x1; x += 1) {
                frame[(((y * w + x) < 0) ? ((frame).length + (y * w + x)) : (y * w + x))] = 255;
            }
        }
    }
    return (Array.isArray((frame)) ? (frame).slice() : Array.from((frame)));
}

function run_12_sort_visualizer() {
    let w = 320;
    let h = 180;
    let n = 124;
    let out_path = "sample/out/12_sort_visualizer.gif";
    
    let start = perf_counter();
    let values = [];
    const __start_4 = 0;
    for (let i = __start_4; i < n; i += 1) {
        values.push((i * 37 + 19) % n);
    }
    let frames = [render(values, w, h)];
    let frame_stride = 16;
    
    let op = 0;
    const __start_5 = 0;
    for (let i = __start_5; i < n; i += 1) {
        let swapped = false;
        const __start_6 = 0;
        for (let j = __start_6; j < n - i - 1; j += 1) {
            if (values[(((j) < 0) ? ((values).length + (j)) : (j))] > values[(((j + 1) < 0) ? ((values).length + (j + 1)) : (j + 1))]) {
                const __tmp_7 = [values[(((j + 1) < 0) ? ((values).length + (j + 1)) : (j + 1))], values[(((j) < 0) ? ((values).length + (j)) : (j))]];
                values[(((j) < 0) ? ((values).length + (j)) : (j))] = __tmp_7[0];
                values[(((j + 1) < 0) ? ((values).length + (j + 1)) : (j + 1))] = __tmp_7[1];
                swapped = true;
            }
            if (op % frame_stride === 0) {
                frames.push(render(values, w, h));
            }
            op += 1;
        }
        if (!swapped) {
            break;
        }
    }
    save_gif(out_path, w, h, frames, grayscale_palette());
    let elapsed = perf_counter() - start;
    console.log("output:", out_path);
    console.log("frames:", (frames).length);
    console.log("elapsed_sec:", elapsed);
}

run_12_sort_visualizer();
