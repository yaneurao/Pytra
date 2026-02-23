// このファイルは EAST ベース TypeScript プレビュー出力です。
// TODO: 専用 TSEmitter 実装へ段階移行する。
const __pytra_root = process.cwd();
const py_runtime = require(__pytra_root + '/src/js_module/py_runtime.js');
const { PYTRA_TYPE_ID, PY_TYPE_BOOL, PY_TYPE_NUMBER, PY_TYPE_STRING, PY_TYPE_ARRAY, PY_TYPE_MAP, PY_TYPE_SET, PY_TYPE_OBJECT, pyRegisterClassType, pyIsInstance } = py_runtime;

import { perf_counter } from "./time.js";
import { grayscale_palette } from "./pytra/utils/gif.js";
import { save_gif } from "./pytra/utils/gif.js";

// 07: Sample that outputs Game of Life evolution as a GIF.

function next_state(grid, w, h) {
    let nxt = [];
    for (let y = 0; y < h; y += 1) {
        let row = [];
        for (let x = 0; x < w; x += 1) {
            let cnt = 0;
            for (let dy = (-1); dy < 2; dy += 1) {
                for (let dx = (-1); dx < 2; dx += 1) {
                    if ((dx !== 0) || (dy !== 0)) {
                        let nx = ((((x + dx) + w)) % w);
                        let ny = ((((y + dy) + h)) % h);
                        cnt += grid[ny][nx];
                    }
                }
            }
            let alive = grid[y][x];
            if ((alive === 1) && ((cnt === 2) || (cnt === 3))) {
                row.push(1);
            } else {
                if ((alive === 0) && (cnt === 3)) {
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
    let width = (w * cell);
    let height = (h * cell);
    let frame = bytearray((width * height));
    for (let y = 0; y < h; y += 1) {
        for (let x = 0; x < w; x += 1) {
            let v = (grid[y][x] ? 255 : 0);
            for (let yy = 0; yy < cell; yy += 1) {
                let base = (((((y * cell) + yy)) * width) + (x * cell));
                for (let xx = 0; xx < cell; xx += 1) {
                    frame[(base + xx)] = v;
                }
            }
        }
    }
    return bytes(frame);
}

function run_07_game_of_life_loop() {
    let w = 144;
    let h = 108;
    let cell = 4;
    let steps = 105;
    let out_path = "sample/out/07_game_of_life_loop.gif";
    
    let start = perf_counter();
    let grid = [[0] * w for _ in range(h)];
    
    // Lay down sparse noise so the whole field is less likely to stabilize too early.
    // Avoid large integer literals so all transpilers handle the expression consistently.
    for (let y = 0; y < h; y += 1) {
        for (let x = 0; x < w; x += 1) {
            let noise = ((((((x * 37) + (y * 73)) + ((x * y) % 19)) + (((x + y)) % 11))) % 97);
            if (noise < 3) {
                grid[y][x] = 1;
            }
        }
    }
    // Place multiple well-known long-lived patterns.
    let glider = [];
    let r_pentomino = [];
    let lwss = [];
    
    for (let gy = 8; gy < (h - 8); gy += 18) {
        for (let gx = 8; gx < (w - 8); gx += 22) {
            let kind = ((((gx * 7) + (gy * 11))) % 3);
            if (kind === 0) {
                let ph = (glider).length;
                for (let py = 0; py < ph; py += 1) {
                    let pw = (glider[py]).length;
                    for (let px = 0; px < pw; px += 1) {
                        if (glider[py][px] === 1) {
                            grid[(((gy + py)) % h)][(((gx + px)) % w)] = 1;
                        }
                    }
                }
            } else {
                if (kind === 1) {
                    let ph = (r_pentomino).length;
                    for (let py = 0; py < ph; py += 1) {
                        let pw = (r_pentomino[py]).length;
                        for (let px = 0; px < pw; px += 1) {
                            if (r_pentomino[py][px] === 1) {
                                grid[(((gy + py)) % h)][(((gx + px)) % w)] = 1;
                            }
                        }
                    }
                } else {
                    let ph = (lwss).length;
                    for (let py = 0; py < ph; py += 1) {
                        let pw = (lwss[py]).length;
                        for (let px = 0; px < pw; px += 1) {
                            if (lwss[py][px] === 1) {
                                grid[(((gy + py)) % h)][(((gx + px)) % w)] = 1;
                            }
                        }
                    }
                }
            }
        }
    }
    let frames = [];
    for (let _ = 0; _ < steps; _ += 1) {
        frames.push(render(grid, w, h, cell));
        grid = next_state(grid, w, h);
    }
    save_gif(out_path, (w * cell), (h * cell), frames, grayscale_palette());
    let elapsed = (perf_counter() - start);
    console.log("output:", out_path);
    console.log("frames:", steps);
    console.log("elapsed_sec:", elapsed);
}

// __main__ guard
run_07_game_of_life_loop();
