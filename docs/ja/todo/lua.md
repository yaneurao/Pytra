<a href="../../en/todo/lua.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Lua backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-01（Lua exception を union_return に切替、P2-LUA-LINT-S1 完了、fixture/sample parity 継続中）

## 運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## 参考資料

- 旧 toolchain1 の Lua emitter: `src/toolchain/emit/lua/`
- toolchain2 の TS emitter（参考実装）: `src/toolchain2/emit/ts/`
- 既存の Lua runtime: `src/runtime/lua/`
- emitter 実装ガイドライン: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json 仕様: `docs/ja/spec/spec-runtime-mapping.md`

## 未完了タスク

### P0-LUA-TYPE-ID-CLEANUP: Lua runtime から __pytra_isinstance を削除する

仕様: [docs/ja/spec/spec-adt.md](../spec/spec-adt.md) §6

Lua は `type()` がネイティブにあるので `__pytra_isinstance` は不要。

1. [ ] [ID: P0-LUA-TYPEID-CLN-S1] `src/runtime/lua/built_in/py_runtime.lua` から `__pytra_isinstance` を削除する
2. [ ] [ID: P0-LUA-TYPEID-CLN-S2] fixture + sample parity に回帰がないことを確認する

### P1-LUA-EMITTER: Lua emitter を toolchain2 に新規実装する

文脈: [docs/ja/plans/p1-lua-emitter.md](../plans/p1-lua-emitter.md)

1. [x] [ID: P1-LUA-EMITTER-S1] `src/toolchain2/emit/lua/` に Lua emitter を新規実装する — CommonRenderer + override 構成。旧 `src/toolchain/emit/lua/` と TS emitter を参考にする。Lua 固有（1-based index、nil、metatables 等）だけ override（2026-04-01）
2. [x] [ID: P1-LUA-EMITTER-S2] `src/runtime/lua/mapping.json` を作成する — `calls`, `types`, `env.target`, `builtin_prefix`, `implicit_promotions` を定義（2026-04-01）
3. [x] [ID: P1-LUA-EMITTER-S3] fixture 全件の Lua emit 成功を確認する（2026-04-01）— `_transpile_in_memory(..., target='lua')` で fixture 136/136 emit success
4. [x] [ID: P1-LUA-EMITTER-S4] Lua runtime を toolchain2 の emit 出力と整合させる（2026-04-01）— Path/json/sys/png/glob/deque/ArgumentParser、class 継承、list/bytearray/string method、linked `pytra_isinstance` を整合
5. [ ] [ID: P1-LUA-EMITTER-S5] fixture + sample の Lua run parity を通す（`lua5.4`）— 2026-04-01 時点で fixture `110/137 pass`、sample `1/18 pass`。`spec-exception.md` に合わせて Lua exception を `union_return` 化し、例外 fixture (`exception_finally_order`, `exception_propagation_raise_from`, `exception_propagation_two_frames`, `exception_user_defined_multi_handler`, `union_return_errorcheck`) は pass に回復。残差は `any_*`、dict/set wrapper、`isinstance_narrowing`、tuple unpack、repr/stringify 系、sample 側の画像 artifact・loop/continue・helper 不足
6. [ ] [ID: P1-LUA-EMITTER-S6] stdlib の Lua parity を通す（`--case-root stdlib`）— 2026-04-01 時点で `11/16 pass`。`argparse_extended`, `dataclasses_extended`, `math_extended`, `re_extended`, `sys_extended` が残差

### P2-LUA-LINT-FIX: Lua emitter のハードコード違反を修正する

1. [x] [ID: P2-LUA-LINT-S1] `check_emitter_hardcode_lint.py` で Lua の違反が 0 件になることを確認する（2026-04-01）— 0 件

### P20-LUA-SELFHOST: Lua emitter で toolchain2 を Lua に変換し実行できるようにする

1. [ ] [ID: P20-LUA-SELFHOST-S0] selfhost 対象コードの型注釈補完（他言語と共通）
2. [ ] [ID: P20-LUA-SELFHOST-S1] toolchain2 全 .py を Lua に emit し、実行できることを確認する
3. [ ] [ID: P20-LUA-SELFHOST-S2] selfhost 用 Lua golden を配置する
4. [ ] [ID: P20-LUA-SELFHOST-S3] `run_selfhost_parity.py --selfhost-lang lua --emit-target lua --case-root fixture` で fixture parity PASS
5. [ ] [ID: P20-LUA-SELFHOST-S4] `run_selfhost_parity.py --selfhost-lang lua --emit-target lua --case-root sample` で sample parity PASS
