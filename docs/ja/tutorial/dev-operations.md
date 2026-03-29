<a href="../../en/tutorial/dev-operations.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# 開発運用ガイド

このページは、[how-to-use.md](./how-to-use.md) には載せない parity、local CI、backend health などの日常開発向け運用手順をまとめたものです。

## 実行時間計測プロトコル（sample）

- `sample/py` 由来の実行時間計測は、fresh transpile 後に実行します。
- 計測回数は `warmup=1` + `repeat=2` を既定とします。
- 代表値は 2 回の**算術平均（average）**を使います（中央値は使いません）。
- コンパイル時間は計測値に含めません。

## runtime parity 運用（sample, 全target）

- `tools/check/runtime_parity_check.py` は stdout だけでなく、`output:` で示された artifact の `size` と `CRC32` まで比較します。
- parity 実行時は case ごとに `sample/out`, `test/out`, `out`, `work/transpile/<target>/<case>` の stale artifact を自動削除します。
- `elapsed_sec` などの不安定行は既定で比較対象外です（`--ignore-unstable-stdout` は互換フラグ）。
- 全14targetを一括検証する場合の canonical wrapper:

```bash
python3 tools/check/check_all_target_sample_parity.py \
  --summary-dir work/logs/all_target_sample_parity
```

- lower-level に `runtime_parity_check.py` を直接使う場合の canonical group:

```bash
python3 tools/check/runtime_parity_check.py \
  --targets cpp \
  --case-root sample \
  --all-samples \
  --east3-opt-level 2 \
  --cpp-codegen-opt 3

python3 tools/check/runtime_parity_check.py \
  --targets js,ts \
  --case-root sample \
  --all-samples \
  --ignore-unstable-stdout \
  --east3-opt-level 2

python3 tools/check/runtime_parity_check.py \
  --targets rs,cs,go,java,kotlin,swift,scala \
  --case-root sample \
  --all-samples \
  --ignore-unstable-stdout \
  --east3-opt-level 2

python3 tools/check/runtime_parity_check.py \
  --targets ruby,lua,php,nim \
  --case-root sample \
  --all-samples \
  --ignore-unstable-stdout \
  --east3-opt-level 2
```

- 実行時間短縮のためにケースを分割する場合（運用例）:
  - `01-03`: `01_mandelbrot 02_raytrace_spheres 03_julia_set`
  - `04-06`: `04_orbit_trap_julia 05_mandelbrot_zoom 06_julia_parameter_sweep`
  - `07-09`: `07_game_of_life_loop 08_langtons_ant 09_fire_simulation`
  - `10-12`: `10_plasma_effect 11_lissajous_particles 12_sort_visualizer`
  - `13-15`: `13_maze_generation_steps 14_raymarching_light_cycle 15_wave_interference_loop`
  - `16-18`: `16_glass_sculpture_chaos 17_monte_carlo_pi 18_mini_language_interpreter`

## linked-program 後の non-C++ backend health check

- linked-program 導入後の non-C++ backend gate は `tools/check/check_noncpp_backend_health.py` を正本とします。
- 日常の最小確認は次の 1 本です。`parity` は toolchain 依存なのでここでは回しません。

```bash
python3 tools/check/check_noncpp_backend_health.py --family all --skip-parity
```

- family を絞る場合は `wave1` / `wave2` / `wave3` を使います。

```bash
python3 tools/check/check_noncpp_backend_health.py --family wave1 --skip-parity
python3 tools/check/check_noncpp_backend_health.py --family wave2 --skip-parity
python3 tools/check/check_noncpp_backend_health.py --family wave3 --skip-parity
```

- `toolchain_missing` は backend bug ではなく、parity 実行環境がないだけの baseline として扱います。
- `tools/run/run_local_ci.py` には `python3 tools/check/check_noncpp_backend_health.py --family all --skip-parity` が組み込まれているため、local CI を通せば non-C++ backend の smoke/transpile gate も同時に監視できます。
- 同じく `python3 tools/check/check_jsonvalue_decode_boundaries.py` も組み込まれているため、`pytra-cli` / `east_io` / `toolchain/link/*` の JSON artifact 境界で raw `json.loads(...)` が再侵入した場合は local CI で fail します。

## Emitter変更時の必須ガード（Stop-Ship）

- `src/toolchain/emit/*/emitter/*.py` を変更した場合は、コミット前に次を必ず実行します。
  - `python3 tools/check/check_emitter_runtimecall_guardrails.py`
  - `python3 tools/check/check_emitter_forbidden_runtime_symbols.py`
  - `python3 tools/check/check_noncpp_east3_contract.py`
- 上記のいずれかが `FAIL` の場合、コミット/プッシュ禁止です（Stop-Ship）。
- runtime/stdlib の呼び出し解決は EAST3 正本情報（`runtime_call`, `resolved_runtime_call`, `resolved_runtime_source`）のみを使い、emitter 側に関数名・モジュール名の分岐/テーブルを増やしてはいけません。
- `java` backend は strict 対象です。runtime dispatch 用の直書きシンボルは allowlist で許可せず、0件を維持します。

## non-C++ backend のコンテナ参照管理運用（v1）

