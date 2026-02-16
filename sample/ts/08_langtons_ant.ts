// このファイルは自動生成です（Python -> TypeScript）。

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync, SpawnSyncReturns } from "node:child_process";

/** 埋め込み元 Python ファイルパス。 */
const PYTRA_SOURCE_PATH: string = "sample/py/08_langtons_ant.py";
/** 埋め込み Python ソースコード。 */
const PYTRA_SOURCE_CODE: string = `# 08: ラングトンのアリの軌跡をGIF出力するサンプル。

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
 * @param interpreter 実行する Python コマンド名。
 * @param scriptPath 一時生成した Python ファイルパス。
 * @param args Python 側へ渡すコマンドライン引数。
 * @returns 同期実行結果。
 */
function runPython(interpreter: string, scriptPath: string, args: string[]): SpawnSyncReturns<Buffer> {
  const env: NodeJS.ProcessEnv = { ...process.env };
  const current = env.PYTHONPATH;
  env.PYTHONPATH = current && current.length > 0
    ? ["src", current].join(path.delimiter)
    : "src";
  return spawnSync(interpreter, [scriptPath, ...args], {
    stdio: "inherit",
    env,
  });
}

/** エントリポイント。 */
function main(): void {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "pytra_ts_"));
  const scriptPath = path.join(tempDir, "embedded.py");
  fs.writeFileSync(scriptPath, PYTRA_SOURCE_CODE, { encoding: "utf8" });

  let result = runPython("python3", scriptPath, process.argv.slice(2));
  if (result.error && (result.error as NodeJS.ErrnoException).code === "ENOENT") {
    result = runPython("python", scriptPath, process.argv.slice(2));
  }

  fs.rmSync(tempDir, { recursive: true, force: true });
  if (result.error) {
    console.error("error: python interpreter not found (python3/python)");
    process.exit(1);
  }
  process.exit(typeof result.status === "number" ? result.status : 1);
}

main();
