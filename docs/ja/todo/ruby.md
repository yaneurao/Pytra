<a href="../../en/todo/ruby.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Ruby backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-30

## 運用ルール

- **旧 toolchain1（`src/toolchain/emit/ruby/`）は変更不可。** 新規開発・修正は全て `src/toolchain2/emit/ruby/` で行う（[spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1）。
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

### P0-RUBY-FIXTURE-PARITY-161: Ruby fixture parity を 161/161 に揃える

文脈: [docs/ja/plans/p0-fixture-parity-161.md](../plans/p0-fixture-parity-161.md)

現状: 155/161 PASS。FAIL: `collections/reversed_basic`, `signature/ok_typed_varargs_representative`, `typing/callable_optional_none`。未実行: `control/for_tuple_iter`, `typing/for_over_return_value`, `typing/nullable_dict_field`。

1. [x] [ID: P0-FIX161-RUBY-S1] 未実行 3 件を `runtime_parity_check_fast.py --targets ruby --case-root fixture` で確定し、fail なら分類へ追加する
2. [x] [ID: P0-FIX161-RUBY-S2] reversed / typed varargs / callable optional の fail を解消し、Ruby fixture parity 161/161 PASS を確認する


### P1-HOST-CPP-EMITTER-RUBY: C++ emitter を ruby で host する

C++ emitter（`toolchain.emit.cpp.cli`、16 モジュール）を ruby に変換し、変換された emitter が C++ コードを正しく生成できることを確認する。C++ emitter の source は selfhost-safe 化済み。

1. [x] [ID: P1-HOST-CPP-EMITTER-RUBY-S1] `python3 src/pytra-cli.py -build src/toolchain/emit/cpp/cli.py --target ruby -o work/selfhost/host-cpp/ruby/` で変換 + build を通す
   - 進捗: 2026-04-30 に `pytra-cli.py -build` の target wiring を修正し、`--target ruby` が `toolchain.emit.ruby.cli` へ到達するようにした。`rm -rf work/selfhost/host-cpp/ruby && timeout 3600s python3 src/pytra-cli.py -build src/toolchain/emit/cpp/cli.py --target ruby -o work/selfhost/host-cpp/ruby/` は変換 PASS（22 files）。
   - 進捗: 2026-04-30 に C++ types の injected mapping を `G_TYPES` 定数化し、Ruby のトップレベルメソッド可視性問題を回避した。`ruby -c work/selfhost/host-cpp/ruby/toolchain_emit_cpp_cli.rb` は `Syntax OK`。実行は CommonRenderer 初期化まで進み、`toolchain_emit_common_profile_loader.rb` の `load_profile_doc` が `__comp_11` 未定義で停止する。原因は Ruby emitter が `ErrorCheck` lowering の `__comp_*` 代入を生成しないこと。
   - 進捗: 2026-04-30 に Ruby emitter の `ErrorReturn`/`ErrorCheck`/`ErrorCatch` lowering、C++ emitter の helper 名衝突回避（`_emit_line`/`_cpp_indent`/`_cpp_emit_blank`）、`header_gen` の Ruby 可視定数化、`class_type_ids.keys()` 反復化を追加した。`ruby -c` は `Syntax OK`、Ruby host 実行は 33 files（`toolchain_emit_cpp_cli.cpp` まで）を書いた後、`toolchain.emit.cpp.emitter` 生成中に 1 時間 timeout（exit 124）。
   - 進捗: 2026-04-30 に C++ emitter 側の `while` + `continue` 無限再処理（`_emit_call` / `_function_param_is_mutated_via_call`）、profile JSON cache 未格納、関数 param meta 再解析、top-level 関数の不要 self mutation 解析、string ops include 判定の巨大 BoolOp 化を修正した。Python 版の単一 `toolchain.emit.cpp.emitter` 出力は 1.17 秒まで短縮。Ruby host は同単一 module がまだ 300 秒 timeout のため、次は Ruby 生成物側の末尾処理を継続調査する。
   - 完了: 2026-04-30 に `header_gen` の `while` + `continue` 無限再処理、Ruby runtime の `dict.pop(key, default)`、dataclass constructor keyword 落ち、Ruby `isinstance(bool)` の FalseClass 漏れ、header-only runtime 出力末尾を修正。`pytra-cli.py -build --target ruby`、`ruby -c`、Ruby host フル manifest 実行が PASS。
2. [x] [ID: P1-HOST-CPP-EMITTER-RUBY-S2] `python3 tools/run/run_emitter_host_parity.py --host-lang ruby --hosted-emitter cpp --case-root fixture` で C++ emitter host parity PASS を確認する（結果は `.parity-results/emitter_host_ruby.json` に自動書き込み）
   - 完了: 2026-04-30 に Ruby-hosted C++ emitter が `work/tmp/build_cli/linked/manifest.json` から 55 files を生成。Python direct C++ emitter を同じ manifest から `work/selfhost/host-cpp/python-full` に再生成し、`diff -ru work/selfhost/host-cpp/python-full work/selfhost/host-cpp/ruby-run` が一致。`.parity-results/emitter_host_ruby.json` に build/parity PASS を記録。

### P1-EMITTER-SELFHOST-RUBY: emit/ruby/cli.py を単独で selfhost C++ build に通す

文脈: [docs/ja/plans/p1-emitter-selfhost-per-backend.md](../plans/p1-emitter-selfhost-per-backend.md)

各 backend emitter は subprocess で独立起動する自己完結プログラム。pytra-cli.py 全体の selfhost とは切り離し、`toolchain.emit.ruby.cli` をエントリに単独で C++ build を通す。

1. [ ] [ID: P1-EMITTER-SELFHOST-RUBY-S1] `python3 src/pytra-cli.py -build src/toolchain/emit/ruby/cli.py --target cpp -o work/selfhost/emit/ruby/` を実行し、変換が通るようにする
   - 進捗: 2026-04-29 に実行し、C++ 出力は途中まで進むが完走せず。`timeout 3600s python3 src/pytra-cli.py -build src/toolchain/emit/ruby/cli.py --target cpp -o work/selfhost/emit/ruby/` は終了コード 124。停止時点で `work/selfhost/emit/ruby/` は 36 ファイルの部分出力（うち C++ 14 件）に留まり、selfhost emitter のエントリ一式生成まで到達しない。
2. [ ] [ID: P1-EMITTER-SELFHOST-RUBY-S2] 生成された C++ を `g++ -std=c++20 -O0` でコンパイルを通す（source 側の型注釈不整合を修正）
3. [ ] [ID: P1-EMITTER-SELFHOST-RUBY-S3] コンパイル済み emitter で既存 fixture の manifest を処理し、Python 版 emitter と parity 一致を確認する


### P0-RUBY-NEW-FIXTURE-PARITY: 新規追加 fixture / stdlib の parity 確認

今セッション（2026-04-01〜05）で追加・更新した fixture と stdlib の parity を確認する。

対象: `bytes_copy_semantics`, `negative_index_comprehensive`, `negative_index_out_of_range`, `callable_optional_none`, `str_find_index`, `eo_extern_opaque_basic`(emit-only), `math_extended`(stdlib), `os_glob_extended`(stdlib)

1. [ ] [ID: P0-RUBY-NEWFIX-S1] 上記 fixture/stdlib の parity を確認する（対象 fixture のみ実行）

### P20-RUBY-SELFHOST: Ruby emitter で toolchain2 を Ruby に変換し実行できるようにする

1. [ ] [ID: P20-RUBY-SELFHOST-S0] selfhost 対象コードの型注釈補完（他言語と共通）
2. [ ] [ID: P20-RUBY-SELFHOST-S1] toolchain2 全 .py を Ruby に emit し、実行できることを確認する
3. [ ] [ID: P20-RUBY-SELFHOST-S2] selfhost 用 Ruby golden を配置する
4. [ ] [ID: P20-RUBY-SELFHOST-S3] `run_selfhost_parity.py --selfhost-lang ruby --emit-target ruby --case-root fixture` で fixture parity PASS
5. [ ] [ID: P20-RUBY-SELFHOST-S4] `run_selfhost_parity.py --selfhost-lang ruby --emit-target ruby --case-root sample` で sample parity PASS
