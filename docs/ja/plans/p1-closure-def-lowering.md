<a href="../../en/plans/p1-closure-def-lowering.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1-CLOSURE-DEF: nested FunctionDef の ClosureDef lowering

最終更新: 2026-03-26
ステータス: 未着手

## 背景

Python の nested FunctionDef（関数内関数）は、Go など一部のターゲット言語では直接表現できない。現状 emitter がこの変換を担っているケースがあるが、外側スコープの変数キャプチャ解析は意味論の決定であり、emitter の責務（表記の写像）ではない。

EAST3 で captures 解析を行い、`ClosureDef` ノード（または FunctionDef への closure metadata 付与）に lower することで、emitter は各言語の closure 構文に写像するだけにする。

## 設計判断

### 対象言語のレベル分類

| レベル | 言語例 | nested function | closure |
|---|---|---|---|
| A: ネイティブサポート | JS, TS, Rust, Swift, Kotlin | そのまま | そのまま |
| B: closure あり | Go, C++, Java, C# | closure に変換 | そのまま |

現行ターゲット全言語が A または B に該当する。closure なし言語（C 等）は現時点で backend になく、対応しない（YAGNI）。

### 責務分離

- **EAST3 共通**: nested FunctionDef を検出し、キャプチャ解析結果を付与した `ClosureDef` に lower する
- **emitter**: `ClosureDef` を各言語の closure 構文に写像するだけ

### キャプチャ解析の内容

1. nested FunctionDef が参照する外側スコープの変数を列挙
2. capture mode の判定（`readonly` / `mutable`）
3. ClosureDef ノードに `captures` リストとして保持

```json
{
  "kind": "ClosureDef",
  "name": "inner",
  "captures": [
    {"name": "x", "mode": "readonly", "type_expr": ...},
    {"name": "y", "mode": "mutable", "type_expr": ...}
  ],
  "args": [...],
  "body": [...],
  "return_type_expr": ...
}
```

### LifetimeAnalysisPass との連携

既存の `LifetimeAnalysisPass`（def-use 解析 + liveness 情報）がキャプチャ解析の基盤になり得る。nested function が外側スコープのどの変数を参照しているかは def-use 情報から導出可能。

### emitter の写像先

| 言語 | 写像先 |
|---|---|
| Go | `inner := func(...) { ... }` |
| C++ | `auto inner = [&x, y](...) { ... };` (readonly は値、mutable は参照) |
| Java | ラムダ or anonymous class |
| C# | ラムダ |
| JS/TS | そのまま nested function（レベル A） |
| Rust | `let inner = \|...\| { ... };` |
| Swift | `let inner = { (...) -> T in ... }` |
| Kotlin | `val inner = { ... -> ... }` |

レベル A 言語では `ClosureDef` を通常の nested function として出力してもよい。

## リスク

- nested function が再帰的に自身を呼ぶケース（名前付き closure が必要）
- mutable capture の Go での制約（Go は全て参照キャプチャだが明示不要）
- C++ の capture mode 選択（`[=]` / `[&]` / 個別指定）の正確な判定

## サブタスク

1. [ID: P1-CLOSURE-DEF-S1] EAST3 の ClosureDef ノード仕様を spec-east.md に追加
2. [ID: P1-CLOSURE-DEF-S2] EAST3 lowering でキャプチャ解析 + ClosureDef 生成を実装
3. [ID: P1-CLOSURE-DEF-S3] fixture 追加（nested function のキャプチャパターン）+ golden 生成
4. [ID: P1-CLOSURE-DEF-S4] 各 emitter の ClosureDef 写像実装 + parity 確認

## 受け入れ基準

1. nested FunctionDef が EAST3 で `ClosureDef` に lower されること
2. captures リストにキャプチャ変数と mode が正しく列挙されること
3. 既存 fixture + sample の parity が維持されること
4. emitter に キャプチャ解析ロジックが存在しないこと

## 決定ログ

- 2026-03-26: nested FunctionDef の変換は emitter の責務ではなく EAST3 lowering で行う方針を決定。現行ターゲット全言語が closure をサポートしているため、closure なし言語（関数抽出+構造体パターン）への対応は YAGNI として見送り。
