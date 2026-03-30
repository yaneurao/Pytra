<a href="../../en/plans/p1-cs-emitter.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1-CS-EMITTER: C# emitter を toolchain2 に新規実装する

最終更新: 2026-03-30
ステータス: 未着手

## 背景

C# は Unity や .NET エコシステムで広く使われており、Pytra のターゲット言語としてユーザー需要が高い。旧 toolchain1 に C# emitter（`src/toolchain/emit/cs/`）と runtime（`src/runtime/cs/`）が存在するが、toolchain2 の新パイプラインに移行する必要がある。

## 設計

### emitter 構成

- `src/toolchain2/emit/cs/` に CommonRenderer + override 構成で実装
- 旧 `src/toolchain/emit/cs/` と TS emitter（`src/toolchain2/emit/ts/`）を参考にする
- C# 固有のノード（namespace、using、property、LINQ、nullable 型等）だけ override

### mapping.json

`src/runtime/cs/mapping.json` に以下を定義:
- `calls`: runtime_call の写像
- `types`: EAST3 型名 → C# 型名（`int64` → `long`, `float64` → `double`, `str` → `string`, `Exception` → `Exception` 等）
- `env.target`: `"\"cs\""`
- `builtin_prefix`: `"py_"`
- `implicit_promotions`: C# の暗黙昇格ペア（C++ とほぼ同じ）

### parity check

- `pytra-cli2 -build --target cs` の対応が必要（インフラ担当に依頼）
- `runtime_parity_check_fast.py --targets cs` で検証
- fixture + sample + stdlib の3段階

## 決定ログ

- 2026-03-30: C# backend 担当を新設。emitter guide に従い toolchain2 emitter を実装する方針。
