<a href="../../../en/plans/archive/20260309-p0-cpp-pyruntime-list-item-cast-retirement.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: C++ `py_runtime.h` `py_list_item_cast` 退役

最終更新: 2026-03-09

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-LISTITEMCAST-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [spec-dev.md](../spec/spec-dev.md)

背景:
- `py_runtime.h` には `py_list_item_cast(const object&)`, `py_list_item_cast(const char*)`, `py_list_item_cast(const U&)` が残っている。
- これらは list mutation helper (`py_list_append_mut`, `py_list_set_at_mut`) の入力正規化を helper 側で吸収する薄い sugar であり、core runtime に置く理由が弱い。
- 実体は `py_to<T>(object)` と `make_object(str(...))` の呼び分けでしかなく、policy が helper 名に隠れているため callsite 側の型責務が見えにくい。
- 今後 `object` carrier をさらに縮退するには、「list item をどこで typed 化するか」を helper ではなく lowering / callsite で説明できる形へ寄せる必要がある。

目的:
- `py_list_item_cast` を `py_runtime.h` から除去し、list item の typed 化を `py_list_append_mut` / `py_list_set_at_mut` の本体または caller 側の explicit conversion へ寄せる。
- list mutation の型責務を helper 名ではなく actual conversion 式で読めるようにする。

非対象:
- `py_to<T>(object)` 本体の設計変更
- `make_object(...)` 群の再設計
- list primitive (`py_list_append_mut`, `py_list_set_at_mut`) 自体の削除

受け入れ基準:
- `py_runtime.h` から `py_list_item_cast` 3 本が削除される。
- checked-in caller は list mutation helper または emitter 側の explicit conversion に置換される。
- representative C++ runtime / backend test が非退行で通る。

確認コマンド:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_cpp_runtime_iterable.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check/runtime_parity_check.py --targets cpp --case-root fixture`

## 1. 方針

1. `py_list_item_cast` の checked-in callsite を棚卸しし、runtime 内 helper 自身に閉じた use だけなのか、emitter/generated まで広がっているのかを固定する。
2. list item の typed 化は helper 名に逃がさず、`py_to<T>(item)` または `py_to<T>(make_object(str(...)))` を直接呼ぶ形に置換する。
3. 置換後に同等の helper 名を別 header へ逃がさない。

## 2. フェーズ

### Phase 1: 棚卸し
- `py_list_item_cast` の checked-in caller を列挙する。
- list mutation helper 側へ inline するか、caller 側へ押し戻すかを決定する。

### Phase 2: 置換
- representative callsite を explicit conversion に置換する。
- regression / inventory guard を更新する。

### Phase 3: 退役
- `py_runtime.h` から helper を削除し、parity / docs / archive を閉じる。

## 3. タスク分解

- [x] [ID: P0-CPP-PYRUNTIME-LISTITEMCAST-01] `py_list_item_cast` を退役する。
- [x] [ID: P0-CPP-PYRUNTIME-LISTITEMCAST-01-S1-01] `py_list_item_cast` の checked-in callsite を棚卸しする。
- [x] [ID: P0-CPP-PYRUNTIME-LISTITEMCAST-01-S1-02] list item conversion の canonical rule を決定ログに固定する。
- [x] [ID: P0-CPP-PYRUNTIME-LISTITEMCAST-01-S2-01] representative callsite を explicit conversion へ置換する。
- [x] [ID: P0-CPP-PYRUNTIME-LISTITEMCAST-01-S2-02] regression / inventory guard を更新する。
- [x] [ID: P0-CPP-PYRUNTIME-LISTITEMCAST-01-S3-01] `py_runtime.h` から `py_list_item_cast` を削除する。
- [x] [ID: P0-CPP-PYRUNTIME-LISTITEMCAST-01-S3-02] parity / docs / archive を更新して閉じる。

## 4. 決定ログ

- 2026-03-09: 本計画は `py_list_item_cast` helper 名の退役を目的とし、`py_to<T>(object)` と `make_object(...)` の core conversion は非対象に維持する。
- 2026-03-09: checked-in callsite は `py_runtime.h` 内の `py_list_append_mut` と `py_list_set_at_mut` だけで、generated / emitter / sample / test code に direct callsite は無かった。
- 2026-03-09: canonical rule は「list item の typed 化は `py_list_append_mut` / `py_list_set_at_mut` 本体へ inline し、`object` は `py_to<T>(item)`、`const char*` は `str(...)` または `py_to<T>(make_object(str(...)))`、その他は explicit constructor / cast で吸収する」と固定した。
- 2026-03-09: `src/runtime/cpp/native/core/py_runtime.h` から `py_list_item_cast` declaration/definition 3 本を削除し、`test_cpp_runtime_iterable.py` に removed inventory guard を追加した。
- 2026-03-09: verification は `test_cpp_runtime_iterable.py`, `test_py2cpp_codegen_issues.py`, fixture parity `cases=3 pass=3 fail=0`, `check_todo_priority.py`, `git diff --check` を通した。
