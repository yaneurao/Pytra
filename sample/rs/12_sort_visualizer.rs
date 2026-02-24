use crate::time::perf_counter;
use crate::pytra::utils::gif::grayscale_palette;
use crate::pytra::utils::gif::save_gif;

// 12: Sample that outputs intermediate states of bubble sort as a GIF.

fn render(values: Vec<i64>, w: i64, h: i64) -> Vec<u8> {
    let mut frame = bytearray((w * h));
    let n = values.len() as i64;
    let bar_w = (w / n);
    let mut i: i64 = 0;
    while i < n {
        let x0 = (i * bar_w) as i64;
        let mut x1 = (((i + 1)) * bar_w) as i64;
        if x1 <= x0 {
            x1 = (x0 + 1);
        }
        let bh = (((values[i as usize] / n)) * h) as i64;
        let mut y = (h - bh);
        let mut y: i64 = y;
        while y < h {
            let mut x: i64 = x0;
            while x < x1 {
                frame[((y * w) + x) as usize] = 255;
                x += 1;
            }
            y += 1;
        }
        i += 1;
    }
    return bytes(frame);
}

fn run_12_sort_visualizer() {
    let w = 320;
    let h = 180;
    let n = 124;
    let out_path = "sample/out/12_sort_visualizer.gif";
    
    let start = perf_counter();
    let mut values: Vec<i64> = vec![];
    let mut i: i64 = 0;
    while i < n {
        values.push(((((i * 37) + 19)) % n));
        i += 1;
    }
    let mut frames: Vec<Vec<u8>> = vec![];
    let frame_stride = 16;
    
    let mut op = 0;
    let mut i: i64 = 0;
    while i < n {
        let mut swapped = false;
        let mut j: i64 = 0;
        while j < ((n - i) - 1) {
            if values[j as usize] > values[(j + 1) as usize] {
                let __tmp_1 = (values[(j + 1) as usize], values[j as usize]);
                values[j as usize] = __tmp_1.0;
                values[(j + 1) as usize] = __tmp_1.1;
                swapped = true;
            }
            if (op % frame_stride) == 0 {
                frames.push(render(values, w, h));
            }
            op += 1;
            j += 1;
        }
        if !swapped {
            py_break;
        }
        i += 1;
    }
    save_gif(out_path, w, h, frames, grayscale_palette());
    let elapsed = (perf_counter() - start);
    println!("{:?}", ("output:", out_path));
    println!("{:?}", ("frames:", frames.len() as i64));
    println!("{:?}", ("elapsed_sec:", elapsed));
}

fn main() {
    run_12_sort_visualizer();
}
