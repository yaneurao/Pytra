// このファイルは自動生成です（Python -> JavaScript）。

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

/** 埋め込み元 Python ファイルパス。 */
const PYTRA_SOURCE_PATH = "sample/py/03_julia_set.py";
/** 埋め込み Python ソースコード。 */
const PYTRA_SOURCE_CODE = `# 03: ジュリア集合を PNG 形式で出力するサンプルです。
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
    width: int = 3840
    height: int = 2160
    max_iter: int = 20000
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
