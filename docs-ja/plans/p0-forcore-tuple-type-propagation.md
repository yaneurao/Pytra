# P0: ForCore tuple unpack 型伝播改善（EAST3 lowering / C++ emitter）

最終更新: 2026-02-27

関連 TODO:
- `docs-ja/todo/index.md` の `ID: P0-FORCORE-TYPE-01`

背景:
- `for line_index, source in enumerate(lines)` のような tuple unpack で、親の `target_type=tuple[int64, str]` は得られていても、`TupleTarget.elements` へ要素型が伝播されず `unknown` になる。
- その結果 C++ emitter 側では `py_at(...)` の戻りを `auto/object` で束縛し、`isdigit/isalpha` など文字列操作時に冗長キャストやコンパイル不整合を生みやすい。
- 現状は runtime 互換優先（fail-closed）で動作を守っているが、決定可能な型まで落とす必要はない。

目的:
- EAST3 lowering で tuple target の要素型を保持し、C++ emitter の `ForCore` tuple unpack で静的束縛できる箇所を `object` から縮退する。

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
- 要素型が不明・不整合な場合は従来どおり `object` フォールバックし、fail-closed を維持する。
- `check_py2cpp_transpile.py` と `sample/18` の変換・コンパイルが通る。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 src/py2cpp.py sample/py/18_mini_language_interpreter.py --output-dir sample/cpp --no-runtime`
- `g++ -std=c++20 -O2 -I src/runtime/cpp sample/cpp/18_mini_language_interpreter.cpp -o /tmp/pytra_sample18_cpp`

決定ログ:
- 2026-02-27: ユーザー質問（型落ち理由）を受け、`ForCore` tuple unpack の要素型伝播不足を独立タスク `P0-FORCORE-TYPE-01` として管理する方針を確定。

## 分解

- [ ] [ID: P0-FORCORE-TYPE-01-S1-01] `target_type=tuple[...]` の要素型を `TupleTarget.elements` へ伝播する lowering 補助を実装する。
- [ ] [ID: P0-FORCORE-TYPE-01-S1-02] C++ tuple unpack emit で要素型既知時に静的束縛し、未知時のみ `object` フォールバックする。
- [ ] [ID: P0-FORCORE-TYPE-01-S2-01] `enumerate(list[str])` を含む回帰テストを追加し、生成コードの型束縛を固定する。
- [ ] [ID: P0-FORCORE-TYPE-01-S2-02] transpile + sample コンパイル検証を実行し、文脈ファイルへ結果を記録する。
