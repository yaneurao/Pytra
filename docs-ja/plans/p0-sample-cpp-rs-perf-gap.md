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
- 2026-02-26: `P0-SAMPLE-CPP-RS-PERF-01-S2-04` として `python3 tools/benchmark_sample_cpp_rs.py 01_mandelbrot 09_fire_simulation 18_mini_language_interpreter --warmup 1 --repeat 5 --emit-json work/perf/cpp_rs_s2_04_20260226.json` を実行し、Rust 側改善寄与を再計測した（中央値）。結果は `01: cpp=0.188 rs=0.750`, `09: cpp=2.075 rs=7.349`, `18: cpp=0.343 rs=1.088`。README 基準値比で Rust は `01:+2.0%`, `09:+0.1%`, `18:-10.5%` と改善が局所的で、比率改善には S3（C++ runtime 側）と S4（frame copy 削減）の継続が必要と判断した。
- 2026-02-26: `P0-SAMPLE-CPP-RS-PERF-01-S3-01` として `src/runtime/cpp/pytra-gen/utils/gif.cpp` に typed fast-path を導入し、GIF hot path から `py_to_int64`/`py_slice`/`py_len` 依存を除去した（カウントはいずれも `0`）。検証は `python3 tools/runtime_parity_check.py --case-root sample --targets cpp --ignore-unstable-stdout 09_fire_simulation 11_lissajous_particles 12_sort_visualizer 16_glass_sculpture_chaos`（`pass=4 fail=0`）で実施した。
- 2026-02-26: `P0-SAMPLE-CPP-RS-PERF-01-S3-02` として `src/runtime/cpp/pytra-gen/utils/png.cpp` に typed fast-path を導入し、PNG hot path から `py_to_int64`/`py_slice`/`py_len` 依存を除去した（カウントはいずれも `0`）。検証は `python3 tools/runtime_parity_check.py --case-root sample --targets cpp --ignore-unstable-stdout 01_mandelbrot 03_julia_set 04_orbit_trap_julia`（`pass=3 fail=0`）で実施した。
- 2026-02-26: `P0-SAMPLE-CPP-RS-PERF-01-S3-03` として `python3 tools/benchmark_sample_cpp_rs.py 11_lissajous_particles 12_sort_visualizer 13_maze_generation_steps 16_glass_sculpture_chaos --warmup 1 --repeat 5 --emit-json work/perf/cpp_rs_s3_03_20260226.json` を実行し、C++ 側改善寄与を再計測した（中央値）。結果は `11: cpp=1.335 rs=0.329`, `12: cpp=1.301 rs=0.332`, `13: cpp=1.059 rs=0.279`, `16: cpp=0.915 rs=0.229`。README 基準値比で C++ は `11:-2.3%`, `12:-0.8%`, `13:-0.6%`, `16:+8.5%` と改善量が小さく、比率ギャップ解消には S4（生成コード側コピー削減）を優先する。
- 2026-02-26: `P0-SAMPLE-CPP-RS-PERF-01-S4-01` として `src/hooks/cpp/emitter/cpp_emitter.py` の `list[T].append` 型合わせで `T=bytes` かつ引数も `bytes` の場合は再コンストラクタを抑止し、`bytes(bytes(frame))` を `bytes(frame)` へ削減した。`python3 src/py2cpp.py sample/py/{09,10,11,14,15}_*.py -o /tmp/pytra_s4_check/*.cpp` で `frames.append(bytes(frame));` を確認し、`python3 tools/check_py2cpp_transpile.py`（`checked=133 ok=133 fail=0 skipped=6`）で回帰なしを確認した。
- 2026-02-26: `P0-SAMPLE-CPP-RS-PERF-01-S4-02` として `python3 tools/runtime_parity_check.py --case-root sample --targets cpp,rs --all-samples --ignore-unstable-stdout` を実行し、`cases=18 pass=18 fail=0` を確認した。`verify_sample_outputs.py` は既定 manifest でも `/tmp` 再生成 manifest（`--golden-manifest /tmp/pytra_s4_verify_manifest.json --refresh-golden --refresh-golden-only`）でも `01/02/03/04/06/12/14/16` が `artifact hash mismatch` となったため既存の C++ vs Python 差分を示す。今回変更影響ケースは前コミット（`f5a319c7`）比較で `09/10/11/15=OK, 14=NG` と一致し、`S4-01` で不一致集合が増えていないことを確認した。
- 2026-02-26: `P0-SAMPLE-CPP-RS-PERF-01-S5-01` として `python3 tools/benchmark_sample_cpp_rs.py --warmup 1 --repeat 5 --emit-json work/perf/cpp_rs_s5_01_20260226.json` を実行し、18件の中央値を `readme.md` / `readme-ja.md` へ反映した。主要値は `01: cpp=0.188 rs=0.771`, `09: cpp=2.047 rs=7.330`, `11: cpp=1.336 rs=0.338`, `16: cpp=0.892 rs=0.226`, `18: cpp=0.326 rs=1.117`。
- 2026-02-26: `P0-SAMPLE-CPP-RS-PERF-01-S5-02` として再計測結果の未解消乖離を文書化した。`>1.5x` は Rust遅延側 `01/04/09/18`、C++遅延側 `07/10/11/12/13/14/15/16`。次アクションは (1) Rust `01/04/18` の PNG/文字列処理 hot path で clone/to_string/境界変換を削減、(2) C++ `07/10/11/12/13/14/15/16` の GIF encode で palette/index/LZW 経路の追加 flatten を実施、(3) 各群で `benchmark_sample_cpp_rs.py` をケース固定で再測定して寄与を段階確認する。
- 2026-02-26: `P0-SAMPLE-CPP-RS-PERF-01-S6-01` として C++ runtime の byte コピー経路を追加最適化した。`src/runtime/cpp/pytra-core/built_in/list.h` で `extend(const list<T>&)` を range insert 化し、`src/runtime/cpp/pytra-gen/utils/gif.cpp` の圧縮チャンク書き出しと `src/runtime/cpp/pytra-gen/utils/png.cpp` の scanline 組み立てを `insert` ベースへ変更した。検証は `python3 tools/runtime_parity_check.py --case-root sample --targets cpp --ignore-unstable-stdout 01_mandelbrot 03_julia_set 04_orbit_trap_julia 09_fire_simulation 11_lissajous_particles 12_sort_visualizer 13_maze_generation_steps 14_raymarching_light_cycle 15_wave_interference_loop 16_glass_sculpture_chaos`（`pass=10 fail=0`）で実施した。
- 2026-02-26: `P0-SAMPLE-CPP-RS-PERF-01-S6-02` として `python3 tools/benchmark_sample_cpp_rs.py 01_mandelbrot 03_julia_set 04_orbit_trap_julia 09_fire_simulation 11_lissajous_particles 12_sort_visualizer 13_maze_generation_steps 14_raymarching_light_cycle 15_wave_interference_loop 16_glass_sculpture_chaos 18_mini_language_interpreter --warmup 1 --repeat 5 --emit-json work/perf/cpp_rs_s6_01_20260226.json` を実行した。S5 比で C++ 中央値は `01:-0.010`, `03:-0.042`, `04:-0.022`, `09:-0.025`, `11:-0.048`, `12:-0.024`, `13:-0.006`, `14:-0.007`, `15:-0.012` と改善し、`16:+0.003`, `18:+0.010` は誤差域で横ばい。外れ値条件（`>1.5x`）はなお未解消で、次段は Rust側 `01/04/18` と C++側 GIF encode の追加分解が必要と判断した。
- 2026-02-26: `P0-SAMPLE-CPP-RS-PERF-01-S7-01` として `src/hooks/rs/emitter/rs_emitter.py` の `for` lower / `Subscript` 描画を更新し、`enumerate(...)` の外側 clone 付与を停止、かつ nested subscript (`a[b][c]`) で中間 `list` clone を避ける経路を追加した。再生成コード確認では `09_fire_simulation` の `clone(` 出現が `12 -> 2`、`18_mini_language_interpreter` は `13 -> 12` に低減した。検証は `python3 tools/check_py2rs_transpile.py`（`checked=132 ok=132 fail=0 skipped=6`）と `python3 tools/runtime_parity_check.py --case-root sample --targets rs,cpp --ignore-unstable-stdout 01_mandelbrot 04_orbit_trap_julia 09_fire_simulation 18_mini_language_interpreter`（`pass=4 fail=0`）および `python3 tools/runtime_parity_check.py --case-root sample --targets rs --all-samples --ignore-unstable-stdout`（`cases=18 pass=18 fail=0`）で実施した。
- 2026-02-26: `P0-SAMPLE-CPP-RS-PERF-01-S7-02` として `python3 tools/benchmark_sample_cpp_rs.py 01_mandelbrot 04_orbit_trap_julia 09_fire_simulation 18_mini_language_interpreter --warmup 1 --repeat 5 --emit-json work/perf/cpp_rs_s7_01_20260226.json` を実行した。S6 比で中央値は `01: cpp=0.177 rs=0.735 (4.15x)`, `04: cpp=0.187 rs=0.337 (1.80x)`, `09: cpp=2.009 rs=0.625 (0.31x)`, `18: cpp=0.332 rs=1.101 (3.32x)`。`09` は Rust clone 抑止で `rs=-6.687s` と大幅改善した一方、`01/18` の Rust 遅延と `09` の逆転乖離（C++ 遅延）が残るため、次段は C++ GIF encode の追加短縮と Rust `str` 比較/辞書アクセス hot path 分解を優先する。
- 2026-02-26: （試行のみ）C++ GIF runtime で `_lzw_encode` の emit ループ共通化と `py_int_to_bytes` 置換を実装し、`python3 tools/runtime_parity_check.py --case-root sample --targets cpp --all-samples --ignore-unstable-stdout`（`cases=18 pass=18 fail=0`）および `python3 tools/benchmark_sample_cpp_rs.py 09_fire_simulation 10_plasma_effect 11_lissajous_particles 12_sort_visualizer 13_maze_generation_steps 14_raymarching_light_cycle 15_wave_interference_loop 16_glass_sculpture_chaos --warmup 1 --repeat 5 --emit-json work/perf/cpp_rs_s8_01_20260226.json` を実行したが、有意な改善が確認できなかったため差分は revert した。
- 2026-02-26: `P0-SAMPLE-CPP-RS-PERF-01-S8-01` として `src/hooks/rs/emitter/rs_emitter.py` で `Subscript -> Attribute` の二重 clone を抑止し、`Compare(==/!=)` の文字列定数比較をリテラル優先へ変更した。再生成コードで `18_mini_language_interpreter` の `clone(` は `12 -> 11`、`to_string(` は `135 -> 125` に低減した。検証は `python3 tools/check_py2rs_transpile.py`（`checked=132 ok=132 fail=0 skipped=6`）と `python3 tools/runtime_parity_check.py --case-root sample --targets rs,cpp --ignore-unstable-stdout 01_mandelbrot 04_orbit_trap_julia 09_fire_simulation 18_mini_language_interpreter`（`pass=4 fail=0`）および `python3 tools/runtime_parity_check.py --case-root sample --targets rs --all-samples --ignore-unstable-stdout`（`cases=18 pass=18 fail=0`）で実施した。
- 2026-02-26: `P0-SAMPLE-CPP-RS-PERF-01-S8-02` として `python3 tools/benchmark_sample_cpp_rs.py 01_mandelbrot 04_orbit_trap_julia 09_fire_simulation 18_mini_language_interpreter --warmup 1 --repeat 5 --emit-json work/perf/cpp_rs_s8_02_20260226.json` を実行した。S7 比で中央値は `01: cpp=0.178 rs=0.735 (4.12x)`, `04: cpp=0.191 rs=0.339 (1.77x)`, `09: cpp=2.045 rs=0.612 (0.30x)`, `18: cpp=0.331 rs=0.994 (3.00x)`。`18` は `rs=-0.107s` 改善したが、外れ値閾値（`>1.5x`）は依然として `01/04/09/18` で未解消。
- 2026-02-26: `P0-SAMPLE-CPP-RS-PERF-01-S9-01` として `src/hooks/rs/emitter/rs_emitter.py` に `bytearray()/bytes()` 空初期化の容量推定 helper（`_infer_byte_buffer_capacity_expr` / `_maybe_render_preallocated_byte_buffer_init`）を追加し、`pixels` などの初期化で `Vec::<u8>::with_capacity(...)` を自動出力するようにした。`01_mandelbrot` / `04_orbit_trap_julia` の再生成コードで `let mut pixels: Vec<u8> = Vec::<u8>::with_capacity((width * height * 3) as usize);` を確認した。検証は `python3 tools/check_py2rs_transpile.py`（`checked=132 ok=132 fail=0 skipped=6`）と `python3 tools/runtime_parity_check.py --case-root sample --targets rs,cpp --ignore-unstable-stdout 01_mandelbrot 04_orbit_trap_julia 09_fire_simulation 18_mini_language_interpreter`（`pass=4 fail=0`）および `python3 tools/runtime_parity_check.py --case-root sample --targets rs --all-samples --ignore-unstable-stdout`（`cases=18 pass=18 fail=0`）で実施した。
- 2026-02-26: `P0-SAMPLE-CPP-RS-PERF-01-S9-02` として `python3 tools/benchmark_sample_cpp_rs.py 01_mandelbrot 04_orbit_trap_julia 09_fire_simulation 18_mini_language_interpreter --warmup 1 --repeat 5 --emit-json work/perf/cpp_rs_s9_01_20260226.json` を実行した。S8 比で中央値は `01: cpp=0.178 rs=0.745 (4.19x)`, `04: cpp=0.195 rs=0.340 (1.74x)`, `09: cpp=2.057 rs=0.609 (0.30x)`, `18: cpp=0.328 rs=0.934 (2.85x)`。`18` はさらに `rs=-0.060s` 改善した一方、`01` は有意改善が出ず、外れ値閾値（`>1.5x`）は依然として `01/04/09/18` で未解消。
- 2026-02-26: `P0-SAMPLE-CPP-RS-PERF-01-S10-01` として `src/hooks/cpp/emitter/operator.py` の `Div` 分岐を修正し、`Path /` 以外の `/` を `py_div(lhs, rhs)` に統一した。これにより C++ 生成コードで `y/(height-1)` / `x/(width-1)` が `py_div(...)` へ置換され、`01/04` の整数除算寄り経路を解消した。検証は `python3 tools/check_py2cpp_transpile.py`（`checked=133 ok=133 fail=0 skipped=6`）、`python3 tools/runtime_parity_check.py --case-root sample --targets cpp,rs --ignore-unstable-stdout 01_mandelbrot 04_orbit_trap_julia 09_fire_simulation 18_mini_language_interpreter`（`pass=4 fail=0`）、`python3 tools/runtime_parity_check.py --case-root sample --targets cpp --all-samples --ignore-unstable-stdout`（`cases=18 pass=18 fail=0`）で実施した。
- 2026-02-26: `P0-SAMPLE-CPP-RS-PERF-01-S10-02` として `python3 tools/benchmark_sample_cpp_rs.py 01_mandelbrot 04_orbit_trap_julia 09_fire_simulation 18_mini_language_interpreter --warmup 1 --repeat 5 --emit-json work/perf/cpp_rs_s10_01_20260226.json` を実行した。S9 比で中央値は `01: cpp=0.837 rs=0.734 (0.88x)`, `04: cpp=0.452 rs=0.339 (0.75x)`, `09: cpp=2.069 rs=0.612 (0.30x)`, `18: cpp=0.334 rs=0.912 (2.74x)`。`01/04` は外れ値閾値（`>1.5x`）を解消した一方、未解消外れ値は `09`（C++遅延）と `18`（Rust遅延）に収束した。
- 2026-02-26: `P0-SAMPLE-CPP-RS-PERF-01-S11-01` として `src/hooks/rs/emitter/rs_emitter.py` を更新し、(1) `enumerate(list)` を `clone().into_iter()` から list 要素型に応じた `iter()/iter().copied()/iter().cloned()` へ切替、(2) `for x in list` でも同様に list 全体 clone を回避する経路を追加した。合わせて `dict[str,*]` lookup 系の key coercion を借用優先へ寄せるため `require_owned=False` 経路を導入した。`18_mini_language_interpreter` の再生成 Rust では `for (line_index, source) in (lines).iter().enumerate()` と `for stmt in (stmts).iter()` へ変換され、`clone(` 出現数は `12 -> 9` に低減した。検証は `python3 tools/check_py2rs_transpile.py`（`checked=132 ok=132 fail=0 skipped=6`）、`python3 tools/runtime_parity_check.py --case-root sample --targets cpp,rs --ignore-unstable-stdout 01_mandelbrot 04_orbit_trap_julia 09_fire_simulation 18_mini_language_interpreter`（`pass=4 fail=0`）、`python3 tools/runtime_parity_check.py --case-root sample --targets rs --all-samples --ignore-unstable-stdout`（`cases=18 pass=18 fail=0`）で実施した。
- 2026-02-26: `P0-SAMPLE-CPP-RS-PERF-01-S11-02` として `python3 tools/benchmark_sample_cpp_rs.py 01_mandelbrot 04_orbit_trap_julia 09_fire_simulation 18_mini_language_interpreter --warmup 1 --repeat 5 --emit-json work/perf/cpp_rs_s11_02_20260226.json` を実行した。S10 比の中央値は `01: cpp=0.835 rs=0.735 (0.88x)`, `04: cpp=0.451 rs=0.337 (0.75x)`, `09: cpp=2.060 rs=0.611 (0.30x)`, `18: cpp=0.335 rs=0.886 (2.64x)`。`18` は `rs=-0.026s`（約 `-2.9%`）改善したが外れ値閾値（`>1.5x`）は未解消で、未解消外れ値は引き続き `09`（C++遅延）/`18`（Rust遅延）。
- 2026-02-26: `P0-SAMPLE-CPP-RS-PERF-01-S12-01` として `src/hooks/rs/emitter/rs_emitter.py` の call lowering を更新し、class method でも引数の ref-mode を参照できるようにした。method 引数は `str` と collection 系のみを `&T` 対象に限定し、`str` は `&str` へ縮退。あわせて by-ref 引数描画 helper を追加し、文字列リテラル引数は直接 `"..."` を渡すようにした。`18_mini_language_interpreter` 再生成 Rust で `fn py_match(&mut self, kind: &str)` / `fn expect(&mut self, kind: &str)` と `self.py_match("LET")` 等を確認した。検証は `python3 tools/check_py2rs_transpile.py`（`checked=132 ok=132 fail=0 skipped=6`）、`python3 tools/runtime_parity_check.py --case-root sample --targets cpp,rs --ignore-unstable-stdout 01_mandelbrot 04_orbit_trap_julia 09_fire_simulation 18_mini_language_interpreter`（`pass=4 fail=0`）、`python3 tools/runtime_parity_check.py --case-root sample --targets rs --all-samples --ignore-unstable-stdout`（`cases=18 pass=18 fail=0`）で実施した。
- 2026-02-26: `P0-SAMPLE-CPP-RS-PERF-01-S12-02` として `python3 tools/benchmark_sample_cpp_rs.py 01_mandelbrot 04_orbit_trap_julia 09_fire_simulation 18_mini_language_interpreter --warmup 1 --repeat 5 --emit-json work/perf/cpp_rs_s12_01_20260226.json` を実行した。S11 比の中央値は `01: cpp=0.832 rs=0.737 (0.89x)`, `04: cpp=0.451 rs=0.341 (0.75x)`, `09: cpp=2.051 rs=0.609 (0.30x)`, `18: cpp=0.342 rs=0.888 (2.60x)`。`18` は速度自体は横ばいだが比率は `2.64x -> 2.60x` へ微減し、未解消外れ値は引き続き `09`（C++遅延）/`18`（Rust遅延）。
- 2026-02-26: `P0-SAMPLE-CPP-RS-PERF-01-S13-01` として `src/runtime/cpp/pytra-gen/utils/gif.cpp` を更新し、(1) `_append_u16_le` helper で `py_int_to_bytes(..., 2, "little")` 呼び出しを直接 `bytearray.append` へ置換、(2) `_lzw_encode` と `save_gif` に `reserve` を導入して再確保を抑止した。検証は `python3 tools/check_py2cpp_transpile.py`（`checked=133 ok=133 fail=0 skipped=6`）および `python3 tools/runtime_parity_check.py --case-root sample --targets cpp --ignore-unstable-stdout 09_fire_simulation 10_plasma_effect 11_lissajous_particles 16_glass_sculpture_chaos`（`cases=4 pass=4 fail=0`）で実施した。
- 2026-02-26: `P0-SAMPLE-CPP-RS-PERF-01-S13-02` として `python3 tools/benchmark_sample_cpp_rs.py 01_mandelbrot 04_orbit_trap_julia 09_fire_simulation 18_mini_language_interpreter --warmup 1 --repeat 5 --emit-json work/perf/cpp_rs_s13_01_20260226.json` を実行した。S12 比の中央値は `01: cpp=0.837 rs=0.735 (0.88x)`, `04: cpp=0.450 rs=0.345 (0.77x)`, `09: cpp=2.042 rs=0.608 (0.30x)`, `18: cpp=0.328 rs=0.877 (2.67x)`。`09` は `cpp=-0.009s` と微改善だが外れ値閾値（`>1.5x`）は未解消で、未解消外れ値は引き続き `09`（C++遅延）/`18`（Rust遅延）。
- 2026-02-26: `P0-SAMPLE-CPP-RS-PERF-01-S14-01` として `src/hooks/rs/emitter/rs_emitter.py` 内の Rust runtime helper を更新し、`py_str_at/py_slice_str` で毎回 `Vec<char>` を構築する実装を撤去した。`str` が ASCII の場合は byte index 直処理、非ASCIIは `chars().nth()/char_indices()` fallback へ切替え、都度アロケーションを抑制した。検証は `python3 tools/check_py2rs_transpile.py`（`checked=132 ok=132 fail=0 skipped=6`）、`python3 tools/runtime_parity_check.py --case-root sample --targets cpp,rs --ignore-unstable-stdout 01_mandelbrot 04_orbit_trap_julia 09_fire_simulation 18_mini_language_interpreter`（`pass=4 fail=0`）、`python3 tools/runtime_parity_check.py --case-root sample --targets rs --all-samples --ignore-unstable-stdout`（`cases=18 pass=18 fail=0`）で実施した。
- 2026-02-26: `P0-SAMPLE-CPP-RS-PERF-01-S14-02` として `python3 tools/benchmark_sample_cpp_rs.py 01_mandelbrot 04_orbit_trap_julia 09_fire_simulation 18_mini_language_interpreter --warmup 1 --repeat 5 --emit-json work/perf/cpp_rs_s14_01_20260226.json` と `python3 tools/benchmark_sample_cpp_rs.py 18_mini_language_interpreter --warmup 1 --repeat 7 --emit-json work/perf/cpp_rs_s14_18_recheck_20260226.json` を実行した。S13 比の中央値は `01: cpp=0.841 rs=0.741 (0.88x)`, `04: cpp=0.453 rs=0.339 (0.75x)`, `09: cpp=2.034 rs=0.612 (0.30x)`, `18: cpp=0.327 rs=0.396 (1.21x)` で、`18` は `rs=0.877 -> 0.396`（約 `-54.8%`）へ大幅改善し外れ値閾値（`>1.5x`）を解消した。`18` 単体再計測でも `cpp=0.330 rs=0.390 (1.18x)` を確認し、未解消外れ値は `09`（C++遅延）へ収束。
- 2026-02-26: `P0-SAMPLE-CPP-RS-PERF-01-S15-01` として C++ core runtime を更新し、`src/runtime/cpp/pytra-core/built_in/list.h` に `data()` accessor を追加、`src/runtime/cpp/pytra-core/built_in/io.h` の `PyFile::write(const BytesLike&)` で contiguous 1byte 要素コンテナを `ofs_.write(...)` 一括書き込みする fast-path を導入した。検証は `python3 tools/check_py2cpp_transpile.py`（`checked=133 ok=133 fail=0 skipped=6`）および `python3 tools/runtime_parity_check.py --case-root sample --targets cpp --ignore-unstable-stdout 09_fire_simulation 10_plasma_effect 11_lissajous_particles 16_glass_sculpture_chaos`（`cases=4 pass=4 fail=0`）で実施した。
- 2026-02-26: `P0-SAMPLE-CPP-RS-PERF-01-S15-02` として `python3 tools/benchmark_sample_cpp_rs.py 01_mandelbrot 04_orbit_trap_julia 09_fire_simulation 18_mini_language_interpreter --warmup 1 --repeat 5 --emit-json work/perf/cpp_rs_s15_01_20260226.json` と `python3 tools/benchmark_sample_cpp_rs.py 01_mandelbrot 09_fire_simulation 18_mini_language_interpreter --warmup 1 --repeat 7 --emit-json work/perf/cpp_rs_s15_recheck_20260226.json` を実行した。S14 比の中央値は `01: cpp=0.748 rs=0.736 (0.98x)`, `04: cpp=0.360 rs=0.339 (0.94x)`, `09: cpp=0.583 rs=0.610 (1.04x)`, `18: cpp=0.336 rs=0.408 (1.22x)` で、再確認でも `01: 0.747/0.735 (0.98x)`, `09: 0.569/0.613 (1.08x)`, `18: 0.331/0.396 (1.20x)` と同傾向を確認した。`09` は外れ値閾値（`>1.5x`）を解消した。