- 対象 backend: `cs/js/ts/go/swift/ruby/lua/php`（Rust/Kotlin は pilot 実装済み）。
- 共通方針:
  - `object/Any/unknown/union(any含む)` へ流れる境界は参照管理境界（ref-boundary）として扱う。
  - 型既知かつ局所 non-escape の経路は値型経路（value-path）として shallow copy を挿入する。
  - 判定不能時は fail-closed で ref-boundary 側へ倒す。
- 生成結果確認:
  - `python3 tools/check/check_py2cs_transpile.py`
  - `python3 tools/check/check_py2js_transpile.py`
  - `python3 tools/check/check_py2ts_transpile.py`
  - `python3 tools/check/check_py2go_transpile.py`
  - `python3 tools/check/check_py2swift_transpile.py`
  - `python3 tools/check/check_py2rb_transpile.py`
  - `python3 tools/check/check_py2lua_transpile.py`
  - `python3 tools/check/check_py2php_transpile.py`
  - `python3 tools/check/runtime_parity_check.py --case-root sample --targets cs,js,ts,go,swift,ruby,lua,php --ignore-unstable-stdout 18_mini_language_interpreter`
- rollback 手段（暫定）:
  - 値型材料化が問題になる箇所は、ローカルの型注釈を `object/Any` 側へ寄せて ref-boundary を強制する。
  - 逆に alias 分離を明示したい場合は、入力 Python 側で `list(...)` / `dict(...)` などの明示コピーを書く。

## selfhost 検証手順（C++ backend -> `py2cpp.cpp`）

前提:
- プロジェクトルートで実行する。
- `g++` が使えること。
- `selfhost/` は検証用の作業ディレクトリ（Git管理外）として扱う。

```bash
# 0) selfhost C++ を生成してビルド（ランタイム .cpp も含めてリンク）
python3 tools/build_selfhost.py > selfhost/build.all.log 2>&1

# 1) ビルドエラーをカテゴリ確認
rg "error:" selfhost/build.all.log
```

コンパイル成功時の比較手順:

```bash
# 2) selfhost 実行ファイルで sample/py/01 を .py 直入力から変換
mkdir -p work/transpile/cpp2
./selfhost/py2cpp.out sample/py/01_mandelbrot.py --target cpp -o work/transpile/cpp2/01_mandelbrot.cpp

# 3) Python 版 C++ backend でも同じ入力を変換
python3 src/pytra-cli.py sample/py/01_mandelbrot.py --target cpp -o work/transpile/cpp/01_mandelbrot.cpp

# 4) direct route が sample 全件で -fsyntax-only まで通るか確認
python3 tools/check/check_selfhost_direct_compile.py

# 5) Python版とselfhost版の出力差分を代表ケースで確認
python3 tools/check/check_selfhost_cpp_diff.py --mode strict --show-diff

# 6) representative e2e を確認
python3 tools/verify_selfhost_end_to_end.py --skip-build \
  --cases sample/py/05_mandelbrot_zoom.py sample/py/18_mini_language_interpreter.py test/fixtures/core/add.py

# 7) stage2 binary を生成して差分確認
python3 tools/build_selfhost_stage2.py
python3 tools/check/check_selfhost_stage2_cpp_diff.py --mode strict

# 8) stage2 binary で sample 全件 parity を確認
python3 tools/check/check_selfhost_stage2_sample_parity.py --skip-build
```

補足:
- `selfhost/py2cpp.out` の `.py` 直入力は current contract です。bridge 経路は調査用 fallback としてだけ扱います。
- `tools/check/check_selfhost_cpp_diff.py` と `tools/check/check_selfhost_stage2_cpp_diff.py` は strict mode を正本にします。
- `tools/check/check_selfhost_stage2_sample_parity.py --skip-build` は `selfhost/py2cpp_stage2.out` を使った full sample parity の canonical command です。representative diff と違い、`sample/py` 全件の transpile + compile + run parity を見ます。
- `tools/check/check_selfhost_direct_compile.py` は `sample/py` 全件を selfhost で変換して `g++ -fsyntax-only` まで見る、最短の compile regression gate です。

失敗時の確認ポイント:
- `build.all.log` の `error:` を先に分類し、型系（`std::any` / `optional`）と構文系（未lowering）を分ける。
- `selfhost/py2cpp.cpp` の該当行に対して、元の `src/toolchain/emit/cpp/cli.py` や generated runtime (`src/runtime/cpp/generated/**`) の ABI が value/ref-first 契約を壊していないか確認する。
- `sample/py/18_mini_language_interpreter.py` のような host/selfhost diff は、selfhost binary を rebuild せずに runtime serializer だけ直したときにも起こりうる。`src/pytra/std/json.py` や generated runtime を直したら `python3 tools/build_selfhost.py` を再実行する。

## CodeEmitter 作業時の変換チェック

`CodeEmitter` を段階的に改修するときは、各ステップごとに次を実行します。

```bash
python3 tools/check/check_py2cpp_transpile.py
python3 tools/check/check_py2rs_transpile.py
python3 tools/check/check_py2js_transpile.py
```

補足:
- 既定では既知の負例フィクスチャ（`test/fixtures/signature/ng_*.py` と `test/fixtures/typing/any_class_alias.py`）を除外して判定します。
- 負例も含めて確認したい場合は `--include-expected-failures` を付けます。
