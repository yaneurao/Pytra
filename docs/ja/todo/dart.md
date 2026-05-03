<a href="../../en/todo/dart.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Dart backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-29

## 運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## 参考資料

- Dart emitter: `src/toolchain/emit/dart/`
- TS emitter（参考実装）: `src/toolchain/emit/ts/`
- Dart runtime: `src/runtime/dart/`
- emitter 実装ガイドライン: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json 仕様: `docs/ja/spec/spec-runtime-mapping.md`

## 未完了タスク

### P0-DART-FIXTURE-PARITY-161: Dart fixture parity を 161/161 に揃える

文脈: [docs/ja/plans/p0-fixture-parity-161.md](../plans/p0-fixture-parity-161.md)

現状: 148/161 PASS。FAIL: `collections/reversed_basic`, `oop/trait_basic`, `oop/trait_with_inheritance`, `signature/ok_typed_varargs_representative`, `strings/str_methods_extended`, `typing/int8`, `typing/integer_promotion`, `typing/isinstance_pod_exact`, `typing/str_repr_containers`, `typing/union_return_errorcheck`。未実行: `control/for_tuple_iter`, `typing/for_over_return_value`, `typing/nullable_dict_field`。

1. [x] [ID: P0-FIX161-DART-S1] 未実行 3 件を `runtime_parity_check_fast.py --targets dart --case-root fixture` で確定し、fail なら分類へ追加する
2. [x] [ID: P0-FIX161-DART-S2] reversed / trait / typed varargs / string methods / int promotion / isinstance / union runtime の fail を解消し、Dart fixture parity 161/161 PASS を確認する


### P1-HOST-CPP-EMITTER-DART: C++ emitter を dart で host する

C++ emitter（`toolchain.emit.cpp.cli`、16 モジュール）を dart に変換し、変換された emitter が C++ コードを正しく生成できることを確認する。C++ emitter の source は selfhost-safe 化済み。

1. [x] [ID: P1-HOST-CPP-EMITTER-DART-S1] `python3 src/pytra-cli.py -build src/toolchain/emit/cpp/cli.py --target dart -o work/selfhost/host-cpp/dart/` で変換 + build を通す
   - 進捗: 2026-04-30 に `pytra-cli.py -build` の target wiring を修正し、`--target dart` が `toolchain.emit.dart.cli` へ到達するようにした。`rm -rf work/selfhost/host-cpp/dart && timeout 3600s python3 src/pytra-cli.py -build src/toolchain/emit/cpp/cli.py --target dart -o work/selfhost/host-cpp/dart/` は変換 PASS（25 files）。
   - 進捗: 2026-04-30 の `dart analyze work/selfhost/host-cpp/dart` は未 PASS。生成ファイルは flat 配置（例: `pytra_std_json.dart`）だが import は `./built_in/py_runtime.dart` / `./std/json.dart` / `./std/pathlib.dart` を参照しており、Dart runtime copy と module output path の整合が先。
   - 進捗: 2026-04-30 に `src/toolchain/emit/dart/cli.py` へ runtime copy を追加し、`built_in/py_runtime.dart` と `std/*.dart` の配置は進んだ。次の blocker は `std/json.dart` / `std/glob.dart` / `std/os.dart` wrapper 欠落と、`field(...)` / `cast(...)` / `dict[str,JsonVal]` など selfhost 向け Dart lowering の未対応。
   - 進捗: 2026-04-30 に Dart emitter が `_cli_module_id` を見るようにし、handwritten runtime 判定の repo root を修正。`pytra.std.pathlib` は生成せず `std/pathlib.dart` を使い、生成 runtime module は `pytra_std_*.dart` へ import する形に揃えた。`std/sys.dart` wrapper も追加済み。
   - 進捗: 2026-04-30 に `Node = dict[str, JsonVal]` 形式の type alias assign を skip、`cast(T, value)` を Dart `as` cast へ変換、dataclass の `field(default_factory=...)` を constructor body 初期化へ展開する対応を追加。`dart analyze` の blocker は import 解決（例: `toolchain_emit_cpp_cli.dart` の `run_emit_cli` / `sys`、`toolchain_emit_cpp_emitter.dart` の helper 群）と nullable 変換に移った。
   - 進捗: 2026-04-30 に selfhost 生成物の import path を flat 出力名（例: `toolchain_emit_common_cli_runner.dart`）へ揃え、`main_guard_body` も import scan 対象に含めた。`toolchain_emit_cpp_cli.dart` の `run_emit_cli` / runtime bundle / `sys.argv` 未解決は解消。次の blocker は nullable 戻り値・`__file__`/`Path.parents`・common renderer 継承/field 解決。
   - 進捗: 2026-04-30 に Python `dict[key]` 相当の Dart `Map` subscript へ non-null assertion を付け、`toolchain_emit_common_code_emitter.dart` の nullable return/assignment blocker を解消。次の先頭 blocker は `toolchain_emit_common_profile_loader.dart` の `__file__` / `Path.parents` と `toolchain_emit_cpp_emitter.dart` の Set 型・renderer 継承。
   - 進捗: 2026-04-30 に `__file__` を `_cli_source_path` 由来の Dart 文字列へ lower し、Dart runtime `Path.parents` を追加。`toolchain_emit_common_profile_loader.dart` の `__file__` / `Path.parents` blocker は解消。残り先頭は `String?` 引数 narrowing、Set 型 narrowing、common renderer 継承/field 解決。
   - 完了: 2026-04-30 に null 比較の条件式 narrowing、typed empty collection、generic Set runtime、dict key iteration、`cast(T, value)` の collection copy、CommonRenderer の public boundary normalization、chained comparison lowering を追加。`dart analyze work/selfhost/host-cpp/dart` は警告のみ、`dart work/selfhost/host-cpp/dart/toolchain_emit_cpp_cli.dart work/tmp/build_cli/linked/manifest.json --output-dir work/selfhost/host-cpp/dart-run` は exit 0 で 55 files を生成。
