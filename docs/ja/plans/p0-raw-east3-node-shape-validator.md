# P0: raw EAST3 validator の node-shape 誤判定を解消する

最終更新: 2026-03-13

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-RAW-EAST3-NODE-SHAPE-VALIDATOR-01`

背景:
- backend test matrix の current snapshot では、`rs` が `any_dict_items` で `raw EAST3 $.body[1].meta.lifetime_analysis.def_use.defs.meta must be an object`、`scala` と `cpp` が `18_mini_language_interpreter` で `raw EAST3 $.body[5].body[5].arg_index.kind must be non-empty string` により fail している。
- どちらも backend 固有 bug ではなく、`src/toolchain/link/program_validator.py` の raw EAST3 invariant check が「任意の dict に現れた `kind` / `meta` キー」を node field と誤認しているのが原因である。
- `lifetime_analysis.def_use.defs["meta"]` は def-use map の変数名であり node metadata ではない。同様に `arg_index["kind"]` も auxiliary map の key であり EAST node kind ではない。
- この誤判定は frontend 共通経路で起きるため、一度直せば `rs/java/rb/scala/cpp` を含む複数 backend の smoke fail をまとめて削減できる。

目的:
- raw EAST3 validator が node-shaped dict だけに `kind` / `meta` / `source_span` / `repr` の invariant を適用するように狭める。
- auxiliary analysis map や index map の key 名 `meta` / `kind` で false positive にならないことを regression test で固定する。
- `any_dict_items` と `18_mini_language_interpreter` が raw validator で止まらず、backend transpile 経路まで進めることを targeted verification で確認する。

対象:
- `src/toolchain/link/program_validator.py`
- `test/unit/common/test_frontend_type_expr.py`
- 必要なら representative smoke / docs / matrix 補足

非対象:
- backend emitter 固有 bug の修正
- `18_mini_language_interpreter` の後段 backend compile/run 品質改善
- raw EAST3 validator 全面再設計

受け入れ基準:
- `validate_raw_east3_doc()` は auxiliary map の `defs["meta"]` や `arg_index["kind"]` を node field と誤認しない。
- 実 node 上の `kind` / `meta` / `source_span` / `dispatch_mode` drift fail-closed は維持される。
- `test/fixtures/typing/any_dict_items.py` と `sample/py/18_mini_language_interpreter.py` が raw EAST3 validator を通過する regression test を持つ。
- targeted transpile として `py2x --target rs/java/ruby/scala/cpp` が少なくとも raw EAST3 validator では止まらない。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src:/workspace/Pytra/test/unit python3 -m unittest discover -s test/unit/common -p 'test_frontend_type_expr.py'`
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src:/workspace/Pytra/test/unit python3 src/py2x.py --target rs test/fixtures/typing/any_dict_items.py -o /tmp/any_dict_items.rs`
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src:/workspace/Pytra/test/unit python3 src/py2x.py --target java test/fixtures/typing/any_dict_items.py -o /tmp/AnyDictItems.java`
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src:/workspace/Pytra/test/unit python3 src/py2x.py --target ruby test/fixtures/typing/any_dict_items.py -o /tmp/any_dict_items.rb`
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src:/workspace/Pytra/test/unit python3 src/py2x.py --target scala sample/py/18_mini_language_interpreter.py -o /tmp/MiniLanguageInterpreter.scala`
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src:/workspace/Pytra/test/unit python3 src/py2x.py --target cpp sample/py/18_mini_language_interpreter.py -o /tmp/mini_language_interpreter.cpp`
- `git diff --check`

実施方針:
1. validator を緩めるのではなく、「node-shaped dict を正しく識別する」方向で修正する。
2. auxiliary map を skip しても、body item や expression field 配下の actual node validation は落とさない。
3. 先に regression test を足し、その後 validator を直す。
4. matrix/smoke の改善は targeted verify で確認し、必要なら次の bundle で test matrix snapshot へ反映する。

## 分解

- [ ] [ID: P0-RAW-EAST3-NODE-SHAPE-VALIDATOR-01] raw EAST3 validator の node-shape 誤判定を解消し、auxiliary map の `meta` / `kind` key で false positive を出さない。
- [x] [ID: P0-RAW-EAST3-NODE-SHAPE-VALIDATOR-01-S1-01] `any_dict_items` / `18_mini_language_interpreter` と synthetic auxiliary-map case を regression test と plan に固定する。
- [x] [ID: P0-RAW-EAST3-NODE-SHAPE-VALIDATOR-01-S2-01] raw EAST3 validator を node-shaped dict 限定へ狭め、actual node fail-closed を維持する。
- [ ] [ID: P0-RAW-EAST3-NODE-SHAPE-VALIDATOR-01-S2-02] targeted backend transpile verification と TODO/decision log を同期し、matrix 上の validator-origin failure を close state へ寄せる。

決定ログ:
- 2026-03-13: TODO が空になったため、新しい P0 seed として backend test matrix の current red から frontend common cause を選んだ。`any_dict_items` と `18_mini_language_interpreter` の raw EAST3 validator false positive を優先する。
- 2026-03-13: `S1-01` で `test_frontend_type_expr.py` に synthetic auxiliary-map regression と actual fixture/sample load regression を追加した。`defs["meta"]` と `arg_index["kind"]` が false positive にならないことを raw validator unit と real input load の両方で固定した。
- 2026-03-13: `S2-01` で `program_validator.py` の object walk に `parent_key` を通し、body/value/target など node container 配下または node hint key を持つ dict だけを EAST3 node と見なすようにした。`py2x --target rs/java/ruby any_dict_items` と `py2x --target scala/cpp 18_mini_language_interpreter` は raw validator で止まらず出力まで進むことを確認した。
