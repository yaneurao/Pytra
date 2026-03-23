# `tools/` スクリプト一覧

<a href="../../en/spec/spec-tools.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>


`tools/` は、Pytra の開発運用を自動化するための補助スクリプト群です。  
目的は次の 3 つです。

- 回帰確認を短時間で繰り返せるようにする。
- selfhost の調査・比較・ビルドを定型化する。
- `src/pytra/` 正本から C++ ランタイム生成物を更新・検証する。

## 1. 日常運用で使うもの

- `tools/run_local_ci.py`
  - 目的: ローカル最小 CI（version gate + todo 優先度ガード + runtime 層分離ガード + non-C++ emitter runtime-call 直書きガード + emitter 禁止 runtime 実装シンボルガード + non-C++ backend health gate + 条件付き sample 再生成 + transpile 回帰 + unit + selfhost build + diff）を一括実行する。
- `tools/check_todo_priority.py`
  - 目的: `docs/ja/todo/index.md` / `docs/ja/plans/*.md` の差分に追加した進捗 `ID` が、未完了の最上位 `ID`（またはその子 `ID`）と一致するかを検証し、優先度逸脱を防止する。`plans` 側は `決定ログ`（`- YYYY-MM-DD: ...`）行のみを進捗判定対象にし、構造整理の ID 列挙は対象外とする。
- `tools/check_jsonvalue_decode_boundaries.py`
  - 目的: `pytra-cli.py` / `east2x.py` / `toolchain/compile/east_io.py` / `toolchain/link/*` の JSON artifact 境界で `json.loads_obj(...)` が正本であることを検証し、raw `json.loads(...)` への再侵入を fail-fast に止める。
- `tools/check_runtime_cpp_layout.py`
  - 目的: `src/runtime/cpp/{built_in,std,utils}` の legacy-closed 維持、`generated/native/pytra` の ownership 境界、`core` compatibility surface と `generated/core` / `native/core` の split 前提を同一 guard で検証する。あわせて `generated/core` / `native/core` lane の存在を要求し、`runtime/cpp/native/core/...` の直接 include を `core/*.h` forwarder 以外で禁止する。
  - 補足: `generated/built_in` / `generated/core` は plain naming と generated marker を必須とし、`native` / `core` への ownership 混在を fail させる。加えて `native/core/py_runtime.h` に `predicates` / `sequence` / `iter_ops` の removed transitive include が再侵入した場合も fail とする。
- `tools/check_py2cpp_transpile.py`
  - 目的: `test/fixtures/` を `pytra-cli.py --target cpp` で一括変換し、失敗ケースを検出する。
  - 主要オプション: `--check-yanesdk-smoke`（Yanesdk の縮小ケースを同時確認）
- `tools/check_py2rs_transpile.py`
  - 目的: `test/fixtures/` と `sample/py` を `pytra-cli.py --target rs` で一括変換し、失敗ケースを検出する。
- `tools/check_py2js_transpile.py`
  - 目的: `test/fixtures/` と `sample/py` を `pytra-cli.py --target js` で一括変換し、失敗ケースを検出する。
- `tools/check_py2cs_transpile.py`
  - 目的: `test/fixtures/` と `sample/py` を `pytra-cli.py --target cs` で一括変換し、失敗ケースを検出する。
- `tools/check_py2go_transpile.py`
  - 目的: `test/fixtures/` と `sample/py` を `pytra-cli.py --target go` で一括変換し、失敗ケースを検出する。
- `tools/check_py2java_transpile.py`
  - 目的: `test/fixtures/` と `sample/py` を `pytra-cli.py --target java` で一括変換し、失敗ケースを検出する。
- `tools/check_py2ts_transpile.py`
  - 目的: `test/fixtures/` と `sample/py` を `pytra-cli.py --target ts` で一括変換し、失敗ケースを検出する。
- `tools/check_py2swift_transpile.py`
  - 目的: `test/fixtures/` と `sample/py` を `pytra-cli.py --target swift` で一括変換し、失敗ケースを検出する。
