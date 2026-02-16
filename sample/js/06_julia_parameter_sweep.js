// このファイルは自動生成です（Python -> JavaScript）。

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

/** 埋め込み元 Python ファイルパス。 */
const PYTRA_SOURCE_PATH = "sample/py/06_julia_parameter_sweep.py";
/** 埋め込み Python ソースコード。 */
const PYTRA_SOURCE_CODE = `# 06: ジュリア集合のパラメータを回してGIF出力するサンプル。

from __future__ import annotations

import math
from time import perf_counter

from py_module.gif_helper import save_gif


def julia_palette() -> bytes:
    # 先頭色は集合内部用に黒固定、残りは高彩度グラデーションを作る。
    palette = bytearray(256 * 3)
    palette[0] = 0
    palette[1] = 0
    palette[2] = 0
    for i in range(1, 256):
        t = (i - 1) / 254.0
        r = int(255.0 * (9.0 * (1.0 - t) * t * t * t))
        g = int(255.0 * (15.0 * (1.0 - t) * (1.0 - t) * t * t))
        b = int(255.0 * (8.5 * (1.0 - t) * (1.0 - t) * (1.0 - t) * t))
        palette[i * 3 + 0] = r
        palette[i * 3 + 1] = g
        palette[i * 3 + 2] = b
    return bytes(palette)


def render_frame(width: int, height: int, cr: float, ci: float, max_iter: int, phase: int) -> bytes:
    frame = bytearray(width * height)
    idx = 0
    for y in range(height):
        zy0 = -1.2 + 2.4 * (y / (height - 1))
        for x in range(width):
            zx = -1.8 + 3.6 * (x / (width - 1))
            zy = zy0
            i = 0
            while i < max_iter:
                zx2 = zx * zx
                zy2 = zy * zy
                if zx2 + zy2 > 4.0:
                    break
                zy = 2.0 * zx * zy + ci
                zx = zx2 - zy2 + cr
                i += 1
            if i >= max_iter:
                frame[idx] = 0
            else:
                # フレーム位相を少し加えて色が滑らかに流れるようにする。
                color_index = 1 + (((i * 224) // max_iter + phase) % 255)
                frame[idx] = color_index
            idx += 1
    return bytes(frame)


def run_06_julia_parameter_sweep() -> None:
    width = 320
    height = 240
    frames_n = 72
    max_iter = 180
    out_path = "sample/out/06_julia_parameter_sweep.gif"

    start = perf_counter()
    frames: list[bytes] = []
    # 既知の見栄えが良い近傍を楕円軌道で巡回し、単調な白飛びを抑える。
    center_cr = -0.745
    center_ci = 0.186
    radius_cr = 0.12
    radius_ci = 0.10
    for i in range(frames_n):
        t = i / frames_n
        angle = 2.0 * math.pi * t
        cr = center_cr + radius_cr * math.cos(angle)
        ci = center_ci + radius_ci * math.sin(angle)
        phase = (i * 5) % 255
        frames.append(render_frame(width, height, cr, ci, max_iter, phase))

    save_gif(out_path, width, height, frames, julia_palette(), delay_cs=8, loop=0)
    elapsed = perf_counter() - start
    print("output:", out_path)
    print("frames:", frames_n)
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_06_julia_parameter_sweep()
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
