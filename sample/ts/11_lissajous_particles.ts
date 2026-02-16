// このファイルは自動生成です（Python -> TypeScript）。

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync, SpawnSyncReturns } from "node:child_process";

/** 埋め込み元 Python ファイルパス。 */
const PYTRA_SOURCE_PATH: string = "sample/py/11_lissajous_particles.py";
/** 埋め込み Python ソースコード。 */
const PYTRA_SOURCE_CODE: string = `# 11: リサージュ運動する粒子をGIF出力するサンプル。

from __future__ import annotations

import math
from time import perf_counter

from py_module.gif_helper import save_gif


def color_palette() -> bytes:
    p = bytearray()
    for i in range(256):
        r = i
        g = (i * 3) % 256
        b = 255 - i
        p.append(r)
        p.append(g)
        p.append(b)
    return bytes(p)


def run_11_lissajous_particles() -> None:
    w = 320
    h = 240
    frames_n = 360
    particles = 48
    out_path = "sample/out/11_lissajous_particles.gif"

    start = perf_counter()
    frames: list[bytes] = []

    for t in range(frames_n):
        frame = bytearray(w * h)

        for p in range(particles):
            phase = p * 0.261799
            x = int((w * 0.5) + (w * 0.38) * math.sin(0.11 * t + phase * 2.0))
            y = int((h * 0.5) + (h * 0.38) * math.sin(0.17 * t + phase * 3.0))
            color = 30 + (p * 9) % 220

            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    xx = x + dx
                    yy = y + dy
                    if xx >= 0 and xx < w and yy >= 0 and yy < h:
                        d2 = dx * dx + dy * dy
                        if d2 <= 4:
                            idx = yy * w + xx
                            v = color - d2 * 20
                            if v < 0:
                                v = 0
                            if v > frame[idx]:
                                frame[idx] = v

        frames.append(bytes(frame))

    save_gif(out_path, w, h, frames, color_palette(), delay_cs=3, loop=0)
    elapsed = perf_counter() - start
    print("output:", out_path)
    print("frames:", frames_n)
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_11_lissajous_particles()
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
