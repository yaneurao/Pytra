// fallback: function has unsupported annotation in native Rust mode: render_frame
// このファイルは自動生成です。編集しないでください。
// 入力 Python: 05_mandelbrot_zoom.py

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
    let source: &str = r#"# 05: マンデルブロ集合ズームをアニメーションGIFとして出力するサンプル。

from __future__ import annotations

from time import perf_counter

from py_module.gif_helper import grayscale_palette, save_gif


def render_frame(width: int, height: int, center_x: float, center_y: float, scale: float, max_iter: int) -> bytes:
    frame = bytearray(width * height)
    idx = 0
    for y in range(height):
        cy = center_y + (y - height * 0.5) * scale
        for x in range(width):
            cx = center_x + (x - width * 0.5) * scale
            zx = 0.0
            zy = 0.0
            i = 0
            while i < max_iter:
                zx2 = zx * zx
                zy2 = zy * zy
                if zx2 + zy2 > 4.0:
                    break
                zy = 2.0 * zx * zy + cy
                zx = zx2 - zy2 + cx
                i += 1
            frame[idx] = int((255.0 * i) / max_iter)
            idx += 1
    return bytes(frame)


def run_05_mandelbrot_zoom() -> None:
    width = 320
    height = 240
    frame_count = 48
    max_iter = 110
    center_x = -0.743643887037151
    center_y = 0.13182590420533
    base_scale = 3.2 / width
    zoom_per_frame = 0.93
    out_path = "sample/out/05_mandelbrot_zoom.gif"

    start = perf_counter()
    frames: list[bytes] = []
    scale = base_scale
    for _ in range(frame_count):
        frames.append(render_frame(width, height, center_x, center_y, scale, max_iter))
        scale *= zoom_per_frame

    save_gif(out_path, width, height, frames, grayscale_palette(), delay_cs=5, loop=0)
    elapsed = perf_counter() - start
    print("output:", out_path)
    print("frames:", frame_count)
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_05_mandelbrot_zoom()
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
