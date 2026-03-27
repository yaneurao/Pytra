<a href="../../../en/plans/archive/20260307-p0-cpp-list-ref-first-completion.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: C++ mutable list の ref-first 完全化（`rc<list<T>>` 正本化）

最終更新: 2026-03-07

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-LIST-REFFIRST-01`
- 先行完了: `docs/ja/plans/p1-list-pyobj-migration.md`（pyobj 既定化と dual model 導入）
- 参照仕様: `docs/ja/spec/spec-cpp-list-reference-semantics.md`

背景:
- 現状の C++ runtime は `rc<list<T>>` を扱えるが、backend は still value-first の逃げ道を残している。
- 具体的には `cpp_list_model=pyobj` でも、concrete typed list の一部を値型 `list<T>` のまま出す分岐が残っている。
- この状態だと、`a = b` の alias 共有を backend 側の局所ヒューリスティクスでしか守れず、mutable container の意味論が安定しない。
- ユーザー方針はすでに固まっている。
  - immutable (`str` など) は value-first でよい。
  - mutable (`list`) は ref-first を正本とする。
  - value 化は「最適化で安全と証明できたときだけ」許可する。

目的:
- C++ backend 内部表現として、mutable `list` を全面的に `rc<list<T>>` 正本へ切り替える。
- `list<T>` を直接生成してよいのは ABI 境界 adapter と、non-escape + alias-safe + SCC 固定済みの最適化結果だけに制限する。
- 現在 emitter に残っている「typed list なら value 側を優先する」設計を撤去する。

対象:
- C++ backend
  - `src/backends/cpp/emitter/*`
  - `src/backends/cpp/lower/*`
  - `src/backends/cpp/optimizer/*`
- C++ runtime
  - `src/runtime/cpp/core/list.h`
  - `src/runtime/cpp/core/py_types.h`
  - `src/runtime/cpp/core/py_runtime.h`
  - `src/runtime/cpp/built_in/*`
  - `src/runtime/cpp/std/*`
- C++ tests / parity
  - `test/unit/backends/cpp/*`
  - `tools/runtime_parity_check.py`

非対象:
- `dict/set/bytearray` の同時 ref-first 化
- 非C++ backend への展開
- ABI そのものの再設計
- `sample/cpp/*.cpp` の手編集

前提ルール:
- `.gen.*` は手編集しない。必ず SoT 再生成で反映する。
- `list<T>` を value で残す理由を「速そうだから」「見た目が短いから」で決めない。
- unknown / dynamic / `Any` / `object` / `@extern` / 未解析 call を含む経路では fail-closed で `rc<list<T>>` を維持する。
- `rc<list<T>>` は backend 内部表現であり、ABI に露出させない。

## 先に固定するべき設計判断

### A. 正本

- mutable list の正本は `rc<list<T>>`。
- `list<T>` は「ABI adapter 用 value」「optimizer が安全証明した結果」のどちらかでのみ生成してよい。

### B. 禁止

- emitter が「concrete typed list だから value にしてよい」と判断すること。
- alias が見えないからという理由だけで value にすること。
- local variable だからという理由だけで value にすること。
- `sample/18` の見た目を短くするために value に戻すこと。

### C. 許可

- `@extern` の引数/戻り値 adapter で `list<T>` を一時的に作る。
- optimizer pass が non-escape + no-alias-sensitive-mutation + SCC 固定済み summary を満たした場合だけ value に縮退する。

## 実装で迷いやすい点

### 1. `rc<list<T>>` に統一すると何が増えるか

- 変数宣言
- 代入
- リストリテラル
- `append/pop/extend/clear/reverse/sort`
- `len/truthy/index/subscript/slice`
- `for` / `enumerate` / `reversed`
- 関数引数
- 関数戻り値
- `Any/object` boxing
- `@extern` ABI adapter

このどれか 1 つでも value 前提が残ると、局所的にまた alias が壊れる。

### 2. 今回やるべきことと、まだやらないこと

今回やる:
- list を ref-first に統一
- value list は optimizer が作る結果だけに押し込む

今回やらない:
- dict/set/bytearray も同時に ref-first 化
- perf 最適化の細部調整

### 3. 実装者がやってはいけない近道

- failing test 1 件だけを見て `if sample18 then ...` のような分岐を足す
- `cpp_list_model=pyobj` のときだけ局所的に `object` fallback へ戻す
- value list と `rc<list<T>>` を callsite ごとに ad-hoc に混在させる

## フェーズ

### Phase 1: 現状棚卸しと禁止分岐の固定

- どこで `list<T>` をそのまま出しているかを網羅する。
- 特に以下を明示的に洗う。
  - `_is_pyobj_forced_typed_list_type`
  - `_is_pyobj_runtime_list_type`
  - list literal / empty init / comprehension / enumerate / subscript の fastpath
  - callsite coercion
  - return coercion
  - runtime helper overload
- 「value を出してよい場所」と「禁止場所」を文書と unit test で固定する。

#### Phase 1 棚卸し結果（2026-03-07）

##### 1. 禁止（backend/runtime 内部に残る value-first 分岐）

- `src/backends/cpp/emitter/type_bridge.py::_is_pyobj_forced_typed_list_type`
  - `cpp_list_model=pyobj` でも concrete typed list を value model 扱いする大元であり、`typed list だから value にしてよい` 判断そのものに該当する。
- `src/backends/cpp/emitter/cpp_emitter.py::_collect_stack_list_locals`
  - 空 `list[...]` ローカルを emitter 側の局所 non-escape 判定だけで `list<T>` へ縮退しており、optimizer 責務へ閉じ込める最終方針に反する。
- `src/backends/cpp/emitter/cpp_emitter.py::_expr_is_stack_list_local`
  - `src/backends/cpp/emitter/stmt.py::emit_annassign`、`src/backends/cpp/emitter/cpp_emitter.py::_render_collection_constructor_call`、`src/backends/cpp/emitter/operator.py::render_binop` などから参照され、list literal / empty init / repeat の value fastpath を維持している。
- `src/backends/cpp/emitter/stmt.py::emit_function`
  - 関数シグネチャの typed list を `const list<T>&` / `list<T>` で描画しており、backend 内部表現の ref-first 正本化がまだ完了していない。
- `src/backends/cpp/emitter/type_bridge.py::_coerce_call_arg`
  - 上記の value-first 関数シグネチャへ合わせて `rc_list_ref(...)` / boxing / unboxing を広く挿入しており、本来 `@extern` / `Any` / `object` 境界へ限定すべき adapter が内部 callsite まで漏れている。

##### 2. ABI adapter 限定で残してよい経路

- `src/runtime/cpp/core/py_runtime.h::make_object(const rc<list<T>>& values)`
  - `rc<list<T>>` から `object` への boxing 境界。内部表現の正本ではなく、`Any/object` 境界 adapter としてのみ残してよい。
- `src/runtime/cpp/core/py_runtime.h::obj_to_rc_list` / `obj_to_rc_list_or_raise`
  - `object` から `rc<list<T>>` へ戻す unboxing 境界。
- `src/runtime/cpp/core/py_runtime.h::py_to_rc_list_from_object`
  - `list[RefClass]` など object list から typed handle list を復元する境界 helper。
- `src/runtime/cpp/core/py_runtime.h::py_to_typed_list_from_object`
  - rollback/value adapter としては残しうるが、backend 内部の既定経路にしてはならない。

##### 3. optimizer 限定

- `src/toolchain/ir/east3_opt_passes/cpp_list_value_local_hint_pass.py`
  - C++ target 限定で `FunctionDef.meta.cpp_value_list_locals_v1` を付与し、empty typed list local の value-lowering 候補を fail-closed で注記する正本 pass。
- `src/backends/cpp/optimizer/*` には、引き続き list value-lowering 専用 pass は存在しない。
- `src/backends/cpp/optimizer/passes/for_iter_mode_hint_pass.py` は反復 hint 専用であり、list value 化を担当していない。さらに `pyobj` mode では hint 付与を抑止している。
- したがって、value 縮退の責務境界は「common EAST3 optimizer が hint を付け、emitter は `cpp_value_list_locals_v1` を読むだけ」とする。emitter 自身が non-escape を再証明してはならない。

### Phase 2: runtime helper の主経路を `rc<list<T>>` に寄せる

- `py_len / py_truthy / py_at / py_set_at / py_slice / py_append / py_extend / py_pop / py_clear / py_reverse / py_sort`
  の主たる mutable list 経路を `rc<list<T>>` 基準に整理する。
- `list<T>` overload は adapter と明示できるものだけ残す。
- `iter_ops` / `contains` / `sequence` 側も `rc<list<T>>` 主体で破綻しないことを確認する。

### Phase 3: emitter/lower を ref-first に切り替える

- list 注釈の local / temp / assignment / field / tuple unpack / loop variable を `rc<list<T>>` 基準に描画する。
- 現在の「typed だから value 側へ寄せる」条件分岐を撤去する。
- `b = a` は handle copy を正本にする。
- list literal は `rc_list_from_value(list<T>{...})` 系へ統一する。
- empty init は `rc_list_new<T>()` または等価 helper に統一する。

### Phase 4: ABI 境界 adapter を明示化する

- `@extern` 引数で `list<T>` が要求されるときだけ `rc_list_copy_value(...)` を入れる。
- `@extern` 戻り値が `list<T>` のときだけ `rc_list_from_value(...)` を入れる。
- `Any/object` 境界は `make_object(const rc<list<T>>& )` / `obj_to_rc_list<T>` を唯一経路にする。
- これ以外の場所では `list<T>` を ABI 以外の理由で復活させない。

### Phase 5: value 縮退を optimizer の責務へ閉じ込める

- 既存の non-escape / interprocedural summary / SCC 固定経路を使って、
  「証明できたときだけ value にする」pass を整理する。
- この pass を無効にした状態でも全 unit/parity が通るようにする。
- つまり correctness は ref-first で成立し、value 化は purely optimization にする。

### Phase 6: 回帰固定

- unit
- fixture parity
- sample parity
- representative codegen assert
を全部更新し、`list` の ref-first 契約を固定する。

## 受け入れ基準

- `cpp_list_model=pyobj` のもとで、mutable list の既定内部表現が `rc<list<T>>` になる。
- emitter に「typed list だから value を優先する」分岐が残らない。
- `python3 -m unittest discover -s test/unit/backends/cpp -p 'test_*.py'` が通る。
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture` が通る。
- `python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples` が通る。
- `optimizer off` 相当でも correctness が壊れない。
- `sample/18` を含む representative case で list alias が Python と一致する。

## 検証コマンド

- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_*.py'`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples`
- `PYTHONPATH=src python3 test/unit/backends/cpp/test_py2cpp_list_pyobj_model.py`

## 分解

- [x] [ID: P0-CPP-LIST-REFFIRST-01] C++ mutable list を全面 ref-first (`rc<list<T>>`) 正本へ切り替え、value list を optimizer 結果だけへ閉じ込める。

- [x] [ID: P0-CPP-LIST-REFFIRST-01-S1-01] 現行 emitter/runtime に残る value-first 分岐を棚卸しし、「禁止」「ABI adapter 限定」「optimizer 限定」に分類する。
- [x] [ID: P0-CPP-LIST-REFFIRST-01-S1-02] `spec-cpp-list-reference-semantics.md` を今回の最終方針（dual model ではなく ref-first 正本）に更新する。
- [x] [ID: P0-CPP-LIST-REFFIRST-01-S1-03] representative codegen test を追加し、「typed list だから value へ寄せる」退行を fail-fast 化する。

- [x] [ID: P0-CPP-LIST-REFFIRST-01-S2-01] runtime helper の list 主経路を `rc<list<T>>` 基準へ整理し、mutable operation の正本 overload を固定する。
- [x] [ID: P0-CPP-LIST-REFFIRST-01-S2-02] `iter_ops` / `contains` / `sequence` / `py_to_*` / `make_object` の list 経路を `rc<list<T>>` 正本へ揃える。
- [x] [ID: P0-CPP-LIST-REFFIRST-01-S2-03] `list<T>` runtime overload のうち ABI adapter 以外のものを縮退・撤去し、残す理由を決定ログへ固定する。

- [x] [ID: P0-CPP-LIST-REFFIRST-01-S3-01] emitter の list 型描画を ref-first に切り替え、`_is_pyobj_forced_typed_list_type` 依存を撤去する。
- [x] [ID: P0-CPP-LIST-REFFIRST-01-S3-02] list literal / empty init / assign / annassign / tuple unpack / comprehension を `rc<list<T>>` 正本へ切り替える。
- [x] [ID: P0-CPP-LIST-REFFIRST-01-S3-03] callsite / return / method dispatch / subscript / for/enumerate/reversed の描画を `rc<list<T>>` 正本へ切り替える。

- [x] [ID: P0-CPP-LIST-REFFIRST-01-S4-01] `@extern` / `Any` / `object` 境界でだけ `list<T>` value adapter を挿入する規則を実装し、他経路から分離する。
- [x] [ID: P0-CPP-LIST-REFFIRST-01-S4-02] ABI adapter 用 helper を整理し、`list<T>` を backend 内部正本として扱う経路をなくす。

- [x] [ID: P0-CPP-LIST-REFFIRST-01-S5-01] optimizer 側で「証明できた list だけ value 化する」責務境界を実装し、correctness と optimization を分離する。
- [x] [ID: P0-CPP-LIST-REFFIRST-01-S5-02] optimizer off / fail-closed 条件でも unit/parity が通ることを確認する。

- [x] [ID: P0-CPP-LIST-REFFIRST-01-S6-01] C++ unit 全体を再実行し、list ref-first 化後の非退行を確認する。
- [x] [ID: P0-CPP-LIST-REFFIRST-01-S6-02] fixture/sample parity を再実行し、artifact を含めて非退行を確認する。
- [x] [ID: P0-CPP-LIST-REFFIRST-01-S6-03] TODO/archive/docs を更新し、この ref-first 契約を完了扱いで固定する。

決定ログ:
- 2026-03-06: ユーザー指示により、C++ list は「条件付き `rc<list<T>>`」ではなく「mutable は全面 ref-first、value は optimizer 結果のみ」へ進める方針を確定した。
- 2026-03-06: 既存の `P1-LIST-PYOBJ-MIG-01` は dual model と pyobj 既定化の計画としては完了済みだが、なお value-first escape hatch が残っているため、本 P0 はその仕上げとして扱う。
- 2026-03-07: `ID: P0-CPP-LIST-REFFIRST-01-S1-01` として現行分岐を棚卸しし、`_is_pyobj_forced_typed_list_type`、`_collect_stack_list_locals`、内部 callsite 向け `rc_list_ref(...)` adapter を「禁止」へ分類した。
- 2026-03-07: optimizer 側には list value-lowering pass が未実装であることを確認し、現状の value 縮退は emitter 内の暫定実装として扱う方針を固定した。
- 2026-03-07: `ID: P0-CPP-LIST-REFFIRST-01-S1-03` として、typed list でも alias 経路は `rc<list<T>>` を維持し、typed call 境界でのみ `rc_list_ref(...)` へ落とす representative codegen test を追加した。
- 2026-03-07: `ID: P0-CPP-LIST-REFFIRST-01-S2-01` として、`py_runtime.h` の list helper を共通 helper 経由へ整理し、`py_slice / py_at / py_append / py_set_at / py_extend / py_pop / py_clear / py_reverse / py_sort` の typed canonical path を `rc<list<T>>` overload から呼ぶ構成へ揃えた。`object` / `list<T>` 側は同じ list helper 本体を通る adapter として扱う。
- 2026-03-07: `ID: P0-CPP-LIST-REFFIRST-01-S2-01` の検証として `test_cpp_runtime_iterable.py`, `test_cpp_runtime_boxing.py`, `test_cpp_runtime_type_id.py`, `tools/check_runtime_cpp_layout.py` を実行し通過した。`test_cpp_runtime_iterable.py` には `rc<list<int64>>` の slice/set_at/append/extend/pop/reverse/sort/clear smoke を追加した。
- 2026-03-07: `ID: P0-CPP-LIST-REFFIRST-01-S2-02` として、`contains.ext.h` / `iter_ops.ext.h` / `sequence.ext.h` に list 共通 helper と `rc<list<T>>` overload を追加し、`py_contains` / `py_reversed` / `py_enumerate` / `py_repeat` を typed handle から直接呼べるようにした。加えて `py_runtime.h` で `make_object(const rc<list<T>>& )` と `obj_to_rc_list<T>` / `py_to_typed_list_from_object<T>` を共有 helper 経由へ整理し、`py_is_list(const rc<list<T>>& )` を追加した。
- 2026-03-07: `ID: P0-CPP-LIST-REFFIRST-01-S2-02` の検証として `test_cpp_runtime_iterable.py`, `test_cpp_runtime_boxing.py`, `test_cpp_runtime_type_id.py`, `tools/check_runtime_cpp_layout.py` を再実行し通過した。`test_cpp_runtime_iterable.py` には `rc<list<int64>>` の contains/reversed/enumerate/repeat/object roundtrip/`py_to<rc<list<int64>>>` smoke を追加した。
- 2026-03-07: `ID: P0-CPP-LIST-REFFIRST-01-S2-03` として、`py_runtime.h` から value-list mutable public overload `py_at(list<T>&)` / `py_set_at(list<T>&)` を撤去した。plain `list<T>` で残すのは、Phase 3 まで selfhost/generated C++ value-path が読んでいる read-only overload（例: `selfhost/py2cpp.cpp` の `py_slice(py_runtime_argv(), ...)`, `test/transpile/cpp/13_maze_generation_steps.cpp` の `py_at(stack, -(1))`, `test/transpile/cpp/18_mini_language_interpreter.cpp` の `py_enumerate(lines)` / `py_contains(env, ...)`）、および runtime 生成コードの local builder が使う `py_append(list<T>&)`、さらに `make_object(list<T>)` / `py_to_typed_list_from_object<T>` / `obj_to_rc_list<T>` などの boxing / rollback adapter に限定する方針を固定した。
- 2026-03-07: `ID: P0-CPP-LIST-REFFIRST-01-S2-03` の検証として `test_cpp_runtime_iterable.py`, `test_cpp_runtime_boxing.py`, `test_cpp_runtime_type_id.py`, `tools/check_runtime_cpp_layout.py`, `tools/check_todo_priority.py` を実行し通過した。`test_cpp_runtime_iterable.py` には plain `list<T>` read-only smoke と runtime overload inventory guard を追加した。
- 2026-03-07: `ID: P0-CPP-LIST-REFFIRST-01-S3-01` として、関数/ラムダ/メソッドの list 型描画を `cpp_signature_type(...)` 基準へ切り替え、`cpp_list_model=pyobj` の typed mutable list を `const rc<list<T>>&` / `rc<list<T>>&` / `rc<list<T>>` で出力するようにした。typed handle call/return は `rc_list_ref(...)` を経由せずそのまま共有し、stack-local value list から ref-first 境界へ出る箇所だけ `rc_list_from_value(...)` を残す構成へ整理した。
- 2026-03-07: `ID: P0-CPP-LIST-REFFIRST-01-S3-01` として、旧 `_is_pyobj_forced_typed_list_type` を retire し、関数境界の ref-first 判定を `_is_pyobj_ref_first_list_type`、stack-local / bytearray / collection builder など value-model 判定を `_is_pyobj_value_model_list_type` へ分離した。これにより、型描画の正本は ref-first へ固定しつつ、Phase 3 後続で残る local value-lowering の責務境界を helper 名の上でも分離した。
- 2026-03-07: `ID: P0-CPP-LIST-REFFIRST-01-S3-01` の検証として `test_py2cpp_codegen_issues.py`, `test_py2cpp_list_pyobj_model.py`, `test_east3_cpp_bridge.py`, `test_cpp_type.py`, `tools/check_todo_priority.py` を実行し通過した。representative codegen assert は sample12/sample13/sample18、tuple unpack、nested subscript assign、len-empty fastpath、list comprehension を ref-first 契約へ更新した。
- 2026-03-07: `ID: P0-CPP-LIST-REFFIRST-01-S3-02` として、`_collect_pyobj_runtime_list_alias_names` を「alias 名」から「stack-local でない typed list local 名」の収集へ広げ、`annassign/assign` の typed list local を empty init・list literal・list comprehension を含めて handle-backed `rc<list<T>>` 宣言へ倒した。これにより、sample08/sample13/sample18 や escaping local builder は `rc_list_from_value(...)` / `py_append(...)` / `py_extend(...)` 正本へ切り替わり、stack-local optimization は empty annotated non-escape local に限定された。
- 2026-03-07: `ID: P0-CPP-LIST-REFFIRST-01-S3-02` として、EAST3 reserve hint が handle-backed list local に対しても成立するよう `reserve` 出力を `rc_list_ref(owner).reserve(...)` へ調整した。`test_py2cpp_codegen_issues.py` には local list comprehension handle test を追加し、`test_py2cpp_codegen_issues.py`, `test_py2cpp_list_pyobj_model.py`, `test_east3_cpp_bridge.py`, `test_cpp_type.py` を再実行して通過した。
- 2026-03-07: `ID: P0-CPP-LIST-REFFIRST-01-S3-03` として、subscript / list method dispatch / for lowering の ref-first list 判定を `Name` 限定 helper から分離し、`py_*` helper 用には call-returned handle と nested subscript を受ける `ref-first list ops` 判定、`rc_list_ref(...)` 用には temporary を避ける `lvalue-only` 判定を導入した。これにより `make()[0]` は `py_at(make(), ...)`、`make().append(...)` は `py_append(make(), ...)`、`for x in xs` は `rc_list_ref(xs)`、`for x in make()` は一時 handle hoist 後の typed loop、`enumerate(make())` / `reversed(make())` は `py_enumerate(...)` / `py_reversed(...)` ベースの typed loop へ戻る。
- 2026-03-07: `ID: P0-CPP-LIST-REFFIRST-01-S3-03` の検証として `test_py2cpp_codegen_issues.py`, `test_east3_cpp_bridge.py`, `test_py2cpp_list_pyobj_model.py`, `test_cpp_type.py` を実行し通過した。`test_py2cpp_codegen_issues.py` には call-returned subscript / method dispatch / typed for / enumerate / reversed regression を追加し、sample13 の nested list access expectation も `py_at(py_at(...), ...)` 契約へ更新した。
- 2026-03-07: `ID: P0-CPP-LIST-REFFIRST-01-S4-01` として、ref-first list target 判定を plain `Name` alias から `Attribute` を含む lvalue へ広げ、class field の typed list を `rc<list<T>>` storage へ揃えた。これにより sample18 `Parser.tokens` / `Parser.expr_nodes` は handle-backed field となり、`this->tokens = tokens` / `this->expr_nodes = this->new_expr_nodes()` のように内部 assignment では `rc_list_copy_value(...)` を使わず、`self.tokens[i]` / `self.expr_nodes.append(...)` も `py_at(...)` / `py_append(...)` の ref-first helper を通るようになった。
- 2026-03-07: `ID: P0-CPP-LIST-REFFIRST-01-S4-01` では plain local value path は維持した。sample13 `candidates` のような block-local typed list は runtime alias 集合へは昇格させず `list<...>` のまま残し、`rc_list_copy_value(...)` は `@extern` / `Any` / `object` 境界と、Phase 5 で optimizer 責務へ閉じ込める暫定 value-local 経路だけに寄せる方針を固定した。
- 2026-03-07: `ID: P0-CPP-LIST-REFFIRST-01-S4-02` として、ABI adapter helper を `ref-first handle -> value list copy` の `_render_pyobj_value_list_copy_adapter(...)` と `ref-first handle -> list<T> arg` の `_render_pyobj_value_list_arg_adapter(...)` へ整理した。`stmt.py` の value-local copy、`module.py` の runtime module arg、`type_bridge.py` の known-function arg はこの 2 helper を通る構成へ揃え、旧 alias-specific 条件分岐の重複を削減した。
- 2026-03-07: `ID: P0-CPP-LIST-REFFIRST-01-S4-02` として、known-function path には `extern_function_names` を導入し、`@extern` function のときだけ `list<T>` target を value ABI として扱うようにした。これにより internal function は引き続き ref-first signature を正本としつつ、`@extern` / runtime module 境界では lvalue handle を `rc_list_ref(...)`、temporary handle を `rc_list_copy_value(...)` へ落とせるようになった。
- 2026-03-07: `ID: P0-CPP-LIST-REFFIRST-01-S5-01` として、`toolchain/ir/east3_opt_passes/cpp_list_value_local_hint_pass.py` を追加し、C++ target に限って `FunctionDef.meta.cpp_value_list_locals_v1` を付与する common EAST3 optimizer pass を導入した。`cpp_emitter.py::_collect_stack_list_locals` はこの hint を読むだけの fail-closed helper へ縮退し、local non-escape の再証明ロジックを emitter から撤去した。
- 2026-03-07: `ID: P0-CPP-LIST-REFFIRST-01-S5-01` では `_collect_assigned_name_types(...)` の loop 再帰を追加し、optimizer hint を持たない block-local typed list は alias 集合に入り ref-first handle へ倒れるよう修正した。これにより sample13 `candidates` は `rc<list<tuple[...]>>` となり、`py_at(candidates, ...)` / `py_append(candidates, ...)` 正本を通る。
- 2026-03-07: `ID: P0-CPP-LIST-REFFIRST-01-S5-01` の検証として `test_east3_optimizer.py`, `test_cpp_non_escape_bridge.py`, `test_py2cpp_codegen_issues.py`, `test_east3_cpp_bridge.py`, `test_py2cpp_list_pyobj_model.py`, `test_cpp_type.py`, `tools/check_todo_priority.py` を実行し通過した。optimizer hint 単体、emitter bridge、sample12/sample13 の fail-closed/ref-first codegen expectation を更新して固定した。
- 2026-03-07: `ID: P0-CPP-LIST-REFFIRST-01-S5-02` として、optimizer off (`east3_opt_level=0`) でも safe local list が value 縮退しない regression を `test_py2cpp_codegen_issues.py` に追加し、`test_cpp_non_escape_bridge.py` には malformed `cpp_value_list_locals_v1` を emitter が無視する fail-closed test を追加した。
- 2026-03-07: `ID: P0-CPP-LIST-REFFIRST-01-S5-02` では opt0 representative parity で露出した nested list 問題を修正した。`_render_pyobj_alias_list_value(...)` は object-returning list comprehension を `py_to<rc<list<T>>>(...)` 経由へ倒し、nested mutable subscript lvalue は `py_list_at_ref(py_at(...), ...)` を使うようにした。runtime 側も `py_to(const object&)` に plain `list<T>` 復元を追加し、nested typed list の object roundtrip を `test_cpp_runtime_iterable.py` で固定した。
- 2026-03-07: `ID: P0-CPP-LIST-REFFIRST-01-S5-02` の検証として `test_py2cpp_codegen_issues.py`, `test_cpp_non_escape_bridge.py`, `test_cpp_runtime_iterable.py`, `test_cpp_runtime_boxing.py` を実行し通過した。representative parity は `tools/runtime_parity_check.py --targets cpp --case-root fixture --east3-opt-level 0 collections/list_alias_shared_mutation stdlib/os_glob_extended` と `tools/runtime_parity_check.py --targets cpp --case-root sample --east3-opt-level 0 08_langtons_ant 12_sort_visualizer 13_maze_generation_steps 18_mini_language_interpreter` を実行し、どちらも全件通過した。
- 2026-03-07: `ID: P0-CPP-LIST-REFFIRST-01-S6-01` として、runtime module list signature の repo-root 依存と `random.choices` / `dict.keys` / `dict.values` の list unbox adapter を修正し、nested list append では `py_append(out, rc_list_copy_value(row))` を使うようにした。fresh rerun の `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src python3 -m unittest discover -s /workspace/Pytra/test/unit/backends/cpp -p 'test_*.py'` は `Ran 505 tests in 1091.285s` で `OK` を確認した。
- 2026-03-07: `ID: P0-CPP-LIST-REFFIRST-01-S6-02` として、`python3 tools/runtime_parity_check.py --targets cpp --case-root fixture` は `cases=3 pass=3 fail=0`、`python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples` は `cases=18 pass=18 fail=0` を確認した。sample parity 中に露出した `07_game_of_life_loop` の nested list append 退行も `ID: P0-CPP-LIST-REFFIRST-01-S6-02` 内で修正し、単体 parity を通した上で全 sample rerun を完了している。
- 2026-03-07: `ID: P0-CPP-LIST-REFFIRST-01-S6-03` として、plan を `docs/ja/plans/archive/20260307-p0-cpp-list-ref-first-completion.md` へ移し、`docs/ja/todo/archive/20260307.md` / `docs/ja/todo/archive/index.md` / `docs/ja/todo/index.md` を更新して ref-first 契約を完了扱いで閉じた。
