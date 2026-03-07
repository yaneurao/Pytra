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

- [ ] [ID: P0-CPP-RUNTIME-LAYOUT-REALIGN-01] C++ runtime の module runtime 層を `generated/` + `native/` + `pytra/` shim へ再編し、suffix ベース ownership から directory ベース ownership へ移行する。

- [ ] [ID: P0-CPP-RUNTIME-LAYOUT-REALIGN-01-S1-01] `generated/` / `native/` / `pytra/` / `core/` の責務境界を spec と plan に明記し、`native` 命名採用理由を固定する。
- [ ] [ID: P0-CPP-RUNTIME-LAYOUT-REALIGN-01-S1-02] 現行 `built_in/std/utils/pytra` 配下のファイルを「generated」「native」「public shim」「core 非対象」に分類し、移行マップを作る。

- [ ] [ID: P0-CPP-RUNTIME-LAYOUT-REALIGN-01-S2-01] runtime emit / runtime_paths / public shim 生成を `generated/` + `pytra/` 前提へ更新する。
- [ ] [ID: P0-CPP-RUNTIME-LAYOUT-REALIGN-01-S2-02] `runtime_symbol_index` / `cpp_runtime_deps.py` / build graph 導線を `generated/native/pytra` 前提へ更新する。
- [ ] [ID: P0-CPP-RUNTIME-LAYOUT-REALIGN-01-S2-03] `check_runtime_cpp_layout.py` を directory ベース ownership 検証へ更新する。

- [ ] [ID: P0-CPP-RUNTIME-LAYOUT-REALIGN-01-S3-01] `std/` の generated runtime を `generated/std/` へ移し、`pytra/std/*.h` shim を同期する。
- [ ] [ID: P0-CPP-RUNTIME-LAYOUT-REALIGN-01-S3-02] `utils/` の generated runtime を `generated/utils/` へ移し、`pytra/utils/*.h` shim を同期する。
- [ ] [ID: P0-CPP-RUNTIME-LAYOUT-REALIGN-01-S3-03] `built_in/` の generated runtime を `generated/built_in/` へ移し、必要な public include 面を同期する。

- [ ] [ID: P0-CPP-RUNTIME-LAYOUT-REALIGN-01-S4-01] 既存 module companion を `native/` へ移し、`native/*.h` を最小化する。
- [ ] [ID: P0-CPP-RUNTIME-LAYOUT-REALIGN-01-S4-02] `os_path` / `math` / `time` など representative module で「宣言は generated、実装は native、公開は pytra shim」を固定する。

- [ ] [ID: P0-CPP-RUNTIME-LAYOUT-REALIGN-01-S5-01] codegen/unit/parity を新レイアウトへ追従させ、旧 `.gen/.ext` 固定前提を更新する。
- [ ] [ID: P0-CPP-RUNTIME-LAYOUT-REALIGN-01-S5-02] archive/docs/guard を更新し、module runtime の suffix ベース ownership を legacy 扱いで閉じる。

決定ログ:
- 2026-03-07: ユーザー方針により、C++ runtime の module runtime 層は `generated/` + `native/` + `pytra/` shim を目標レイアウトとし、`handwritten` ではなく「C++ 固有 companion」を示す `native` を採用する。
- 2026-03-07: 本計画では `core/` を low-level runtime として維持し、まず `built_in/std/utils + pytra` の ownership 整理にスコープを限定する。
