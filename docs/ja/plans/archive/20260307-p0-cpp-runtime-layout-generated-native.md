<a href="../../../en/plans/archive/20260307-p0-cpp-runtime-layout-generated-native.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: C++ runtime レイアウト再編（`generated/` + `native/` + `pytra/` shim）

最終更新: 2026-03-07

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-RUNTIME-LAYOUT-REALIGN-01`
- 参照仕様: `docs/ja/spec/spec-runtime.md`
- 参照仕様: `docs/ja/spec/spec-abi.md`
- 先行整理: `docs/ja/plans/archive/20260307-p0-cpp-os-path-wrapper-retirement.md`
- 過去案: `docs/ja/plans/archive/p1-runtime-layout-unification.md`

背景:
- 現行の `src/runtime/cpp/` は、責務ディレクトリとして `core/`, `built_in/`, `std/`, `utils/` を持ちつつ、ファイル所有権は `*.gen.*` / `*.ext.*` suffix で表している。
- この方式はビルド上は成立しているが、`os_path.ext.h` のように「自動生成できる宣言」と「暫定 wrapper 宣言」が同じ責務ディレクトリに並び、所有権が見えにくい。
- 一方で `src/runtime/cpp/pytra/` は、現在は実体ではなく generated public include shim として機能しており、生成コードにとっては stable include path である。
- 既存の archived plan では `handwritten` という呼称も検討されたが、今回の方針では「人が書いたか」より「Python SoT から変換できない C++ 固有 companion か」を重視し、`native/` という責務名を採用する。

目的:
- C++ runtime の module runtime 層を、suffix ベースの所有権表現から directory ベースの所有権表現へ移行する。
- `src/runtime/cpp/pytra/` は generated public shim として残し、生成コードの stable include path を維持する。
- `generated/` と `native/` の責務を明確にし、`os_path.ext.h` のような「薄い手書き宣言ファイル」が再び生えにくい構造へ寄せる。

対象:
- `src/runtime/cpp/` の module runtime 層
  - `built_in/`
  - `std/`
  - `utils/`
  - `pytra/`
- C++ runtime 生成導線
  - `src/backends/cpp/cli.py`
  - `src/backends/cpp/emitter/runtime_paths.py`
- runtime artifact/tooling
  - `tools/gen_runtime_symbol_index.py`
  - `tools/cpp_runtime_deps.py`
  - `tools/check_runtime_cpp_layout.py`
- C++ 関連 docs / tests
  - `docs/ja/spec/spec-runtime.md`
  - `docs/ja/spec/spec-abi.md`
  - `test/unit/backends/cpp/*`
  - `test/unit/tooling/test_runtime_symbol_index.py`

非対象:
- `src/runtime/cpp/core/` の責務再定義
- 非C++ backend の runtime レイアウト変更
- runtime API の新機能追加
- `sample/cpp/*.cpp` の手編集
- `generated/` / `native/` への移行前に、既存 `.gen/.ext` 全ファイルを無計画に一括 rename すること

前提ルール:
- `pytra/` は public include shim 専用であり、実装正本を置く場所ではない。
- `generated/` は `src/pytra/{built_in,std,utils}/*.py` からの自動生成物のみを置く。
- `native/` は C++ 標準ライブラリ / filesystem / chrono / regex / OS / ABI glue など、Python SoT だけでは表現できない companion のみを置く。
- `native/` を「何でも手書きで置いてよい雑多フォルダ」にしてはならない。
- 宣言の正本は原則 `generated/*.h` に置き、`native/*.h` は template / inline helper など本当に必要な場合だけに制限する。

## 先に固定する設計判断

### A. 目標レイアウト

```text
src/runtime/cpp/
  core/
  generated/
    built_in/
    std/
    utils/
  native/
    built_in/
    std/
    utils/
  pytra/
    built_in/
    std/
    utils/
```

### B. 各ディレクトリの意味

- `core/`
  - 低レベル runtime 基盤。container / object 表現 / ABI / I/O / GC など。
- `generated/`
  - SoT から機械生成された module runtime。
- `native/`
  - C++ target 固有 companion。`generated/` の代替実装置き場ではない。
- `pytra/`
  - generated public shim。生成コードが include する stable path。

### C. 命名で避けるもの

- `extern/`
  - `@extern` と意味が衝突しやすい。
- `handwritten/`
  - 「誰が編集したか」は示せても、「なぜ存在するか」が弱い。
- suffix だけでの ownership 管理
  - `*.gen.*` / `*.ext.*` は移行期間の legacy とする。

## 実装で迷いやすい点

### 1. `native/` は何でも置ける場所ではない

置いてよい:
- `math` の C++ 標準ライブラリ接着
- `os_path` / `glob` の filesystem 接着
- `time` の chrono 接着
- typed helper のうち SoT だけでは出せない最小 companion

置いてはいけない:
- SoT と同等の本体ロジックの複製
- temporary wrapper だけの宣言ファイル
- backend の都合だけで増える ad-hoc helper

### 2. `pytra/` は残すが、実体は置かない

- 生成コードは `#include "pytra/std/time.h"` のような stable include を使い続ける。
- `pytra/` 自体は generated shim であり、`generated/` / `native/` を束ねるだけにする。
- user code / emitter が `generated/` や `native/` を直接 include してはならない。

### 3. `core/` は今回の rename 対象ではない

- `core/` は module runtime ではなく low-level runtime なので、`generated/native` へ混ぜない。
- まずは `built_in/std/utils + pytra` の ownership を directory 化する。
- `core/` の suffix cleanup は別件として扱う。

## フェーズ

### Phase 1: layout 契約の固定

- `generated/` / `native/` / `pytra/` の責務を spec と plan へ明記する。
- `native` を「C++ 固有 companion」の意味に固定し、`handwritten` / `extern` 案との差分を決定ログへ残す。
- 現行 `.gen/.ext` 方式は「現行実装」であり、移行対象であることを明記する。

### Phase 2: path / tooling 契約の設計

- runtime emit 出力先を `generated/` と `pytra/` に分ける規則を定義する。
- `runtime_symbol_index` と `cpp_runtime_deps.py` が `generated/native/pytra` をどう解決するか決める。
- `check_runtime_cpp_layout.py` を suffix ベースから directory ベースへどう移すかを定義する。

### Phase 3: generated 層の移行

- `built_in/std/utils` の生成物を `generated/` へ移す。
- `--emit-runtime-cpp` は `generated/*.h/.cpp` を正本出力とし、`pytra/*.h` shim を同時生成する。
- `pytra/` shim は generated-only を維持する。

### Phase 4: native companion 層の移行

- 既存 `*.ext.cpp` / `*.ext.h` のうち module companion を `native/` へ移す。
- `native/*.h` が本当に必要かを各モジュールで再判定し、不要な wrapper 宣言は削除する。
- `os_path` のように `generated/*.h` だけで宣言が足りるモジュールは、`native/*.cpp` のみを残す。

### Phase 5: build / include / test の同期

- emitter の include は引き続き `pytra/...` を使う。
- build graph / compile source 収集は `generated/native` から導出する。
- runtime unit / codegen unit / parity を更新し、旧 `.gen/.ext` 固定前提を落とす。

### Phase 6: legacy cleanup

- `.gen/.ext` naming を module runtime から段階撤去する。
- archive / docs / guard を更新し、suffix ベース運用を legacy 扱いで閉じる。

## Phase 1 実施結果

2026-03-07 時点の棚卸しでは、`src/runtime/cpp/` の module runtime 層は次の内訳だった。

- `generated`: 36 files
- `native`: 9 files
- `public shim`: 10 files
- `core` 非対象: 13 files
- `other`: 1 file (`std/README.md`)

分類結果:

- `built_in/`
  - generated:
    - `contains`, `iter_ops`, `predicates`, `sequence`, `string_ops`, `type_id` の `*.gen.h/.gen.cpp`
  - native:
    - `contains.ext.h`
    - `iter_ops.ext.h`
    - `sequence.ext.h`
  - public shim:
    - 現時点ではなし
- `std/`
  - generated:
    - `argparse`, `glob`, `json`, `math`, `os`, `os_path`, `pathlib`, `random`, `re`, `sys`, `time`, `timeit`
  - native:
    - `glob.ext.cpp`
    - `math.ext.cpp`
    - `os.ext.cpp`
    - `os_path.ext.cpp`
    - `sys.ext.cpp`
    - `time.ext.cpp`
  - public shim:
    - `pytra/std/{glob,math,os,os_path,pathlib,random,re,time}.h`
  - other:
    - `std/README.md`
- `utils/`
  - generated:
    - `assertions`, `gif`, `png` の `*.gen.h/.gen.cpp`
  - native:
    - 現時点ではなし
  - public shim:
    - `pytra/utils/{gif,png}.h`
- `core/`
  - `README.md`, `dict.ext.h`, `exceptions.ext.h`, `gc.ext.cpp`, `gc.ext.h`, `io.ext.cpp`, `io.ext.h`, `list.ext.h`, `py_runtime.ext.h`, `py_scalar_types.ext.h`, `py_types.ext.h`, `set.ext.h`, `str.ext.h`
  - 本計画の移行対象外とする

移行マップ:

- `built_in/*.gen.h/.gen.cpp` -> `generated/built_in/*.h/.cpp`
- `std/*.gen.h/.gen.cpp` -> `generated/std/*.h/.cpp`
- `utils/*.gen.h/.gen.cpp` -> `generated/utils/*.h/.cpp`
- `*.ext.cpp` -> `native/<domain>/*.cpp`
- `*.ext.h` -> 原則廃止し、template / inline helper など例外時のみ `native/<domain>/*.h` として存続可
- `pytra/<domain>/*.h` -> generated public shim として維持
- `core/*` -> 本計画では移動しない

## Phase 2 実施結果

- `runtime_output_rel_tail(...)` は module runtime の generated 正本を `generated/<domain>/<module>` へ解決するよう更新した。
- `--emit-runtime-cpp` は `src/runtime/cpp/generated/.../*.h|*.cpp` を出力し、`src/runtime/cpp/pytra/.../*.h` forwarder を同時生成するよう更新した。
- generated public shim は `runtime/cpp/generated/.../*.h` を必須 include とし、`runtime/cpp/native/.../*.h` は存在時のみ追加 include する方針へ切り替えた。
- header pruning helper も `runtime/cpp/{generated,native,pytra}/...` include を module namespace へ解決できるよう更新した。
- `runtime_symbol_index` は C++ module runtime の `public_headers` に `pytra` public shim と generated/native header を載せ、`lookup_target_module_primary_header("cpp", ...)` は `pytra/...` を優先するよう更新した。
- `cpp_runtime_deps.py` / build graph は `runtime_symbol_index` の header-to-source index を優先し、path heuristic でも `pytra/generated/native` から `.cpp` 候補を導出できるよう更新した。
- `check_runtime_cpp_layout.py` は `src/runtime/cpp/{built_in,std,utils}` を legacy-closed bucket とし、`generated/`、`native/`、`pytra/`、`core/` の ownership 境界を同一 guard で監査できるよう更新した。

## Phase 3 実施結果

- `src/runtime/cpp/std/*.gen.h|*.gen.cpp` を `src/runtime/cpp/generated/std/*.h|*.cpp` へ移し、checked-in std generated artifact の正本配置を実ファイルとして切り替えた。
- `src/runtime/cpp/pytra/std/*.h` は `runtime/cpp/generated/std/*.h` を forward する shim に同期した。
- `src/runtime/cpp/std/*.ext.cpp` は `runtime/cpp/generated/std/*.h` を include するよう更新し、legacy `std/` 直下には native companion と `README.md` だけを残した。
- `tools/check_runtime_std_sot_guard.py` も std generated artifact の配置を `generated/std` 前提へ更新し、`pytra/` public shim を generated 扱いに寄せた。
- `src/runtime/cpp/utils/*.gen.h|*.gen.cpp` を `src/runtime/cpp/generated/utils/*.h|*.cpp` へ移し、checked-in utils generated artifact の正本配置を実ファイルとして切り替えた。
- `src/runtime/cpp/pytra/utils/*.h` は `runtime/cpp/generated/utils/*.h` を forward する shim に同期し、`assertions` 用 shim も追加した。
- `tools/runtime_generation_manifest.json` / `tools/verify_image_runtime_parity.py` / `tools/check_runtime_std_sot_guard.py` / `runtime_symbol_index` 系 test を `generated/utils` 前提へ更新した。
- `src/runtime/cpp/built_in/*.gen.h|*.gen.cpp` を `src/runtime/cpp/generated/built_in/*.h|*.cpp` へ移し、legacy `built_in/` 直下は native helper header (`*.ext.h`) だけを残す構成へ切り替えた。
- `src/runtime/cpp/pytra/built_in/*.h` shim を追加し、generated std artifact の built-in import も `pytra/built_in/*.h` / `pytra/std/sys.h` へ寄せた。
- `py_runtime.ext.h` / runtime symbol index / type_id・iterable 系 test を `generated/built_in` + `pytra/built_in` 前提へ更新した。
- `src/runtime/cpp/std/*.ext.cpp` を `src/runtime/cpp/native/std/*.cpp` へ、`src/runtime/cpp/built_in/*.ext.h` を `src/runtime/cpp/native/built_in/*.h` へ移し、legacy module companion を `native/` 配下へ揃えた。
- `py_runtime.ext.h` と `pytra/built_in/*.h` は `native/built_in/*.h` を参照するよう更新し、runtime symbol index / build graph / pyobj smoke も `native/std/*.cpp` compile source を期待するよう同期した。
- `math` / `os_path` / `time` について、runtime symbol index test で「primary header は `pytra/std/*.h`」「compile source は `native/std/*.cpp`」「native 実装は `generated/std/*.h` を include」「`native/std/*.h` は持たない」を直接検証する representative contract を追加した。
- tracked repo 上の codegen/unit 前提に残っていた旧 `.gen/.ext` 固定 path は解消し、`runtime_symbol_index` / build graph / iterable/pyobj smoke / image parity を新 layout 前提で通した。
- `test/transpile/cpp/*/Makefile` は untracked generated artifact として現行 `gen_makefile_from_manifest.py` で再生成し、fixture (`math_extended`, `pathlib_extended`, `import_pytra_runtime_png`) と sample (`01_mandelbrot`, `18_mini_language_interpreter`) の C++ parity を確認した。

## Phase 6 実施結果

- `check_runtime_cpp_layout.py` は module runtime legacy dir (`src/runtime/cpp/{built_in,std,utils}`) に `.h/.cpp` が再侵入した時点で fail する guard へ切り替え、`legacy-closed module files: 0` を正規状態として固定した。
- `runtime_symbol_index` / `cpp_runtime_deps.py` / public shim 生成は、C++ module runtime について legacy `*.gen/*.ext` path を探索しない形へ締め、`generated/native/pytra` のみを ownership 正本として扱う。
- `docs/ja/spec/spec-runtime.md` / `docs/ja/spec/spec-abi.md` を現行 layout 前提へ更新し、suffix ベース ownership は `core/` と未移行 target だけに閉じた。

## 受け入れ基準

- `src/runtime/cpp/pytra/` は generated public shim 専用になる。
- module runtime の ownership が `generated/` と `native/` のディレクトリで判別できる。
- `native/` は C++ 固有 companion のみに限定され、SoT 重複ロジックを持たない。
- `generated user code -> pytra shim -> generated/native` の経路が成立する。
- `tools/gen_runtime_symbol_index.py` と `tools/cpp_runtime_deps.py` が新レイアウトで動作する。
- `tools/check_runtime_cpp_layout.py` が新しい ownership 境界を検証できる。

## 確認コマンド（予定）

- `python3 tools/check_todo_priority.py`
- `python3 tools/gen_runtime_symbol_index.py --check`
- `python3 tools/check_runtime_cpp_layout.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_*.py'`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples`

## 分解

- [x] [ID: P0-CPP-RUNTIME-LAYOUT-REALIGN-01] C++ runtime の module runtime 層を `generated/` + `native/` + `pytra/` shim へ再編し、suffix ベース ownership から directory ベース ownership へ移行する。

- [x] [ID: P0-CPP-RUNTIME-LAYOUT-REALIGN-01-S1-01] `generated/` / `native/` / `pytra/` / `core/` の責務境界を spec と plan に明記し、`native` 命名採用理由を固定する。
- [x] [ID: P0-CPP-RUNTIME-LAYOUT-REALIGN-01-S1-02] 現行 `built_in/std/utils/pytra` 配下のファイルを「generated」「native」「public shim」「core 非対象」に分類し、移行マップを作る。

- [x] [ID: P0-CPP-RUNTIME-LAYOUT-REALIGN-01-S2-01] runtime emit / runtime_paths / public shim 生成を `generated/` + `pytra/` 前提へ更新する。
- [x] [ID: P0-CPP-RUNTIME-LAYOUT-REALIGN-01-S2-02] `runtime_symbol_index` / `cpp_runtime_deps.py` / build graph 導線を `generated/native/pytra` 前提へ更新する。
- [x] [ID: P0-CPP-RUNTIME-LAYOUT-REALIGN-01-S2-03] `check_runtime_cpp_layout.py` を directory ベース ownership 検証へ更新する。

- [x] [ID: P0-CPP-RUNTIME-LAYOUT-REALIGN-01-S3-01] `std/` の generated runtime を `generated/std/` へ移し、`pytra/std/*.h` shim を同期する。
- [x] [ID: P0-CPP-RUNTIME-LAYOUT-REALIGN-01-S3-02] `utils/` の generated runtime を `generated/utils/` へ移し、`pytra/utils/*.h` shim を同期する。
- [x] [ID: P0-CPP-RUNTIME-LAYOUT-REALIGN-01-S3-03] `built_in/` の generated runtime を `generated/built_in/` へ移し、必要な public include 面を同期する。

- [x] [ID: P0-CPP-RUNTIME-LAYOUT-REALIGN-01-S4-01] 既存 module companion を `native/` へ移し、`native/*.h` を最小化する。
- [x] [ID: P0-CPP-RUNTIME-LAYOUT-REALIGN-01-S4-02] `os_path` / `math` / `time` など representative module で「宣言は generated、実装は native、公開は pytra shim」を固定する。

- [x] [ID: P0-CPP-RUNTIME-LAYOUT-REALIGN-01-S5-01] codegen/unit/parity を新レイアウトへ追従させ、旧 `.gen/.ext` 固定前提を更新する。
- [x] [ID: P0-CPP-RUNTIME-LAYOUT-REALIGN-01-S5-02] archive/docs/guard を更新し、module runtime の suffix ベース ownership を legacy 扱いで閉じる。

決定ログ:
- 2026-03-07: ユーザー方針により、C++ runtime の module runtime 層は `generated/` + `native/` + `pytra/` shim を目標レイアウトとし、`handwritten` ではなく「C++ 固有 companion」を示す `native` を採用する。
- 2026-03-07: 本計画では `core/` を low-level runtime として維持し、まず `built_in/std/utils + pytra` の ownership 整理にスコープを限定する。
- 2026-03-07: Phase 1 棚卸しでは `generated 36 / native 9 / public shim 10 / core 非対象 13 / other 1` を確認し、`pytra/` shim は現行では `std/` と `utils/` にのみ存在する。
- 2026-03-07: 現行の `*.ext.h` 残存は `built_in` helper 3 件のみであり、移行先では例外的な `native/*.h` に縮退させる方針を固定する。
- 2026-03-07: `runtime_output_rel_tail` と `--emit-runtime-cpp` は `generated/<domain>/<module>` を正本出力先とし、public shim は `pytra/...` に残す方針で実装を切り替えた。
- 2026-03-07: generated public shim は `runtime/cpp/generated/.../*.h` を forward し、`native/*.h` は存在時のみ forward する。`native/` 自動生成は行わない。
- 2026-03-07: `runtime_symbol_index` の C++ primary header は `pytra/...` shim を優先し、`public_headers` / `compile_sources` は `generated/native` の ownership をそのまま反映する。
- 2026-03-07: `cpp_runtime_deps.py` は index 優先・path heuristic 補完の二段構えとし、C++ module runtime では `pytra/generated/native` だけを探索対象にする。
- 2026-03-07: `check_runtime_cpp_layout.py` は `src/runtime/cpp/{built_in,std,utils}` を legacy-closed module dir として扱い、`.h/.cpp` の再侵入を fail-fast する guard へ更新した。
- 2026-03-07: `std` generated artifact は checked-in 実ファイルとして `generated/std` へ移し、`std/` 直下は native companion (`*.ext.cpp`) と補足文書だけを残す構成へ切り替えた。
- 2026-03-07: `utils` generated artifact も checked-in 実ファイルとして `generated/utils` へ移し、`pytra/utils/*.h` shim と runtime parity / manifest / index test を同時更新して旧 `utils/*.gen.*` 参照を解消した。
- 2026-03-07: `utils` の再生成物は list ref-first TODO の未完了分で semantic drift を含んだため、本フェーズでは旧 checked-in artifact の挙動を `generated/utils` へ持ち上げ、レイアウト移行と semantic change を分離した。
- 2026-03-07: `built_in` generated artifact も rename ベースで `generated/built_in` へ移し、`pytra/built_in/*.h` shim を追加した。generated std artifact は stable include 面として `pytra/built_in/*.h` を参照するよう合わせた。
- 2026-03-07: legacy module companion 9 件 (`std/*.ext.cpp` 6 + `built_in/*.ext.h` 3) を `native/` へ移し、layout guard 上も `legacy module files: 0` を確認した。checked-in `test/transpile/cpp/*/Makefile` の stale path は generated fixture 更新タスク `S5-01` でまとめて同期する。
- 2026-03-07: representative module 契約は `math / os_path / time` を canonical example とし、runtime symbol index test で `generated -> native -> pytra shim` の三層を直接検証する形で固定した。
- 2026-03-07: `test/transpile/cpp/*/Makefile` は repo tracked file ではなく generated artifact なので、`S5-01` では `tools/gen_makefile_from_manifest.py` で再生成して parity 検証に使い、tracked repo 側には unit/test/guard の新 layout 前提だけを記録した。
- 2026-03-07: `S5-02` で module runtime の suffix ベース ownership は legacy-closed とし、legacy dir には補足文書以外の `.h/.cpp` を置かない方針を guard / spec / archive へ反映した。
