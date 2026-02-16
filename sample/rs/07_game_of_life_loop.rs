// fallback: unsupported annotation: Subscript(value=Name(id='list', ctx=Load()), slice=Subscript(value=Name(id='list', ctx=Load()), slice=Name(id='int', ctx=Load()), ctx=Load()), ctx=Load())
// このファイルは自動生成です。編集しないでください。
// 入力 Python: 07_game_of_life_loop.py

use std::env;
use std::process::Command;

fn run_with(interpreter: &str, source: &str) -> Option<i32> {
    let mut cmd = Command::new(interpreter);
    cmd.arg("-c").arg(source);

    // sample/py が `from py_module ...` を使うため `PYTHONPATH=src` を付与する。
    let py_path = match env::var("PYTHONPATH") {
        Ok(v) if !v.is_empty() => format!("src:{}", v),
        _ => "src".to_string(),
    };
    cmd.env("PYTHONPATH", py_path);

    // 親プロセスの標準入出力をそのまま使う。
    let status = cmd.status().ok()?;
    Some(status.code().unwrap_or(1))
}

fn main() {
    let source: &str = r#"# 07: Game of Life の進化をGIF出力するサンプル。

from __future__ import annotations

from time import perf_counter

from py_module.gif_helper import grayscale_palette, save_gif


def next_state(grid: list[list[int]], w: int, h: int) -> list[list[int]]:
    nxt: list[list[int]] = []
    for y in range(h):
        row: list[int] = []
        for x in range(w):
            cnt = 0
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    if dx != 0 or dy != 0:
                        nx = (x + dx + w) % w
                        ny = (y + dy + h) % h
                        cnt += grid[ny][nx]
            alive = grid[y][x]
            if alive == 1 and (cnt == 2 or cnt == 3):
                row.append(1)
            elif alive == 0 and cnt == 3:
                row.append(1)
            else:
                row.append(0)
        nxt.append(row)
    return nxt


def render(grid: list[list[int]], w: int, h: int, cell: int) -> bytes:
    width = w * cell
    height = h * cell
    frame = bytearray(width * height)
    for y in range(h):
        for x in range(w):
            v = 255 if grid[y][x] else 0
            for yy in range(cell):
                base = (y * cell + yy) * width + x * cell
                for xx in range(cell):
                    frame[base + xx] = v
    return bytes(frame)


def run_07_game_of_life_loop() -> None:
    w = 96
    h = 72
    cell = 3
    steps = 70
    out_path = "sample/out/07_game_of_life_loop.gif"

    start = perf_counter()
    grid: list[list[int]] = []
    for y in range(h):
        row: list[int] = []
        for x in range(w):
            row.append(1 if ((x * 17 + y * 31 + 13) % 11) < 3 else 0)
        grid.append(row)

    frames: list[bytes] = []
    for _ in range(steps):
        frames.append(render(grid, w, h, cell))
        grid = next_state(grid, w, h)

    save_gif(out_path, w * cell, h * cell, frames, grayscale_palette(), delay_cs=4, loop=0)
    elapsed = perf_counter() - start
    print("output:", out_path)
    print("frames:", steps)
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_07_game_of_life_loop()
"#;

    // python3 を優先し、無ければ python を試す。
    if let Some(code) = run_with("python3", source) {
        std::process::exit(code);
    }
    if let Some(code) = run_with("python", source) {
        std::process::exit(code);
    }

    eprintln!("error: python interpreter not found (python3/python)");
    std::process::exit(1);
}
