# P0: C++ `os.path` legacy wrapper 退役（`pytra::std::os_path::*` 正本化）

最終更新: 2026-03-07

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-OSPATH-WRAPPER-RETIRE-01`
- 先行修復: `docs/ja/plans/archive/20260306-p0-cpp-unit-regression-recovery.md` の `ID: P0-CPP-REGRESSION-RECOVERY-01-S3-02`

背景:
- 2026-03-06 の unit 回帰復旧では、`os.path` / `glob` compile break を止血するために `src/runtime/cpp/std/os_path.ext.h` と `py_os_path_*` wrapper を追加した。
- その結果、`src/pytra/std/os_path.py` から自動生成される `src/runtime/cpp/std/os_path.gen.h` とは別に、手書きの wrapper 宣言が `os_path.ext.h` に残っている。
- `os_path.ext.cpp` の namespace 実装 `pytra::std::os_path::*` 自体は `@extern` の手実装として妥当だが、`py_os_path_*` は canonical source に存在しない legacy ABI であり、現在は `src/backends/cpp/profiles/runtime_calls.json` がそれを正本として参照している。
- この状態は「自動生成できる宣言」と「互換 wrapper 宣言」が二重に見え、runtime layout の理解を悪化させる。特に `math` など同系統 module は `pytra::std::math::*` 直呼びで成立しており、`os_path` だけが例外になっている。

目的:
- C++ backend の `os.path` 呼び先を `py_os_path_*` wrapper から `pytra::std::os_path::*` へ戻し、`os_path.ext.h` を削除する。
- `os_path` の公開面を「SoT 由来の `os_path.gen.h` + 手書き実装 `os_path.ext.cpp`」へ整理し、手書き宣言の重複をなくす。
- 2026-03-06 の暫定復旧で得た compile-source/public-header 追跡の修正は維持しつつ、legacy helper 名だけを退役させる。

対象:
- `src/backends/cpp/profiles/runtime_calls.json`
- `src/runtime/cpp/std/os_path.ext.h`
- `src/runtime/cpp/std/os_path.ext.cpp`
- `src/runtime/cpp/pytra/std/os_path.h`
- `src/backends/cpp/cli.py`
- `test/unit/backends/cpp/test_py2cpp_features.py`
- `test/unit/backends/cpp/test_cpp_runtime_symbol_index_integration.py`
- `test/unit/pylib/test_pylib_os_glob.py`
- `tools/gen_runtime_symbol_index.py`

非対象:
- `os.py` の Python fallback alias (`from pytra.std import os_path as path`) の削除
- `.gen.*` / `.ext.*` 命名規則の repo 全体刷新
- `glob` / `pathlib` / `os` runtime の別件 API 追加
- `src/runtime/cpp/pytra/` 全体の配置換え
- `sample/cpp/*.cpp` の手編集

前提ルール:
- `.gen.*` は手編集しない。必要な差分は SoT 再生成か生成導線修正で反映する。
- `os_path.ext.h` を消す前に、`py_os_path_*` へ依存する backend/test/runtime index をすべて洗い出す。
- `runtime_calls.json` は「呼び先名の一括置換テーブル」ではなく、`os.path` が `pytra.std.os_path` module に属することを壊さない形で更新する。
- `glob` は `os_path` と同時に壊れやすいので、`os.path` だけ見て満足しない。

## 先に固定する設計判断

### A. 正本

- `pytra::std::os_path::*` が C++ runtime の正本 API。
- `src/runtime/cpp/std/os_path.gen.h` が宣言の正本。
- `src/runtime/cpp/std/os_path.ext.cpp` は namespace 実装のみを持つ。

### B. 退役対象

- `src/runtime/cpp/std/os_path.ext.h`
- `os_path.ext.cpp` 内の `py_os_path_*` wrapper 定義
- `runtime_calls.json` 内の `py_os_path_*` 呼び先
- wrapper 名を前提にした codegen assert

### C. 維持するもの

- `src/pytra/std/os.py` の `os_path as path` alias
- `pytra/std/os_path.h` という public include 名
- `CppModuleEmitter` / `cpp_runtime_deps.py` が module attr から実 runtime module を回収する経路
- `os.path` / `pytra.std.os_path` / `pytra.std.os.path` の import 解決そのもの

## 実装で迷いやすい点

### 1. 何を消してよくて、何を消してはいけないか

消してよい:
- `py_os_path_join` などの wrapper 宣言/定義
- `pytra/std/os_path.h` からの `.ext.h` forward
- wrapper 名に依存する unit test

消してはいけない:
- `pytra::std::os_path::join` など namespace 実装
- `os.py` 側の `path` alias
- `os.path` module owner metadata
- public include `pytra/std/os_path.h` 自体

### 2. 2026-03-06 の暫定復旧で何が本当に必要だったか

必要だったもの:
- `os.path` を `pytra.std.os_path` module として回収する import / runtime module 追跡
- public shim header を compile-source 追跡対象に含めること

不要になったもの:
- `py_os_path_*` という free function wrapper ABI
- その宣言を保持する `os_path.ext.h`

### 3. `runtime_calls.json` の更新で壊しやすい点

- `os.path.join` を `pytra::std::os::path::join` にしてはいけない。正しい owner は `pytra::std::os_path`。
- `pytra.std.os.path` / `os.path` / `pytra.std.os_path` の 3 系統を揃えて更新する。
- `glob` の compile test は `os_path` 依存も含むので、`os_path` だけの局所 pass で終わらせない。

## フェーズ

### Phase 1: 依存の棚卸しと正本 API の固定

- `py_os_path_*` を参照する backend / runtime / test / docs を洗い出す。
- `pytra::std::os_path::*` を正本 API とし、`os_path.ext.h` を暫定互換層として扱う判断を計画書へ固定する。
- 2026-03-06 の復旧で必要だった修正と、今回退役させる互換 wrapper を分離して記録する。

### Phase 2: backend の呼び先を namespace API へ戻す

- `runtime_calls.json` の `pytra.std.os.path` / `os.path` / `pytra.std.os_path` を `pytra::std::os_path::*` へ更新する。
- `test_py2cpp_features.py` の `os_path` codegen assert を wrapper 名から namespace 名へ更新する。
- `math` と同様に「public module include + namespace call」で成立することを確認する。

### Phase 3: runtime 側の legacy wrapper を撤去する

- `src/runtime/cpp/std/os_path.ext.h` を削除する。
- `src/runtime/cpp/std/os_path.ext.cpp` から `py_os_path_*` 定義を削除し、`pytra::std::os_path::*` 実装だけを残す。
- `src/runtime/cpp/pytra/std/os_path.h` が `os_path.gen.h` のみを forward する状態へ戻ることを確認する。
- 必要なら `--emit-runtime-cpp` で `os.py` / `os_path.py` / `glob.py` を再生成し、public shim の出力が generic rule だけで成立することを確認する。

### Phase 4: compile-source / symbol index / import 経路の非退行確認

- `tools/gen_runtime_symbol_index.py --check` が通ることを確認する。
- `test_cpp_runtime_symbol_index_integration.py` と `test_pylib_os_glob.py` で、public header / compile-source 追跡が wrapper なしでも壊れないことを確認する。
- `os_glob_extended_runtime` を再確認し、2026-03-06 に止血した regressions が再発していないことを確認する。

### Phase 5: TODO / docs / archive を同期する

- 本 P0 の進捗と判断を `docs/ja/todo/index.md` と本計画書の `決定ログ` に記録する。
- 実装完了時は archive へ移す前に、「なぜ wrapper が要らなくなったか」を 1 行で残す。

## 受け入れ基準

- `src/backends/cpp/profiles/runtime_calls.json` に `py_os_path_*` が残らない。
- `src/runtime/cpp/std/os_path.ext.h` が存在しない。
- `src/runtime/cpp/std/os_path.ext.cpp` は `pytra::std::os_path::*` 実装だけを持ち、free function wrapper を持たない。
- `src/runtime/cpp/pytra/std/os_path.h` は `os_path.gen.h` だけを public include として forward する。
- `test_os_path_calls_use_runtime_helpers` 相当の codegen test が `pytra::std::os_path::*` を期待して通る。
- `test_os_glob_extended_runtime` と `test_pylib_os_glob.py` が通り、2026-03-06 の compile break が再発しない。
- `python3 tools/check_todo_priority.py` が通る。

## 検証コマンド

- `python3 tools/check_todo_priority.py`
- `python3 tools/gen_runtime_symbol_index.py --check`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k os_path`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k os_glob_extended_runtime`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_symbol_index_integration.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/pylib -p 'test_pylib_os_glob.py'`

## 分解

- [ ] [ID: P0-CPP-OSPATH-WRAPPER-RETIRE-01] C++ `os.path` の legacy wrapper ABI を退役し、`pytra::std::os_path::*` を codegen/runtime の正本へ戻す。

- [ ] [ID: P0-CPP-OSPATH-WRAPPER-RETIRE-01-S1-01] `py_os_path_*` 参照箇所を backend/runtime/test/docs で棚卸しし、残すべき import/module 追跡と退役対象 wrapper を分離する。
- [ ] [ID: P0-CPP-OSPATH-WRAPPER-RETIRE-01-S1-02] 2026-03-06 の暫定復旧のうち、今回保持する修正（module attr 回収・public shim compile-source 追跡）と消す修正（wrapper ABI）を決定ログへ固定する。

- [ ] [ID: P0-CPP-OSPATH-WRAPPER-RETIRE-01-S2-01] `runtime_calls.json` の `os.path` 系呼び先を `pytra::std::os_path::*` へ更新し、wrapper 名依存を backend から外す。
- [ ] [ID: P0-CPP-OSPATH-WRAPPER-RETIRE-01-S2-02] `test_py2cpp_features.py` の `os.path` codegen assert を namespace 正本へ更新し、`pytra::std::os::path::*` の誤 namespace を fail-fast 化する。

- [ ] [ID: P0-CPP-OSPATH-WRAPPER-RETIRE-01-S3-01] `src/runtime/cpp/std/os_path.ext.h` を削除し、public shim が `.ext.h` なしで成立することを確認する。
- [ ] [ID: P0-CPP-OSPATH-WRAPPER-RETIRE-01-S3-02] `src/runtime/cpp/std/os_path.ext.cpp` から `py_os_path_*` を削除し、namespace 実装だけを残す。
- [ ] [ID: P0-CPP-OSPATH-WRAPPER-RETIRE-01-S3-03] 必要な runtime 再生成と symbol index 更新を行い、`pytra/std/os_path.h` の include 面を単純化する。

- [ ] [ID: P0-CPP-OSPATH-WRAPPER-RETIRE-01-S4-01] `os_glob_extended_runtime` / runtime symbol index / pylib `glob` を再検証し、wrapper 退役後も compile-source/import 解決が壊れないことを確認する。
- [ ] [ID: P0-CPP-OSPATH-WRAPPER-RETIRE-01-S4-02] TODO と決定ログを更新し、「なぜ `os_path.ext.h` を消せたか」を文書化して完了扱いにする。

決定ログ:
- 2026-03-07: ユーザー指示により、`os_path.ext.h` は current design を表す正規ファイルではなく、2026-03-06 の unit 回帰復旧で追加された暫定互換層として整理し直す方針を固定した。
- 2026-03-07: 本計画では `pytra::std::os_path::*` を正本 API、`os_path.gen.h` を宣言の正本とし、`py_os_path_*` free function wrapper と `os_path.ext.h` は退役対象として扱う。
