// このファイルは自動生成です。編集しないでください。
// 入力 Python: 10_plasma_effect.py

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
    let source: &str = r#"# 10: プラズマエフェクトをGIF出力するサンプル。

from __future__ import annotations

import math
from time import perf_counter

from py_module.gif_helper import grayscale_palette, save_gif


def run_10_plasma_effect() -> None:
    w = 320
    h = 240
    frames_n = 72
    out_path = "sample/out/10_plasma_effect.gif"

    start = perf_counter()
    frames: list[bytes] = []

    for t in range(frames_n):
        frame = bytearray(w * h)
        i = 0
        for y in range(h):
            for x in range(w):
                dx = x - 160
                dy = y - 120
                v = (
                    math.sin((x + t * 2.0) * 0.045)
                    + math.sin((y - t * 1.2) * 0.05)
                    + math.sin((x + y + t * 1.7) * 0.03)
                    + math.sin(math.sqrt(dx * dx + dy * dy) * 0.07 - t * 0.18)
                )
                c = int((v + 4.0) * (255.0 / 8.0))
                if c < 0:
                    c = 0
                if c > 255:
                    c = 255
                frame[i] = c
                i += 1
        frames.append(bytes(frame))

    save_gif(out_path, w, h, frames, grayscale_palette(), delay_cs=3, loop=0)
    elapsed = perf_counter() - start
    print("output:", out_path)
    print("frames:", frames_n)
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_10_plasma_effect()
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