- `tools/check_py2kotlin_transpile.py`
  - 目的: `test/fixtures/` と `sample/py` を `pytra-cli.py --target kotlin` で一括変換し、失敗ケースを検出する。
- `tools/check_py2scala_transpile.py`
  - 目的: `test/fixtures/` と `sample/py` を `pytra-cli.py --target scala` で一括変換し、失敗ケースを検出する。
- `tools/check_yanesdk_py2cpp_smoke.py`
  - 目的: Yanesdk canonical 対象（`library 1本 + game 7本`）が `pytra-cli.py --target cpp` を通るか確認する。
- `tools/check_microgpt_original_py2cpp_regression.py`
  - 目的: 原本 `materials/refs/microgpt/microgpt-20260222.py` を固定入力にし、`py2cpp` の失敗ステージ（A〜F）または成功を検査して再発を検知する。
- `tools/build_multi_cpp.py`
  - 目的: `pytra-cli.py --target cpp --multi-file` が出力した `manifest.json` を読み、関連 `*.cpp` と runtime をまとめてビルドする。
- `tools/gen_makefile_from_manifest.py`
  - 目的: `manifest.json` を受け取り、`all`, `run`, `clean` を含む `Makefile` を生成する。
- `tools/verify_multi_file_outputs.py`
  - 目的: `sample/py` の multi-file 出力をビルド・実行し、単一ファイル出力との実行結果一致を確認する。
- `tools/check_transpiler_version_gate.py`
  - 目的: 変換器関連ファイルが変更されたとき、`src/toolchain/misc/transpiler_versions.json` の対応コンポーネント（`shared` / 言語別）で minor 以上のバージョン更新が行われているかを検証する。
- `tools/regenerate_samples.py`
  - 目的: `sample/py` から各 `sample/<lang>` を再生成し、`src/toolchain/misc/transpiler_versions.json` のバージョン・トークンが変わらない限り再生成を skip する。
  - 主要オプション: `--verify-cpp-on-diff`（C++ 生成差分が出たケースだけ `runtime_parity_check.py --targets cpp` で compile/run 検証）
- `tools/run_regen_on_version_bump.py`
  - 目的: `transpiler_versions.json` の minor 以上の更新を検出したときだけ `regenerate_samples.py` を起動し、影響言語のみ再生成する。
- `tools/sync_todo_history_translation.py`
  - 目的: `docs/ja/todo/archive` を正本として `docs/en/todo/archive` の日付ファイル雛形と index を同期し、`--check` で同期漏れを検出する。
- `tools/check_east3_golden.py`
  - 目的: EAST3 スナップショットテスト（`test/east3_fixtures/` の golden file と EAST3 出力の差分チェック）。`--check-runtime-east` で `src/runtime/east/` の `.east` ファイル鮮度チェック。`--update` で再生成。
- `tools/verify_image_runtime_parity.py`
  - 目的: 画像ランタイム（PNG/GIF）の Python 正本と C++ 側の一致を確認する。
- `tools/check_runtime_std_sot_guard.py`
  - 目的: `src/pytra/std/*.py` / `src/pytra/utils/*.py` を正本とする運用を検査し、`rs/cs` では `src/runtime/{rs,cs}/generated/**` を canonical generated lane として監査しつつ、legacy `pytra-gen` lane への手書き実装再流入（現行ガード対象: `json/assertions/re/typing`）を fail させる。あわせて C++ `std/utils` 全体の責務境界（`generated/native` ownership + required manual impl split）も検証する。
- `tools/check_runtime_core_gen_markers.py`
  - 目的: `rs/cs` では `src/runtime/<lang>/generated/**` を canonical generated lane として `source/generated-by` marker を強制し、legacy `pytra-gen/pytra-core` は未移行 backend 向けの scan target としてのみ扱う。加えて C++ では `src/runtime/cpp/generated/core/**` の marker 必須、`src/runtime/cpp/native/core/**` の marker 禁止と legacy `src/runtime/cpp/core/**` 再出現時の marker 混入も監査する（`tools/runtime_core_gen_markers_allowlist.txt` 基準）。
  - 補足: C++ `generated/built_in` / `generated/std` / `generated/utils` も同じ marker 契約で監査し、`generated/core` を low-level pure helper lane として扱う前提を壊す増分を止める。
