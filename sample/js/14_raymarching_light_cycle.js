// このファイルは自動生成です（Python -> JavaScript）。

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

/** 埋め込み元 Python ファイルパス。 */
const PYTRA_SOURCE_PATH = "sample/py/14_raymarching_light_cycle.py";
/** 埋め込み Python ソースコード。 */
const PYTRA_SOURCE_CODE = `# 14: 簡易レイマーチ風の光源移動シーンをGIF出力するサンプル。

from __future__ import annotations

import math
from time import perf_counter

from py_module.gif_helper import save_gif


def palette() -> bytes:
    p = bytearray()
    for i in range(256):
        r = int(20 + i * 0.9)
        if r > 255:
            r = 255
        g = int(10 + i * 0.7)
        if g > 255:
            g = 255
        b = int(30 + i)
        if b > 255:
            b = 255
        p.append(r)
        p.append(g)
        p.append(b)
    return bytes(p)


def scene(x: float, y: float, light_x: float, light_y: float) -> int:
    x1 = x + 0.45
    y1 = y + 0.2
    x2 = x - 0.35
    y2 = y - 0.15
    r1 = math.sqrt(x1 * x1 + y1 * y1)
    r2 = math.sqrt(x2 * x2 + y2 * y2)
    blob = math.exp(-7.0 * r1 * r1) + math.exp(-8.0 * r2 * r2)

    lx = x - light_x
    ly = y - light_y
    l = math.sqrt(lx * lx + ly * ly)
    lit = 1.0 / (1.0 + 3.5 * l * l)

    v = int(255.0 * blob * lit * 5.0)
    if v < 0:
        return 0
    if v > 255:
        return 255
    return v


def run_14_raymarching_light_cycle() -> None:
    w = 320
    h = 240
    frames_n = 84
    out_path = "sample/out/14_raymarching_light_cycle.gif"

    start = perf_counter()
    frames: list[bytes] = []

    for t in range(frames_n):
        frame = bytearray(w * h)
        a = (t / frames_n) * math.pi * 2.0
        light_x = 0.75 * math.cos(a)
        light_y = 0.55 * math.sin(a * 1.2)

        i = 0
        for y in range(h):
            py = (y / (h - 1)) * 2.0 - 1.0
            for x in range(w):
                px = (x / (w - 1)) * 2.0 - 1.0
                frame[i] = scene(px, py, light_x, light_y)
                i += 1

        frames.append(bytes(frame))

    save_gif(out_path, w, h, frames, palette(), delay_cs=3, loop=0)
    elapsed = perf_counter() - start
    print("output:", out_path)
    print("frames:", frames_n)
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_14_raymarching_light_cycle()
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
