<a href="../../../en/plans/archive/20260306-p0-cpp-pyobj-rc-list-alias.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: C++ `cpp_list_model=pyobj` の alias 維持を `object` ではなく `rc<list<T>>` へ置換する

最終更新: 2026-03-06

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYOBJ-RCLIST-ALIAS-01`

背景:
- 現状の `cpp_list_model=pyobj` では、`a: list[int] = [...] ; b = a` のような alias 共有ケースで、value list のままだと Python の参照セマンティクスを再現できない。
- 応急処置として alias 名を `object` (`rc<PyObj>`) へ戻す修正を入れたが、この方式だと `PyListObj(list<object>)` へ boxing され、typed 要素型情報を失う。
- その結果、`list<int64>` を保持していた経路でも `list<object>` への詰め替えと `make_object` / `py_to<T>` が増え、生成コードが不必要に動的化する。
- ユーザー方針として、ABI には `rc<>` を露出させない。一方で backend 内部表現としては `rc<list<T>>` を使ってよい。したがって alias 維持は `object` ではなく `rc<list<T>>` で表現するのが自然である。

目的:
- `cpp_list_model=pyobj` の alias 維持経路を `object` から `rc<list<T>>` へ置き換える。
- typed list の要素型を保持したまま alias 共有を成立させる。
- `@extern` / ABI 境界では従来どおり `list<T>` を使い、`rc<>` を ABI に漏らさない。

対象:
- C++ emitter:
  - `src/backends/cpp/emitter/cpp_emitter.py`
  - `src/backends/cpp/emitter/stmt.py`
  - `src/backends/cpp/emitter/type_bridge.py`
  - `src/backends/cpp/emitter/call.py`
  - 必要に応じて `operator.py`, `collection_expr.py`, `runtime_expr.py`
- C++ runtime:
  - `src/runtime/cpp/core/list.ext.h`
  - `src/runtime/cpp/core/py_runtime.ext.h`
  - 必要に応じて `src/runtime/cpp/core/py_types.ext.h`
- テスト:
  - `tools/unittest/emit/cpp/test_py2cpp_list_pyobj_model.py`
  - `tools/unittest/emit/cpp/test_py2cpp_codegen_issues.py`
  - `tools/unittest/emit/cpp/test_cpp_runtime_*`

非対象:
- `@extern` ABI 型の変更
- `dict/set/tuple` の同時 `rc<>` 化
- 全言語 backend への同時展開
- `cpp_list_model=value` の意味変更

設計方針:
- 方針A: `rc<list<T>>` は backend 内部表現であり、ABI ではない。
  - `@extern` 宣言・`spec-abi.md` の値型 ABI は引き続き `list<T>` のままとする。
  - call/return 境界で必要なときだけ `rc<list<T>> <-> list<T>` 変換を入れる。
- 方針B: alias 維持が必要な名前だけ `rc<list<T>>` を使う。
  - すべての list を一律 `rc<list<T>>` にしない。
  - non-escape local / stack 縮退済み list は引き続き `list<T>` を維持してよい。
- 方針C: dynamic object と typed alias handle を分離する。
  - `object` は `Any/object` 境界専用に保つ。
  - typed alias は `rc<list<T>>` で持ち、`py_append` なども typed handle overload を追加して使う。
- 方針D: fail-closed を維持する。
  - 型不明・外部呼び出し・union・`Any/object` 経由は `object` または既存安全経路へ倒す。
  - alias 推論が曖昧なら `rc<list<T>>` 化しない。

## フェーズ計画

### Phase 0: 契約固定

- `rc<list<T>>` を「pyobj alias 維持専用の内部表現」として定義する。
- `object` / `list<T>` / `rc<list<T>>` の責務境界を明文化する。
- 現状の `object` fallback が過剰 boxing を生む箇所を固定する。

### Phase 1: runtime typed-handle 層の導入

- `rc<list<T>>` を扱う helper 群を追加する。
- `len/index/slice/append/extend/pop/clear/reverse/sort` を `rc<list<T>>` でも呼べるようにする。
- `rc<list<T>> -> object`、`object -> rc<list<T>>`、`list<T> -> rc<list<T>>` の最小 adapter を追加する。

### Phase 2: emitter の型決定を `rc<list<T>>` へ切替

- alias 共有が必要な list 名を `object` ではなく `rc<list<T>>` として宣言する。
- `b = a` は handle copy にし、`make_object(a)` のような過剰 boxing を禁止する。
- list method/subscript/len/slice などの描画を `rc<list<T>>` aware にする。

### Phase 3: 境界適応

- 関数引数/返り値/局所一時変数で `rc<list<T>>` と `list<T>` が混在する箇所に adapter を追加する。
- `@extern` や runtime generated module 呼び出しでは ABI どおり `list<T>` へ正規化する。
- `Any/object` へ流れる箇所だけ `object` boxing を残す。

### Phase 4: 回帰固定と `object` fallback の縮小

- alias fixture と sample parity を通す。
- 既存の `object` fallback のうち、alias 用にだけ入れた暫定分岐を撤去する。
- 今回の責務境界を docs/spec/todo に反映する。

## 受け入れ基準

- `test/fixtures/collections/list_alias_shared_mutation.py` が C++ `cpp_list_model=pyobj` で Python と一致する。
- 上記ケースの生成コードで alias 名が `object` ではなく `rc<list<int64>>` 相当の typed handle として出る。
- `py_append/py_pop/py_len/py_slice` など主要 list 操作が `rc<list<T>>` 経路で成立する。
- `@extern` 境界の ABI は `list<T>` のままで、`rc<>` が漏れない。
- `tools/check/check_runtime_cpp_layout.py` と関連 unit が通る。

## リスクと対策

- リスク: `rc<list<T>>` と `list<T>` の混在で cast 分岐が散る。
  - 対策: runtime helper overload を先に作り、emitter 側は helper 呼び出しへ寄せる。
- リスク: alias 推論の誤判定で不要な `rc<>` が増える。
  - 対策: 初期段階では「Name-to-Name 代入で共有が確定したローカル」のみ対象に限定する。
- リスク: ABI 境界に `rc<>` が漏れる。
  - 対策: `type_bridge/call` に明示 adapter を入れ、`@extern` 対象回帰を追加する。
- リスク: `object` fallback と二重実装になり保守負債化する。
  - 対策: 本計画の最後に alias 用 `object` fallback を撤去するタスクを含める。

## 確認コマンド（予定）

- `python3 tools/check/check_todo_priority.py`
- `python3 tools/check/check_runtime_cpp_layout.py`
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src python3 tools/unittest/emit/cpp/test_py2cpp_list_pyobj_model.py`
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src python3 tools/unittest/emit/cpp/test_cpp_runtime_boxing.py`
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src python3 tools/unittest/emit/cpp/test_cpp_runtime_iterable.py`
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src python3 tools/unittest/emit/cpp/test_cpp_runtime_type_id.py`

## 分解

- [x] [ID: P0-CPP-PYOBJ-RCLIST-ALIAS-01-S1-01] `object` / `list<T>` / `rc<list<T>>` の責務境界を plan/spec で固定し、`@extern` ABI 非対象を明記する。
- [x] [ID: P0-CPP-PYOBJ-RCLIST-ALIAS-01-S1-02] 現状の alias fallback で `object` boxing が入る生成ケースを fixture ベースで固定する。

- [x] [ID: P0-CPP-PYOBJ-RCLIST-ALIAS-01-S2-01] C++ runtime に `rc<list<T>>` typed handle helper（生成/参照/値変換）を追加する。
- [x] [ID: P0-CPP-PYOBJ-RCLIST-ALIAS-01-S2-02] `py_len/py_append/py_extend/py_pop/py_slice/py_at` の `rc<list<T>>` overload を追加する。
- [x] [ID: P0-CPP-PYOBJ-RCLIST-ALIAS-01-S2-03] `rc<list<T>> <-> object`、`rc<list<T>> <-> list<T>` の最小 adapter を runtime に追加する。

- [x] [ID: P0-CPP-PYOBJ-RCLIST-ALIAS-01-S3-01] emitter の alias 共有名判定を `object` fallback ではなく `rc<list<T>>` 宣言へ切り替える。
- [x] [ID: P0-CPP-PYOBJ-RCLIST-ALIAS-01-S3-02] `Assign/AnnAssign` の `b = a` / 空 list 初期化 / literal 初期化で `make_object(...)` を出さず handle copy / handle new を使う。
- [x] [ID: P0-CPP-PYOBJ-RCLIST-ALIAS-01-S3-03] method call / subscript / len / slice / truthy 判定の描画を `rc<list<T>>` aware に更新する。

- [x] [ID: P0-CPP-PYOBJ-RCLIST-ALIAS-01-S4-01] 関数引数・返り値・callsite coercion で `rc<list<T>>` と `list<T>` の adapter 挿入条件を整理し、ABI 境界で `list<T>` を維持する。
- [x] [ID: P0-CPP-PYOBJ-RCLIST-ALIAS-01-S4-02] `Any/object` へ流れる箇所だけ `object` boxing を残し、alias 用に入れた `object` fallback を縮小・撤去する。

- [x] [ID: P0-CPP-PYOBJ-RCLIST-ALIAS-01-S5-01] alias fixture / runtime unit / C++ backend unit を追加更新して回帰を固定する。
- [x] [ID: P0-CPP-PYOBJ-RCLIST-ALIAS-01-S5-02] sample representative case（少なくとも `sample/18`）で compile/run を確認し、決定ログへ結果を残す。

決定ログ:
- 2026-03-06: ユーザー指示により、`cpp_list_model=pyobj` の alias 維持を `object` ではなく `rc<list<T>>` へ置換する P0 計画を起票した。
- 2026-03-06: 本計画で導入する `rc<list<T>>` は backend 内部表現であり、`docs/ja/spec/spec-abi.md` の値型 ABI には露出させない方針を固定した。
- 2026-03-06: 初期対象は「Name-to-Name 代入で alias 化が確定した list ローカル」のみに限定し、一括 `rc<>` 化は行わない。
- 2026-03-06: [ID: `P0-CPP-PYOBJ-RCLIST-ALIAS-01-S1-01`] `docs/ja/spec/spec-abi.md` と `docs/ja/spec/spec-runtime.md` を更新し、`rc<list<T>>` は backend 内部 typed handle であって ABI 型ではないこと、`@extern` 境界では `list<T>` へ正規化すること、helper 配置先は `src/runtime/<lang>/core/` であることを明文化した。
- 2026-03-06: [ID: `P0-CPP-PYOBJ-RCLIST-ALIAS-01-S1-02`] fixture `test/fixtures/collections/list_alias_shared_mutation.py` を `cpp_list_model=pyobj` で再生成し、現状の fallback が `object a = make_object(list<int64>{1, 2});` / `object b = make_object(a);` / `py_append(b, make_object(3));` になることを固定した。これは alias 共有は満たすが typed 要素型を失う、という本計画の出発点である。
- 2026-03-06: [ID: `P0-CPP-PYOBJ-RCLIST-ALIAS-01-S2-01`] `RcObject` を `PyObj` 専用から一般化し、`list<T>` を `pytra::gc::RcObject` 継承へ変更した。`py_types.ext.h` に `rc_list_new / rc_list_from_value / rc_list_ref / rc_list_copy_value` と `py_is_rc_list_handle` trait を追加し、typed handle を runtime の first-class な内部表現として扱える状態にした。
- 2026-03-06: [ID: `P0-CPP-PYOBJ-RCLIST-ALIAS-01-S2-02`] `py_runtime.ext.h` に `py_len / py_append / py_extend / py_pop / py_slice / py_at / py_set_at / py_clear / py_reverse / py_sort` の `rc<list<T>>` overload を追加した。これにより alias 用 typed handle でも list mutation / indexing / slicing を object boxing なしで呼べる。
- 2026-03-06: [ID: `P0-CPP-PYOBJ-RCLIST-ALIAS-01-S2-03`] `make_object(const rc<list<T>>&)` と `obj_to_rc_list<T>` / `obj_to_rc_list_or_raise`、`py_to<rc<list<T>>>` / `py_object_try_cast<rc<list<T>>>` を追加した。`rc<list<T>> -> object` は boxed copy、`object -> rc<list<T>>` は typed unbox copy とし、ABI ではなく backend 内部 adapter に留めた。
- 2026-03-06: [ID: `P0-CPP-PYOBJ-RCLIST-ALIAS-01-S2-01`] 検証として `test_cpp_runtime_boxing.py`, `test_cpp_runtime_iterable.py`, `test_cpp_runtime_type_id.py`, `test_py2cpp_list_pyobj_model.py`, `tools/check/check_runtime_cpp_layout.py` を実行し通過した。加えて ad-hoc の `rc<list<int64>>` smoke を `g++ -std=c++20` でコンパイル実行し、`len/append/extend/pop/set_at/object roundtrip` が成立することを確認した。
- 2026-03-06: [ID: `P0-CPP-PYOBJ-RCLIST-ALIAS-01-S3-01`] emitter の alias 名判定を `object` runtime list から分離し、alias 名だけ `rc<list<T>>` handle 経路へ切り替えた。`_uses_pyobj_runtime_list_expr()` は alias 名で false、`_uses_pyobj_rc_list_expr()` を追加して method/index path の dispatch を分離した。
- 2026-03-06: [ID: `P0-CPP-PYOBJ-RCLIST-ALIAS-01-S3-02`] `AnnAssign/Assign` の alias ターゲット宣言を `rc<list<T>>` に変更し、`b = a` は handle copy、list literal / empty list / list comprehension は `rc_list_from_value(...)` へ寄せた。`list_alias_shared_mutation.py` の生成結果は `rc<list<int64>> a = rc_list_from_value(list<int64>{1, 2}); rc<list<int64>> b = a;` となり、`make_object(...)` fallback が消えた。
- 2026-03-06: [ID: `P0-CPP-PYOBJ-RCLIST-ALIAS-01-S3-03`] method call / subscript / len / slice / truthy の `rc<list<T>>` aware 描画を追加した。`ListAppend/ListExtend/ListPop/ListClear/ListReverse/ListSort` は alias handle なら `py_*` overload を呼び、subscript は `py_at(handle, ...)`、truthy/len compare fastpath は `.empty()` へ縮退せず `py_len(handle)` を使うようにした。ad-hoc case `a/b alias + append/pop/subscript/slice/truthy/reverse/sort` を C++ 変換・コンパイル・実行し `True` を確認した。
- 2026-03-06: [ID: `P0-CPP-PYOBJ-RCLIST-ALIAS-01-S4-01`] callsite / return 境界に adapter を追加した。`consume(xs: list[int])` へ alias handle `b` を渡すケースは `consume(rc_list_ref(b))` へ lower され、`return b` で `return_type=list[int]` の場合は `return rc_list_copy_value(b);` を返す。module function coercion も同様に `rc_list_ref(...)` を使う。
- 2026-03-06: [ID: `P0-CPP-PYOBJ-RCLIST-ALIAS-01-S4-02`] alias 用に入れていた `object` fallback は emitter から撤去した。alias 名は `object` ではなく `rc<list<T>>` handle として保持し、`Any/object` へ流れる箇所だけ `make_object(handle)` を許可する構成に整理した。
- 2026-03-06: [ID: `P0-CPP-PYOBJ-RCLIST-ALIAS-01-S5-01`] `test_py2cpp_list_pyobj_model.py` に function boundary parity case を追加し、`consume(b)` / `return b` / `bool(b)` / `c[0]` を Python と C++ `cpp_list_model=pyobj` で比較固定した。回帰テストは 3 件で通過した。
- 2026-03-06: [ID: `P0-CPP-PYOBJ-RCLIST-ALIAS-01-S5-02`] representative case として既存 `sample/18` parity test を再実行し通過した。加えて ad-hoc boundary case 2 件（引数境界・返り値境界）を `g++ -std=c++20` でコンパイル実行し、`consume(rc_list_ref(b))` と `return rc_list_copy_value(b)` が成立することを確認した。