- `tools/check_runtime_pytra_gen_naming.py`
  - 目的: canonical generated lane（`rs/cs` は `src/runtime/<lang>/generated/**`、未移行 backend は `pytra-gen/**`）の `std|utils` 配置と素通し命名（`<module>.py -> <module>.<ext>`）を検査し、`image_runtime.*` / `runtime/*.php` などの命名・配置違反増分を fail させる（`tools/runtime_pytra_gen_naming_allowlist.txt` 基準）。
- `tools/check_emitter_runtimecall_guardrails.py`
  - 目的: non-C++ emitter の `if/elif` 文字列分岐における runtime/stdlib 関数名直書きの増分を検知し、allowlist 外を fail させる（`tools/emitter_runtimecall_guardrails_allowlist.txt` 基準）。
- `tools/check_emitter_forbidden_runtime_symbols.py`
  - 目的: `src/toolchain/emit/*/emitter/*.py` における禁止 runtime 実装シンボル（`__pytra_write_rgb_png` / `__pytra_save_gif` / `__pytra_grayscale_palette`）の混入増分を検知し、allowlist 外を fail させる（`tools/emitter_forbidden_runtime_symbols_allowlist.txt` 基準）。

### 1.1 Emitter 変更 Stop-Ship チェックリスト（必須）

- 対象: `src/toolchain/emit/*/emitter/*.py` を変更したコミット。
- コミット前に次の 3 コマンドを必ず実行する。
  - `python3 tools/check_emitter_runtimecall_guardrails.py`
  - `python3 tools/check_emitter_forbidden_runtime_symbols.py`
  - `python3 tools/check_noncpp_east3_contract.py`
- 3 コマンドのいずれかが `FAIL` の場合は Stop-Ship 扱いとし、コミット/プッシュ/レビュー依頼を禁止する。
- レビュー時は次の 3 項目を checklist として確認する。
  - [ ] 上記 3 コマンドの実行ログがある。
  - [ ] `src/toolchain/emit/*/emitter/*.py` に禁止 runtime 実装シンボルの増分がない。
  - [ ] runtime/stdlib 呼び出し解決が EAST3 正本（`runtime_call` / `resolved_runtime_call` / `resolved_runtime_source`）のみを利用している。

## 2. selfhost 関連

- `tools/build_selfhost.py`
  - 目的: selfhost 用 `selfhost/py2cpp.out` を生成する（生成 C++ への手動 main パッチなし）。
- `tools/build_selfhost_stage2.py`
  - 目的: `selfhost/py2cpp.out` で `selfhost/py2cpp.py` を再変換し、2段自己変換バイナリ `selfhost/py2cpp_stage2.out` を生成する。
- `tools/prepare_selfhost_source.py`
  - 目的: `CodeEmitter` などを selfhost 用ソースへ展開し、自己完結化する。
- `tools/selfhost_transpile.py`
  - 目的: 暫定ブリッジとして `.py -> EAST JSON -> selfhost` 経路を実行する。
- `tools/check_selfhost_cpp_diff.py`
  - 目的: Python 版と selfhost 版の生成 C++ 差分を比較する。
  - 主要オプション: `--mode strict`, `--show-diff`, `--selfhost-driver`
- `tools/check_selfhost_direct_compile.py`
  - 目的: selfhost の `.py` 直入力経路を `sample/py` で一括変換し、`g++ -fsyntax-only` でコンパイル回帰を即時検出する。
- `tools/check_selfhost_stage2_cpp_diff.py`
  - 目的: Python 版と 2段自己変換版（`selfhost/py2cpp_stage2.out`）の生成 C++ 差分を比較する。
  - 主要オプション: `--skip-build`, `--mode strict`, `--show-diff`
