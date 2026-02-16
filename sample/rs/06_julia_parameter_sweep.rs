// fallback: function has unsupported annotation in native Rust mode: render_frame
// このファイルは自動生成です。編集しないでください。
// 入力 Python: 06_julia_parameter_sweep.py

#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;

fn main() {
    let source: &str = r#"# 06: ジュリア集合のパラメータを回してGIF出力するサンプル。

from __future__ import annotations

from time import perf_counter

from py_module.gif_helper import grayscale_palette, save_gif


def render_frame(width: int, height: int, cr: float, ci: float, max_iter: int) -> bytes:
    frame = bytearray(width * height)
    idx = 0
    for y in range(height):
        zy0 = -1.2 + 2.4 * (y / (height - 1))
        for x in range(width):
            zx = -1.8 + 3.6 * (x / (width - 1))
            zy = zy0
            i = 0
            while i < max_iter:
                zx2 = zx * zx
                zy2 = zy * zy
                if zx2 + zy2 > 4.0:
                    break
                zy = 2.0 * zx * zy + ci
                zx = zx2 - zy2 + cr
                i += 1
            frame[idx] = int((255.0 * i) / max_iter)
            idx += 1
    return bytes(frame)


def run_06_julia_parameter_sweep() -> None:
    width = 320
    height = 240
    frames_n = 50
    max_iter = 120
    out_path = "sample/out/06_julia_parameter_sweep.gif"

    start = perf_counter()
    frames: list[bytes] = []
    for i in range(frames_n):
        t = i / frames_n
        cr = -0.8 + 0.32 * t
        ci = 0.156 + 0.22 * (0.5 - t)
        frames.append(render_frame(width, height, cr, ci, max_iter))

    save_gif(out_path, width, height, frames, grayscale_palette(), delay_cs=4, loop=0)
    elapsed = perf_counter() - start
    print("output:", out_path)
    print("frames:", frames_n)
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_06_julia_parameter_sweep()
"#;
    std::process::exit(py_runtime::run_embedded_python(source));
}
