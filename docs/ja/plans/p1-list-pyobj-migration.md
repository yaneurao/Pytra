# P1: C++ `list` の PyObj/RC モデル移行（段階導入）

最終更新: 2026-02-28

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-LIST-PYOBJ-MIG-01`
- 依存: `ID: P1-EAST3-NONESCAPE-IPA-01`（関数間 non-escape 注釈）

背景:
- 現行 C++ runtime の `list<T>` は `std::vector<T>` ラッパの値モデルであり、`rc<PyObj>` 管理の対象ではない。
- `Any/object` 境界に入ると `PyListObj(list<object>)` へ boxing されるが、静的型経路は値コピー中心で Python の参照セマンティクスとの差分が残る。
- ユーザー方針として、`list` を PyObj/RC モデルへ寄せたうえで non-escape 経路のみ RAII/stack 最適化で縮退したい。

目的:
- `list` を「既定で PyObj/RC 管理される参照モデル」に移行する。
- ただし移行初期は fail-closed と互換を優先し、段階導入（dual model）で回帰面積を管理する。
- 最終的に `EAST3 non-escape` 注釈と接続し、局所 non-escape 経路のみ stack/RAII 化できる下地を作る。

対象:
- C++ runtime:
  - `src/runtime/cpp/pytra-core/built_in/list.h`
  - `src/runtime/cpp/pytra-core/built_in/py_runtime.h`
  - 必要に応じて `dict.h`/`set.h`（`list` 依存箇所のみ）
- C++ backend:
  - `src/hooks/cpp/emitter/*`
  - `src/hooks/cpp/optimizer/*`（RAII 縮退 pass 追加時）
- EAST3 optimizer:
  - `P1-EAST3-NONESCAPE-IPA-01` の注釈利用
- テスト/検証:
  - `test/unit/test_cpp_runtime_*`
  - `test/unit/test_py2cpp_*`
  - `tools/check_py2cpp_transpile.py`
  - `tools/runtime_parity_check.py`

非対象:
- `str/dict/set` の同時 PyObj 化（本タスクでは扱わない）
- 全 backend への同時展開
- aggressive 最適化（意味保存証明なしの置換）

設計方針:
- 方針A（移行初期）: dual model
  - `list` の旧値モデルをすぐ削除せず、backend オプションで `value` / `pyobj` を切替可能にする。
  - 既定は段階的に切替（最初は `value` 維持、回帰固定後 `pyobj` へ変更）。
- 方針B（安全側）: fail-closed
  - 変換不能・型不明・外部呼び出し絡みは `pyobj` 継続、stack 化しない。
- 方針C（責務分離）:
  - EAST3 は「non-escape 判定注釈」まで。
  - 実際の `pyobj -> stack` 置換は C++ optimizer/emitter 側で適用。

## フェーズ計画

### Phase 0: 仕様固定・差分可視化

- `list` 参照セマンティクスの契約（代入 alias / 引数共有 / 返り値共有）を文書化する。
- 既存 fixture/sample で「値コピー前提」になっている箇所を棚卸しする。
- alias 期待ケース（`a = b; b.append(...)`）を回帰テストとして追加し、現状差分を明示する。

### Phase 1: runtime に PyObj list モデルを導入（互換共存）

- `list` の PyObj 側実装（テンプレート or wrapper）を追加し、RC で管理可能にする。
- `make_object` / `obj_to_*` / iterable hook を新 list モデルへ接続する。
- 旧モデルとの相互変換（必要最小）を置き、段階切替中の compile break を抑える。

### Phase 2: backend の list 生成を model switch 化

- C++ emitter の型出力・リテラル・append/pop/for-range を model switch 経由へ統一。
- `--cpp-list-model {value,pyobj}`（仮名）を追加し、生成物を明示的に比較可能にする。
- `sample/18` を含む representative cases で `pyobj` モデルの compile/run/parity を成立させる。

### Phase 3: non-escape 注釈との接続（RAII 縮退）

- `P1-EAST3-NONESCAPE-IPA-01` の `meta` 注釈を C++ 側へ受け渡す。
- non-escape が証明できる local list のみ stack/RAII へ縮退する pass を追加する。
- unknown/external/dynamic call 混在時は常に heap(pyobj) を維持する。

### Phase 4: 既定切替と後片付け

- 回帰（transpile/smoke/parity/perf）通過後、既定を `pyobj` へ切替。
- 旧値モデルの暫定互換コードを段階撤去する（ただし rollback 可能な期間を設ける）。
- docs/spec/how-to-use へ運用差分を同期する。

#### S4-03 確定: 旧 `value` 互換コードの撤去計画

- 互換コードの対象（撤去候補）
  - C++ emitter の `cpp_list_model == "value"` 分岐（型描画/collection op/for lower の value 専用分岐）
  - runtime の `list<T>(object)` / `obj_to_list<T>` など value 側 bridge
  - `py2cpp` の rollback オプション（`--cpp-list-model value`）
- 撤去の段階
  - Stage A（現行）: `pyobj` を既定化し、`value` は rollback 専用で維持。
  - Stage B（次ID）: `value` 分岐の利用実態を `sample + fixture + selfhost` で再計測し、未使用/低使用を確認。
  - Stage C（次ID）: emitter の value 専用分岐を段階撤去し、`pyobj` 単一路へ縮退。
  - Stage D（次ID）: runtime bridge（`list<T>(object)` など）を最小化し、不要経路を削除。
  - Stage E（次ID）: `--cpp-list-model value` を削除し、CLI 契約を `pyobj` 固定へ更新。
- 別ID起票条件（fail-closed）
  - `value` 撤去で `check_py2cpp_transpile` / `runtime_parity_check --targets cpp` / selfhost のいずれかに退行が出る場合。
  - `list` 以外（`dict/set/tuple`）へ同時波及し、変更半径が本IDの受け入れ基準を超える場合。
  - 既存ユーザー導線で rollback 必須ケースが残り、段階的 deprecation 期間の明示が必要な場合。

## 受け入れ基準

- `pyobj` list モデルで `check_py2cpp_transpile` と C++ smoke が通る。
- alias 期待ケースが Python と一致する。
- `sample/py` 主要ケースで `runtime_parity_check --targets cpp` が非退行。
- non-escape 不明経路は stack 化されず fail-closed を維持する。
- `value` / `pyobj` の差分比較ログが取得でき、既定切替判断材料が揃う。

## リスクと対策

- リスク: 型シグネチャ連鎖変更で compile break 多発。
  - 対策: dual model + 切替フラグ + small-batch migration。
- リスク: RC 増加による性能劣化。
  - 対策: non-escape 注釈を利用した限定 RAII 縮退を同計画で実施。
- リスク: `Any/object` 境界と静的型経路の二重実装化。
  - 対策: list model switch の入口を emitter 基底ヘルパへ集約し分岐点を一本化。

## 検証コマンド（予定）

- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2cpp_transpile.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_cpp_runtime_*.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_*.py' -v`
- `python3 tools/runtime_parity_check.py --case-root sample --targets cpp --all-samples --ignore-unstable-stdout`

決定ログ:
- 2026-02-28: ユーザー指示により、`str/dict/set` へ広げる前に `list` 単体で PyObj/RC モデル移行を優先する方針を確定した。
- 2026-02-28: 移行リスク抑制のため、`value/pyobj` dual model を前提に段階切替する方針を採用した。
- 2026-02-28: `docs/ja/spec/spec-cpp-list-reference-semantics.md` を新設し、現行 `value model` 契約（コピー代入）と移行先 `pyobj model` 契約（alias 共有）を明文化した。
- 2026-02-28: alias 期待 fixture `test/fixtures/collections/list_alias_shared_mutation.py` を追加し、`python3 tools/runtime_parity_check.py --case-root fixture --targets cpp list_alias_shared_mutation` で `output mismatch`（Python=`True`, C++=`False`）を確認して差分を固定した。
- 2026-02-28: `sample/py` + `test/fixtures` を AST スキャンし、list 型注釈を持つ `name = name` 代入の候補を棚卸しした結果、現時点の候補は `test/fixtures/collections/list_alias_shared_mutation.py:7 (b = a)` の 1 件のみだった。
- 2026-02-28: runtime の `PyListIterObj` を owner list 参照型へ拡張し、`PyListObj::py_iter_or_raise()` が snapshot ではなく owner 実体を保持する iterator を返すよう変更した。
- 2026-02-28: `test_cpp_runtime_iterable.py` に「反復中 `py_append` した要素を iterator が観測する」回帰を追加し、`test_cpp_runtime_iterable.py` / `test_cpp_runtime_boxing.py` の runtime compile-run テストがともに通過することを確認した。
- 2026-02-28: `obj_to_list_obj()` を runtime へ追加し、`obj_to_list_ptr` / `py_append` を PyListObj 取得ヘルパ経由へ集約した。加えて `make_object(const list<object>&)` / `make_object(list<object>&&)` を追加し、list<object> boxing の直接経路を導入した。
- 2026-02-28: `test_cpp_runtime_boxing.py` に `obj_to_list_obj` 回帰を追加し、runtime compile-run テストが通過することを確認した。
- 2026-02-28: 旧値モデル互換ブリッジとして `list<T>(object)` 経路が維持されることを `test_cpp_runtime_boxing.py` で固定した（`list<int64> legacy_list = list<int64>(as_list)` が動作し、PyListObj 側サイズが不変であることを確認）。
- 2026-02-28: runtime 単体テストに list モデル回帰（owner 連動 iterator / `obj_to_list_obj` / legacy bridge）を追加し、`test_cpp_runtime_iterable.py` と `test_cpp_runtime_boxing.py` が通過することを確認した。
- 2026-02-28: C++ emitter に `cpp_list_model`（`value|pyobj`）設定を追加し、`_cpp_type_text(list[...])` を model switch 経由へ集約した。`pyobj` モード時は list 型を `object` へ描画する。
- 2026-02-28: `test_cpp_type.py` に list model switch 回帰を追加し、`python3 tools/check_py2cpp_transpile.py`（`checked=134 ok=134 fail=0 skipped=6`）と合わせて非退行を確認した。
- 2026-02-28: `pyobj` list モード向けに runtime helper（`py_extend/py_pop/py_clear/py_reverse/py_sort`）を追加し、emitter 側で `ListAppend/ListExtend/ListPop/ListClear/ListReverse/ListSort` を object runtime 呼び出しへ切り替えた。
- 2026-02-28: list literal を `make_object(list<...>{...})` へ描画する分岐と、`list(...)` ctor の `pyobj` 経路、`Subscript` の list index を `py_at(...)` へ寄せる分岐を追加した。
- 2026-02-28: `test_py2cpp_codegen_issues.py` に `pyobj` list モード回帰を追加し、`test_cpp_runtime_iterable.py` / `test_py2cpp_codegen_issues.py` / `check_py2cpp_transpile.py`（`checked=134 ok=134 fail=0 skipped=6`）の通過を確認した。
- 2026-02-28: `for` 反復モード判定を `cpp_list_model=pyobj` 時に `list[...]` 型へ fail-closed で `runtime_protocol` を選ぶよう更新し、list comprehension を `object` 戻り・`make_object(__out)` で成立させた。`test_py2cpp_codegen_issues.py`（61件）と `check_py2cpp_transpile.py`（`checked=134 ok=134 fail=0 skipped=6`）の通過を確認した。
- 2026-02-28: `ForCore(RuntimeIterForPlan)` で `cpp_list_model=pyobj` かつ `iter_expr` が `list[...]` のとき static typed 反復を無効化し、`py_dyn_range` + runtime unbox へ強制した。合わせて `Subscript(list)` の `py_at` 結果を式型へ unbox する経路、`AnnAssign` の空 list 初期化を `make_object(list<object>{})` へ寄せる経路を追加した。
- 2026-02-28: runtime の `py_enumerate(const object&)` / `py_enumerate(const object&, int64)` を追加し、`pyobj` list モデルの runtime 反復で index 可能な `list<object>` 形へ正規化した。`test_py2cpp_list_pyobj_model.py`（2件: `sample/18` + `list_alias_shared_mutation`）/ `test_py2cpp_codegen_issues.py`（61件）/ `check_py2cpp_transpile.py`（`checked=134 ok=134 fail=0 skipped=6`）の通過を確認した。
- 2026-02-28: C++ emitter に non-escape 受け渡し状態（`non_escape_summary_map` / `function_non_escape_summary_map` / `current_function_non_escape_summary` / `non_escape_callsite_records`）を追加し、`meta.non_escape_summary`・`FunctionDef.meta.escape_summary`・`Call.meta.non_escape_callsite` を C++ 側で収集できる経路を実装した。`test_cpp_non_escape_bridge.py`（2件）/ `test_py2cpp_codegen_issues.py`（61件）/ `check_py2cpp_transpile.py`（`checked=134 ok=134 fail=0 skipped=6`）の通過を確認した。
- 2026-02-28: `cpp_list_model=pyobj` 時に non-escape な空 list ローカル（`AnnAssign list[...] = []`）のみ value-model へ fail-closed 縮退する経路を追加した。`Call.meta.non_escape_callsite` による escape 判定を優先し、unknown/external 呼び出しは縮退対象から除外する。`test_py2cpp_codegen_issues.py` に縮退成功/escape維持の回帰（2件）を追加し、`test_cpp_non_escape_bridge.py`（2件）/ `test_py2cpp_list_pyobj_model.py`（2件）/ `test_py2cpp_codegen_issues.py`（63件）/ `check_py2cpp_transpile.py`（`checked=134 ok=134 fail=0 skipped=6`）で非退行を確認した。
- 2026-02-28: fail-closed 固定として `test_py2cpp_codegen_issues.py` に unknown/external/dynamic call 混在ケースの回帰（2件）を追加し、`cpp_list_model=pyobj` 下でも local list が stack 縮退しないこと（`object xs` + `py_append` 維持）を確認した。`test_py2cpp_codegen_issues.py`（65件）で通過を確認した。
- 2026-02-28: `tools/benchmark_cpp_list_models.py` を追加し、`value`/`pyobj` の transpile+compile+run（`warmup=1`,`repeat=3`）を比較できるようにした。`work/logs/cpp_list_model_compare_20260228_all.json` の実測では成功 6/18（`01,02,03,04,17,18`）、失敗 12/18（`05..16`）で、成功ケース中央値は `elapsed=0.999x` / `bin=1.000x` / `src=1.000x`（pyobj/value）。差分は `18` に集中（`elapsed=1.954x`,`changed_lines=344`）し、既定切替は「未実施（S4-02 へ継続）」と判断した。
- 2026-02-28: `py2cpp` に `--cpp-list-model {value,pyobj}` を追加し、single-file/multi-file の両経路で `CppEmitter.cpp_list_model` へ伝播するようにした。`parse_py2cpp_argv` 回帰（`test_py2cpp_features.py` 1件）と API override 回帰（`test_py2cpp_codegen_issues.py` 66件）を追加し、`python3 src/py2cpp.py sample/py/18_mini_language_interpreter.py --cpp-list-model pyobj` で `py_append/make_object(list<object>{})` 出力、`check_py2cpp_transpile.py`（`checked=134 ok=134 fail=0 skipped=6`）通過を確認した。
- 2026-02-28: `pyobj` での二段添字代入 compile blocker（`object(...)[x] = ...`）を解消するため `py_set_at` runtime helper と `Assign(Subscript)` の lower を追加した。`test_py2cpp_codegen_issues.py` に nested subscript 代入回帰を追加し、`check_py2cpp_transpile.py` は通過。再ベンチ（`work/logs/cpp_list_model_compare_20260228_cases07_09_after_setat.json`）で `07/08/09` は compile fail から runtime fail（`setitem on non-list object`）へ遷移したため、次段の blocker は row 構築/boxing 経路の補正と整理した。
- 2026-02-28: `pyobj` で list repeat が `py_repeat(make_object(list<int64>{0}), w)` へ出力されると `07/08/09` で row が list object ではなくなり `setitem on non-list object` が発生するため、`operator.py` で `cpp_list_model=pyobj` 時の list repeat 入力を `list<T>(object_expr)` へ明示 unbox する補正を追加した。`test_py2cpp_codegen_issues.py` に回帰（`test_pyobj_list_model_list_repeat_unboxes_to_value_list_before_py_repeat`）を追加し、68件通過を確認した。
- 2026-02-28: 上記修正後に `07/08/09` が `frame size mismatch` で失敗したため、runtime の `py_object_try_cast` が `uint8` を含む算術型を未対応だった点を修正した。`test_cpp_runtime_boxing.py` に `object -> bytes/list<bytes>` 変換回帰を追加し、`tools/benchmark_cpp_list_models.py 07_game_of_life_loop 08_langtons_ant 09_fire_simulation --warmup 0 --repeat 1 --allow-failures` で 3件とも実行成功することを確認した。
- 2026-02-28: `12_sort_visualizer` で `render(const object&)` 呼び出しに stack 縮退した `list<int64>` がそのまま渡される compile blocker を確認した。`type_bridge._coerce_call_arg` で `cpp_list_model=pyobj` かつ list 注釈シグネチャ時の effective target を `object` へ寄せ、stack list だけ `make_object(...)` する補正を追加した。`test_py2cpp_codegen_issues.py` に回帰（`test_pyobj_list_model_boxes_stack_list_when_call_target_param_is_list_annotation`）を追加し、`benchmark_cpp_list_models.py 12_sort_visualizer --warmup 0 --repeat 1 --allow-failures` で実行成功を確認した。
- 2026-02-28: `13_maze_generation_steps` で tuple/list runtime blocker（`index access on non-indexable object`）を確認した。原因は `make_object(list<T>)` 内の `make_object(v)` が tuple overload を拾えず tuple 要素が `object()` に潰れる点と、pyobj list subscript の tuple unbox 不足だった。tuple boxing overload を `list<T>` より前に配置し、`_render_unbox_target_cast` に `tuple[...]` 用 `::std::make_tuple(py_at(...))` 変換を追加して解消した。`test_py2cpp_codegen_issues.py` の tuple subscript 回帰（`test_pyobj_list_model_tuple_subscript_unboxes_to_make_tuple_before_destructure`）と `benchmark_cpp_list_models.py 13_maze_generation_steps --warmup 0 --repeat 1 --allow-failures` 実行成功を確認した。
- 2026-02-28: `05..16` の `pyobj` 単独 compile/run 検証を追加実施し、12件すべて成功（`passed=12 failed=0`）を確認した。検証コマンドは `python3 src/py2cpp.py ... --cpp-list-model pyobj` + `g++ -O0` + 実行をケースごとに回す one-shot スクリプト。これにより `S4-02-S2` を完了扱いとした。
- 2026-02-28: `parse_py2cpp_argv` の `cpp_list_model_opt` 既定を `pyobj` に切替し、`py2cpp` 本体の fallback も `pyobj` へ統一した。`docs/ja/how-to-use.md` の C++ 節へ rollback 手順（`--cpp-list-model value`）を追記し、`test_parse_py2cpp_argv_defaults_cpp_list_model_to_pyobj` と `python3 tools/check_todo_priority.py` / `python3 tools/check_py2cpp_transpile.py` の通過を確認した。さらに `python3 src/py2cpp.py sample/py/18_mini_language_interpreter.py --single-file` と `--cpp-list-model value` の比較で、既定は `object lines = make_object(list<object>{});`、rollback 指定時は `list<str> lines = ...;` へ切り替わることを確認した。これにより `S4-02-S3` と親 `S4-02` を完了扱いとした。
- 2026-02-28: `S4-03` として、旧 `value` 互換コードの撤去対象（emitter 分岐 / runtime bridge / CLI rollback）と段階撤去ステージ（A〜E）を確定した。あわせて別ID起票条件（parity/selfhost 退行、`list` 以外への波及、deprecation 期間明示の必要）を定義し、本IDの範囲を固定した。
- 2026-02-28: `S4-04` として `docs/ja/how-to-use.md`（既定/rollback 手順）、`docs/ja/spec/spec-cpp-list-reference-semantics.md`（pyobj 既定 + value rollback 契約）、`docs/ja/todo/index.md`（親/子ID完了）を同期した。`python3 tools/check_todo_priority.py` を再実行し、TODO運用整合が崩れていないことを確認した。

## 分解

- [x] [ID: P1-LIST-PYOBJ-MIG-01-S0-01] `list` 参照セマンティクス契約（alias/共有/破壊的更新）を docs/spec に明文化する。
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S0-02] alias 期待 fixture（`a=b` 後の `append/pop` 共有）を追加し、現状差分を可視化する。
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S0-03] 現行 sample/fixture のうち list 値コピーに依存する箇所を棚卸しして決定ログに固定する。

- [x] [ID: P1-LIST-PYOBJ-MIG-01-S1-01] runtime に新 list PyObj モデル（型・寿命・iter/len/truthy 契約）を追加する。
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S1-02] `make_object` / `obj_to_*` / `py_iter_or_raise` を新 list モデル対応へ拡張する。
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S1-03] 旧値モデルとの互換ブリッジ（最小）を追加し、段階移行中の compile break を抑える。
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S1-04] runtime 単体テスト（構築・alias・iter・境界変換）を追加する。

- [x] [ID: P1-LIST-PYOBJ-MIG-01-S2-01] C++ emitter の list 型描画を model switch（`value|pyobj`）経由へ集約する。
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S2-02] list literal/ctor/append/extend/pop/index/slice の出力を `pyobj` モデル対応へ更新する。
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S2-03] for/enumerate/comprehension の list 反復 lower を `pyobj` list で成立させる。
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S2-04] `sample/18` を含む代表 fixture の compile/run/parity を `pyobj` モデルで通す。

- [x] [ID: P1-LIST-PYOBJ-MIG-01-S3-01] `P1-EAST3-NONESCAPE-IPA-01` の注釈を C++ 側へ受け渡す経路を追加する。
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S3-02] non-escape local list のみ stack/RAII へ縮退する Cpp pass を追加する。
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S3-03] unknown/external/dynamic call 混在時に縮退しない fail-closed 回帰テストを追加する。

- [x] [ID: P1-LIST-PYOBJ-MIG-01-S4-01] `value` vs `pyobj` の性能/サイズ/差分を sample で比較し、既定切替判断を記録する。
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S4-02] 既定モデルを `pyobj` に切替し、rollback 手順（フラグで `value` 復帰）を整備する。
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S4-02-S1] rollback 準備として `py2cpp` に `--cpp-list-model {value,pyobj}` を追加し、single/multi-file 出力へ反映する。
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S4-02-S2] `sample` 失敗 12 件（`05..16`）の compile/runtime blocker を段階解消し、`pyobj` モデルの実行成立範囲を拡張する。
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S4-02-S2-S1] pyobj で `grid[y][x] = ...` が `object[...]` へ落ちる compile blocker を `py_set_at(...)` lower で解消する。
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S4-02-S2-S2] `07/08/09` の runtime 失敗（`setitem on non-list object`）原因を特定し、`py_set_at` 入力が list object になるよう lower/runtime を補正する。
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S4-02-S2-S3] `12_sort_visualizer` の compile blocker（list 注釈引数が `object` シグネチャへ合わない）を callsite boxing 補正で解消する。
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S4-02-S2-S4] `13_maze_generation_steps` の tuple/list runtime blocker（tuple boxing 欠落と tuple subscript unbox 欠落）を解消する。
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S4-02-S3] 既定モデルを `pyobj` へ切替し、`--cpp-list-model value` を rollback 手順として運用記述へ反映する。
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S4-03] 旧値モデルの互換コード撤去計画（別ID起票条件を含む）を確定する。
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S4-04] docs/how-to-use/spec/todo の運用記述を同期し、最終受け入れ基準を満たす。
