<a href="../../en/todo/go.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Go backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-05-03

## 運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## 未完了タスク

### P0-GO-FIXTURE-PARITY-161: Go fixture parity を 161/161 に揃える

文脈: [docs/ja/plans/p0-fixture-parity-161.md](../plans/p0-fixture-parity-161.md)

現状: 154/161 PASS。FAIL: `collections/reversed_basic`, `signature/ok_typed_varargs_representative`, `typing/isinstance_union_narrowing`, `typing/optional_none`。未実行: `control/for_tuple_iter`, `typing/for_over_return_value`, `typing/nullable_dict_field`。

1. [x] [ID: P0-FIX161-GO-S1] 未実行 3 件を `runtime_parity_check_fast.py --targets go --case-root fixture` で確定し、fail なら分類へ追加する
2. [x] [ID: P0-FIX161-GO-S2] reversed / typed varargs / union narrowing / optional の fail を解消し、Go fixture parity 161/161 PASS を確認する


### P1-HOST-CPP-EMITTER-GO: C++ emitter を go で host する

C++ emitter（`toolchain.emit.cpp.cli`、16 モジュール）を go に変換し、変換された emitter が C++ コードを正しく生成できることを確認する。C++ emitter の source は selfhost-safe 化済み。

1. [x] [ID: P1-HOST-CPP-EMITTER-GO-S1] `python3 src/pytra-cli.py -build src/toolchain/emit/cpp/cli.py --target go -o work/selfhost/host-cpp/go/` で変換 + build を通す
2. [x] [ID: P1-HOST-CPP-EMITTER-GO-S2] `python3 tools/run/run_emitter_host_parity.py --host-lang go --hosted-emitter cpp --case-root fixture` で C++ emitter host parity PASS を確認する（結果は `.parity-results/emitter_host_go.json` に自動書き込み）
   - 2026-04-29: `diff -ru work/selfhost/host-cpp/python work/selfhost/host-cpp/go-run` の一致を再確認し、`.parity-results/emitter_host_go.json` に build/parity PASS を記録。`gen_backend_progress.py` で emitter host マトリクスに反映済み。

### P1-EMITTER-SELFHOST-GO: emit/go/cli.py を単独で selfhost C++ build に通す

文脈: [docs/ja/plans/p1-emitter-selfhost-per-backend.md](../plans/p1-emitter-selfhost-per-backend.md)

各 backend emitter は subprocess で独立起動する自己完結プログラム。pytra-cli.py 全体の selfhost とは切り離し、`toolchain.emit.go.cli` をエントリに単独で C++ build を通す。

1. [x] [ID: P1-EMITTER-SELFHOST-GO-S1] `python3 src/pytra-cli.py -build src/toolchain/emit/go/cli.py --target cpp -o work/selfhost/emit/go/` を実行し、変換が通るようにする
   - 2026-04-28: Go CLI を selfhost-safe な単独 manifest runner にし、Go emitter/types の `JsonVal = Any` / `frozenset` / 未パラメータ化 `list` 起因の C++ surface を整理。`python3 src/pytra-cli.py -build src/toolchain/emit/go/cli.py --target cpp -o work/selfhost/emit/go/` で 40 cpp ファイルの emit を確認。
2. [x] [ID: P1-EMITTER-SELFHOST-GO-S2] 生成された C++ を `g++ -std=c++20 -O0` でコンパイルを通す（source 側の型注釈不整合を修正）
   - 2026-04-28: Go emitter の selfhost C++ 生成で崩れていた `JsonVal` 辞書/リスト、callable signature、try/error handling、内部 helper 名衝突を修正。`rm -rf work/selfhost/emit/go && python3 src/pytra-cli.py -build src/toolchain/emit/go/cli.py --target cpp -o work/selfhost/emit/go/` 後、`g++ -std=c++20 -O0 ... -o work/selfhost/emit/go/emitter_go_cpp` の link 成功を確認。
3. [x] [ID: P1-EMITTER-SELFHOST-GO-S3] コンパイル済み emitter で既存 fixture の manifest を処理し、Python 版 emitter と parity 一致を確認する
   - 2026-04-28: `work/tmp/build_add/linked/manifest.json` を Python 版 Go emitter と `work/selfhost/emit/go/emitter_go_cpp` の両方で処理し、`diff -ru work/selfhost/parity/go/python_cli work/selfhost/parity/go/compiled` の一致を確認。


