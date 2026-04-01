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
- 2026-04-01: stdlib parity は `16/16 pass` まで回復。Path/json/sys/png/glob/deque/ArgumentParser、class 継承、list/bytearray/string method、linked `pytra_isinstance` を Lua runtime/emitter に実装。
- 2026-04-01: fixture parity は `119/137 pass` まで改善。`StaticRangeForPlan`、staticmethod dispatch、varargs 復元、list concat、zip/sum、table repr を追加。
- 2026-04-01: sample parity は `1/18 pass`。画像 artifact、loop/continue、helper 関数不足、sample 特有の lowered パターンが残る。
- 2026-04-01: `docs/ja/spec/spec-exception.md` に合わせて Lua profile を `exception_style=union_return` に変更。`ErrorReturn` / `ErrorCheck` / `ErrorCatch` を emitter に実装し、`pytra.built_in.error` を pure Python exception class として emit/load するように修正。例外 fixture 5 件は pass に回復。
- 2026-04-01: 例外方式変更後の full fixture は `110/137 pass`、stdlib は `11/16 pass`。残差は `any_*`、dict/set wrapper、`isinstance_narrowing`、tuple unpack、repr/stringify、`math_extended`、`re_extended`、`sys_extended`、`argparse_extended`、`dataclasses_extended`。
