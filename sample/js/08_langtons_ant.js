// このファイルは自動生成です（Python -> JavaScript）。

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

/** 埋め込み元 Python ファイルパス。 */
const PYTRA_SOURCE_PATH = "sample/py/08_langtons_ant.py";
/** 埋め込み Python ソースコード。 */
const PYTRA_SOURCE_CODE = `# 08: ラングトンのアリの軌跡をGIF出力するサンプル。

from __future__ import annotations

from time import perf_counter

from py_module.gif_helper import grayscale_palette, save_gif


def capture(grid: list[list[int]], w: int, h: int) -> bytes:
    frame = bytearray(w * h)
    i = 0
    for y in range(h):
        for x in range(w):
            frame[i] = 255 if grid[y][x] else 0
            i += 1
    return bytes(frame)


def run_08_langtons_ant() -> None:
    w = 420
    h = 420
    out_path = "sample/out/08_langtons_ant.gif"

    start = perf_counter()

    grid: list[list[int]] = []
    for gy in range(h):
        row: list[int] = []
        for gx in range(w):
            row.append(0)
        grid.append(row)
    x = w // 2
    y = h // 2
    d = 0

    steps_total = 600000
    capture_every = 3000
    frames: list[bytes] = []

    for i in range(steps_total):
        if grid[y][x] == 0:
            d = (d + 1) % 4
            grid[y][x] = 1
        else:
            d = (d + 3) % 4
            grid[y][x] = 0

        if d == 0:
            y = (y - 1 + h) % h
        elif d == 1:
            x = (x + 1) % w
        elif d == 2:
            y = (y + 1) % h
        else:
            x = (x - 1 + w) % w

        if i % capture_every == 0:
            frames.append(capture(grid, w, h))

    save_gif(out_path, w, h, frames, grayscale_palette(), delay_cs=5, loop=0)
    elapsed = perf_counter() - start
    print("output:", out_path)
    print("frames:", len(frames))
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_08_langtons_ant()
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
