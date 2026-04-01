<a href="../../en/plans/p1-lua-emitter.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1-LUA-EMITTER: Lua emitter を toolchain2 に新規実装する

最終更新: 2026-04-01
ステータス: 進行中

## 背景

旧 toolchain1 に Lua emitter と runtime が存在するが、toolchain2 の新パイプラインに移行する必要がある。

## 設計

- `src/toolchain2/emit/lua/` に CommonRenderer + override 構成で実装
- 旧 `src/toolchain/emit/lua/` と TS emitter（`src/toolchain2/emit/ts/`）を参考にする
- `src/runtime/lua/mapping.json` に `calls`, `types`, `env.target`, `builtin_prefix`, `implicit_promotions` を定義
- parity check: `runtime_parity_check_fast.py --targets lua` で fixture + sample + stdlib の3段階検証

## 決定ログ

- 2026-03-31: Lua backend 担当を新設。emitter guide に従い toolchain2 emitter を実装する方針。
- 2026-04-01: `src/toolchain2/emit/lua/` と `src/runtime/lua/mapping.json` の実装存在を確認。fixture emit は 136/136 success。
- 2026-04-01: `check_emitter_hardcode_lint.py --lang lua -v --no-write` を 0 件まで解消。
- 2026-04-01: parity は未完了。代表残差は `add`, `deque_basic`, `class_instance`, `json_*`, `sys_extended`, `argparse_extended`, `pathlib_extended`。
