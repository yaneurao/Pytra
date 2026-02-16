// このファイルは自動生成です（Python -> TypeScript）。

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync, SpawnSyncReturns } from "node:child_process";

/** 埋め込み元 Python ファイルパス。 */
const PYTRA_SOURCE_PATH: string = "sample/py/12_sort_visualizer.py";
/** 埋め込み Python ソースコード。 */
const PYTRA_SOURCE_CODE: string = `# 12: バブルソートの途中状態をGIF出力するサンプル。

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
