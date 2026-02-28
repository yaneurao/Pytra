import { perf_counter } from "./pytra/std/time.js";
import { grayscale_palette } from "./pytra/utils/gif.js";
import { save_gif } from "./pytra/utils/gif.js";

// 07: Sample that outputs Game of Life evolution as a GIF.

function next_state(grid, w, h) {
    let nxt = [];
    const __start_1 = 0;
    for (let y = __start_1; y < h; y += 1) {
        let row = [];
        const __start_2 = 0;
        for (let x = __start_2; x < w; x += 1) {
            let cnt = 0;
            const __start_3 = -1;
            for (let dy = __start_3; dy < 2; dy += 1) {
                const __start_4 = -1;
                for (let dx = __start_4; dx < 2; dx += 1) {
                    if (dx !== 0 || dy !== 0) {
                        let nx = (x + dx + w) % w;
                        let ny = (y + dy + h) % h;
                        cnt += grid[(((ny) < 0) ? ((grid).length + (ny)) : (ny))][(((nx) < 0) ? ((grid[(((ny) < 0) ? ((grid).length + (ny)) : (ny))]).length + (nx)) : (nx))];
                    }
                }
            }
            let alive = grid[(((y) < 0) ? ((grid).length + (y)) : (y))][(((x) < 0) ? ((grid[(((y) < 0) ? ((grid).length + (y)) : (y))]).length + (x)) : (x))];
            if (alive === 1 && cnt === 2 || cnt === 3) {
                row.push(1);
            } else {
                if (alive === 0 && cnt === 3) {
                    row.push(1);
                } else {
                    row.push(0);
                }
            }
        }
        nxt.push(row);
    }
    return nxt;
}

function render(grid, w, h, cell) {
    let width = w * cell;
    let height = h * cell;
    let frame = (typeof (width * height) === "number" ? new Array(Math.max(0, Math.trunc(Number((width * height))))).fill(0) : (Array.isArray((width * height)) ? (width * height).slice() : Array.from((width * height))));
    const __start_5 = 0;
    for (let y = __start_5; y < h; y += 1) {
        const __start_6 = 0;
        for (let x = __start_6; x < w; x += 1) {
            let v = (grid[(((y) < 0) ? ((grid).length + (y)) : (y))][(((x) < 0) ? ((grid[(((y) < 0) ? ((grid).length + (y)) : (y))]).length + (x)) : (x))] ? 255 : 0);
            const __start_7 = 0;
            for (let yy = __start_7; yy < cell; yy += 1) {
                let base = (y * cell + yy) * width + x * cell;
                const __start_8 = 0;
                for (let xx = __start_8; xx < cell; xx += 1) {
                    frame[(((base + xx) < 0) ? ((frame).length + (base + xx)) : (base + xx))] = v;
                }
            }
        }
    }
    return (Array.isArray((frame)) ? (frame).slice() : Array.from((frame)));
}

