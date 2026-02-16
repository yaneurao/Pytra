// このファイルは自動生成です（Python -> JavaScript）。

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

/** 埋め込み元 Python ファイルパス。 */
const PYTRA_SOURCE_PATH = "sample/py/11_lissajous_particles.py";
/** 埋め込み Python ソースコード。 */
const PYTRA_SOURCE_CODE = `# 11: リサージュ運動する粒子をGIF出力するサンプル。

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
