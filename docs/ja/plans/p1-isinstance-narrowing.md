<a href="../../en/plans/p1-isinstance-narrowing.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1-ISINSTANCE-NARROWING: isinstance 後の自動型ナローイング

最終更新: 2026-03-27
ステータス: 完了

## 背景

現在 Pytra では union 型や nominal ADT（`JsonVal` 等）に対してメソッド呼び出しを行うには、`isinstance` で判定した後に手動で `cast` する必要がある。

```python
# 現状: 手動 cast が必要
if isinstance(stmt, dict):
    d: dict[str, JsonVal] = cast(dict[str, JsonVal], stmt)
    d.get("key")
```

TypeScript の型ガード、Kotlin の smart cast と同様に、`if isinstance(x, T):` の if ブロック内で `x` の型を自動的に `T` に narrowing する機能を導入する。

```python
# 提案: isinstance 後の if ブロック内で自動 narrowing
if isinstance(stmt, dict):
    stmt.get("key")  # stmt は dict[str, JsonVal] として扱える
```

## 設計

### 責務の置き場所

resolve 段（EAST2）だけの変更で実現する。

| 層 | 責務 |
|---|---|
| **EAST2 (resolve)** | `if isinstance(x, T):` を検出し、if ブロック内で `x` の型環境を `T` に更新 |
| EAST3 | narrowing 済みの型情報をそのまま保持（追加作業なし） |
| emitter | narrowing 済みの `resolved_type` を写像するだけ（追加作業なし） |

### 実装方針

1. resolve が `If` 文の条件式を解析し、`isinstance(x, T)` パターンを検出
2. if ブロック（`body`）の型環境で `x` の型を `T` に上書き
3. `elif isinstance(x, U):` も同様に処理
4. early return guard: `if not isinstance(x, T): return` の後、関数の残り全体で `x` を `T` に narrowing
5. ternary isinstance: `y = x if isinstance(x, T) else None` で真側の `x` を `T` に narrowing
6. narrowing は暗黙 cast として EAST2 の型情報に反映（`resolved_type` / `type_expr` を更新）

### v1 スコープ

| パターン | 例 | v1 対応 |
|---|---|---|
| if ブロック内 narrowing | `if isinstance(x, T): x.method()` | 対応 |
| elif narrowing | `elif isinstance(x, U): x.method()` | 対応 |
| early return guard | `if not isinstance(x, T): return` → 以降 x は T | 対応 |
| ternary isinstance | `y = x if isinstance(x, T) else None` | 対応 |
| ブロック内伝播（ループ等） | `if isinstance(x, list): for item in x` | 対応（基本 narrowing の自然な帰結） |
| `isinstance` と `and` の組み合わせ | `if isinstance(x, T) and len(x) > 0:` | 対応 |
| `not isinstance(...) or ...: continue` の guard | `if not isinstance(x, T) or pred(x): continue` | 対応 |
| `else` ブロックでの除外型推論 | `else: # x は T ではない` | 対応しない |
| `x` が if ブロック内で再代入される場合 | `x = other_value` | narrowing を無効化（安全側） |

### early return guard の設計

`if not isinstance(x, T): return`（または `raise` / `break` / `continue`）は、if ブロックが必ず脱出するため、後続の文で `x` の型が `T` に確定する。

```python
def process(val: JsonVal) -> str:
    if not isinstance(val, dict):
        return ""
    # ここ以降 val は dict[str, JsonVal]
    val.get("key")  # OK
```

resolve はこれを「if ブロックの全分岐が脱出する（return/raise/break/continue）」ことを検出し、後続の型環境で narrowing を適用する。

### ternary isinstance の設計

`y = x if isinstance(x, T) else default` の真側で `x` を `T` として解決する。

```python
owner_node = owner if isinstance(owner, dict) else None
# owner_node の型は dict[str, JsonVal] | None
```

### 既存仕様との整合

- `cast` は引き続き明示的に使える（後方互換）
- narrowing は resolve が型環境を更新するだけであり、新しい EAST ノードは不要
- `type_expr` が正本という原則は維持

## リスク

- `isinstance(x, T)` の `T` が generic 型（`dict[str, JsonVal]` 等）の場合、型パラメータの推論が必要
- nominal ADT の variant narrowing との整合（`isinstance(x, Cat)` で `Animal` → `Cat`）
- ネストした `isinstance`（`if isinstance(x, A): if isinstance(x.field, B):`）の扱い

## サブタスク

1. [ID: P1-NARROW-S1] resolve に isinstance 条件式の検出 + if/elif ブロック内型環境更新を実装
2. [ID: P1-NARROW-S2] early return guard の対応（`if not isinstance(x, T): return` 後の fallthrough narrowing）
3. [ID: P1-NARROW-S3] ternary isinstance の対応（`y = x if isinstance(x, T) else None`）
4. [ID: P1-NARROW-S4] 再代入検出による narrowing 無効化の実装
5. [ID: P1-NARROW-S5] fixture 追加（全 narrowing パターン）+ golden 生成 + parity 確認

## 受け入れ基準

1. `if isinstance(x, T):` の if ブロック内で `x` が `T` として型解決されること
2. `elif isinstance(x, U):` でも同様に動作すること
3. `if not isinstance(x, T): return` の後で `x` が `T` として型解決されること
4. `y = x if isinstance(x, T) else None` の真側で `x` が `T` として型解決されること
5. narrowing が if ブロック内のループ等に自然に伝播すること
6. if ブロック内で `x` に再代入がある場合、narrowing が無効化されること
7. 既存の手動 `cast` パターンが引き続き動作すること（後方互換）
8. 既存 fixture / sample の parity が維持されること

## 決定ログ

- 2026-03-27: selfhost の call_graph.py で JsonVal → dict narrowing が Go に落ちない問題を契機に、isinstance 後の自動型ナローイングを仕様化。resolve 段の型環境更新で実現し、emitter に負担をかけない設計とする。
- 2026-03-27: go-selfhost 担当の報告を受け、v1 スコープを拡大。early return guard、ternary isinstance、ブロック内伝播を v1 に含める。
- 2026-03-27: 実装では narrowing の正本を resolver/EAST に集約し、emitter での guard-aware scope 追跡は採用しない。`JsonVal` の narrowing 先は `dict[str,JsonVal]` / `list[JsonVal]` を canonical とする。
- 2026-03-27: `and` 連結条件と `not isinstance(...) or ...: continue` 形式の fallthrough guard は v1 に含める。再代入が起きた名前は同一ブロック内でも narrow 済み型環境から即座に外す。