function run_07_game_of_life_loop() {
    let w = 144;
    let h = 108;
    let cell = 4;
    let steps = 105;
    let out_path = "sample/out/07_game_of_life_loop.gif";
    
    let start = perf_counter();
    let grid = (() => { let __out = []; for (const _ of (() => { const __out = []; const __start = 0; const __stop = h; const __step = 1; if (__step === 0) { return __out; } if (__step > 0) { for (let __i = __start; __i < __stop; __i += __step) { __out.push(__i); } } else { for (let __i = __start; __i > __stop; __i += __step) { __out.push(__i); } } return __out; })()) { __out.push((() => { const __base = ([0]); const __n = Math.max(0, Math.trunc(Number(w))); let __out = []; for (let __i = 0; __i < __n; __i += 1) { for (const __v of __base) { __out.push(__v); } } return __out; })()); } return __out; })();
    
    // Lay down sparse noise so the whole field is less likely to stabilize too early.
    // Avoid large integer literals so all transpilers handle the expression consistently.
    const __start_9 = 0;
    for (let y = __start_9; y < h; y += 1) {
        const __start_10 = 0;
        for (let x = __start_10; x < w; x += 1) {
            let noise = (x * 37 + y * 73 + x * y % 19 + (x + y) % 11) % 97;
            if (noise < 3) {
                grid[(((y) < 0) ? ((grid).length + (y)) : (y))][(((x) < 0) ? ((grid[(((y) < 0) ? ((grid).length + (y)) : (y))]).length + (x)) : (x))] = 1;
            }
        }
    }
    // Place multiple well-known long-lived patterns.
    let glider = [[0, 1, 0], [0, 0, 1], [1, 1, 1]];
    let r_pentomino = [[0, 1, 1], [1, 1, 0], [0, 1, 0]];
    let lwss = [[0, 1, 1, 1, 1], [1, 0, 0, 0, 1], [0, 0, 0, 0, 1], [1, 0, 0, 1, 0]];
    
    const __start_11 = 8;
    for (let gy = __start_11; gy < h - 8; gy += 18) {
        const __start_12 = 8;
        for (let gx = __start_12; gx < w - 8; gx += 22) {
            let kind = (gx * 7 + gy * 11) % 3;
            if (kind === 0) {
                let ph = (glider).length;
                const __start_13 = 0;
                for (let py = __start_13; py < ph; py += 1) {
                    let pw = (glider[(((py) < 0) ? ((glider).length + (py)) : (py))]).length;
                    const __start_14 = 0;
                    for (let px = __start_14; px < pw; px += 1) {
                        if (glider[(((py) < 0) ? ((glider).length + (py)) : (py))][(((px) < 0) ? ((glider[(((py) < 0) ? ((glider).length + (py)) : (py))]).length + (px)) : (px))] === 1) {
                            grid[((((gy + py) % h) < 0) ? ((grid).length + ((gy + py) % h)) : ((gy + py) % h))][((((gx + px) % w) < 0) ? ((grid[((((gy + py) % h) < 0) ? ((grid).length + ((gy + py) % h)) : ((gy + py) % h))]).length + ((gx + px) % w)) : ((gx + px) % w))] = 1;
                        }
                    }
                }
            } else {
                if (kind === 1) {
                    let ph = (r_pentomino).length;
                    const __start_15 = 0;
                    for (let py = __start_15; py < ph; py += 1) {
                        let pw = (r_pentomino[(((py) < 0) ? ((r_pentomino).length + (py)) : (py))]).length;
                        const __start_16 = 0;
                        for (let px = __start_16; px < pw; px += 1) {
                            if (r_pentomino[(((py) < 0) ? ((r_pentomino).length + (py)) : (py))][(((px) < 0) ? ((r_pentomino[(((py) < 0) ? ((r_pentomino).length + (py)) : (py))]).length + (px)) : (px))] === 1) {
                                grid[((((gy + py) % h) < 0) ? ((grid).length + ((gy + py) % h)) : ((gy + py) % h))][((((gx + px) % w) < 0) ? ((grid[((((gy + py) % h) < 0) ? ((grid).length + ((gy + py) % h)) : ((gy + py) % h))]).length + ((gx + px) % w)) : ((gx + px) % w))] = 1;
                            }
                        }
                    }
                } else {
                    let ph = (lwss).length;
                    const __start_17 = 0;
                    for (let py = __start_17; py < ph; py += 1) {
                        let pw = (lwss[(((py) < 0) ? ((lwss).length + (py)) : (py))]).length;
                        const __start_18 = 0;
                        for (let px = __start_18; px < pw; px += 1) {
                            if (lwss[(((py) < 0) ? ((lwss).length + (py)) : (py))][(((px) < 0) ? ((lwss[(((py) < 0) ? ((lwss).length + (py)) : (py))]).length + (px)) : (px))] === 1) {
                                grid[((((gy + py) % h) < 0) ? ((grid).length + ((gy + py) % h)) : ((gy + py) % h))][((((gx + px) % w) < 0) ? ((grid[((((gy + py) % h) < 0) ? ((grid).length + ((gy + py) % h)) : ((gy + py) % h))]).length + ((gx + px) % w)) : ((gx + px) % w))] = 1;
                            }
                        }
                    }
                }
            }
        }
    }
    let frames = [];
    const __start_19 = 0;
    for (let _ = __start_19; _ < steps; _ += 1) {
        frames.push(render(grid, w, h, cell));
        grid = next_state(grid, w, h);
    }
    save_gif(out_path, w * cell, h * cell, frames, grayscale_palette());
    let elapsed = perf_counter() - start;
    console.log("output:", out_path);
    console.log("frames:", steps);
    console.log("elapsed_sec:", elapsed);
}

run_07_game_of_life_loop();