- `tools/check_selfhost_stage2_sample_parity.py`
  - 目的: `selfhost/py2cpp_stage2.out` を使って `sample/py/*.py` 全件の transpile + compile + run parity を確認する。

補足:
- 2026-03-08 時点で C++ selfhost の stage1 build、direct `.py` route、representative host/selfhost diff、stage2 build は current runtime/layout 契約で green である。
- 2026-03-09 時点で `tools/check_selfhost_stage2_sample_parity.py --skip-build` により stage2 selfhost binary の full sample parity（`pass=18 fail=0`）も green である。
- `tools/selfhost_transpile.py` は direct `.py` route の代替ではなく、調査時の fallback としてだけ扱う。
- `tools/summarize_selfhost_errors.py`
  - 目的: selfhost ビルドログのエラーをカテゴリ別に集計する。
- `tools/selfhost_error_hotspots.py`
  - 目的: エラー集中箇所を関数単位で集約する。
- `tools/selfhost_error_report.py`
  - 目的: selfhost エラー解析結果のレポートを整形出力する。

### 2.1 selfhost 暴走ガード（実装済み）

selfhost の調査時に、深い再帰・巨大構文木・シンボル爆発で実行が長時間化するケースを早期停止できるよう、以下のガードを `pytra-cli.py --target cpp` / 共通 CLI へ段階導入する。

- `--guard-profile {off,default,strict}`
  - 既定は `default`。`off` は制限無効、`strict` は調査向けに低い上限を適用する。
  - `default` の既定値:
    - `max-ast-depth=800`
    - `max-parse-nodes=2000000`
    - `max-symbols-per-module=200000`
    - `max-scope-depth=400`
    - `max-import-graph-nodes=5000`
    - `max-import-graph-edges=20000`
    - `max-generated-lines=2000000`
  - `strict` の既定値:
    - `max-ast-depth=200`
    - `max-parse-nodes=200000`
    - `max-symbols-per-module=20000`
    - `max-scope-depth=120`
    - `max-import-graph-nodes=1000`
    - `max-import-graph-edges=4000`
    - `max-generated-lines=300000`
- 個別上限オプション（`guard_profile` より優先）
  - `--max-ast-depth`
  - `--max-parse-nodes`
  - `--max-symbols-per-module`
  - `--max-scope-depth`
  - `--max-import-graph-nodes`
  - `--max-import-graph-edges`
  - `--max-generated-lines`

失敗契約:

- いずれかの上限超過時は、`input_invalid(kind=limit_exceeded, stage=<parse|analyze|emit>, limit=<name>, value=<n>)` 形式で fail-fast する。
- `tools/build_selfhost.py` など selfhost 実行系ツールは、必要に応じて `--timeout-sec` 併用でプロセス時間上限を設定できるようにする。

## 3. 言語間確認
- `tools/runtime_parity_check.py`
  - 目的: 複数ターゲット言語でのランタイム平準化チェックを実行する。
  - 補足: `elapsed_sec` / `elapsed` / `time_sec` のような不安定な時間行は、既定で比較対象から除外する。
  - 補足: artifact 比較は `output:` で報告された生成物に対して `存在 + size + CRC32` を必須一致条件とする。
  - 補足: ケース実行前に `sample/out`, `test/out`, `out` の同名 artifact を削除し、前回実行物の取り違えを防止する。
  - 補足: timeout 時は process-group 単位で kill し、`*_swift.out` などの子プロセス孤立を許容しない。
- `tools/check_all_target_sample_parity.py`
  - 目的: canonical parity group（`cpp`, `js_ts`, `compiled`, `scripting_mixed`）を順に実行し、全 target sample parity を確定する。
  - 主要オプション: `--groups`, `--east3-opt-level`, `--cpp-codegen-opt`, `--summary-dir`
- `tools/check_noncpp_backend_health.py`
  - 目的: linked-program 後の non-C++ backend health gate を family 単位で集約し、`primary_failure` / `toolchain_missing` / family の broken/green を 1 コマンドで確認する。
  - 主要オプション: `--family`, `--targets`, `--skip-parity`, `--summary-json`
