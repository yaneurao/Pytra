<a href="../../en/todo/nim.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Nim backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-27

## 運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## 参考資料

- Nim emitter: `src/toolchain/emit/nim/`
- TS emitter（参考実装）: `src/toolchain/emit/ts/`
- Nim runtime: `src/runtime/nim/`
- emitter 実装ガイドライン: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json 仕様: `docs/ja/spec/spec-runtime-mapping.md`

## 未完了タスク

### P0-NIM-FIXTURE-PARITY-161: Nim fixture parity を 161/161 に揃える

文脈: [docs/ja/plans/p0-fixture-parity-161.md](../plans/p0-fixture-parity-161.md)

現状: 142/161 PASS。FAIL: `collections/list_repeat`, `collections/nested_types`, `collections/reversed_basic`, `collections/sorted_basic`, `oop/trait_basic`, `oop/trait_with_inheritance`, `signature/ok_typed_varargs_representative`, `strings/str_methods_extended`, `typing/isinstance_chain_narrowing`, `typing/isinstance_union_narrowing`, `typing/object_container_access`, `typing/tuple_unpack_variants`, `typing/type_alias_pep695`, `typing/typed_container_access`, `typing/union_basic`, `typing/union_list_mixed`。未実行: `control/for_tuple_iter`, `typing/for_over_return_value`, `typing/nullable_dict_field`。

1. [x] [ID: P0-FIX161-NIM-S1] 未実行 3 件を `runtime_parity_check_fast.py --targets nim --case-root fixture` で確定し、fail なら分類へ追加する
2. [x] [ID: P0-FIX161-NIM-S2] collection / trait / typed varargs / string methods / isinstance / union / tuple / typed container の fail を解消し、Nim fixture parity 161/161 PASS を確認する


### P1-HOST-CPP-EMITTER-NIM: C++ emitter を nim で host する

C++ emitter（`toolchain.emit.cpp.cli`、16 モジュール）を nim に変換し、変換された emitter が C++ コードを正しく生成できることを確認する。C++ emitter の source は selfhost-safe 化済み。

1. [ ] [ID: P1-HOST-CPP-EMITTER-NIM-S1] `python3 src/pytra-cli.py -build src/toolchain/emit/cpp/cli.py --target nim -o work/selfhost/host-cpp/nim/` で変換 + build を通す
   - 2026-04-28: host C++ emitter の Nim emit は `python3 src/pytra-cli.py -build src/toolchain/emit/cpp/cli.py --target nim -o work/selfhost/host-cpp/nim/` で 20 ファイル生成まで到達。`nim c --out:work/selfhost/host-cpp/nim/emitter_cpp_nim work/selfhost/host-cpp/nim/toolchain_emit_cpp_cli.nim` は dataclass constructor ordering / keyword args / `SystemExit` / `Path.read_text(encoding=...)` を修正後、`json.loads(...).raw` が `JsonNode` のまま `PyObj` に入らない箇所で停止中。
2. [ ] [ID: P1-HOST-CPP-EMITTER-NIM-S2] nim 版 C++ emitter で fixture manifest を処理し、Python 版 emitter と parity 一致を確認する

### P1-EMITTER-SELFHOST-NIM: emit/nim/cli.py を単独で selfhost C++ build に通す

文脈: [docs/ja/plans/p1-emitter-selfhost-per-backend.md](../plans/p1-emitter-selfhost-per-backend.md)

各 backend emitter は subprocess で独立起動する自己完結プログラム。pytra-cli.py 全体の selfhost とは切り離し、`toolchain.emit.nim.cli` をエントリに単独で C++ build を通す。

