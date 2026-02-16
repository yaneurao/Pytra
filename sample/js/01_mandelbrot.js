// このファイルは自動生成です（Python -> JavaScript）。

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

/** 埋め込み元 Python ファイルパス。 */
const PYTRA_SOURCE_PATH = "sample/py/01_mandelbrot.py";
/** 埋め込み Python ソースコード。 */
const PYTRA_SOURCE_CODE = `# 01: マンデルブロ集合を PNG 画像として出力するサンプルです。
# 将来のトランスパイルを意識して、構文はなるべく素直に書いています。

from time import perf_counter
from py_module import png_helper


def escape_count(cx: float, cy: float, max_iter: int) -> int:
    """1点 (cx, cy) の発散までの反復回数を返す。"""
    x: float = 0.0
    y: float = 0.0
    for i in range(max_iter):
        x2: float = x * x
        y2: float = y * y
        if x2 + y2 > 4.0:
            return i
        y = 2.0 * x * y + cy
        x = x2 - y2 + cx
    return max_iter


def color_map(iter_count: int, max_iter: int) -> tuple[int, int, int]:
    """反復回数を RGB に変換する。"""
    if iter_count >= max_iter:
        return (0, 0, 0)

    # 簡単なグラデーション（青系 -> 黄系）
    t: float = iter_count / max_iter
    r: int = int(255.0 * (t * t))
    g: int = int(255.0 * t)
    b: int = int(255.0 * (1.0 - t))
    return (r, g, b)


def render_mandelbrot(
    width: int,
    height: int,
    max_iter: int,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
) -> bytearray:
    """マンデルブロ画像の RGB バイト列を生成する。"""
    pixels: bytearray = bytearray()

    for y in range(height):
        py: float = y_min + (y_max - y_min) * (y / (height - 1))

        for x in range(width):
            px: float = x_min + (x_max - x_min) * (x / (width - 1))
            it: int = escape_count(px, py, max_iter)
            r: int
            g: int
            b: int
            if it >= max_iter:
                r = 0
                g = 0
                b = 0
            else:
                t: float = it / max_iter
                r = int(255.0 * (t * t))
                g = int(255.0 * t)
                b = int(255.0 * (1.0 - t))
            pixels.append(r)
            pixels.append(g)
            pixels.append(b)

    return pixels


def run_mandelbrot() -> None:
    width: int = 1600
    height: int = 1200
    max_iter: int = 1000
    out_path: str = "sample/out/mandelbrot_01.png"

    start: float = perf_counter()

    pixels: bytearray = render_mandelbrot(
        width,
        height,
        max_iter,
        -2.2,
        1.0,
        -1.2,
        1.2,
    )
    png_helper.write_rgb_png(out_path, width, height, pixels)

    elapsed: float = perf_counter() - start
    print("output:", out_path)
    print("size:", width, "x", height)
    print("max_iter:", max_iter)
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_mandelbrot()
`;

/**
 * Python インタプリタで埋め込みソースを実行する。
 * @param { interpreter: string, scriptPath: string, args: string[] } params 実行パラメータ。
 * @returns { status: number|null, error?: Error } 実行結果。
 */
function runPython(params) {
  const env = { ...process.env };
  const current = env.PYTHONPATH;
  env.PYTHONPATH = current && current.length > 0
    ? ["src", current].join(path.delimiter)
    : "src";
  return spawnSync(params.interpreter, [params.scriptPath, ...params.args], {
    stdio: "inherit",
    env,
  });
}

/** エントリポイント。 */
function main() {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "pytra_js_"));
  const scriptPath = path.join(tempDir, "embedded.py");
  fs.writeFileSync(scriptPath, PYTRA_SOURCE_CODE, { encoding: "utf8" });

  let result = runPython({ interpreter: "python3", scriptPath, args: process.argv.slice(2) });
  if (result.error && result.error.code === "ENOENT") {
    result = runPython({ interpreter: "python", scriptPath, args: process.argv.slice(2) });
  }

  fs.rmSync(tempDir, { recursive: true, force: true });
  if (result.error) {
    console.error("error: python interpreter not found (python3/python)");
    process.exit(1);
  }
  process.exit(typeof result.status === "number" ? result.status : 1);
}

main();
