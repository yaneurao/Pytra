use crate::time::perf_counter;
use crate::pytra::runtime::gif::grayscale_palette;
use crate::pytra::runtime::gif::save_gif;

// 13: Sample that outputs DFS maze-generation progress as a GIF.

fn capture(grid: Vec<Vec<i64>>, w: i64, h: i64, scale: i64) -> Vec<u8> {
    let width = w * scale;
    let height = h * scale;
    let mut frame = bytearray(width * height);
    let mut y: i64 = 0;
    while y < h {
        let mut x: i64 = 0;
        while x < w {
            let v = ((grid[y as usize][x as usize] == 0) ? 255 : 40);
            let mut yy: i64 = 0;
            while yy < scale {
                let base = (y * scale + yy) * width + x * scale;
                let mut xx: i64 = 0;
                while xx < scale {
                    frame[base + xx as usize] = v;
                    xx += 1;
                }
                yy += 1;
            }
            x += 1;
        }
        y += 1;
    }
    return bytes(frame);
}

fn run_13_maze_generation_steps() {
    // Increase maze size and render resolution to ensure sufficient runtime.
    let cell_w = 89;
    let cell_h = 67;
    let scale = 5;
    let capture_every = 20;
    let out_path = "sample/out/13_maze_generation_steps.gif";
    
    let start = perf_counter();
    let mut grid: Vec<Vec<i64>> = [[1] * cell_w for _ in range(cell_h)];
    let mut stack: Vec<(i64, i64)> = vec![];
    grid[1 as usize][1 as usize] = 0;
    
    let dirs: Vec<(i64, i64)> = vec![];
    let mut frames: Vec<Vec<u8>> = vec![];
    let mut step = 0;
    
    while stack.len() != 0 {
        let __tmp_1 = stack[(-1) as usize];
        x = __tmp_1.0;
        y = __tmp_1.1;
        let mut candidates: Vec<(i64, i64, i64, i64)> = vec![];
        let mut k: i64 = 0;
        while k < 4 {
            let __tmp_2 = dirs[k as usize];
            dx = __tmp_2.0;
            dy = __tmp_2.1;
            let mut nx = x + dx;
            let mut ny = y + dy;
            if (nx >= 1) && (nx < cell_w - 1) && (ny >= 1) && (ny < cell_h - 1) && (grid[ny as usize][nx as usize] == 1) {
                if dx == 2 {
                    candidates.push((nx, ny, x + 1, y));
                } else {
                    if dx == (-2) {
                        candidates.push((nx, ny, x - 1, y));
                    } else {
                        if dy == 2 {
                            candidates.push((nx, ny, x, y + 1));
                        } else {
                            candidates.push((nx, ny, x, y - 1));
                        }
                    }
                }
            }
            k += 1;
        }
        if candidates.len() as i64 == 0 {
            stack.pop().unwrap_or_default();
        } else {
            let sel = candidates[(x * 17 + y * 29 + stack.len() as i64 * 13) % candidates.len() as i64 as usize];
            (nx, ny, wx, wy) = sel;
            grid[wy as usize][wx as usize] = 0;
            grid[ny as usize][nx as usize] = 0;
            stack.push((nx, ny));
        }
        if step % capture_every == 0 {
            frames.push(capture(grid, cell_w, cell_h, scale));
        }
        step += 1;
    }
    frames.push(capture(grid, cell_w, cell_h, scale));
    save_gif(out_path, cell_w * scale, cell_h * scale, frames, grayscale_palette());
    let elapsed = perf_counter() - start;
    println!("{:?}", ("output:", out_path));
    println!("{:?}", ("frames:", frames.len() as i64));
    println!("{:?}", ("elapsed_sec:", elapsed));
}

fn main() {
    run_13_maze_generation_steps();
}
