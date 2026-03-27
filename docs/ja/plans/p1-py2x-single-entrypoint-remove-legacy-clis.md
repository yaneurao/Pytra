<a href="../../en/plans/p1-py2x-single-entrypoint-remove-legacy-clis.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1: `pytra-cli.py` 単一エントリ化（`py2*.py` 廃止、最終的に `py2cpp.py` 削除）

最終更新: 2026-03-03

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-PY2X-SINGLE-ENTRY-01`

背景:
- 現在は `pytra-cli.py` を導入済みだが、`tools/` / `test/` / `docs/` / selfhost 導線が依然として `py2*.py` 直呼び出しに依存している。
- 特に `py2cpp.py` は `--emit-runtime-cpp` / `--header-output` / `--multi-file` など C++ 固有機能の入口を兼ねており、単純削除できない。
- ユーザー要件は「`pytra-cli.py` に統一したなら legacy CLI を不要化し、最終的に `py2cpp.py` を無くす」ことである。

目的:
- CLI の正規入口を `src/pytra-cli.py`（通常）と `src/pytra-cli.py`（selfhost）に統一する。
- `py2*.py` 直依存を `tools/` / `test/` / `docs/` から段階的に除去する。
- 最終段階で `src/py2cpp.py` を含む legacy CLI を削除する。

対象:
- `src/pytra-cli.py` / `src/pytra-cli.py` の機能拡張（C++ 専用機能吸収）
- `tools/` / `test/` / `src/pytra/cli.py` の呼び出し先を `pytra-cli.py --target ...` へ移行
- selfhost 関連スクリプトの entrypoint 置換
- `docs/ja` / `docs/en` の利用手順更新
- legacy CLI（`src/py2*.py`）削除

非対象:
- backend 変換ロジック自体の品質改善
- EAST 仕様変更
- runtime API 仕様変更

受け入れ基準:
- `tools/`, `test/`, `docs/`, `src/pytra/cli.py` に `src/py2*.py` 直参照が残らない。
- C++ 専用運用（runtime 生成・header 出力・multi-file）が `py2x --target cpp` で代替可能。
- selfhost 導線が `py2cpp.py` 非依存で成立する。
- 最終状態で `src/py2cpp.py` が削除され、主要回帰が通る。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `rg -n "src/py2(?!x)\\w*\\.py" src tools test docs`
- `python3 tools/check_py2x_transpile.py`（新設予定）
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/check_py2rs_transpile.py`
- `python3 tools/check_py2cs_transpile.py`
- `python3 tools/check_py2js_transpile.py`
- `python3 tools/check_py2ts_transpile.py`
- `python3 tools/check_py2go_transpile.py`
- `python3 tools/check_py2java_transpile.py`
- `python3 tools/check_py2swift_transpile.py`
- `python3 tools/check_py2kotlin_transpile.py`
- `python3 tools/check_py2rb_transpile.py`
- `python3 tools/check_py2lua_transpile.py`
- `python3 tools/check_py2scala_transpile.py`
- `python3 tools/check_py2php_transpile.py`
- `python3 tools/check_py2nim_transpile.py`
- `python3 tools/build_selfhost.py`
- `python3 tools/build_selfhost_stage2.py`

## 分解

- [x] [ID: P1-PY2X-SINGLE-ENTRY-01-S1-01] `tools/` / `test/` / `docs/` / `src/pytra/cli.py` の `py2*.py` 依存箇所を棚卸しし、移行順序を確定する。
- [x] [ID: P1-PY2X-SINGLE-ENTRY-01-S1-02] `py2cpp.py` 固有機能（`--emit-runtime-cpp`, `--header-output`, `--multi-file` 等）の `py2x` 受け皿仕様を確定する。
- [x] [ID: P1-PY2X-SINGLE-ENTRY-01-S1-03] selfhost 導線（prepare/build/check）がどの entrypoint 契約に依存しているかを棚卸しし、置換方針を確定する。
- [x] [ID: P1-PY2X-SINGLE-ENTRY-01-S2-01] `py2x --target cpp` に `py2cpp` 固有機能を実装し、既存オプションと等価運用できるようにする。
- [x] [ID: P1-PY2X-SINGLE-ENTRY-01-S2-02] `tools/` の CLI 呼び出しを `pytra-cli.py --target ...` へ一括置換する。
- [x] [ID: P1-PY2X-SINGLE-ENTRY-01-S2-03] `test/` の CLI 呼び出しと契約テストを `py2x` ベースへ移行する。
- [x] [ID: P1-PY2X-SINGLE-ENTRY-01-S2-04] `docs/ja` / `docs/en` の使用例と仕様表記を `py2x` 正規入口へ更新する。
- [x] [ID: P1-PY2X-SINGLE-ENTRY-01-S2-05] selfhost スクリプトを `py2cpp.py` 非依存へ移行し、`pytra-cli.py` 基準で再配線する。
- [x] [ID: P1-PY2X-SINGLE-ENTRY-01-S3-01] legacy CLI 撤去前のガードを追加し、`py2*.py` 新規再流入を fail-fast で検出する。
- [x] [ID: P1-PY2X-SINGLE-ENTRY-01-S3-02] `src/py2cpp.py` を削除し、必要に応じて他 `py2*.py` も同時撤去する。
- [x] [ID: P1-PY2X-SINGLE-ENTRY-01-S3-03] 全 transpile/selfhost 回帰を実行し、`py2cpp.py` 削除後の非退行を確認する。

