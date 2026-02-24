use crate::time::perf_counter;
use crate::pytra::runtime::gif::grayscale_palette;
use crate::pytra::runtime::gif::save_gif;

// 08: Sample that outputs Langton's Ant trajectories as a GIF.

fn capture(grid: Vec<Vec<i64>>, w: i64, h: i64) -> Vec<u8> {
    let mut frame = bytearray(w * h);
    let mut y: i64 = 0;
    while y < h {
        let row_base = y * w;
        let mut x: i64 = 0;
        while x < w {
            frame[row_base + x as usize] = (grid[y as usize][x as usize] ? 255 : 0);
            x += 1;
        }
        y += 1;
    }
    return bytes(frame);
}

fn run_08_langtons_ant() {
    let w = 420;
    let h = 420;
    let out_path = "sample/out/08_langtons_ant.gif";
    
    let start = perf_counter();
    
    let mut grid: Vec<Vec<i64>> = [[0] * w for _ in range(h)];
    let mut x = w / 2;
    let mut y = h / 2;
    let mut d = 0;
    
    let steps_total = 600000;
    let capture_every = 3000;
    let mut frames: Vec<Vec<u8>> = vec![];
    let mut i: i64 = 0;
    while i < steps_total {
        if grid[y as usize][x as usize] == 0 {
            d = (d + 1) % 4;
            grid[y as usize][x as usize] = 1;
        } else {
            d = (d + 3) % 4;
            grid[y as usize][x as usize] = 0;
        }
        if d == 0 {
            y = (y - 1 + h) % h;
        } else {
            if d == 1 {
                x = (x + 1) % w;
            } else {
                if d == 2 {
                    y = (y + 1) % h;
                } else {
                    x = (x - 1 + w) % w;
                }
            }
        }
        if i % capture_every == 0 {
            frames.push(capture(grid, w, h));
        }
        i += 1;
    }
    save_gif(out_path, w, h, frames, grayscale_palette());
    let elapsed = perf_counter() - start;
    println!("{:?}", ("output:", out_path));
    println!("{:?}", ("frames:", frames.len() as i64));
    println!("{:?}", ("elapsed_sec:", elapsed));
}

fn main() {
    run_08_langtons_ant();
}
