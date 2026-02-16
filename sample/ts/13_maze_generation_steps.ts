// このファイルは自動生成です（Python -> TypeScript）。

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync, SpawnSyncReturns } from "node:child_process";

/** 埋め込み元 Python ファイルパス。 */
const PYTRA_SOURCE_PATH: string = "sample/py/13_maze_generation_steps.py";
/** 埋め込み Python ソースコード。 */
const PYTRA_SOURCE_CODE: string = `# 13: DFS迷路生成の進行状況をGIF出力するサンプル。

from __future__ import annotations

from time import perf_counter

from py_module.gif_helper import grayscale_palette, save_gif


def capture(grid: list[list[int]], w: int, h: int, scale: int) -> bytes:
    width = w * scale
    height = h * scale
    frame = bytearray(width * height)
    for y in range(h):
        for x in range(w):
            v = 255 if grid[y][x] == 0 else 40
            for yy in range(scale):
                base = (y * scale + yy) * width + x * scale
                for xx in range(scale):
                    frame[base + xx] = v
    return bytes(frame)


def run_13_maze_generation_steps() -> None:
    # 実行時間を十分に確保するため、迷路サイズと描画解像度を上げる。
    cell_w = 89
    cell_h = 67
    scale = 5
    capture_every = 20
    out_path = "sample/out/13_maze_generation_steps.gif"

    start = perf_counter()
    grid: list[list[int]] = []
    for _ in range(cell_h):
        row: list[int] = []
        for _ in range(cell_w):
            row.append(1)
        grid.append(row)
    stack: list[tuple[int, int]] = [(1, 1)]
    grid[1][1] = 0

    dirs: list[tuple[int, int]] = [(2, 0), (-2, 0), (0, 2), (0, -2)]
    frames: list[bytes] = []
    step = 0

    while len(stack) > 0:
        last_index = len(stack) - 1
        x, y = stack[last_index]
        candidates: list[tuple[int, int, int, int]] = []
        for k in range(4):
            dx, dy = dirs[k]
            nx = x + dx
            ny = y + dy
            if nx >= 1 and nx < cell_w - 1 and ny >= 1 and ny < cell_h - 1 and grid[ny][nx] == 1:
                if dx == 2:
                    candidates.append((nx, ny, x + 1, y))
                elif dx == -2:
                    candidates.append((nx, ny, x - 1, y))
                elif dy == 2:
                    candidates.append((nx, ny, x, y + 1))
                else:
                    candidates.append((nx, ny, x, y - 1))

        if len(candidates) == 0:
            stack.pop()
        else:
            sel = candidates[(x * 17 + y * 29 + len(stack) * 13) % len(candidates)]
            nx, ny, wx, wy = sel
            grid[wy][wx] = 0
            grid[ny][nx] = 0
            stack.append((nx, ny))

        if step % capture_every == 0:
            frames.append(capture(grid, cell_w, cell_h, scale))
        step += 1

    frames.append(capture(grid, cell_w, cell_h, scale))
    save_gif(out_path, cell_w * scale, cell_h * scale, frames, grayscale_palette(), delay_cs=4, loop=0)
    elapsed = perf_counter() - start
    print("output:", out_path)
    print("frames:", len(frames))
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_13_maze_generation_steps()
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
