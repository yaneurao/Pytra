use crate::time::perf_counter;
use crate::pytra::utils::gif::grayscale_palette;
use crate::pytra::utils::gif::save_gif;

// 07: Sample that outputs Game of Life evolution as a GIF.

fn next_state(grid: Vec<Vec<i64>>, w: i64, h: i64) -> Vec<Vec<i64>> {
    let mut nxt: Vec<Vec<i64>> = vec![];
    let mut y: i64 = 0;
    while y < h {
        let mut row: Vec<i64> = vec![];
        let mut x: i64 = 0;
        while x < w {
            let mut cnt = 0;
            let mut dy: i64 = -1;
            while dy < 2 {
                let mut dx: i64 = -1;
                while dx < 2 {
                    if (dx != 0) || (dy != 0) {
                        let nx = (x + dx + w) % w;
                        let ny = (y + dy + h) % h;
                        cnt += grid[ny as usize][nx as usize];
                    }
                    dx += 1;
                }
                dy += 1;
            }
            let alive = grid[y as usize][x as usize];
            if (alive == 1) && ((cnt == 2) || (cnt == 3)) {
                row.push(1);
            } else {
                if (alive == 0) && (cnt == 3) {
                    row.push(1);
                } else {
                    row.push(0);
                }
            }
            x += 1;
        }
        nxt.push(row);
        y += 1;
    }
    return nxt;
}

fn render(grid: Vec<Vec<i64>>, w: i64, h: i64, cell: i64) -> Vec<u8> {
    let width = w * cell;
    let height = h * cell;
    let mut frame = bytearray(width * height);
    let mut y: i64 = 0;
    while y < h {
        let mut x: i64 = 0;
        while x < w {
            let v = (grid[y as usize][x as usize] ? 255 : 0);
            let mut yy: i64 = 0;
            while yy < cell {
                let base = (y * cell + yy) * width + x * cell;
                let mut xx: i64 = 0;
                while xx < cell {
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

fn run_07_game_of_life_loop() {
    let w = 144;
    let h = 108;
    let cell = 4;
    let steps = 105;
    let out_path = "sample/out/07_game_of_life_loop.gif";
    
    let start = perf_counter();
    let mut grid: Vec<Vec<i64>> = [[0] * w for _ in range(h)];
    let mut y: i64 = 0;
    while y < h {
        let mut x: i64 = 0;
        while x < w {
            let noise = (x * 37 + y * 73 + x * y % 19 + (x + y) % 11) % 97;
            if noise < 3 {
                grid[y as usize][x as usize] = 1;
            }
            x += 1;
        }
        y += 1;
    }
    // Place multiple well-known long-lived patterns.
    let glider = vec![];
    let r_pentomino = vec![];
    let lwss = vec![];
    let mut gy: i64 = 8;
    while gy < h - 8 {
        let mut gx: i64 = 8;
        while gx < w - 8 {
            let kind = (gx * 7 + gy * 11) % 3;
            if kind == 0 {
                let mut ph = glider.len() as i64;
                let mut py: i64 = 0;
                while py < ph {
                    let mut pw = glider[py as usize].len() as i64;
                    let mut px: i64 = 0;
                    while px < pw {
                        if glider[py as usize][px as usize] == 1 {
                            grid[(gy + py) % h as usize][(gx + px) % w as usize] = 1;
                        }
                        px += 1;
                    }
                    py += 1;
                }
            } else {
                if kind == 1 {
                    let mut ph = r_pentomino.len() as i64;
                    let mut py: i64 = 0;
                    while py < ph {
                        let mut pw = r_pentomino[py as usize].len() as i64;
                        let mut px: i64 = 0;
                        while px < pw {
                            if r_pentomino[py as usize][px as usize] == 1 {
                                grid[(gy + py) % h as usize][(gx + px) % w as usize] = 1;
                            }
                            px += 1;
                        }
                        py += 1;
                    }
                } else {
                    let mut ph = lwss.len() as i64;
                    let mut py: i64 = 0;
                    while py < ph {
                        let mut pw = lwss[py as usize].len() as i64;
                        let mut px: i64 = 0;
                        while px < pw {
                            if lwss[py as usize][px as usize] == 1 {
                                grid[(gy + py) % h as usize][(gx + px) % w as usize] = 1;
                            }
                            px += 1;
                        }
                        py += 1;
                    }
                }
            }
            gx += 22;
        }
        gy += 18;
    }
    let mut frames: Vec<Vec<u8>> = vec![];
    let mut _: i64 = 0;
    while _ < steps {
        frames.push(render(grid, w, h, cell));
        grid = next_state(grid, w, h);
        _ += 1;
    }
    save_gif(out_path, w * cell, h * cell, frames, grayscale_palette());
    let elapsed = perf_counter() - start;
    println!("{:?}", ("output:", out_path));
    println!("{:?}", ("frames:", steps));
    println!("{:?}", ("elapsed_sec:", elapsed));
}

fn main() {
    run_07_game_of_life_loop();
}
