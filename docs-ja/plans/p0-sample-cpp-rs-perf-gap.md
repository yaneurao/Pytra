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

S1 固定化（差分表自動抽出）:
- 抽出コマンド: `python3 tools/report_cpp_rs_gap.py --readme readme.md --top 8 --emit-json work/perf/cpp_rs_gap_readme_20260226.json`
- Rust が遅い外れ値（`rs/cpp >= 2.0`）: `09` / `18` / `01`
- Rust が速い外れ値（`cpp/rs >= 2.0`）: `11` / `12` / `16` / `13` / `14` / `10` / `15`
- S2/S3 は上記 10 ケースを優先対象として改善する。

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

計測プロトコル（S1-02）:
1. 入力固定:
   - 対象は `sample/py` 18 件固定（`__init__` 除外）。
   - 計測対象は `cpp` と `rs` のみ。
2. ビルド条件固定:
   - C++: `g++ -std=c++20 -O2`。
   - Rust: `rustc -O`。
   - 両言語とも「同一ソースから fresh transpile」した生成物を使う。
3. 実行計測:
   - 1 回 warmup 実行後、5 回本計測する。
   - 各回はバイナリ実行時間ではなく、プログラムが出力する `elapsed_sec` を採用する（コンパイル時間は除外）。
   - ケースごとの代表値は中央値（median）を採用する。
4. 受け入れ判定:
   - parity（stdout/artefact）は `runtime_parity_check` + `verify_sample_outputs` で別途保証する。
   - 乖離判定は `max(cpp/rs, rs/cpp)` を使い、外れ値閾値は `> 1.5x` とする。
5. 記録:
   - 結果は JSON と Markdown で保存し、README（日英）へ反映する。
   - 反映時は「計測日」「マシン/ツールチェイン」「warmup/repeat/中央値」を文書に明記する。

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
- 2026-02-26: `P0-SAMPLE-CPP-RS-PERF-01-S1-01` として `tools/report_cpp_rs_gap.py` を追加し、README 表から C++/Rust 差分表を自動抽出する導線を固定した。抽出結果より優先外れ値を `01/09/10/11/12/13/14/15/16/18` に確定した。
- 2026-02-26: `P0-SAMPLE-CPP-RS-PERF-01-S1-02` として計測プロトコル（fresh transpile, warmup=1, repeat=5, median, compile時間除外, parity分離検証）を文書化した。
- 2026-02-26: `P0-SAMPLE-CPP-RS-PERF-01-S2-01` として Rust runtime 呼び出しの `save_gif`/`write_rgb_png` を借用渡しへ変更し、call lower の media 特例から不要 clone を除去した。`/tmp/rs_01.rs` で `write_rgb_png(&(out_path), ..., &(pixels))`、`/tmp/rs_09.rs` で `save_gif(&(out_path), ..., &(frames), &(fire_palette()), ...)` を確認。検証は `python3 tools/runtime_parity_check.py --case-root sample --targets rs,cpp --ignore-unstable-stdout 01_mandelbrot 09_fire_simulation 11_lissajous_particles 16_glass_sculpture_chaos`（`pass=4 fail=0`）と `python3 tools/check_py2rs_transpile.py`（`checked=132 ok=132 fail=0 skipped=6`）を使用した。
- 2026-02-26: `P0-SAMPLE-CPP-RS-PERF-01-S2-02` として Rust emitter の list subscript read を copy 型判定付きに変更し、`list[int|float|bool|char|usize|isize]` 要素では clone しないようにした。`09_fire_simulation` の再生成コードで `a/b/c/d` と `frame[idx]` 代入時の末端要素 clone が消えていることを確認し、`python3 tools/check_py2rs_transpile.py`（`checked=132 ok=132 fail=0 skipped=6`）および `python3 tools/runtime_parity_check.py --case-root sample --targets rs,cpp --ignore-unstable-stdout 09_fire_simulation 18_mini_language_interpreter`（`pass=2 fail=0`）で回帰なしを確認した。
- 2026-02-26: `P0-SAMPLE-CPP-RS-PERF-01-S2-03` として string 比較で定数側を `&str` に落とし、`to_string` 二重適用を抑止する helper（`_ensure_string_owned`）を導入した。`18_mini_language_interpreter` の再生成コードで `if ch == \" \"/\"+\"/...` へ簡約され、`to_string(` 出現数は `174 -> 135` に低減した。検証は `python3 tools/check_py2rs_transpile.py`（`checked=132 ok=132 fail=0 skipped=6`）と `python3 tools/runtime_parity_check.py --case-root sample --targets rs,cpp --ignore-unstable-stdout 09_fire_simulation 18_mini_language_interpreter`（`pass=2 fail=0`）を使用した。