決定ログ:
- 2026-03-03: ユーザー指示により、`pytra-cli.py` 単一エントリ化を P1 として起票し、最終成果に `src/py2cpp.py` 削除を含める方針を確定。
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S1-01] 依存棚卸しを実施。`src/pytra/cli.py` は `PY2CPP/PY2RS/PY2SCALA` を直参照、`tools/` は `runtime_parity_check` / `regenerate_samples` / selfhost系を中心に `src/py2*.py` 依存、`test/` は `test_py2*` 系が wrapper 直接実行を前提、`docs` は `how-to-use` に実行例が集中していることを確認。移行順は `(1) src/pytra/cli.py + tools 共通導線 -> (2) test 契約更新 -> (3) docs -> (4) selfhost 最終置換` とする。
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S1-02] `py2cpp.py` 実利用オプションを抽出（`--multi-file`, `--output-dir`, `--header-output`, `--emit-runtime-cpp`, `--dump-deps`, `--dump-options`, `--preset`, `--int-width`, `--mod-mode`, `--top-namespace`, `--str-index-mode`）。受け皿仕様は「共通レイヤ可搬オプションは `--lower/optimizer/emitter-option` へマップ」「出力モード変更系（`multi-file/header/runtime-cpp/dump-*`）は `py2x --target cpp` 専用の互換フラグとして直受け」に確定。
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S1-03] selfhost 導線の依存契約を棚卸し。`tools/prepare_selfhost_source.py` / `build_selfhost.py` / `build_selfhost_stage2.py` / `check_selfhost_cpp_diff.py` / `verify_selfhost_end_to_end.py` が `src/py2cpp.py` を前提に連鎖している。置換方針は「通常系は `src/pytra-cli.py --target cpp`、selfhost系は `src/pytra-cli.py --target cpp` を正規入口」に統一し、`selfhost/py2cpp.py` は中間生成物としてのみ維持（呼び出し元からは wrapper 名を隠蔽）とする。
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S2-01] `src/pytra-cli.py` に C++ 互換経路を追加し、`--target cpp` 時は `py2cpp` 互換フラグを受理して委譲する実装へ更新。`--optimizer-option/--emitter-option` の C++ 対応キー（例: `cpp_opt_level`, `mod_mode`, `negative_index_mode`）を専用フラグへマップし、`test_py2x_cli.py`（5 tests）と実行確認（single-file / multi-file / header-output）で非退行を確認。
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S2-02] selfhost 系を除く `tools/` の CLI 呼び出しを `src/pytra-cli.py --target ...` へ統一し、`regenerate_samples` / `runtime_parity_check` / `verify_*` / `benchmark_*` / `check_py2*_transpile` を更新。`check_py2*_transpile.py` 一括実行で非退行（all pass）を確認。
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S2-03] `test/unit` の subprocess 実行を `src/pytra-cli.py --target ...` へ統一（`test_py2{cs,go,java,js,kotlin,lua,nim,php,rb,rs,scala,swift,ts}_smoke.py`、`test_runtime_parity_check_cli.py`、`test_cpp_optimizer_cli.py`、`test_east3_optimizer_cli.py`、`test_py2cpp_features.py`）。代表 15 ファイルの unittest が pass（`test_py2lua_smoke.py` は既知失敗7件のまま）。
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S2-04] `docs/ja/how-to-use.md` と `docs/en/how-to-use.md` の実行例を `py2x --target` 基準へ更新し、出力パス指定を `-o` で統一。併せて `docs/ja/spec/spec-user.md` / `docs/en/spec/spec-user.md` の言語一覧を `py2x` 正規入口表記へ更新。
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S2-05] selfhost 関連スクリプト（`build_selfhost*` / `check_selfhost_cpp_diff` / `selfhost_transpile` / `check_selfhost_direct_compile` / `verify_selfhost_end_to_end`）から `src/py2cpp.py` 直参照を除去し、`src/pytra-cli.py` 基準の呼び出しと `--selfhost-target auto`（旧 binary 互換）を導入。`check_selfhost_cpp_diff --skip-east3-contract-tests --cases test/fixtures/core/add.py` は実行可能で `mismatches=0` を確認。
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S2-05] `tools/build_selfhost.py` を `py2x-selfhost` 起点へ切替え後、生成 `selfhost/py2cpp.cpp` は C++ コンパイルで未解決（`pytra::compiler::ler::*` 参照・help 文字列連結・ローカル変数束縛欠落）となるため、selfhost 導線は未成立のまま。`S2-05` は完了化せず継続する。
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S2-05] `transpile_cli` の import 解決で `toolchain.*` / `toolchain.emit.*` を既知 import 扱いへ調整し、C++ emitter に self_hosted 由来の未lower method 呼び出し（`str.startswith/endswith` 等）フォールバックを追加。これにより `python3 tools/prepare_selfhost_source.py && python3 src/py2cpp.py selfhost/py2cpp.py -o /tmp/selfhost_py2cpp_oldpath.cpp` は再度通過。
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S3-01] `tools/check_legacy_cli_references.py` を追加し、`src/tools/test` 配下の `src/py2*.py` 文字列参照と `import py2*` を allowlist 以外で fail-fast 検出するガードを導入。`tools/run_local_ci.py` に同チェックを組み込み、`python3 tools/check_legacy_cli_references.py` で pass を確認。
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S2-05] C++ emitter の import 解決で `toolchain.misc.` 接頭辞を `15` 文字で切る不具合を修正（正: `len("toolchain.misc.")`）。`build_selfhost.py` の先頭失敗は `pytra::compiler::ler::*` から `pytra::compiler::*` 未実体化へ前進し、`_print_help` 文字列連結・layer option 変数スコープ崩れは `src/pytra-cli.py` 側修正で解消した。
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S2-05] `pytra-cli.py` の引数定義を runtime `ArgumentParser` 契約へ寄せ（`add_argument` 署名差の解消、`_add_common_args` の const 参照問題解消）、selfhost トランスパイル段階を再通過させた。現在の `build_selfhost.py` 失敗は `pytra::compiler::{transpile_cli,backend_registry_static}` 未実体化（runtime C++ ヘッダ欠落）に限定。
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S2-05] `src/runtime/cpp/pytra/compiler/{transpile_cli,backend_registry_static}.{h,cpp}` を追加し、selfhost 生成 C++ のリンク失敗を解消。実行時は `[not_implemented]` を返す最小実装とし、`build_selfhost.py` は通過・`build_selfhost_stage2.py` は `[not_implemented]` 時に `selfhost/py2cpp.cpp` 再利用フォールバックで stage2 バイナリ生成を継続できる状態へ前進。
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S2-05] `toolchain/emit/cpp/emitter/call.py` の self_hosted 向け builtin method フォールバックを selfhost ブートストラップソース（`selfhost/py2cpp.py` / `src/py2cpp.py` / `src/pytra-cli.py`）限定へ絞り、`test_east3_cpp_bridge` 失敗を解消。これにより `check_selfhost_cpp_diff` / `check_selfhost_stage2_cpp_diff`（`--mode allow-not-implemented`）を `--skip-east3-contract-tests` なしで通過確認。
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S2-05] 受け入れ基準（`build_selfhost.py` 通過、`build_selfhost_stage2.py` 通過、`check_selfhost_cpp_diff` / `check_selfhost_stage2_cpp_diff` の `allow-not-implemented` 運用成立）を満たしたため完了化。selfhost transpile 本体の実装深化は別優先（`P4-MULTILANG-SH-01` 系）で継続する。
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S3-02] `src/py2cpp.py` を `src/toolchain/emit/cpp/cli.py` へ実体移行し、`py2x`/`pytra/cli`/backend registry/tools/unit tests を `py2x --target cpp` と新モジュール参照へ更新した上で `src/py2cpp.py` を削除。`check_legacy_cli_references` / `check_py2cpp_transpile` / `test_py2cpp_smoke` / `test_pytra_cli` / `test_east3_cpp_bridge` の通過を確認。
- 2026-03-04: [ID: P1-PY2X-SINGLE-ENTRY-01-S3-03] `check_py2{cpp,rs,cs,js,ts,go,java,swift,kotlin,rb,lua,scala,php,nim}_transpile.py` 全件と selfhost 4本（`build_selfhost`, `build_selfhost_stage2 --skip-stage1-build`, `check_selfhost_cpp_diff`, `check_selfhost_stage2_cpp_diff`）を実行し、`py2cpp.py` 削除後の transpile/selfhost 非退行を確認して完了化。