### P7-GO-SELFHOST-RUNTIME: Go selfhost バイナリを実際に動かして parity PASS する

文脈: [docs/ja/plans/p7-go-selfhost-runtime.md](../plans/p7-go-selfhost-runtime.md)

P6 で go build は通ったが、selfhost バイナリが実際に fixture/sample/stdlib を変換して parity PASS するにはまだギャップがある。

1. [x] [ID: P7-GO-SELFHOST-RT-S1] linker の type_id 割り当てで外部ベースクラス（CommonRenderer(ABC) 等）の階層解決を修正する — object にフォールバックする
   - 2026-05-03: `src/toolchain/link/type_id.py` で import symbol / module alias 経由の外部 base FQCN が linked class set に無い場合は `object` にフォールバックするよう修正。`tools/unittest/toolchain2/test_linker_spec_conform2.py::test_type_id_external_imported_base_falls_back_to_object` を追加し、`CommonRenderer` 外部 base が `type_id_base_map[fqcn] == type_id_table["object"]` になることを固定。
2. [x] [ID: P7-GO-SELFHOST-RT-S2] Go emitter 自身の Go 翻訳を selfhost build seed に含める — `emit/go/` を selfhost バイナリへ含められるようにする
   - 2026-05-03: `tools/run/run_selfhost_parity.py` の Go selfhost build entry を `src/pytra-cli.py` から `src/toolchain/emit/go/cli.py` に切り替え、Go emitter 自身を Go 翻訳して selfhost バイナリへ入れる経路に変更。`tools/unittest/selfhost/test_run_selfhost_parity.py::test_build_selfhost_binary_go_uses_go_emitter_cli_entry` で `pytra-cli.py -build src/toolchain/emit/go/cli.py --target go` を使うことを固定。
3. [x] [ID: P7-GO-SELFHOST-RT-S3] CLI wrapper（Go emitter CLI の generated `main`）を追加する — EAST3 JSON を読んで Go コードを emit する最小エントリポイント
   - 2026-05-03: `src/toolchain/emit/go/cli.py` が `-emit MANIFEST_DIR -o OUT --target go` 互換、単体 EAST3 JSON 入力、runtime/go copy を処理するよう更新。`tools/unittest/toolchain2/test_go_emitter_cli_selfhost.py` で pytra-cli 互換引数、非 Go target reject、単体 EAST3 JSON から `app_main.go` を書く経路を固定。
4. [x] [ID: P7-GO-SELFHOST-RT-S4] `python3 tools/run/run_selfhost_parity.py --selfhost-lang go` を実行し、fixture parity PASS を確認する
   - 完了: 2026-05-03 に Docker 隔離環境（`pytra-devcontainer-check`、Python 3.12 + Go toolchain）で Go emitter selfhost binary を再生成し、`PYTHONPYCACHEPREFIX=work/tmp/pycache PYTHONPATH=src python3 tools/run/run_selfhost_parity.py --selfhost-lang go` が fixture 161/161 PASS。主な修正は `isinstance` narrowing、None 判定、constructor / runtime call 戻り型推論、typed list/set/dict literal、tuple call result wrapping、Path / deque / zip / sum / min / max / true division / `perf_counter` / math 関数の Go lowering。
5. [x] [ID: P7-GO-SELFHOST-RT-S5] Go selfhost sample artifact parity を 18/18 に揃える
   - 完了: 2026-05-03 に Docker 隔離環境（`pytra-devcontainer-check`）で Go selfhost binary を再生成し、`PYTHONPYCACHEPREFIX=work/tmp/pycache PYTHONPATH=src:tools/check python3 tools/run/run_selfhost_parity.py --selfhost-lang go --case-root sample --all-samples --cmd-timeout-sec 300` が sample 18/18 PASS。残っていた PNG/GIF artifact-size mismatch は、Go 1.19 互換の map clear 実装と、bytearray を第一引数で変更する helper（`_png_append` / `_gif_append` 形）を Go では戻り値で受ける emitter 修正により解消。
