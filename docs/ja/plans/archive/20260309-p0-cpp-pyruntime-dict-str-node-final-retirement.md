# P0: C++ `py_runtime.h` 残存 `dict_get_node(dict<str, str>)` 最終退役

最終更新: 2026-03-09

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-DICT-STR-NODE-FINAL-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [archive/20260308-p0-cpp-pyruntime-dict-str-node-retirement.md](./archive/20260308-p0-cpp-pyruntime-dict-str-node-retirement.md)

背景:
- 過去 tranche で `dict_get_node(dict<str, str>, ...)` の overload は大きく削ったが、[py_runtime.h](../../src/runtime/cpp/native/core/py_runtime.h) には canonical 1 本がまだ残っている。
- これは `dict<str, str>` に対する薄い sugar であり、`find` と同値である。
- もし checked-in callsite が無いか、ごく限定的なら、`py_runtime.h` から完全に外して callsite 側 explicit lookup へ寄せられる。

目的:
- 残存 `dict_get_node(dict<str, str>, ...)` の checked-in callsite を棚卸しし、不要であれば完全削除する。
- もし selfhost artifact 等で残るなら、残す理由を決定ログへ固定する。

対象:
- `src/runtime/cpp/native/core/py_runtime.h` の `dict_get_node(const dict<str, str>&, ...)`
- checked-in callsite と representative tests

非対象:
- `dict<str, object>` 系 helper
- `JsonObj` API

受け入れ基準:
- 残存 `dict_get_node(dict<str, str>, ...)` の checked-in callsite が明確になっている。
- callsite が explicit lookup へ置換されるか、残置理由が固定されている。
- 可能なら helper 自体が削除され、inventory guard で再侵入を防いでいる。

確認コマンド:
- `PYTHONPATH=src python3 test/unit/backends/cpp/test_cpp_runtime_iterable.py`
- `PYTHONPATH=src python3 test/unit/backends/cpp/test_py2cpp_codegen_issues.py`
- `python3 tools/check_todo_priority.py`

## フェーズ

### Phase 1: 棚卸し

- `dict_get_node(` の checked-in callsite を棚卸しする。
- selfhost / generated artifact 依存が残るかどうかを確認する。

### Phase 2: 置換または最終判断

- representative callsite を `find` / `contains` ベースの explicit lookup へ置換する。
- 置換できない場合は残置理由を決定ログへ固定する。

### Phase 3: helper 削除と固定

- 削除可能なら `py_runtime.h` から helper を削除する。
- inventory guard / docs / archive を更新する。

## タスク分解

- [x] [ID: P0-CPP-PYRUNTIME-DICT-STR-NODE-FINAL-01] 残存 `dict_get_node(dict<str, str>)` を最終整理する。
- [x] [ID: P0-CPP-PYRUNTIME-DICT-STR-NODE-FINAL-01-S1-01] checked-in callsite を棚卸しする。
- [x] [ID: P0-CPP-PYRUNTIME-DICT-STR-NODE-FINAL-01-S1-02] 削除可否と残置条件を決定ログへ固定する。
- [x] [ID: P0-CPP-PYRUNTIME-DICT-STR-NODE-FINAL-01-S2-01] representative callsite を explicit lookup へ置換する。
- [x] [ID: P0-CPP-PYRUNTIME-DICT-STR-NODE-FINAL-01-S2-02] helper を削除または残置理由を確定する。
- [x] [ID: P0-CPP-PYRUNTIME-DICT-STR-NODE-FINAL-01-S3-01] guard / docs / archive を更新する。

## 決定ログ

- 2026-03-09: 以前の tranche は overload 削減までで止めており、canonical `dict_get_node(dict<str, str>, ...)` 1 本は未整理で残っている。今回は「完全削除できるか」の最終判定を目的にし、残す場合でも理由を明示的に固定する。
- 2026-03-09: checked-in source を棚卸しすると direct callsite は見つからず、残っていたのは runtime inventory guard だけだった。`backend_registry_static` は `dict<str, str>` を受けるが helper 自体は使っていないため、representative callsite 置換は不要と判断した。
- 2026-03-09: `src/runtime/cpp/native/core/py_runtime.h` から canonical `dict_get_node(const dict<str, str>&, ...)` を削除し、`test_cpp_runtime_iterable.py` の inventory guard を `NotIn` へ反転した。
