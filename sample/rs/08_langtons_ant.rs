// fallback: unsupported annotation: Subscript(value=Name(id='list', ctx=Load()), slice=Subscript(value=Name(id='list', ctx=Load()), slice=Name(id='int', ctx=Load()), ctx=Load()), ctx=Load())
// このファイルは自動生成です。編集しないでください。
// 入力 Python: 08_langtons_ant.py

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
    let source: &str = r#"# 08: ラングトンのアリの軌跡をGIF出力するサンプル。

from __future__ import annotations

from time import perf_counter

from py_module.gif_helper import grayscale_palette, save_gif


def capture(grid: list[list[int]], w: int, h: int) -> bytes:
    frame = bytearray(w * h)
    i = 0
    for y in range(h):
        for x in range(w):
            frame[i] = 255 if grid[y][x] else 0
            i += 1
    return bytes(frame)


def run_08_langtons_ant() -> None:
    w = 240
    h = 240
    out_path = "sample/out/08_langtons_ant.gif"

    start = perf_counter()

    grid: list[list[int]] = []
    for gy in range(h):
        row: list[int] = []
        for gx in range(w):
            row.append(0)
        grid.append(row)
    x = w // 2
    y = h // 2
    d = 0

    steps_total = 180000
    capture_every = 3000
    frames: list[bytes] = []

    for i in range(steps_total):
        if grid[y][x] == 0:
            d = (d + 1) % 4
            grid[y][x] = 1
        else:
            d = (d + 3) % 4
            grid[y][x] = 0

        if d == 0:
            y = (y - 1 + h) % h
        elif d == 1:
            x = (x + 1) % w
        elif d == 2:
            y = (y + 1) % h
        else:
            x = (x - 1 + w) % w

        if i % capture_every == 0:
            frames.append(capture(grid, w, h))

    save_gif(out_path, w, h, frames, grayscale_palette(), delay_cs=5, loop=0)
    elapsed = perf_counter() - start
    print("output:", out_path)
    print("frames:", len(frames))
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_08_langtons_ant()
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
