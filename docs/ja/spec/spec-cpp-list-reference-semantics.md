# C++ list 参照セマンティクス仕様（pyobj 既定）

この文書は C++ backend の `list` について、現行契約（pyobj 既定）と rollback 互換（value）を定義する。

## 1. 目的

- `list` の意味論を「現在は何を保証し、どこが未保証か」で明示する。
- `P1-LIST-PYOBJ-MIG-01` の段階移行中に、回帰判定の基準を固定する。
- `pyobj` 既定運用と rollback（`--cpp-list-model value`）の境界条件を明確化する。

## 2. 適用範囲

- 対象: C++ runtime / C++ emitter で生成される `list[...]`。
- 非対象: `dict` / `set` / `str` の参照モデル移行（別タスク）。

## 3. 用語

- `value model`: `list<T>` が値として保持・代入される rollback 互換モデル。
- `pyobj model`: `list` 自体を `PyObj` 派生 + `rc<>` で保持する参照モデル。
- `alias`: `b = a` のように同一 list を共有すること。
- `ref-first`: mutable 値はまず共有参照表現で保持し、証明できた経路だけ値型へ縮退する方針。

## 4. 現行運用（2026-02-28時点）

- `py2cpp` の `list` モデル既定は `pyobj`。
- rollback が必要な場合のみ `--cpp-list-model value` を指定する。
- 既定 `pyobj` 下では `list` は参照共有セマンティクスを維持する表現で扱われる。
- 実装上は `object`（PyListObj）または `rc<list<T>>` の typed handle を使ってよい。
- どちらを使うかは backend 内部の実装選択であり、契約上重要なのは alias 共有が壊れないことである。

## 5. 互換契約（value model: rollback 専用）

- `list<T>` は値型として扱われ、`b = a` はコピーを生成する。
- `append/pop/extend` は受け取った list 値に対して破壊的更新を行う。
- `Any/object` 境界でのみ `PyListObj(list<object>)` へ boxing される。
- したがって、静的型経路では Python の alias 共有と差分が生じうる。

## 6. 目標契約（pyobj model）

- `list` は既定で参照共有され、`b = a` 後の `append/pop` が相互に観測可能。
- 関数引数・戻り値・属性格納でも同一 list の共有を維持する。
- `Any/object` 境界の boxing/unboxing は no-op 互換（同一実体を保持）を優先する。

### 6.1 ref-first 原則

- `list` は mutable であるため、C++ backend 内部では ref-first を正本とする。
- `list<T>` を最初から値型として lower してはならない。
- 値型化は rollback 互換または最適化結果としてのみ許可する。
- つまり、`value model` は設計上の目標形ではなく、互換・比較・段階移行のための退避路である。

## 7. 破壊的更新の契約

- `append/pop/extend/clear` は list 実体に対して in-place に作用する。
- 共有 alias がある場合、すべての参照から更新結果が観測できなければならない。
- 非 alias（別実体）の場合のみ独立に更新される。

## 8. PyListObj の寿命/iter 契約

- `PyListObj::py_iter_or_raise()` は list 値の snapshot ではなく owner list 実体を参照する iterator を返す。
- iterator は owner list の寿命を保持する（owner 参照が失効した場合は停止）。
- 反復中に `py_append` された要素は、未走査範囲に存在する限り反復結果へ反映される。
- `py_try_len` / `py_truthy` は owner list 実体の現在状態に対して評価される。

## 9. 段階移行ポリシー

- Phase 1: `value|pyobj` dual model を許容し、切替フラグで比較可能にする。
- Phase 2: `pyobj` モデルで transpile/smoke/parity を安定化する。
- Phase 3: non-escape 注釈付き経路のみ stack/RAII へ縮退する。
- Phase 4: 既定を `pyobj` へ切替済み。`value` は rollback 期間中のみ維持し、撤去は別IDで段階実施する。

### 9.1 値型縮退の前提解析

値型縮退は、局所最適化だけで決めてはならない。

最低条件:

- mutation 解析
  - どの変数 / 引数 / 属性が list を破壊的更新するかを把握する。
- alias 解析
  - `b = a`、引数受け渡し、戻り値、属性格納、container 格納などで共有が発生するかを把握する。
- escape 解析
  - 関数外へ返るか、`Any/object` へ入るか、未知関数 / `@extern` へ渡るかを把握する。
- call graph + SCC
  - 再帰・相互再帰を含む関数群では、SCC 単位で summary を固定してから縮退可否を決める。

禁止:

- 同一関数内だけ見て「たぶん安全」と判断して値型へ落とすこと。
- 破壊的更新の有無だけを見て alias/escape を無視すること。
- `Any/object` や未知呼び出しを含む経路で値型縮退すること。

## 10. fail-closed ルール

- 変換不能・型不明・外部呼び出し混在経路は最適化を適用しない。
- non-escape が証明できない list を stack 化しない。
- 意味論が不明な場合は heap/pyobj 側に倒す。
- alias の可能性を否定できない list を値型化しない。
- call graph / SCC summary が未確定の段階で interprocedural な値型化をしない。

## 11. 受け入れ判定

- alias 期待 fixture（`a=b` 後の `append/pop`）で Python と一致する。
- `check_py2cpp_transpile` / C++ smoke / sample parity を満たす。
- 差分が残る期間は計画書の決定ログに「ケース名・差分内容」を固定する。

## 12. 将来の横展開

- この ref-first 原則は `list` 固有ではなく、将来的には `dict` / `set` / `bytearray` にも同じ考え方で適用する。
- ただし本書の具体的な契約と回帰判定は `list` に限定する。
