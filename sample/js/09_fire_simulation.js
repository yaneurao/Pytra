// このファイルは自動生成です（Python -> JavaScript）。

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

/** 埋め込み元 Python ファイルパス。 */
const PYTRA_SOURCE_PATH = "sample/py/09_fire_simulation.py";
/** 埋め込み Python ソースコード。 */
const PYTRA_SOURCE_CODE = `# 09: 簡易ファイアエフェクトをGIF出力するサンプル。

from __future__ import annotations

from time import perf_counter

from py_module.gif_helper import save_gif


def fire_palette() -> bytes:
    p = bytearray()
    for i in range(256):
        r = 0
        g = 0
        b = 0
        if i < 85:
            r = i * 3
            g = 0
            b = 0
        elif i < 170:
            r = 255
            g = (i - 85) * 3
            b = 0
        else:
            r = 255
            g = 255
            b = (i - 170) * 3
        p.append(r)
        p.append(g)
        p.append(b)
    return bytes(p)


def run_09_fire_simulation() -> None:
    w = 380
    h = 260
    steps = 420
    out_path = "sample/out/09_fire_simulation.gif"

    start = perf_counter()
    heat: list[list[int]] = []
    for _ in range(h):
        row: list[int] = []
        for _ in range(w):
            row.append(0)
        heat.append(row)
    frames: list[bytes] = []

    for t in range(steps):
        for x in range(w):
            val = 170 + ((x * 13 + t * 17) % 86)
            heat[h - 1][x] = val

        for y in range(1, h):
            for x in range(w):
                a = heat[y][x]
                b = heat[y][(x - 1 + w) % w]
                c = heat[y][(x + 1) % w]
                d = heat[(y + 1) % h][x]
                v = (a + b + c + d) // 4
                cool = 1 + ((x + y + t) % 3)
                nv = v - cool
                heat[y - 1][x] = nv if nv > 0 else 0

        frame = bytearray(w * h)
        i = 0
        for yy in range(h):
            for xx in range(w):
                frame[i] = heat[yy][xx]
                i += 1
        frames.append(bytes(frame))

    save_gif(out_path, w, h, frames, fire_palette(), delay_cs=4, loop=0)
    elapsed = perf_counter() - start
    print("output:", out_path)
    print("frames:", steps)
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_09_fire_simulation()
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
