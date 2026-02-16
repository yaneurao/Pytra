// このファイルは自動生成です。編集しないでください。
// 入力 Python: 09_fire_simulation.py

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
    let source: &str = r#"# 09: 簡易ファイアエフェクトをGIF出力するサンプル。

from __future__ import annotations

from time import perf_counter

from py_module.gif_helper import save_gif


def fire_palette() -> bytes:
    p = bytearray()
    for i in range(256):
        r = 0
        g = 0
        b = 0
        if i < 85:
            r = i * 3
            g = 0
            b = 0
        elif i < 170:
            r = 255
            g = (i - 85) * 3
            b = 0
        else:
            r = 255
            g = 255
            b = (i - 170) * 3
        p.append(r)
        p.append(g)
        p.append(b)
    return bytes(p)


def run_09_fire_simulation() -> None:
    w = 220
    h = 140
    steps = 110
    out_path = "sample/out/09_fire_simulation.gif"

    start = perf_counter()
    heat: list[list[int]] = []
    for _ in range(h):
        row: list[int] = []
        for _ in range(w):
            row.append(0)
        heat.append(row)
    frames: list[bytes] = []

    for t in range(steps):
        for x in range(w):
            val = 170 + ((x * 13 + t * 17) % 86)
            heat[h - 1][x] = val

        for y in range(1, h):
            for x in range(w):
                a = heat[y][x]
                b = heat[y][(x - 1 + w) % w]
                c = heat[y][(x + 1) % w]
                d = heat[(y + 1) % h][x]
                v = (a + b + c + d) // 4
                cool = 1 + ((x + y + t) % 3)
                nv = v - cool
                heat[y - 1][x] = nv if nv > 0 else 0

        frame = bytearray(w * h)
        i = 0
        for yy in range(h):
            for xx in range(w):
                frame[i] = heat[yy][xx]
                i += 1
        frames.append(bytes(frame))

    save_gif(out_path, w, h, frames, fire_palette(), delay_cs=4, loop=0)
    elapsed = perf_counter() - start
    print("output:", out_path)
    print("frames:", steps)
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_09_fire_simulation()
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
