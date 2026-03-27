<a href="../../en/language/nominal-adt-v1.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# nominal ADT v1 ガイド

最終更新: 2026-03-11

この文書は、nominal ADT を Pytra の正式言語機能として扱うための v1 surface と、現時点の rollout 状態をまとめた migration note です。

## canonical v1 surface

- family 宣言は top-level `class` に `@sealed` を付けて表します。
- variant は同じ module 内の top-level `class` とし、family を単一継承します。
- payload variant は `@dataclass` を必須にします。
- constructor は variant class 呼び出しで表します。例: `Just(1)`
- variant access は `isinstance(x, Just)` で narrow した後の field access を正本にします。
- built-in `JsonValue` lane と user-defined nominal ADT lane は、どちらも `nominal_adt` category を共有します。

## selfhost-safe 制約

現時点で representative に固定しているのは次です。

- same-module / family-first の top-level family / variant
- payload variant の `@dataclass` 必須
- function-local / class-local の nominal ADT declaration は非対象
- `match/case` の user-facing source surface はまだ canonical v1 に含めない

この制約は、selfhost parser と representative backend を fail-closed で揃えるための staged rollout です。

## backend rollout 状態

- C++:
  - representative nominal ADT v1 declaration / constructor / variant check / projection をサポート
  - representative `NominalAdtMatch` lane は `if / else if` に lower
  - plain `Match` は `unsupported Match lane` で fail-closed
- Rust / C#:
  - representative nominal ADT v1 lane を `unsupported_syntax` で fail-closed
- Go / Java / Kotlin / Scala / Swift / Nim / JS / TS / Lua / Ruby / PHP:
  - representative nominal ADT `Match` lane を backend-local `unsupported stmt kind: Match` で fail-closed

## migration 指針

- 既存の class hierarchy で closed sum type を表している場合は、family を `@sealed` にし、variant を top-level class へ寄せてください。
- payload を持つ variant は `@dataclass` を付けてください。
- variant payload の読み出しは、当面 `match/case` ではなく `isinstance(...)` + field access を使ってください。
- `JsonValue` のような built-in nominal ADT lane と揃えるため、`object` fallback や ad-hoc cast に逃がさないでください。

## 関連

- v1 user surface: [spec-user](../spec/spec-user.md)
- ADT / pattern / `match` schema: [spec-east](../spec/spec-east.md)
- C++ representative support: [py2cpp サポートマトリクス](./cpp/spec-support.md)
