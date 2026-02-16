// fallback: unsupported annotation: Subscript(value=Name(id='list', ctx=Load()), slice=Name(id='bytes', ctx=Load()), ctx=Load())
// このファイルは自動生成です。編集しないでください。
// 入力 Python: 10_plasma_effect.py

#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;

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
    std::process::exit(py_runtime::run_embedded_python(source));
}
