# P1: C++ `py_runtime.h` を `@template` ベースで縮退させる

最終更新: 2026-03-08

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01`

関連:
- [20260308-p1-cpp-py-runtime-core-slimming.md](./20260308-p1-cpp-py-runtime-core-slimming.md)
- [20260308-p2-linked-runtime-helper-template-v1.md](./20260308-p2-linked-runtime-helper-template-v1.md)
- [p2-runtime-sot-linked-program-integration.md](../p2-runtime-sot-linked-program-integration.md)
- [p2-runtime-helper-generics-under-linked-program.md](../p2-runtime-helper-generics-under-linked-program.md)
- [spec-template.md](../../spec/spec-template.md)
- [spec-runtime.md](../../spec/spec-runtime.md)
- [spec-abi.md](../../spec/spec-abi.md)

背景:
- 2026-03-08 時点で `@template("T", ...)` は linked runtime helper 向け generic surface の canonical syntax として方針固定済みだが、実装はまだ入っていない。
- 一方、`src/runtime/cpp/native/core/py_runtime.h` には、`sum`, `min`, `max`, `zip`, `sorted` のような高水準 helper や collection/string helper の残骸がまだ多く、low-level glue へ縮退し切れていない。
- 以前の `P1-CPP-PY-RUNTIME-SLIM-01` で string helper 第一波は `generated/built_in` へ戻したが、generic を必要とする helper は `@template` と linked-program specialization が無いと pure Python SoT へ戻しにくい。
- `@abi` は generated helper 境界を固定する実務解として有効だが、helper 自体を ordinary module として linked-program optimizer に載せ、さらに generic 化できるなら、`@abi` を helper ごとに増やすより自然で、より積極的な最適化も可能になる。
- したがって次段は「`@template` を runtime helper 限定で実装し、その lane を使って `py_runtime.h` の generic helper を SoT 側へ戻す」計画として扱うのがよい。

目的:
- runtime helper 限定の `@template("T", ...)` を実装し、linked-program 段で implicit specialization できる最小 lane を作る。
- `py_runtime.h` に残っている generic helper 候補を pure Python SoT 側へ戻し、C++ では generated helper として使う。
- `native/core/py_runtime.h` を low-level ABI / object / container / process glue 中心へさらに縮退させる。
- generic helper を `object` 退化や target 固有 hand-written helper へ逃がさず、typed specialization 前提で扱えるようにする。

対象:
- `@template("T", ...)` の parser / EAST / linked metadata / validator / specialization collector / monomorphization
- runtime helper 限定の generic function 実装
- `src/pytra/built_in/*.py` への generic helper 追加
- C++ runtime generation と `py_runtime.h` からの helper 撤去
- representative C++ backend/runtime/parity tests
- `docs/ja/spec/{spec-template,spec-runtime,spec-abi,spec-east,spec-linker}.md`

非対象:
- user code 全般への generic/template 一般公開
- `@instantiate(...)` の導入
- generic class / method / nested generic
- 全 backend 同時対応
- `PyObj` / `object` / `rc<>` / `type_id` / low-level dynamic bridge の SoT 化
- `py_runtime.h` を 1 回で空にすること

受け入れ基準:
- runtime helper 限定で `@template("T", ...)` が実装され、linked-program 段で deterministic に specialization される。
- specialization collector は raw decorator ではなく `FunctionDef.meta.template_v1` を正本にする。
- `sum`, `min`, `max`, `zip`, `sorted` のうち少なくとも 2 系統以上が pure Python SoT 側へ移り、C++ では specialized generated helper を使う。
- `native/core/py_runtime.h` から、上記 helper に対応する高水準実装が撤去される。
- C++ backend / runtime unit / fixture parity / sample parity が非退行で通る。
- docs 上で「`@template` を何のために導入したか」と「`py_runtime.h` から何をどこへ移すか」の責務境界が明文化される。

依存関係:
- `@template` v1 syntax decision は完了済みとする。
- linked-program optimizer の基本導線は既に完了済みとする。
- `runtime SoT linked-program integration` の本命案は将来残るが、本計画では runtime helper 限定の最小 lane を先行実装してよい。
- `@abi` は helper 境界の補助として維持するが、本計画では generic helper の primary mechanism にはしない。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_runtime_cpp_layout.py`
- `python3 tools/check_runtime_core_gen_markers.py`
- `python3 tools/gen_runtime_symbol_index.py --check`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_*template*.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/link -p 'test_*template*.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_*.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_*.py'`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples`

## 1. 問題の本質

問題は `py_runtime.h` が大きいことではなく、「generic を必要とする helper を SoT に戻す lane が無いので、C++ native core に残り続ける」ことにある。

いま string helper 第一波は戻せているが、次の helper は generic support が無いと戻しづらい。

- `sum`
- `min`
- `max`
- `zip`
- `sorted`
- 今後の `head/take/keys/values/items` 系 helper

これらを hand-written C++ に残すと:

- 他言語と SoT を共有しにくい
- backend ごとに最適化方針が分散する
- `object` 退化か hand-written template に逃げやすい
- `py_runtime.h` の縮退が止まる

したがって、`@template` を runtime helper 限定で実装し、その lane を使って generic helper を pure Python SoT へ戻すのが本質解になる。

## 2. 基本方針

1. `@template("T", ...)` は runtime helper の top-level function 限定で実装する。
2. explicit instantiation は入れず、linked-program 段で callsite から implicit specialization する。
3. generic helper の実体は `src/pytra/built_in/*.py` を正本とし、C++ では specialization 後の generated helper を使う。
4. `native/core/py_runtime.h` は低レベル glue に限定し、generic helper の正本を置かない。
5. `@abi` は必要な boundary case にだけ残し、generic helper の primary mechanism にしない。

## 3. `py_runtime.h` から戻す候補

第一波候補:
- `sum`
- `min`
- `max`

第二波候補:
- `zip`
- `sorted`

保留候補:
- `dict.keys` / `dict.values` / `dict.items`
- `take/head/tail`
- object bridge を強く噛む helper

分類基準:
- generic parameter だけで表現できる helperは `@template` 候補
- `object` / `std::any` / dynamic dispatch を本質的に必要とする helper は保留
- `rc<>` / `type_id` / process I/O / OS glue は `native/core` に残す

## 4. 実装戦略

### Phase 1: inventory と契約固定

- `py_runtime.h` に残る generic helper 候補を棚卸しする。
- `spec-template` / `spec-runtime` / `spec-east` / `spec-linker` に helper-limited `@template` の責務境界を反映する。
- specialization 命名、collector 入口、invalid case の diagnostics 方針を決める。

### Phase 2: `@template` 最小実装

- parser で `@template("T", ...)` を受理する。
- `FunctionDef.meta.template_v1` を正本 metadata にする。
- validator で `runtime helper only` / `top-level function only` / duplicate param 禁止を enforce する。
- linked-program 側で specialization collector と monomorphization の最小実装を入れる。

### Phase 3: generic helper の SoT 移管

- `src/pytra/built_in/*.py` に generic helper を追加する。
- representative helper を specialized generated helper として C++ へ出す。
- `native/core/py_runtime.h` から対応する hand-written helper を撤去する。

### Phase 4: regression 固定

- runtime symbol index / build graph / emitter / runtime tests を追従させる。
- fixture/sample parity を再実行し、非退行を固定する。
- docs と decision log を同期する。

## 5. タスク分解

- [x] [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01] `@template` を runtime helper 限定で実装し、generic helper を pure Python SoT 側へ戻すことで C++ `py_runtime.h` を縮退させる。
- [x] [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S1-01] `py_runtime.h` に残る generic helper 候補を棚卸しし、第一波 / 第二波 / 保留へ分類する。
- [x] [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S1-02] `spec-template` / `spec-runtime` / `spec-east` / `spec-linker` に helper-limited `@template` の責務境界と specialization 契約を追記する。
- [x] [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S2-01] parser / EAST metadata / validator で `@template("T", ...)` を runtime helper 限定で受理する。
- [x] [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S2-02] linked-program 側に specialization collector と monomorphization の最小実装を入れる。
- [x] [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S3-01] `sum` / `min` / `max` を pure Python generic helper として SoT 側へ移し、C++ generated helper へ切り替える。
- [x] [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S3-02] `zip` / `sorted` のうち少なくとも 1 系統以上を同様に移し、`py_runtime.h` から hand-written helper を撤去する。
- [x] [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S4-01] runtime symbol index / build graph / representative backend/runtime tests を新 contract へ追従させる。
- [x] [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S4-02] fixture/sample parity・docs 同期・必要な guard 追加まで完了し、本計画を閉じる。

## 6. 決定ログ

- 2026-03-08: `@template("T", ...)` の syntax decision は完了済みとし、本計画は「syntax 決定」ではなく「実装して `py_runtime.h` を減らす」フェーズとして扱う。
- 2026-03-08: `@abi` は helper 境界の補助として残るが、generic helper を戻す主手段にはしない。generic helper は linked-program ordinary call として specialization する。
- 2026-03-08: 最初から全 helper を generic 化せず、`sum/min/max` を第一波、`zip/sorted` を第二波に分けて進める。
- 2026-03-08 [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S1-01]: `src/runtime/cpp/native/core/py_runtime.h` を棚卸しし、generic helper 候補の中で first-wave を `sum(list<T>)` / `py_min` / `py_max`、second-wave を `zip(list<A>, list<B>)` / `sorted(list<T>)` / `sorted(set<T>)` に固定した。これらはファイル末尾の高水準 algorithm helper 群としてまとまっており、`PyObj/object/rc<>/type_id` などの low-level glue と直接結びついていないため、`@template` lane へ戻す優先度が高い。
- 2026-03-08 [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S1-01]: 保留候補は `py_dict_keys` / `py_dict_values` / `py_dict_items` とした。理由は typed overload と `object` / `optional<dict<str, object>>` overload が同居しており、generic helper 化の前に「typed path だけを `@template` 化するか」「dynamic bridge を native/core に残すか」を `S1-02` で決める必要があるため。
- 2026-03-08 [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S1-01]: `py_len`, `py_at`, `py_append`, `py_extend`, `py_pop`, `py_dict_get*`, `py_div`, `py_floordiv`, `py_mod`, `py_to_*`, `py_runtime_*` は inventory 対象には含めたが、low-level container primitive / dynamic bridge / process glue と判断し、本計画の generic helper 縮退対象から外す。
- 2026-03-08 [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S1-02]: `spec-template` / `spec-east` / `spec-linker` / `spec-runtime` に、`@template` v1 は runtime helper 限定・linked implicit specialization 限定であり、specialization collector の canonical owner は linker であることを追記した。backend や ProgramWriter が raw decorator から template seed を再発見することは禁止する。
- 2026-03-08 [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S1-02]: `sum/min/max/zip/sorted` の generic helper lane は `src/pytra/built_in/*.py` -> linked-program specialization -> `generated/built_in` と固定し、`native/core/py_runtime.h` に新しい hand-written template helper を足して延命しない方針を決めた。
- 2026-03-08 [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S2-01]: self-hosted parser に `@template("T", ...)` の最小受理を追加し、`FunctionDef.meta.template_v1 = {schema_version, params, scope=runtime_helper, instantiation_mode=linked_implicit}` を出すようにした。`@abi` と併用可能だが、class/method への適用、keyword form、重複 param は parser/validator で fail-fast する。
- 2026-03-08 [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S2-01]: `validate_template_module(...)` を `core.py` / `east3.py` / `global_optimizer.py` に差し、optimized EAST3 と linked-program 経路でも canonical metadata を保つようにした。v1 の runtime helper provenance は `pytra.built_in.*` / `src/pytra/built_in/*` で最低限 enforce し、specialization collector 自体は `S2-02` に残す。
- 2026-03-08 [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S2-02]: linked-program optimizer の先頭で runtime helper template specialization collector を走らせ、`meta.template_v1` と callsite concrete type tuple から deterministic に monomorphization する最小実装を追加した。materialized clone は `FunctionDef.meta.template_specialization_v1` を持ち、program-wide summary は `link-output.global.runtime_template_specializations_v1` に集約する。
- 2026-03-08 [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S2-02]: first slice として same-module / imported-symbol 両方の specialization rewrite を `test_global_optimizer.py` で固定した。template 定義本体は linked module から除き、specialized function と import binding / ImportFrom rewrite だけを残す。
- 2026-03-08 [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S3-01]: `src/pytra/built_in/numeric_ops.py` を追加し、`sum(list[T])`, `py_min(T, T)`, `py_max(T, T)` を `@template` helper として SoT 側へ置いた。`sum` は `@abi(args={"values":"value"}, ret="value")` を併用して C++ generated header で `const list<T>&` 署名を維持する。
- 2026-03-08 [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S3-01]: C++ runtime emit は template helper module を header-only generated module として扱う。`src/backends/cpp/cli.py` に header-only 分岐を追加し、`numeric_ops.cpp` は生成せず `generated/built_in/numeric_ops.h` に template 定義を残すようにした。
- 2026-03-08 [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S3-01]: `src/runtime/cpp/native/core/py_runtime.h` から `sum(list<T>)` と 2-arg `py_min/py_max` の hand-written 実装を撤去し、`generated/built_in/numeric_ops.h` を include する形へ切り替えた。3 引数以上の `py_min/py_max` だけは variadic wrapper として残し、binary helper は generated template に委譲する。
- 2026-03-08 [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S3-02]: `src/pytra/built_in/zip_ops.py` を追加し、`zip(list[A], list[B]) -> list[tuple[A, B]]` を `@template("A", "B")` + `@abi(args={"lhs":"value","rhs":"value"}, ret="value")` helper として SoT 側へ移した。C++ runtime emit は header-only generated module `generated/built_in/zip_ops.h` と public shim `pytra/built_in/zip_ops.h` を生成し、`zip_ops.cpp` は持たない。
- 2026-03-08 [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S3-02]: linked specialization で local typed temporary を安全に materialize できるよう、`runtime_template_specializer.py` の型置換を `annotation` フィールドまで広げた。これにより template helper 内の `AnnAssign` も concrete type へ正規化される。
- 2026-03-08 [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S3-02]: `src/runtime/cpp/native/core/py_runtime.h` から generic `zip(const list<A>&, const list<B>&)` を撤去し、generated `zip_ops.h` へ委譲した。`zip(const object&, const object&)` は dynamic bridge として残し、内部で generated template `zip(*l, *r)` を呼ぶ最小構成に留めた。
- 2026-03-08 [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S3-02]: 第二波の `sorted` family はこの tranche では見送った。builtin lowering が `zip` ほど明示されておらず、`zip` だけで第二の generic helper family と header-only generated module lane を成立できたため、残りは `S4` 以降の regression/guard 同期を優先する。
- 2026-03-08 [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S4-01]: `test_runtime_symbol_index.py` に `pytra.built_in.numeric_ops` / `pytra.built_in.zip_ops` の header-only generated contract を追加し、`companions=["generated"]`, `public_headers=pytra/.../*.h`, `compile_sources=[]` を固定した。header-only template helper は runtime symbol index 上も `.cpp` を持たない canonical module として扱う。
- 2026-03-08 [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S4-01]: `test_cpp_runtime_build_graph.py` で `runtime/cpp/core/py_runtime.h` から collect される runtime source 集合に `generated/built_in/numeric_ops.cpp` / `zip_ops.cpp` が再侵入しないことを固定した。header-only generated helper は build graph 上でも phantom compile source を持たない。
- 2026-03-08 [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S4-02]: `tools/check_runtime_cpp_layout.py` に `sum/min/max/zip` の hand-written template helper body が `native/core/py_runtime.h` へ再侵入したら fail する guard を追加し、`test_check_runtime_cpp_layout.py` で `zip(const list<A>& lhs, const list<B>& rhs)` の duplicate 検出を固定した。template helper lane を導入した後に core header へ逆流させないことを stop-ship にした。
- 2026-03-08 [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S4-02]: `docs/ja/spec/spec-runtime.md` と `docs/ja/how-to-use.md` を同期し、`numeric_ops` / `zip_ops` は header-only generated module なので `compile_sources=[]` が canonical であり、空の `.cpp` を作らないことを明記した。runtime symbol index / build graph / C++ runtime docs の説明を同じ契約へ揃えた。
- 2026-03-08 [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S4-02]: `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture` で `cases=3 pass=3 fail=0`、`python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples` で `cases=18 pass=18 fail=0` を確認し、本計画を archive へ移した。

## 7. `S1-01` 棚卸し結果

対象ファイル:
- [py_runtime.h](../../../../src/runtime/cpp/native/core/py_runtime.h)

### 第一波

- `sum(const list<T>& values)`
- `py_min(const A& a, const B& b, ...)`
- `py_max(const A& a, const B& b, ...)`

理由:
- 数値/比較ベースの単純 generic helper で、`@template` の最初の適用対象として分かりやすい。
- `object` 直依存なのは `sum(const list<object>&)` / `sum(const object&)` の bridge 側だけで、本体 algorithm は SoT 側へ戻しやすい。
- `sum/min/max` を移せれば、`@template` specialization collector と generated helper 生成の縦 slice を最小で検証できる。

### 第二波

- `zip(const list<A>& lhs, const list<B>& rhs)`
- `sorted(const list<T>& values)`
- `sorted(const set<T>& values)`

理由:
- collection builder / reorder helper として generic 化の価値が高い。
- ただし `zip` は tuple specialization を伴い、`sorted` は ordering contract を含むため、第一波より collector / lowering / regression の確認範囲が広い。

### 保留

- `py_dict_keys`
- `py_dict_values`
- `py_dict_items`

理由:
- typed overload と dynamic/object overload が 1 つの family に同居している。
- `dict[K, V] -> list[K]` / `list[V]` / `list<object>` のどこまでを `@template` lane へ出すかを先に決めないと、native/core 側の dynamic bridge と責務がぶつかる。

### 本計画の対象外として固定

- `py_len`
- `py_at`
- `py_append`
- `py_extend`
- `py_pop`
- `py_dict_get*`
- `py_div` / `py_floordiv` / `py_mod`
- `py_to_*`
- `py_runtime_*`

理由:
- いずれも low-level container primitive / dynamic bridge / process glue / scalar conversion であり、`py_runtime.h` から generic helper を減らす本計画の主対象ではない。

## 8. `S1-02` 契約固定結果

- `spec-template`
  - `@template` v1 は runtime helper only の surface とし、implicit specialization の seed は `meta.template_v1` と linked-program 内で観測された concrete type tuple だけから決まる。
  - explicit instantiation を持たない v1 では、scope を runtime helper に閉じることで collector の責任範囲と specialization 数を program 管理下に保つ。
- `spec-east`
  - `FunctionDef.meta.template_v1` は宣言 metadata だけを持ち、materialized specialization 一覧は入れない。
  - backend は raw decorator を再解釈せず、linked module に残った canonical metadata を使う。
- `spec-linker`
  - specialization collector / monomorphization の canonical owner は linker。
  - backend / ProgramWriter は runtime helper template specialization を再構築してはならない。
  - implicit specialization は `link-input.v1` / `link-output.v1` が列挙した module 集合の中だけで完結する。
- `spec-runtime`
  - `sum/min/max/zip/sorted` は `@template` + linked specialization を primary lane として `generated/built_in` へ戻す。
  - `native/core/py_runtime.h` に新しい hand-written template helper を足してこの系統を延命してはならない。

## 9. `S2-01` 実装結果

- parser / EAST metadata
  - self-hosted parser は `@template("T", ...)` を top-level function で受理し、`decorators` の raw 文字列と `meta.template_v1` の canonical metadata を両方保持する。
  - `@abi` と `@template` は同一 function 上で共存できる。
- parser fail-fast
  - `@template()` のような空引数、keyword form、非文字列、重複 param、class/method 適用は parse/build 時点で reject する。
- validator
  - `validate_template_module(...)` を追加し、optimized EAST3 / linked-program 入力で `template_v1` shape を正規化・検証する。
  - v1 の runtime helper provenance は `pytra.built_in.*` / `src/pytra/built_in/*` で最低限 enforce し、scope を外れた `@template` は parser 後でも fail-closed に reject する。
  - specialization collector / monomorphization 自体は `S2-02` に残す。
