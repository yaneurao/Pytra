import { perf_counter } from "./time.js";
import { grayscale_palette } from "./pytra/utils/gif.js";
import { save_gif } from "./pytra/utils/gif.js";

// 12: Sample that outputs intermediate states of bubble sort as a GIF.

function render(values, w, h) {
    let frame = bytearray(w * h);
    let n = (values).length;
    let bar_w = w / n;
    for (let i = 0; i < n; i += 1) {
        let x0 = Math.trunc(Number(i * bar_w));
        let x1 = Math.trunc(Number((i + 1) * bar_w));
        if (x1 <= x0) {
            x1 = x0 + 1;
        }
        let bh = Math.trunc(Number((values[i] / n) * h));
        let y = h - bh;
        for (let y = y; y < h; y += 1) {
            for (let x = x0; x < x1; x += 1) {
                frame[y * w + x] = 255;
            }
        }
    }
    return bytes(frame);
}

function run_12_sort_visualizer() {
    let w = 320;
    let h = 180;
    let n = 124;
    let out_path = "sample/out/12_sort_visualizer.gif";
    
    let start = perf_counter();
    let values = [];
    for (let i = 0; i < n; i += 1) {
        values.push((i * 37 + 19) % n);
    }
    let frames = [];
    let frame_stride = 16;
    
    let op = 0;
    for (let i = 0; i < n; i += 1) {
        let swapped = false;
        for (let j = 0; j < n - i - 1; j += 1) {
            if (values[j] > values[j + 1]) {
                const __tmp_1 = [values[j + 1], values[j]];
                values[j] = __tmp_1[0];
                values[j + 1] = __tmp_1[1];
                swapped = true;
            }
            if (op % frame_stride === 0) {
                frames.push(render(values, w, h));
            }
            op += 1;
        }
        if (!swapped) {
            py_break;
        }
    }
    save_gif(out_path, w, h, frames, grayscale_palette());
    let elapsed = perf_counter() - start;
    console.log("output:", out_path);
    console.log("frames:", (frames).length);
    console.log("elapsed_sec:", elapsed);
}

// __main__ guard
run_12_sort_visualizer();
