# P0: stdlib 型仕様の正本化（core 直書き撤去）

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-STDLIB-SOT-01`
- `docs/ja/todo/index.md` の `ID: P0-STDLIB-SOT-02`

背景:
- 現在 `src/pytra/compiler/east_parts/core.py` に `perf_counter -> float64` など標準ライブラリ仕様が直書きされている。
- `pytra/std/time.py` などライブラリ実装側にも型情報が存在し、仕様の二重管理になっている。
- 仕様の正本が compiler 側に分散すると、`pytra/std` 変更時に compiler 側追従漏れが発生しやすい。

目的:
- 標準ライブラリ型仕様の正本を `pytra/std` 側に一本化し、`core.py` は参照者へ縮退する。
- `core.py` から標準ライブラリ個別知識（`perf_counter` / `Path` / `str.*` など）の直書きを段階撤去する。

対象:
- `src/pytra/compiler/east_parts/core.py`
- `src/pytra/std/`（型仕様の参照元）
- `src/pytra/compiler/` 配下の stdlib シグネチャ参照層（新設）
- `test/unit` の型推論・lowering 回帰

非対象:
- 全 backend の同時大改修
- stdlib API 自体の仕様変更
- runtime 実装最適化

受け入れ基準:
- `core.py` にある `perf_counter` など標準ライブラリ戻り値型の直書きが参照層経由へ置換される。
- `pytra/std` 側シグネチャを変更した際に compiler 側へ反映される（重複定義を持たない）。
- 既存の transpile/smoke テストが回帰しない。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 -m unittest discover -s test/unit -p 'test_*core*.py' -v`
- `python3 -m unittest discover -s test/unit -p 'test_py2cpp_smoke.py' -v`

決定ログ:
- 2026-02-28: ユーザー指示により、`pytra/std` を型仕様の唯一正本にし、`core.py` の標準ライブラリ知識を撤去する P0 方針を確定した。
- 2026-02-28: [ID: `P0-STDLIB-SOT-01-S1-01`] `core.py` の標準ライブラリ直書きを棚卸しし、置換対象を「組み込み関数 map」「owner 型別 method map」「`perf_counter` 戻り値直書き」に分類して固定した。
- 2026-02-28: [ID: `P0-STDLIB-SOT-01-S1-02`] `docs/ja/spec/spec-stdlib-signature-source-of-truth.md` を追加し、正本/参照境界、取得単位、fail-closed を文書化した。
- 2026-02-28: [ID: `P0-STDLIB-SOT-01-S2-01`] `src/pytra/compiler/stdlib/signature_registry.py` を新設し、`pytra/std/*.py` から関数/メソッド戻り値注釈を読み取る参照層を追加した。
- 2026-02-28: [ID: `P0-STDLIB-SOT-01-S2-02`] `core.py` の `perf_counter -> float64` 直書きを廃止し、`lookup_stdlib_function_return_type("perf_counter")` 参照へ置換した。`test_stdlib_signature_registry.py`、`test_east_core.py` の新規ケース、`test_py2cpp_codegen_issues.py` の既存 perf_counter 回帰で確認した。
- 2026-02-28: [ID: `P0-STDLIB-SOT-01-S2-03`] `str/Path/int/list/set/dict/unknown` の method runtime map と `Path` 属性型 map を `signature_registry.py` へ移管し、`core.py` から巨大 map 直書きを撤去した。`test_stdlib_signature_registry.py` と `test_east_core.py` の既存 lower 回帰で挙動維持を確認した。
- 2026-03-01: [ID: `P0-STDLIB-SOT-02`] 完了扱いだったが、`core.py` に `fn_name == "perf_counter"` 直分岐が残存していたため再オープン。`core.py` からの `perf_counter` 文字列依存を完全撤去し、再混入を防ぐ回帰を追加する方針を確定した。

## 棚卸し結果（S1-01）

- 組み込み関数 call 直書き:
  - `print/len/range/zip/str/int/float/bool/min/max/perf_counter/open/iter/next/reversed/enumerate/any/all/ord/chr/bytes/bytearray/list/set/dict`
- 例外/特殊 call 直書き:
  - `Exception/RuntimeError -> std::runtime_error`
  - `Path -> Path`
- owner 型別 method map 直書き:
  - `str`: `strip/lstrip/rstrip/startswith/endswith/find/rfind/replace/join/isdigit/isalpha`
  - `Path`: `mkdir/exists/write_text/read_text/parent/name/stem`
  - `int`: `to_bytes`
  - `list`: `append/extend/pop/clear/reverse/sort`
  - `set`: `add/discard/remove/clear`
  - `dict`: `get/pop/items/keys/values`
  - `unknown`: `append/extend/pop/get/items/keys/values/isdigit/isalpha`

## 分解

- [x] [ID: P0-STDLIB-SOT-01-S1-01] `core.py` の標準ライブラリ知識直書き箇所（`perf_counter` / `Path` / `str.*` / `dict.*` 等）を棚卸しし、置換対象を固定する。
- [x] [ID: P0-STDLIB-SOT-01-S1-02] `pytra/std` を正本とするシグネチャ参照仕様（取得単位・型表現・未定義時の fail-closed）を文書化する。
- [x] [ID: P0-STDLIB-SOT-01-S2-01] compiler 側に stdlib シグネチャ参照層を新設し、`core.py` から直接文字列マップを参照しない構成へ切り替える。
- [x] [ID: P0-STDLIB-SOT-01-S2-02] `perf_counter` を含む代表ケースを参照層経由へ移し、`core.py` の戻り値型直書きを撤去する。
- [x] [ID: P0-STDLIB-SOT-01-S2-03] `Path` / `str.*` などメソッド系マッピングを段階移行し、`core.py` の責務を構文解析+EAST整形へ限定する。
- [x] [ID: P0-STDLIB-SOT-01-S3-01] 回帰テスト（型推論・lowering・sample 代表ケース）を追加し、`pytra/std` 仕様変更時の検知を固定する。
- [ ] [ID: P0-STDLIB-SOT-02] `core.py` の `fn_name == "perf_counter"` 直分岐を撤去し、stdlib シグネチャ参照層へ一本化する。
- [ ] [ID: P0-STDLIB-SOT-02-S1-01] `core.py` から `perf_counter` 文字列依存を削除し、`BuiltinCall` 判定を import 解決情報または共通 resolver 経由へ移行する。
- [ ] [ID: P0-STDLIB-SOT-02-S1-02] `test_east_core.py` に再混入防止回帰を追加する。
- [ ] [ID: P0-STDLIB-SOT-02-S2-01] `test_py2cpp_codegen_issues.py` と `check_py2cpp_transpile.py` で非退行を確認する。
