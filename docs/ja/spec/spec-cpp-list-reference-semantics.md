# C++ list 参照セマンティクス仕様（移行前提）

この文書は C++ backend の `list` について、現行挙動と移行先契約（PyObj/RC モデル）を定義する。

## 1. 目的

- `list` の意味論を「現在は何を保証し、どこが未保証か」で明示する。
- `P1-LIST-PYOBJ-MIG-01` の段階移行中に、回帰判定の基準を固定する。
- `value` モデルから `pyobj` モデルへ切り替える際の契約差分を最小化する。

## 2. 適用範囲

- 対象: C++ runtime / C++ emitter で生成される `list[...]`。
- 非対象: `dict` / `set` / `str` の参照モデル移行（別タスク）。

## 3. 用語

- `value model`: `list<T>` が値として保持・代入される現行モデル。
- `pyobj model`: `list` 自体を `PyObj` 派生 + `rc<>` で保持する参照モデル。
- `alias`: `b = a` のように同一 list を共有すること。

## 4. 現行契約（value model）

- `list<T>` は値型として扱われ、`b = a` はコピーを生成する。
- `append/pop/extend` は受け取った list 値に対して破壊的更新を行う。
- `Any/object` 境界でのみ `PyListObj(list<object>)` へ boxing される。
- したがって、静的型経路では Python の alias 共有と差分が生じうる。

## 5. 目標契約（pyobj model）

- `list` は既定で参照共有され、`b = a` 後の `append/pop` が相互に観測可能。
- 関数引数・戻り値・属性格納でも同一 list の共有を維持する。
- `Any/object` 境界の boxing/unboxing は no-op 互換（同一実体を保持）を優先する。

## 6. 破壊的更新の契約

- `append/pop/extend/clear` は list 実体に対して in-place に作用する。
- 共有 alias がある場合、すべての参照から更新結果が観測できなければならない。
- 非 alias（別実体）の場合のみ独立に更新される。

## 7. 段階移行ポリシー

- Phase 1: `value|pyobj` dual model を許容し、切替フラグで比較可能にする。
- Phase 2: `pyobj` モデルで transpile/smoke/parity を安定化する。
- Phase 3: non-escape 注釈付き経路のみ stack/RAII へ縮退する。
- Phase 4: 既定を `pyobj` へ切替し、`value` は rollback 期間後に撤去する。

## 8. fail-closed ルール

- 変換不能・型不明・外部呼び出し混在経路は最適化を適用しない。
- non-escape が証明できない list を stack 化しない。
- 意味論が不明な場合は heap/pyobj 側に倒す。

## 9. 受け入れ判定

- alias 期待 fixture（`a=b` 後の `append/pop`）で Python と一致する。
- `check_py2cpp_transpile` / C++ smoke / sample parity を満たす。
- 差分が残る期間は計画書の決定ログに「ケース名・差分内容」を固定する。
