// このファイルは自動生成です（Python -> TypeScript）。

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync, SpawnSyncReturns } from "node:child_process";

/** 埋め込み元 Python ファイルパス。 */
const PYTRA_SOURCE_PATH: string = "sample/py/10_plasma_effect.py";
/** 埋め込み Python ソースコード。 */
const PYTRA_SOURCE_CODE: string = `# 10: プラズマエフェクトをGIF出力するサンプル。

from __future__ import annotations

import math
from time import perf_counter

from py_module.gif_helper import grayscale_palette, save_gif


def run_10_plasma_effect() -> None:
    w = 320
    h = 240
    frames_n = 216
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
