# P0: ForCore tuple unpack 型伝播改善（EAST3 lowering / C++ emitter）

最終更新: 2026-02-27

関連 TODO:
- `docs-ja/todo/index.md` の `ID: P0-FORCORE-TYPE-01`

背景:
- `for line_index, source in enumerate(lines)` のような tuple unpack で、親の `target_type=tuple[int64, str]` は得られていても、`TupleTarget.elements` へ要素型が伝播されず `unknown` になる。
- その結果 C++ emitter 側では `py_at(...)` の戻りを `auto/object` で束縛し、`isdigit/isalpha` など文字列操作時に冗長キャストやコンパイル不整合を生みやすい。
- 現状は runtime 互換優先（fail-closed）で動作を守っているが、決定可能な型まで落とす必要はない。
- 上記改善後も `ForCore(RuntimeIterForPlan)` の loop carrier は `for (object __itobj : py_dyn_range(...))` に固定され、`enumerate(list[T])` のように要素型が確定していても header 段で型が落ちる。

目的:
- EAST3 lowering で tuple target の要素型を保持し、C++ emitter の `ForCore` tuple unpack で静的束縛できる箇所を `object` から縮退する。
- `enumerate(list[T])` など要素型が確定する runtime 反復では、loop header 自体を typed tuple で生成し、`object` carrier 依存を減らす。

対象:
- `src/pytra/compiler/east_parts/east2_to_east3_lowering.py`
- `src/hooks/cpp/emitter/stmt.py`
- `test/unit/test_east3_cpp_bridge.py`（必要に応じて関連 smoke）

非対象:
- 全面的な型推論エンジンの再設計
- `ForCore` 以外の構文（`Assign`/`with`/`match`）の型伝播再設計
- C++ runtime API の仕様変更

受け入れ基準:
- `target_type=tuple[...]` が解釈可能な場合、`TupleTarget.elements[].target_type` へ要素型が設定される。
- C++ `ForCore` tuple unpack で要素型が既知なら `int64/str/...` で直接束縛される。
- C++ `ForCore(RuntimeIterForPlan)` で `iter_expr` が `enumerate(list[T])` 等の既知型 iterable のとき、loop header が typed tuple（例: `const std::tuple<int64, str>&`）で生成される。
- 要素型が不明・不整合な場合は従来どおり `object` フォールバックし、fail-closed を維持する。
- `check_py2cpp_transpile.py` と `sample/18` の変換・コンパイルが通る。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `python3 -m unittest discover -s test/unit -p 'test_east2_to_east3_lowering.py' -v`
- `python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 src/py2cpp.py sample/py/18_mini_language_interpreter.py -o /tmp/18.cpp --dump-east3-before-opt /tmp/18.east3.before.json`
- `RUNTIME_SRCS=$(python3 - <<'PY'`<br>`from pathlib import Path`<br>`root = Path('/workspace/Pytra')`<br>`paths = [p.as_posix() for p in sorted((root/'src'/'runtime'/'cpp'/'base').glob('*.cpp'))]`<br>`paths += [p.as_posix() for p in sorted((root/'src'/'runtime'/'cpp'/'pytra').rglob('*.cpp'))]`<br>`print(' '.join(paths))`<br>`PY`<br>`) ; g++ -std=c++20 -O2 -I src/runtime/cpp -I src /tmp/18.cpp $RUNTIME_SRCS -o /tmp/pytra_sample18_cpp`

決定ログ:
- 2026-02-27: ユーザー質問（型落ち理由）を受け、`ForCore` tuple unpack の要素型伝播不足を独立タスク `P0-FORCORE-TYPE-01` として管理する方針を確定。
- 2026-02-27: [ID: `P0-FORCORE-TYPE-01-S1-01`] `east2_to_east3_lowering` に tuple 型分解（`tuple[...] -> elements[]`）を実装し、`For` lowering で `target_type=unknown` のとき `iter_element_type` を補助利用して `TupleTarget.elements[].target_type` を埋めるよう更新した。
- 2026-02-27: [ID: `P0-FORCORE-TYPE-01-S1-02`] C++ `stmt.py` の `ForCore` tuple unpack で、要素 `target_type` が unknown の場合は親 `target_type=tuple[...]` から要素型を復元して `int64/str/...` 束縛を選び、復元不能時のみ `auto/object` にフォールバックするよう更新した。
- 2026-02-27: [ID: `P0-FORCORE-TYPE-01-S2-01`] `test_east2_to_east3_lowering.py` に tuple target 型伝播テスト 2件、`test_east3_cpp_bridge.py` に `ForCore` tuple unpack（既知型束縛 / unknown フォールバック）テスト 2件を追加した。
- 2026-02-27: [ID: `P0-FORCORE-TYPE-01-S2-02`] `python3 -m unittest discover -s test/unit -p 'test_east2_to_east3_lowering.py' -v`（`22/22`）/ `python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -v`（`80/80`）/ `python3 tools/check_py2cpp_transpile.py`（`checked=133 ok=133 fail=0 skipped=6`）を確認。`py2cpp` で `sample/18` を `/tmp/18.cpp` へ生成し、`tokenize` で `int64 line_index` / `str source` が出ることと、`/tmp/pytra_sample18_cpp` コンパイル・実行成功を確認した。
- 2026-02-27: [ID: `P0-FORCORE-TYPE-01-S3-01`] ユーザー要望に基づき、`enumerate(list[T])` など既知型 runtime iterable で loop header が `object` になる問題を最優先で解消する方針を追加した。

## 分解

- [x] [ID: P0-FORCORE-TYPE-01-S1-01] `target_type=tuple[...]` の要素型を `TupleTarget.elements` へ伝播する lowering 補助を実装する。
- [x] [ID: P0-FORCORE-TYPE-01-S1-02] C++ tuple unpack emit で要素型既知時に静的束縛し、未知時のみ `object` フォールバックする。
- [x] [ID: P0-FORCORE-TYPE-01-S2-01] `enumerate(list[str])` を含む回帰テストを追加し、生成コードの型束縛を固定する。
- [x] [ID: P0-FORCORE-TYPE-01-S2-02] transpile + sample コンパイル検証を実行し、文脈ファイルへ結果を記録する。
- [ ] [ID: P0-FORCORE-TYPE-01-S3-01] `ForCore(RuntimeIterForPlan)` の typed iterable fastpath を実装し、`enumerate(list[T])` の loop header を typed tuple へ切り替える。
- [ ] [ID: P0-FORCORE-TYPE-01-S3-02] typed header fastpath の回帰テスト（unit + `sample/18` 生成確認）を追加して固定する。