- `tools/check_noncpp_runtime_generated_cpp_baseline_contract.py`
  - 目的: `cpp/generated/{built_in,std,utils}` 由来の 25-module baseline と、legacy rollout inventory / active runtime policy wording の同期を検証する。
- `tools/export_backend_test_matrix.py`
  - 目的: `test/unit/toolchain/emit/**` と shared starred smoke を実行し、JA/EN の backend test matrix docs を再生成する。
- `tools/check_scala_parity.py`
  - 目的: Scala3 向けに `sample` 全件 + fixture 正例マニフェストの parity を一括実行し、再実行導線を固定する。
  - 主要オプション: `--skip-fixture`, `--fixture-manifest`, `--east3-opt-level`, `--summary-dir`

### 3.1 smoke テスト運用（`py2x` 共通化後）

- 共通 smoke（CLI 成功、`--east-stage 2` 拒否、`load_east`、add fixture）は `test/unit/common/test_py2x_smoke_common.py` を正本とする。
- 言語別 smoke（`test/unit/toolchain/emit/<lang>/test_py2*_smoke.py`）は言語固有の emitter/runtime 契約だけを保持し、共通ケースを再実装しない。
- 各言語 smoke には責務境界コメント（`Language-specific smoke suite...`）を必須とし、`tools/check_noncpp_east3_contract.py` で静的検証する。
- smoke 実行時の `PYTHONPATH` は `src:.:test/unit` を正本とする。`comment_fidelity.py` など `test/unit` 直下 helper を読む smoke suite があるため、`test/unit` を落として実行してはならない。
- 回帰の推奨順は次の 3 本:
- `PYTHONPATH=src:.:test/unit python3 -m unittest discover -s test/unit/common -p 'test_py2x_smoke*.py'`
- `python3 tools/check_noncpp_east3_contract.py --skip-transpile`
- `python3 tools/check_py2<lang>_transpile.py`（対象言語分）

### 3.2 non-C++ backend health matrix（linked-program 後）

- non-C++ backend の recovery baseline は `static_contract -> common_smoke -> target_smoke -> transpile -> parity` の順で評価する。
- `parity` は前段 gate をすべて通した target にだけ実行する。前段 failure がある target を parity failure として集計してはならない。
- `toolchain_missing` は `runtime_parity_check.py` の skip をそのまま infra baseline として保持し、`parity_fail` と分離して扱う。
- 2026-03-08 snapshot では Wave 1 は `js/ts` が green、`rs/cs` が `toolchain_missing`、Wave 2 の `go/java/kotlin/swift/scala` と Wave 3 の `ruby/lua/php/nim` も sample parity 18 case 全件 `toolchain_missing` とする。
- 日常の family 単位 health check は `python3 tools/check_noncpp_backend_health.py --family wave1` のように実行し、family status は `broken_targets == 0` なら `green` とする。`toolchain_missing` は family を壊さず、別カウンタで表示する。
- `tools/run_local_ci.py` は `python3 tools/check_noncpp_backend_health.py --family all --skip-parity` を含み、parity 非依存の smoke/transpile gate を日常回帰へ常設する。
- `tools/run_local_ci.py` は `python3 tools/check_jsonvalue_decode_boundaries.py` も含み、selfhost/host の JSON artifact 境界が raw `json.loads(...)` へ戻る増分を local CI で止める。

### 3.3 全target sample parity 完了条件

