// fallback: function has unsupported annotation in native Rust mode: run_pi_trial
// このファイルは自動生成です。編集しないでください。
// 入力 Python: 04_monte_carlo_pi.py

#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;

fn main() {
    let source: &str = r#"# 10: モンテカルロ法で円周率を推定するサンプルです。
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
    samples: int = 18000000
    seed: int = 123456789

    start: float = perf_counter()
    pi_est: float = run_pi_trial(samples, seed)
    elapsed: float = perf_counter() - start

    print("samples:", samples)
    print("pi_estimate:", pi_est)
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_monte_carlo_pi()
"#;
    std::process::exit(py_runtime::run_embedded_python(source));
}
