// このファイルは自動生成です。編集しないでください。
// 入力 Python: 11_lissajous_particles.py

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
    let source: &str = r#"# 11: リサージュ運動する粒子をGIF出力するサンプル。

from __future__ import annotations

import math
from time import perf_counter

from py_module.gif_helper import save_gif


def color_palette() -> bytes:
    p = bytearray()
    for i in range(256):
        r = i
        g = (i * 3) % 256
        b = 255 - i
        p.append(r)
        p.append(g)
        p.append(b)
    return bytes(p)


def run_11_lissajous_particles() -> None:
    w = 320
    h = 240
    frames_n = 80
    particles = 24
    out_path = "sample/out/11_lissajous_particles.gif"

    start = perf_counter()
    frames: list[bytes] = []

    for t in range(frames_n):
        frame = bytearray(w * h)

        for p in range(particles):
            phase = p * 0.261799
            x = int((w * 0.5) + (w * 0.38) * math.sin(0.11 * t + phase * 2.0))
            y = int((h * 0.5) + (h * 0.38) * math.sin(0.17 * t + phase * 3.0))
            color = 30 + (p * 9) % 220

            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    xx = x + dx
                    yy = y + dy
                    if xx >= 0 and xx < w and yy >= 0 and yy < h:
                        d2 = dx * dx + dy * dy
                        if d2 <= 4:
                            idx = yy * w + xx
                            v = color - d2 * 20
                            if v < 0:
                                v = 0
                            if v > frame[idx]:
                                frame[idx] = v

        frames.append(bytes(frame))

    save_gif(out_path, w, h, frames, color_palette(), delay_cs=3, loop=0)
    elapsed = perf_counter() - start
    print("output:", out_path)
    print("frames:", frames_n)
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_11_lissajous_particles()
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
