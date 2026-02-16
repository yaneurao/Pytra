// このファイルは自動生成です（Python -> TypeScript）。

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync, SpawnSyncReturns } from "node:child_process";

/** 埋め込み元 Python ファイルパス。 */
const PYTRA_SOURCE_PATH: string = "sample/py/04_monte_carlo_pi.py";
/** 埋め込み Python ソースコード。 */
const PYTRA_SOURCE_CODE: string = `# 10: モンテカルロ法で円周率を推定するサンプルです。
# import random を使わず、LCG を自前実装してトランスパイル互換性を高めています。

from time import perf_counter


def lcg_next(state: int) -> int:
    # 32bit LCG
    return (1664525 * state + 1013904223) % 4294967296


def run_pi_trial(total_samples: int, seed: int) -> float:
    inside: int = 0
    state: int = seed

    for _ in range(total_samples):
        state = lcg_next(state)
        x: float = state / 4294967296.0

        state = lcg_next(state)
        y: float = state / 4294967296.0

        dx: float = x - 0.5
        dy: float = y - 0.5
        if dx * dx + dy * dy <= 0.25:
            inside += 1

    return 4.0 * inside / total_samples


def run_monte_carlo_pi() -> None:
    samples: int = 54000000
    seed: int = 123456789

    start: float = perf_counter()
    pi_est: float = run_pi_trial(samples, seed)
    elapsed: float = perf_counter() - start

    print("samples:", samples)
    print("pi_estimate:", pi_est)
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_monte_carlo_pi()
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