- canonical parity target order は `cpp,rs,cs,js,ruby,lua,php,ts,go,java,swift,kotlin,scala,nim` とする。これは `list_parity_targets()` の返却順と一致させる。
- 「全target parity green」は `python3 tools/runtime_parity_check.py --targets cpp,rs,cs,js,ruby,lua,php,ts,go,java,swift,kotlin,scala,nim --case-root sample --all-samples --ignore-unstable-stdout --east3-opt-level 2 --cpp-codegen-opt 3` 実行時に、全 target / 全 18 sample case が `ok` のみで完了する状態を指す。
- full green 判定では `toolchain_missing` を例外扱いしない。`case_missing`, `python_failed`, `python_artifact_missing`, `toolchain_missing`, `transpile_failed`, `run_failed`, `output_mismatch`, `artifact_presence_mismatch`, `artifact_missing`, `artifact_size_mismatch`, `artifact_crc32_mismatch` はすべて 0 件でなければならない。
- target 群を分けて確認する場合も、基準は同じとする。
  - baseline target: `python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples --east3-opt-level 2 --cpp-codegen-opt 3`
  - JS/TS: `python3 tools/runtime_parity_check.py --targets js,ts --case-root sample --all-samples --ignore-unstable-stdout --east3-opt-level 2`
  - compiled target: `python3 tools/runtime_parity_check.py --targets rs,cs,go,java,kotlin,swift,scala --case-root sample --all-samples --ignore-unstable-stdout --east3-opt-level 2`
  - scripting / mixed target: `python3 tools/runtime_parity_check.py --targets ruby,lua,php,nim --case-root sample --all-samples --ignore-unstable-stdout --east3-opt-level 2`
- 日常の full-target 再実行は `python3 tools/check_all_target_sample_parity.py --summary-dir work/logs/all_target_sample_parity` を canonical wrapper とする。wrapper は上記 4 group を順に実行し、`all-target-summary.json` に統合結果を書き出す。

### 3.4 Debian 12 parity bootstrap snapshot

- 2026-03-08 時点の current machine は Debian 12 (`bookworm`) / `root` 前提で bootstrap を実施した。
- compiled target の bootstrap command:
  - `apt-get update`
  - `apt-get install -y rustc mono-mcs golang-go openjdk-17-jdk kotlin scala nim`
  - `apt-get install -y binutils-gold gcc git libcurl4-openssl-dev libedit-dev libpython3-dev libsqlite3-dev uuid-dev gnupg2`
  - `curl -fL -o /opt/swift-6.2.2-RELEASE-debian12.tar.gz https://download.swift.org/swift-6.2.2-release/debian12/swift-6.2.2-RELEASE/swift-6.2.2-RELEASE-debian12.tar.gz`
  - `tar -xf /opt/swift-6.2.2-RELEASE-debian12.tar.gz -C /opt`
  - `ln -sfn /opt/swift-6.2.2-RELEASE-debian12/usr/bin/swift /usr/local/bin/swift`
  - `ln -sfn /opt/swift-6.2.2-RELEASE-debian12/usr/bin/swiftc /usr/local/bin/swiftc`
- scripting / mixed target の bootstrap command:
  - `apt-get install -y ruby lua5.4 php-cli`
- bootstrap 後の `runner_needs` 実測では `cpp,rs,cs,js,ruby,lua,php,ts,go,java,swift,kotlin,scala,nim` がすべて `OK` になっていることを確認済みとする。

## 4. 更新ルール

- `tools/` に新しいスクリプトを追加した場合は、この `docs/ja/spec/spec-tools.md` を同時に更新します。
- スクリプトの目的は「何を自動化するために存在するか」を 1 行で明記します。
- 破壊的変更（引数仕様の変更、廃止、統合）がある場合は、`docs/ja/tutorial/how-to-use.md` の関連コマンド例も同期更新します。
- sample 再生成は「変換器ソース差分」ではなく `src/toolchain/misc/transpiler_versions.json` の minor 以上の更新をトリガーにします。
- 変換器関連ファイル（`src/py2*.py`, `src/pytra/**`, `src/toolchain/emit/**`, `src/toolchain/emit/**/profiles/**`）を変更したコミットでは、`tools/check_transpiler_version_gate.py` を通過させる必要があります。
- バージョン更新で sample 再生成したときは、`tools/run_regen_on_version_bump.py --verify-cpp-on-diff` を使い、生成差分が出た C++ ケースを compile/run 検証します。
- ツールチェイン互換用の shim は `tools/shims/` 配下に配置し、ルート直下へ `.chain` のような専用ディレクトリを新設しません。
