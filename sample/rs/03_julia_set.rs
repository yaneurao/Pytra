// このファイルは自動生成です。編集しないでください。
// 入力 Python: 03_julia_set.py

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
    let source: &str = r#"# 03: ジュリア集合を PNG 形式で出力するサンプルです。
# トランスパイル互換を意識し、単純なループ中心で実装しています。

from time import perf_counter
from py_module import png_helper


def render_julia(width: int, height: int, max_iter: int, cx: float, cy: float) -> bytearray:
    pixels: bytearray = bytearray()

    for y in range(height):
        zy0: float = -1.2 + 2.4 * (y / (height - 1))

        for x in range(width):
            zx: float = -1.8 + 3.6 * (x / (width - 1))
            zy: float = zy0

            i: int = 0
            while i < max_iter:
                zx2: float = zx * zx
                zy2: float = zy * zy
                if zx2 + zy2 > 4.0:
                    break
                zy = 2.0 * zx * zy + cy
                zx = zx2 - zy2 + cx
                i += 1

            r: int = 0
            g: int = 0
            b: int = 0
            if i >= max_iter:
                r = 0
                g = 0
                b = 0
            else:
                t: float = i / max_iter
                r = int(255.0 * (0.2 + 0.8 * t))
                g = int(255.0 * (0.1 + 0.9 * (t * t)))
                b = int(255.0 * (1.0 - t))

            pixels.append(r)
            pixels.append(g)
            pixels.append(b)

    return pixels


def run_julia() -> None:
    width: int = 1280
    height: int = 720
    max_iter: int = 520
    out_path: str = "sample/out/julia_03.png"

    start: float = perf_counter()
    pixels: bytearray = render_julia(width, height, max_iter, -0.8, 0.156)
    png_helper.write_rgb_png(out_path, width, height, pixels)
    elapsed: float = perf_counter() - start

    print("output:", out_path)
    print("size:", width, "x", height)
    print("max_iter:", max_iter)
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_julia()
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
