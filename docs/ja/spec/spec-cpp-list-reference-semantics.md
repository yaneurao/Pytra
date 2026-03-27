<a href="../../en/spec/spec-cpp-list-reference-semantics.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# C++ list 参照セマンティクス仕様（ref-first 正本）

この文書は C++ backend の mutable `list` について、最終契約である ref-first 正本と、そこから外れてよい例外条件を定義する。

## 1. 目的

- mutable `list` の backend 内部表現を `rc<list<T>>` 正本として固定する。
- `list<T>` value 生成を許す条件を「ABI adapter 限定」または「optimizer 証明済み」に限定する。
- 回帰判定で守るべき alias / mutation / boxing 境界の契約を明確化する。

## 2. 適用範囲

- 対象: C++ runtime / C++ emitter で生成される `list[...]`。
- 非対象: `dict` / `set` / `str` の参照モデル移行（別タスク）。

## 3. 用語

- `ref-first`: mutable 値はまず共有参照表現で保持し、証明できた経路だけ値型へ縮退する方針。
- `ABI adapter`: `@extern` / `Any` / `object` / 互換 API 境界でのみ一時的に `list<T>` value を作る adapter。
- `optimizer-only value lowering`: non-escape / alias / mutation / call graph / SCC 条件を満たしたときだけ optimizer が許可する値型縮退。
- `legacy value model`: 撤去済み。かつて `--cpp-list-model value` で利用可能だった rollback 互換モード。
- `alias`: `b = a` のように同一 list を共有すること。

## 4. 正本契約

- `py2cpp` の `list` モデル既定は `pyobj`。
- mutable `list` の backend 内部正本は `rc<list<T>>`。
- alias、破壊的更新、引数受け渡し、戻り値、属性格納、反復、添字アクセスをまたいでも、まずは共有参照を維持する。
- `list<T>` を backend 内部の通常経路で直接生成してはならない。
- emitter は次の理由で `list<T>` value を選んではならない。
  - concrete typed list だから
  - local variable だから
  - alias が見えないから
  - sample の見た目を短くしたいから

## 5. `list<T>` value を許す例外条件

### 5.1 ABI adapter 限定

- `@extern` の引数/戻り値 adapter。
- `Any/object` boxing / unboxing 境界。
- rollback 互換 API を維持するための限定 helper。

この用途では `list<T>` value helper を残してよいが、backend 内部の主経路に漏らしてはならない。

### 5.2 optimizer-only value lowering

- `list<T>` value 化は optimizer が安全と証明した場合だけ許可する。
- 最低条件:
  - mutation 解析
  - alias 解析
  - escape 解析
  - call graph / SCC 固定
- correctness は ref-first のまま成立しなければならず、value 化は purely optimization でなければならない。

## 6. alias / mutation 契約

- `list` は既定で参照共有され、`b = a` 後の `append/pop` が相互に観測可能。
- 関数引数・戻り値・属性格納でも同一 list の共有を維持する。
- `Any/object` 境界の boxing/unboxing は no-op 互換（同一実体を保持）を優先する。

## 7. 破壊的更新の契約

- `append/pop/extend/clear` は list 実体に対して in-place に作用する。
- 共有 alias がある場合、すべての参照から更新結果が観測できなければならない。
- 非 alias（別実体）の場合のみ独立に更新される。

## 8. PyListObj の寿命/iter 契約

- `PyListObj::py_iter_or_raise()` は list 値の snapshot ではなく owner list 実体を参照する iterator を返す。
- iterator は owner list の寿命を保持する（owner 参照が失効した場合は停止）。
- 反復中に `py_append` された要素は、未走査範囲に存在する限り反復結果へ反映される。
- `py_try_len` / `py_truthy` は owner list 実体の現在状態に対して評価される。

## 9. fail-closed ルール

- 変換不能・型不明・外部呼び出し混在経路は最適化を適用しない。
- non-escape が証明できない list を stack 化しない。
- 意味論が不明な場合は heap/pyobj 側に倒す。
- alias の可能性を否定できない list を値型化しない。
- call graph / SCC summary が未確定の段階で interprocedural な値型化をしない。

## 10. 境界 helper の扱い

- `make_object(const rc<list<T>>& values)`、`obj_to_rc_list<T>`、`obj_to_rc_list_or_raise<T>`、`py_to_rc_list_from_object<T>`、`py_to_typed_list_from_object<T>` は境界 helper としてのみ使う。
- これらを emitter 内部の既定表現選択に流用してはならない。
- 内部 callsite / return / local variable のために `rc_list_ref(...)` や `list<T>(...)` を広く挿入する設計は、本仕様では未完了実装として扱う。

## 11. legacy rollback 契約（撤去済み）

- `--cpp-list-model value` は撤去済み。pyobj（ref-first）が唯一のモード。
- 旧 `legacy value model`（値型 list、コピー代入）は完全に削除された。

## 12. 受け入れ判定

- alias 期待 fixture（`a=b` 後の `append/pop`）で Python と一致する。
- `check_py2cpp_transpile` / C++ smoke / sample parity を満たす。
- 差分が残る期間は計画書の決定ログに「ケース名・差分内容」を固定する。

## 13. 将来の横展開

- この ref-first 原則は `list` 固有ではなく、将来的には `dict` / `set` / `bytearray` にも同じ考え方で適用する。
- ただし本書の具体的な契約と回帰判定は `list` に限定する。