2. [x] [ID: P1-HOST-CPP-EMITTER-DART-S2] `python3 tools/run/run_emitter_host_parity.py --host-lang dart --hosted-emitter cpp --case-root fixture` で C++ emitter host parity PASS を確認する（結果は `.parity-results/emitter_host_dart.json` に自動書き込み）
   - 完了: 2026-04-30 に Python direct C++ emitter を同じ manifest から `work/selfhost/host-cpp/python-full` に再生成し、`diff -ru work/selfhost/host-cpp/python-full work/selfhost/host-cpp/dart-run` が一致。`.parity-results/emitter_host_dart.json` に build/parity PASS を記録。

### P1-EMITTER-SELFHOST-DART: emit/dart/cli.py を単独で selfhost C++ build に通す

文脈: [docs/ja/plans/p1-emitter-selfhost-per-backend.md](../plans/p1-emitter-selfhost-per-backend.md)

各 backend emitter は subprocess で独立起動する自己完結プログラム。pytra-cli.py 全体の selfhost とは切り離し、`toolchain.emit.dart.cli` をエントリに単独で C++ build を通す。

1. [x] [ID: P1-EMITTER-SELFHOST-DART-S1] `python3 src/pytra-cli.py -build src/toolchain/emit/dart/cli.py --target cpp -o work/selfhost/emit/dart/` を実行し、変換が通るようにする
   - 進捗: 2026-04-30 に `src/toolchain/emit/swift/emitter.py` の暗黙の隣接文字列結合を明示的な `+` 結合へ修正し、`error: build failed: expected ) but got "var __out: [Any] = []; "` は解消済み。
   - 進捗: 2026-04-30 に `rm -rf work/selfhost/emit/dart && timeout 3600s python3 src/pytra-cli.py -build src/toolchain/emit/dart/cli.py --target cpp -o work/selfhost/emit/dart/` を実行し、exit 124 で 1 時間 timeout。部分生成は 36 files / 13 `*.cpp`。
   - 完了: 2026-05-03 に Dart emitter が検査関数 1 個のために Swift emitter 全体を import していた依存を解消。Docker Python 3.12 で `rm -rf work/selfhost/emit/dart && timeout 3600s python3 src/pytra-cli.py -build src/toolchain/emit/dart/cli.py --target cpp -o work/selfhost/emit/dart/` は exit 0（parsed/resolved/compiled/optimized 4 files、linked 15 modules、emitted 23 files）。
2. [ ] [ID: P1-EMITTER-SELFHOST-DART-S2] 生成された C++ を `g++ -std=c++20 -O0` でコンパイルを通す（source 側の型注釈不整合を修正）
3. [ ] [ID: P1-EMITTER-SELFHOST-DART-S3] コンパイル済み emitter で既存 fixture の manifest を処理し、Python 版 emitter と parity 一致を確認する
