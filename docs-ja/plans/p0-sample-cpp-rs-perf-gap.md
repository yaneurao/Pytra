# P0: sample C++/Rust 実行時間乖離の是正

最終更新: 2026-02-26

関連 TODO:
- `docs-ja/todo/index.md` の `ID: P0-SAMPLE-CPP-RS-PERF-01`

背景:
- `readme.md` / `readme-ja.md` の sample 計測表で、C++ と Rust の実行時間差が一部ケースで 3x 前後まで開いている。
- 変換対象は同一 Python ソースであり、言語差はあっても極端な差分はボトルネック偏在を示す可能性が高い。
- 現状の値（2026-02-26 時点）では、Rust 側が遅いケースと C++ 側が遅いケースが混在しており、単純なコンパイラ最適化差だけでは説明できない。

現状分析（2026-02-26）:
- Rust が遅い外れ値:
  - `09_fire_simulation`: `cpp=2.114s`, `rs=7.342s`（`rs/cpp=3.47`）
  - `18_mini_language_interpreter`: `cpp=0.424s`, `rs=1.216s`（`rs/cpp=2.87`）
  - `01_mandelbrot`: `cpp=0.277s`, `rs=0.735s`（`rs/cpp=2.65`）
- Rust が速い外れ値:
  - `11_lissajous_particles`: `cpp/rs=3.90`
  - `12_sort_visualizer`: `cpp/rs=3.81`
  - `13_maze_generation_steps`: `cpp/rs=3.61`
  - `16_glass_sculpture_chaos`: `cpp/rs=3.65`
- Rust emitter の所有権安全側実装が、ホットループで clone を過剰生成している。
  - call 引数 clone 規則: `src/hooks/rs/emitter/rs_emitter.py` の `_clone_owned_call_args` / `save_gif,write_rgb_png` 特例。
  - subscript 読み取り clone 規則: `src/hooks/rs/emitter/rs_emitter.py` の `owner_t.startswith("list[") -> clone`。
- C++ 側は GIF/PNG runtime が互換レイヤ経由で `py_to_int64`/`py_len`/`py_slice` を多用し、画像系ケースで変換コストが支配しやすい。
  - `src/runtime/cpp/pytra-gen/utils/gif.cpp`
  - `src/runtime/cpp/pytra-gen/utils/png.cpp`
- 計測値自体は README に反映済みだが、再現プロトコル（反復回数/中央値採用/コンパイル時間除外）が文書として固定されていない。

目的:
- C++/Rust の実行時間差を「外れ値が出ない状態」まで縮小する。
- clone/互換変換コストなど、コード生成で回避可能なオーバーヘッドを優先的に除去する。
- 再計測手順と判定基準を固定し、以後の回帰で差分を追跡可能にする。

対象:
- Rust emitter: `src/hooks/rs/emitter/rs_emitter.py`
- C++ runtime（GIF/PNG）: `src/runtime/cpp/pytra-gen/utils/gif.cpp`, `src/runtime/cpp/pytra-gen/utils/png.cpp`
- C++ 生成経路のフレームコピー箇所（`sample` 主要ケース）
- 計測手順の文書化と README 表更新

非対象:
- Python sample アルゴリズム自体の仕様変更
- C++/Rust 以外の言語最適化
- CPU 依存最適化（`-march=native` 等）を前提にした局所チューニング

改善方針:
1. Rust 側の不要 clone/to_string を先に削る。
2. C++ GIF/PNG runtime の互換レイヤ経由を縮小し、typed fast-path を追加する。
3. 計測プロトコルを固定し、差分を数値で判定する。

受け入れ基準:
- `sample/py` 18 件を C++/Rust で再計測し、結果と手順が文書化される。
- 現状で 2x 以上開いている外れ値（`01/09/11/12/13/16/18`）をすべて `<= 1.5x` に縮小する。
- 出力整合（stdout + artefact hash/size）が維持される。
- README（日英）の計測表が最新値へ更新される。

実行コマンド（基準）:
- `python3 tools/runtime_parity_check.py --case-root sample --targets cpp,rs --all-samples --ignore-unstable-stdout`
- `python3 tools/verify_sample_outputs.py --targets cpp,rs`
- （再計測スクリプト導入後）`python3 tools/benchmark_sample_cpp_rs.py --repeat 5 --warmup 1 --emit-json ...`

## 分解

- [ ] [ID: P0-SAMPLE-CPP-RS-PERF-01-S1-01] 現行 README 値の C++/Rust 差分表（比率順）を自動抽出し、外れ値ケースを固定する。
- [ ] [ID: P0-SAMPLE-CPP-RS-PERF-01-S1-02] 再現可能な計測プロトコル（warmup/repeat/中央値、コンパイル時間の扱い）を文書化する。
- [ ] [ID: P0-SAMPLE-CPP-RS-PERF-01-S2-01] Rust emitter の `save_gif`/`write_rgb_png` 呼び出しで不要な所有権 clone を除去する。
- [ ] [ID: P0-SAMPLE-CPP-RS-PERF-01-S2-02] Rust emitter の list subscript read で、コピー不要型（`i64/f64/bool/u8`）の clone を抑止する。
- [ ] [ID: P0-SAMPLE-CPP-RS-PERF-01-S2-03] Rust emitter の文字列比較/トークナイズ経路で `to_string()` 連鎖を削減する。
- [ ] [ID: P0-SAMPLE-CPP-RS-PERF-01-S2-04] `01/09/18` を再計測し、Rust 側改善の寄与をケース別に記録する。
- [ ] [ID: P0-SAMPLE-CPP-RS-PERF-01-S3-01] C++ GIF runtime に `py_slice`/`py_len`/`py_to_int64` 依存を減らす fast-path を追加する。
- [ ] [ID: P0-SAMPLE-CPP-RS-PERF-01-S3-02] C++ PNG runtime の scanline/chunk 処理を typed 操作中心へ寄せる。
- [ ] [ID: P0-SAMPLE-CPP-RS-PERF-01-S3-03] `11/12/13/16` を再計測し、C++ 側改善の寄与をケース別に記録する。
- [ ] [ID: P0-SAMPLE-CPP-RS-PERF-01-S4-01] `sample` 生成コードのフレーム二重コピー（例: `bytes(bytes(frame))`）を削減する方針を実装に反映する。
- [ ] [ID: P0-SAMPLE-CPP-RS-PERF-01-S4-02] 出力 parity を維持したまま高速化できることを `runtime_parity_check`/`verify_sample_outputs` で確認する。
- [ ] [ID: P0-SAMPLE-CPP-RS-PERF-01-S5-01] C++/Rust 18 件の再計測結果を `readme.md` / `readme-ja.md` へ反映する。
- [ ] [ID: P0-SAMPLE-CPP-RS-PERF-01-S5-02] 乖離が残るケースは「未解消要因」と次の打ち手を文書へ追記する。

決定ログ:
- 2026-02-26: `P0-SAMPLE-CPP-RS-PERF-01` を最優先で新設。外れ値は Rust clone/to_string 過多と C++ GIF/PNG 互換レイヤ負荷の双方で発生しており、片側最適化だけでは収束しないため、Rust/C++ 両面で段階是正する。
