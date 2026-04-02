<a href="../../en/todo/ruby.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Ruby backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-02

## 運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## 参考資料

- 旧 toolchain1 の Ruby emitter: `src/toolchain/emit/rb/`
- toolchain2 の TS emitter（参考実装）: `src/toolchain2/emit/ts/`
- 既存の Ruby runtime: `src/runtime/ruby/`
- emitter 実装ガイドライン: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json 仕様: `docs/ja/spec/spec-runtime-mapping.md`

## 未完了タスク

### P0-RUBY-TYPE-ID-CLEANUP: Ruby runtime から __pytra_isinstance を削除する

仕様: [docs/ja/spec/spec-adt.md](../spec/spec-adt.md) §6

Ruby は `is_a?` がネイティブにあるので `__pytra_isinstance` は不要。

1. [x] [ID: P0-RUBY-TYPEID-CLN-S1] `src/runtime/ruby/built_in/py_runtime.rb` から `__pytra_isinstance` を削除する — runtime helper 削除と mapping 整理を実施（2026-04-02）
2. [x] [ID: P0-RUBY-TYPEID-CLN-S2] fixture + sample parity に回帰がないことを確認する — `runtime_parity_check_fast.py --targets ruby --east3-opt-level 1` で fixture `138/138 PASS` を確認（2026-04-02）

### P1-RUBY-EMITTER: Ruby emitter を toolchain2 に新規実装する

文脈: [docs/ja/plans/p1-ruby-emitter.md](../plans/p1-ruby-emitter.md)

1. [x] [ID: P1-RUBY-EMITTER-S1] `src/toolchain2/emit/ruby/` に Ruby emitter を新規実装する — CommonRenderer + override 構成。TS emitter を参考に実装完了（2026-03-31）
2. [x] [ID: P1-RUBY-EMITTER-S2] `src/runtime/ruby/mapping.json` を作成する — `calls`, `types`, `env.target`, `builtin_prefix`, `implicit_promotions` を定義（2026-03-31）
3. [x] [ID: P1-RUBY-EMITTER-S3] fixture 全件の Ruby emit 成功を確認する — 全1031件のlinked EAST3で emit 成功、0 failures（2026-03-31）
4. [x] [ID: P1-RUBY-EMITTER-S4] Ruby runtime を toolchain2 の emit 出力と整合させる — py_runtime.rb に不足していた15関数を追加（2026-03-31）
5. [x] [ID: P1-RUBY-EMITTER-S5] fixture + sample の Ruby run parity を通す（`ruby`） — fixture parity `138/138 PASS`、残件 5 件（`gc_reassign`, `integer_promotion`, `obj_attr_space`, `str_repr_containers`, `super_init`）を解消（2026-04-02）
6. [x] [ID: P1-RUBY-EMITTER-S6] stdlib の Ruby parity を通す（`--case-root stdlib`） — stdlib `16/16 PASS`、sample `18/18 PASS`、fixture `138/138 PASS` を確認。残件だった `12_sort_visualizer` は Ruby emitter の `Swap` 実装修正で解消（2026-04-02）

### P2-RUBY-LINT-FIX: Ruby emitter のハードコード違反を修正する

1. [x] [ID: P2-RUBY-LINT-S1] `check_emitter_hardcode_lint.py` で Ruby の違反が 0 件になることを確認する — class name / Python syntax / skip pure Python を解消し 0 件確認（2026-04-02）

### P20-RUBY-SELFHOST: Ruby emitter で toolchain2 を Ruby に変換し実行できるようにする

1. [ ] [ID: P20-RUBY-SELFHOST-S0] selfhost 対象コードの型注釈補完（他言語と共通）
2. [ ] [ID: P20-RUBY-SELFHOST-S1] toolchain2 全 .py を Ruby に emit し、実行できることを確認する
3. [ ] [ID: P20-RUBY-SELFHOST-S2] selfhost 用 Ruby golden を配置する
4. [ ] [ID: P20-RUBY-SELFHOST-S3] `run_selfhost_parity.py --selfhost-lang ruby --emit-target ruby --case-root fixture` で fixture parity PASS
5. [ ] [ID: P20-RUBY-SELFHOST-S4] `run_selfhost_parity.py --selfhost-lang ruby --emit-target ruby --case-root sample` で sample parity PASS
