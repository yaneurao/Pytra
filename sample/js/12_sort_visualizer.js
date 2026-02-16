// このファイルは自動生成です（Python -> JavaScript）。

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

/** 埋め込み元 Python ファイルパス。 */
const PYTRA_SOURCE_PATH = "sample/py/12_sort_visualizer.py";
/** 埋め込み Python ソースコード。 */
const PYTRA_SOURCE_CODE = `# 12: バブルソートの途中状態をGIF出力するサンプル。

from __future__ import annotations

from time import perf_counter

from py_module.gif_helper import grayscale_palette, save_gif


def render(values: list[int], w: int, h: int) -> bytes:
    frame = bytearray(w * h)
    n = len(values)
    bar_w = w / n
    for i in range(n):
        x0 = int(i * bar_w)
        x1 = int((i + 1) * bar_w)
        if x1 <= x0:
            x1 = x0 + 1
        bh = int(((values[i] / n) * h))
        y = h - bh
        for y in range(y, h):
            for x in range(x0, x1):
                frame[y * w + x] = 255
    return bytes(frame)


def run_12_sort_visualizer() -> None:
    w = 320
    h = 180
    n = 124
    out_path = "sample/out/12_sort_visualizer.gif"

    start = perf_counter()
    values: list[int] = []
    for i in range(n):
        values.append((i * 37 + 19) % n)

    frames: list[bytes] = [render(values, w, h)]

    op = 0
    for i in range(n):
        swapped = False
        for j in range(n - i - 1):
            if values[j] > values[j + 1]:
                tmp = values[j]
                values[j] = values[j + 1]
                values[j + 1] = tmp
                swapped = True
            if op % 8 == 0:
                frames.append(render(values, w, h))
            op += 1
        if not swapped:
            break

    save_gif(out_path, w, h, frames, grayscale_palette(), delay_cs=3, loop=0)
    elapsed = perf_counter() - start
    print("output:", out_path)
    print("frames:", len(frames))
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_12_sort_visualizer()
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