1. [x] [ID: P1-EMITTER-SELFHOST-NIM-S1] `python3 src/pytra-cli.py -build src/toolchain/emit/nim/cli.py --target cpp -o work/selfhost/emit/nim/` を実行し、変換が通るようにする
   - 2026-04-16: nim/types.py の `_NIM_NORMALIZED_RESERVED` 末尾エントリの inline comment を literal 外へ移動（parser の `_join_continuation_lines` が joined 行内の `#` 以降を stripping して closing `}` が失われる問題を回避）。nim/cli.py を自己完結化し、typing.Callable を含む cli_runner.py に依存しないよう parse/load/module_id ロジックをインライン化。11 cpp ファイルの emit が通った。
2. [x] [ID: P1-EMITTER-SELFHOST-NIM-S2] 生成された C++ を `g++ -std=c++20 -O0` でコンパイルを通す(source 側の型注釈不整合を修正)
   - 2026-04-28: `python3 src/pytra-cli.py -build src/toolchain/emit/nim/cli.py --target cpp -o work/selfhost/emit/nim/` 後、生成 C++ と C++ runtime を `g++ -std=c++20 -O0` でリンクし、`work/selfhost/emit/nim/emitter_nim_cpp` 生成まで確認。
3. [x] [ID: P1-EMITTER-SELFHOST-NIM-S3] コンパイル済み emitter で既存 fixture の manifest を処理し、Python 版 emitter と parity 一致を確認する
   - 2026-04-28: `test/fixture/source/py/core/add.py` から生成した `work/tmp/build_add/linked/manifest.json` を対象に、`PYTHONPATH=src python3 -m toolchain.emit.nim.cli ...` と `work/selfhost/emit/nim/emitter_nim_cpp ...` の出力を `diff -ru work/selfhost/parity/nim/python_cli work/selfhost/parity/nim/compiled` で比較し一致を確認。


### P20-NIM-SELFHOST: Nim emitter で toolchain2 を Nim に変換し実行できるようにする

1. [ ] [ID: P20-NIM-SELFHOST-S0] selfhost 対象コードの型注釈補完（他言語と共通）
2. [ ] [ID: P20-NIM-SELFHOST-S1] toolchain2 全 .py を Nim に emit し、compile + 実行できることを確認する
   - 2026-04-16: `pytra-cli -build src/toolchain/emit/nim/cli.py --target nim` 経路を修復。進捗:
     - `_emit_nim` を subprocess 委譲 + runtime copy（`_copy_nim_runtime_files`）に変更（`_emit_go` 等と同形）
     - 出力 flat directory に合わせ、emitter の import を slash → underscore に変更（`pytra.` prefix 除去も廃止）
     - function パラメータが body で再代入されるケースに shadow `var x = x` 挿入を追加
     - py_runtime.nim に runtime 補強を追加: `py_str_strip(s, chars)`, `py_str_lstrip/rstrip(s, chars)`, `py_str_split(s, sep, maxsplit)`, `py_str_startswith/endswith(s, tuple)`, `contains(tuple, string)` 
     - union 型の `iterator items*` 重複衝突を解消（dict オプション側の items は list オプションが共存するとき skip）
   - 残 blocker (compile がまだ通らない): 同じ options 集合を持つ union type が複数名で生成され、dict converter → `[](union, key)` の呼び出しが曖昧になる（`PyUnion_void_bool_..._dict_string_PyObj` と `PyUnion_bool_..._void` 等）。union 名の正規化（options の順序安定化か、options 集合 hash 化）が必要。これは nim/emitter.py の PyUnion 名生成側または、より上流の resolve/linker 層の union 正規化に関わる。追加の設計判断が要るため pause。
3. [ ] [ID: P20-NIM-SELFHOST-S2] selfhost 用 Nim golden を配置する
4. [ ] [ID: P20-NIM-SELFHOST-S3] `run_selfhost_parity.py --selfhost-lang nim --emit-target nim --case-root fixture` で fixture parity PASS
5. [ ] [ID: P20-NIM-SELFHOST-S4] `run_selfhost_parity.py --selfhost-lang nim --emit-target nim --case-root sample` で sample parity PASS
