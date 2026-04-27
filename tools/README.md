# tools/ 管理台帳

このファイルは `tools/` ディレクトリの管理台帳です。
**新規ファイルを追加するときは必ずこのファイルも同時に更新してください。**
台帳に記載のないファイルは CI チェック (`tools/check/check_tools_ledger.py`) で fail になります。

## ディレクトリ構成

```
tools/
├── check/          # 検証・ガードスクリプト
├── gen/            # 生成スクリプト
├── run/            # 実行・CI スクリプト
├── unittest/       # ユニットテスト（pytest）
├── unregistered/   # 旧ツール・実験的ツール（CI 対象外）
├── *.json / *.txt  # 設定・allowlist ファイル
└── README.md       # 本ファイル（管理台帳）
```

## ルール

- `tools/` 直下への新規 `.py` ファイル追加は**禁止**。必ずサブディレクトリに配置する。
- 新規スクリプトは `check/` / `gen/` / `run/` のいずれか適切なフォルダへ配置する。
- CI 非対象の実験的スクリプトは `unregistered/` に配置する。
- ファイルを追加・削除・移動したら **必ず本台帳を同時に更新する**。

---

## tools/check/ — 検証・ガードスクリプト

### `audit_image_runtime_sot.py`
画像エンコーダランタイムのレイアウト（`native/generated`）を言語ごとに監査する。
`native` レーンは画像エンコーダコアシンボルを含まず、`generated` レーンは `source/generated-by` マーカーを持つことを検証。
必要に応じてトランスパイルプローブを走らせ、Python 正本との整合性も確認する。

### `check_all_target_sample_parity.py`
`runtime_parity_check.py`（fast-backed 正規エントリ）を言語グループ（cpp / js+ts / コンパイル系 / スクリプト系）ごとに一括実行する。
EAST3 最適化レベルやコード生成オプションをグループ別に設定して呼び出す。
全言語の sample parity を一コマンドで確定させるためのラッパー。

### `check_emitter_hardcode_lint.py`
`src/toolchain2/emit/*/` 配下の emitter ソースを grep し、モジュール名・runtime 関数名・ターゲット定数・クラス名等のハードコードを検出する（P6-EMITTER-LINT）。
違反は言語 × カテゴリのマトリクスとして stdout に出力する（exit code は常に 0、違反でも fail しない）。
オプション: `--verbose`（詳細表示）/ `--lang <lang>`（言語絞り込み）/ `--category <cat>`（カテゴリ絞り込み）

### `check_east_stage_boundary.py`
EAST コンパイルパイプラインのステージ間境界を保護し、ステージをまたぐ依存の混入を防ぐ。
import・関数呼び出し・文字列リテラルの AST 走査でクロスステージ参照違反を検出する。
設計仕様に基づくステージ間ポリシーの遵守を強制する。

### `check_emitter_forbidden_runtime_symbols.py`
`src/toolchain/emit/*/emitter/*.py` に禁止 runtime 実装シンボル（`__pytra_write_rgb_png` / `__pytra_save_gif` / `__pytra_grayscale_palette`）の混入がないことを検証する。
違反があれば allowlist 外のものを fail とする。
既知の技術的負債は `emitter_forbidden_runtime_symbols_allowlist.txt` で明示管理する。

### `check_emitter_runtimecall_guardrails.py`
non-C++ emitter の `if/elif` 文字列分岐における runtime/stdlib 関数名の直書きを検知する。
allowlist 外の直書き増分を fail とし、EAST3 正本（`runtime_call` / `resolved_runtime_call`）経由の解決を強制する。
既知の技術的負債は `emitter_runtimecall_guardrails_allowlist.txt` で追跡管理する。

### `check_jsonvalue_decode_boundaries.py`
`pytra-cli.py` / `east2x.py` / `toolchain/compile/east_io.py` / `toolchain/link/*` の JSON artifact 境界で `json.loads_obj(...)` が正本であることを検証する。
raw `json.loads(...)` への再侵入を fail-fast に止める。
JSON 境界での型安全性ポリシーを強制する。

### `check_legacy_cli_references.py`
廃止済み `py2*.py` ラッパーファイルと import 参照の再導入を防止する。
`src/` / `tools/` / `test/` をスキャンし、レガシー `py2*` モジュール参照を検出する。
正規の `py2x` エントリポイントは正規表現で除外し誤検知を防ぐ。

### `check_legacy_transpile_checkers_absent.py`
言語ごとの廃止済みトランスパイルチェッカースクリプト（`check_py2cpp_transpile.py` 等 10 件）の再導入を防止する。
`tools/` から `check_py2*_transpile.py` パターンをスキャンして再出現を検出する。

### `check_mapping_json.py`
`src/runtime/<lang>/mapping.json` ファイルの妥当性と完全性を全言語分検証する。
valid JSON・`calls` キー存在・`builtin_prefix` 存在・`env.target` 必須エントリ・空文字エントリなしを確認する。
emitter ガイド §7.1–7.3 の仕様に準拠していることを保証する。

### `check_multilang_quality_regression.py`
多言語品質メトリクス（ファイル数・行数・変換済み量など）が記録済みベースラインに対して回帰していないかを検証する。
Markdown ドキュメントから品質テーブルをパースし、言語ごとのメトリクス現在値と比較する。
許容される段階移行は逆行プレビューマーカーで区別する。

### `check_noncpp_backend_health.py`
non-C++ バックエンド（rs/cs/js/ts/go/java/swift/kotlin 等）の健全性を集約検証する。
各ターゲットの静的チェック・スモークテスト・transpile・parity を言語ファミリー（wave1/2/3）単位でまとめて実行する。
対象言語の導入段階と問題カテゴリを統合レポートにまとめる。

### `check_noncpp_east3_contract.py`
non-C++ トランスパイラの EAST3 3 層コントラクトと回帰ルートを検証する。
各ターゲット（rs/cs/js/ts 等）のスモークテスト・transpile・契約テストを実行する。
ロードマップに基づく言語ごとの進捗確認にも使用できる。

### `check_runtime2_references_absent.py`
ソース・ツール・テストコードがレガシー `src/runtime2` パスを参照していないことを確認する。
`.py` / `.md` / `.json` / `.yaml` 等の複数形式をスキャンし `src/runtime2/` と `runtime2/cpp/` 参照を検出する。
allowlist ベースで既知の技術的負債を管理する。

### `check_runtime_call_coverage.py`
EAST3 golden に出現する `runtime_call` / `resolved_runtime_call` と各言語の `mapping.json` calls テーブルを双方向に照合する。
EAST 側の未登録 runtime call と、mapping 側の未使用キーを検出し、runtime mapping のカバレッジ回帰を防ぐ。
`--lang` / `--direction` で対象言語や検証方向を絞り込める。

### `check_runtime_core_gen_markers.py`
`rs/cs` では `src/runtime/<lang>/generated/**` を canonical generated lane として `source/generated-by` marker を強制し、legacy `pytra-gen/pytra-core` は未移行 backend 向けの scan target としてのみ扱う。
C++ では `src/runtime/cpp/generated/core/**` の marker 必須・`native/core/**` の marker 禁止と legacy `src/runtime/cpp/core/**` 再出現時の marker 混入も監査する。
既知の許可済みファイルは `runtime_core_gen_markers_allowlist.txt` で管理する。

### `check_runtime_legacy_shims.py`
ランタイムレイアウト移行中のレガシー `*_module` シムを監視・制限する。
`js_module` / `ts_module` シムの完全一致検証、禁止レガシー参照スキャンを行う。
移行完了状態への強制ガードとして機能する。

### `check_runtime_pytra_gen_naming.py`
canonical generated lane（`rs/cs` は `src/runtime/<lang>/generated/**`、未移行 backend は `pytra-gen/**`）の `std|utils` 配置と素通し命名（`<module>.py → <module>.<ext>`）を検査する。
`image_runtime.*` / `runtime/*.php` などの命名・配置違反増分を fail させる。
既知の許可済みファイルは `runtime_pytra_gen_naming_allowlist.txt` で管理する。

### `check_runtime_special_generators_absent.py`
言語別ランタイムジェネレータスクリプト（`gen_*_from_canonical.py` 系）の再導入を防止する。
`tools/` ディレクトリから古いジェネレータパターンをスキャンし、廃止状態を強制する。
`gen_runtime_from_manifest.py` への統一集約を強制する。

### `check_runtime_std_sot_guard.py`
`src/pytra/std/*.py` / `src/pytra/utils/*.py` を正本とする運用を検査する。
`rs/cs` では `src/runtime/{rs,cs}/generated/**` を canonical generated lane として監査しつつ、legacy `pytra-gen` lane への手書き実装再流入（現行ガード対象: `json/assertions/re/typing`）を fail させる。
C++ `std/utils` 全体の責務境界（`generated/native` ownership + required manual impl split）も検証する。

### `check_sample_regen_clean.py`
再生成済みサンプル出力が git 未コミット差分を持たないことを確認する。
`sample/cpp` / `rs` / `cs` / `js` / `ts` / `go` / `java` / `swift` 等の git status を確認する。
差分がある場合は `regenerate_samples.py` の実行を指示する。

### `check_todo_priority.py`
`docs/ja/todo/index.md` / `docs/ja/plans/*.md` の差分に追加した進捗 ID が、未完了の最上位 ID（またはその子 ID）と一致するかを検証し、優先度逸脱を防止する。
`plans` 側は `決定ログ`（`- YYYY-MM-DD: ...`）行のみを進捗判定対象にし、構造整理の ID 列挙は対象外とする。
git diff ベースで変更分のみをチェックするため高速に動作する。

### `check_tools_ledger.py`
`tools/README.md` 台帳と `tools/check/` / `tools/gen/` / `tools/run/` の実スクリプトの同期を検証する。
台帳に記載のないファイルがあれば fail、`tools/` 直下への `.py` ファイル直置きも fail とする。
`run_local_ci.py` の先頭ステップに組み込まれており、台帳未更新の追加を CI で検知できる。

### `check_transpiler_version_gate.py`
変換器関連ファイルが変更されたとき、`src/toolchain/misc/transpiler_versions.json` の対応コンポーネント（`shared` / 言語別）で PATCH 以上のバージョン更新が行われているかを検証する。
git diff から共有・言語別依存パスの変更を検出し、バージョン番号の変更を強制する。
MINOR / MAJOR はユーザーの明示指示がある場合のみ許容する。

### `runtime_parity_check.py`
複数言語へのトランスパイル結果を実行し、stdout / stderr / 成果物 CRC32 を Python 正本と比較する多言語 parity チェックの正規エントリ。
transpile 段は in-memory API で実行する。
`--category` でカテゴリ絞り込み可能。結果は `.parity-results/<target>_<case-root>.json` に自動蓄積される。
言語別非対応機能リストで既知制限を区別し、`gen_backend_progress.py` の入力データにもなる。

### `runtime_parity_check_fast.py`
`runtime_parity_check.py` の互換エイリアス。
同じ fast 実装を呼び、既存のコマンドライン互換を維持する。

### `runtime_parity_shared.py`
`runtime_parity_check.py` / `runtime_parity_check_fast.py` から共有される parity helper 群。
case stem 解決、ターゲット実行、出力正規化、`.parity-results/` 保存、進捗ページ更新などを集約する。
直接実行用の公開 CLI ではなく、parity checker の内部共有モジュールとして扱う。

### `verify_image_runtime_parity.py`
Python 正本の画像ランタイム（`src/pytra/utils/png.py` / `gif.py`）と C++ ランタイム（`src/runtime/east/utils/`）の PNG / GIF 生成バイト列の同等性を検証する。
`g++` でコンパイルした検証ハーネスを使って実行比較を行う。
画像ランタイムの Python↔C++ 一致を保証する。

### データファイル（`tools/check/` 内）

| ファイル | 用途 |
|---|---|
| `check_py2x_profiles.json` | `check_py2x_transpile.py` が読み込む言語別プロファイル設定 |
| `emitter_forbidden_runtime_symbols_allowlist.txt` | `check_emitter_forbidden_runtime_symbols.py` の許可済み既知違反リスト |
| `emitter_runtimecall_guardrails_allowlist.txt` | `check_emitter_runtimecall_guardrails.py` の許可済み既知違反リスト |
| `runtime_core_gen_markers_allowlist.txt` | `check_runtime_core_gen_markers.py` の許可済みファイルリスト |
| `runtime_pytra_gen_naming_allowlist.txt` | `check_runtime_pytra_gen_naming.py` の許可済みファイルリスト |

---

## tools/gen/ — 生成スクリプト

### `export_backend_test_matrix.py`
バックエンドスモークテストの実行結果を Markdown テーブルにエクスポートする。
`tools/unittest/` のスモークテストを実行し、duration・status・詳細を収集する。
`docs/ja/language/backend-test-matrix.md` と `docs/en/` を同時に更新する。

### `gen_backend_progress.py`
`.parity-results/<target>_<case-root>.json` に蓄積されたパリティ結果を読み込み、バックエンド進捗ページを生成する。
fixture / sample の parity マトリックスと selfhost マトリックスを作成し、アイコン（🟩/🟥/🟨/⬜/⚠）で可視化する。
`docs/ja/language/backend-progress.md` と `docs/en/` を同時に出力する。

### `gen_sample_benchmark.py`
`.parity-results/*_sample.json` に記録された `elapsed_sec` を読み込み、`sample/README-ja.md` と `sample/README.md` の「実行速度の比較」テーブルを自動更新する。
計測されていない言語/ケースは既存値を維持（上書きしない）。PyPy は parity check 対象外のため常に手動値を保持する。
`runtime_parity_check_fast.py --benchmark` 実行後に手動または自動で呼び出す（10 分以内の再実行はスキップ）。

### `gen_makefile_from_manifest.py`
`manifest.json` を受け取り、`all` / `run` / `clean` ターゲットを含む `Makefile` を生成する。
C++ ランタイムソースと依存関係を `manifest.json` と `cpp_runtime_deps` から収集する。
ビルドフラグ（`-O` 最適化レベル）の正規化とコンパイルルール生成も行う。

### `gen_runtime_symbol_index.py`
`src/pytra/built_in/` / `src/pytra/std/` / `src/pytra/utils/` からランタイムシンボルインデックスを生成する。
関数シグネチャ・クラス定義・変数をパースし、JSON 化された schema v1 形式で `tools/runtime_symbol_index.json` に出力する。
数学・画像特化アダプタ種別の設定を含む。`src/toolchain/frontends/` と `src/toolchain2/resolve/` から参照される。

### `regenerate_golden.py`
`toolchain2` パイプラインで golden file を全段（parse→resolve→compile→optimize）再生成する。
各段の出力で既存の golden file を上書きする。
fixture / sample / pytra ごとに異なるソース・出力ディレクトリ構成を持つ。

### `regenerate_selfhost_golden.py`
`test/selfhost/east3-opt/` に格納済みの east3-opt golden ファイルを各ターゲット言語に emit し、
`test/selfhost/<lang>/` に配置する。既存ファイルとの差分（追加・削除・変更）を報告した上でファイルを書き換える。
モジュール単位でサブプロセスを起動し、タイムアウトしたモジュール（大規模 east3-opt 等）はスキップする。
主要オプション: `--target cpp,go,rs,ts`（デフォルト: 全言語） / `--dry-run`（書き込みなし） / `--timeout`（秒、デフォルト 30）

### `regenerate_samples.py`
`sample/py` から各 `sample/<lang>` を再生成する。
`src/toolchain/misc/transpiler_versions.json` のバージョン・トークンが変わらない限り再生成をスキップする。
主要オプション: `--verify-cpp-on-diff`（C++ 生成差分が出たケースだけ `runtime_parity_check.py` で compile/run 検証）

### `strip_east1_type_info.py`
EAST1 golden file から型解決情報（`resolved_type` / `runtime_module_id` / `semantic_tag` 等）を除去する。
`spec-east1.md` の仕様に準拠した形式に整形するためのクリーニングツール。
構文構造は変更せず、型注釈はソースのまま保持する。

---

## tools/run/ — 実行・CI スクリプト

### `run_local_ci.py`
ローカル最小 CI（version gate / TODO 優先度ガード / runtime 層分離ガード / non-C++ emitter ガード / backend health gate / transpile 回帰 / unit test / selfhost build / diff）を一括実行する。
60 以上のステップを固定順序で実行し、全体品質を一コマンドで検証できる。
`tools/check/` / `tools/unittest/` 各種を統合してオーケストレーションする。

### `run_selfhost_parity.py`
selfhost parity チェックを実行し、結果を `.parity-results/selfhost_<lang>.json` に記録する。
`--selfhost-lang python` では既存の `.parity-results/*.json` を集計して `selfhost_python.json` を生成する。
コンパイル済み selfhost（go/rs/cpp/ts）は selfhost バイナリ経由で east3-opt モジュールを transpile し、Python 正本と出力比較を行う。
主要オプション: `--selfhost-lang`（python/go/rs/cpp/ts） / `--emit-target`（cpp 等） / `--case-root`（fixture/sample） / `--dry-run`

### `run_regen_on_version_bump.py`
`transpiler_versions.json` の MINOR 以上の更新を検出したときだけ `regenerate_samples.py` を起動する。
影響を受ける言語のみを再生成することで、不要な全言語再生成を避ける。
PATCH バンプでは再生成を行わない設計になっている。

### `sync_todo_history_translation.py`
`docs/ja/todo/archive` を正本として `docs/en/todo/archive` の日付ファイル雛形と index を同期する。
`--check` フラグで同期漏れを検出できる。
SHA256 ハッシュで原文変更を追跡し、翻訳済み（done）/ 未翻訳（pending）の状態を管理する。

---

## tools/unittest/ — ユニットテスト

pytest で実行するテストファイル群。`test_emit_cases.py` は `test/cases/emit/**.json` を走査するデータ駆動 emitter テストランナー。
`test_pipeline_cases.py` は `test/cases/{east1,east2,east3}/**.json` を走査するデータ駆動 pipeline テストランナー。
`test_pylib_cases.py` は `test/cases/pylib/**.json` を走査するデータ駆動 pytra stdlib shim テストランナー。
サブディレクトリ構成:

| サブディレクトリ | 内容 |
|---|---|
| `common/` | 言語横断・共通テスト |
| `compile/` | コンパイルフェーズテスト |
| `emit/` | emitter テスト（言語別サブディレクトリあり） |
| `ir/` | IR テスト |
| `link/` | リンクフェーズテスト |
| `selfhost/` | selfhost テスト |
| `toolchain2/` | toolchain2 テスト |
| `tooling/` | ツール系テスト |

トップレベルファイル:

| ファイル | 目的 |
|---|---|
| `comment_fidelity.py` | コメント保持テスト |
| `test_discovery_router.py` | テスト検出ルーターテスト |

---

## tools/ ルートの設定・データファイル

| ファイル | 目的 |
|---|---|
| `runtime_generation_manifest.json` | runtime 生成マニフェスト（`unregistered/` および `unittest/tooling/` から参照） |
| `runtime_symbol_index.json` | runtime シンボルインデックス（`gen_runtime_symbol_index.py` が生成、`src/toolchain/frontends/` と `src/toolchain2/resolve/` からも参照されるため tools/ 直下に置く） |

---

## tools/unregistered/ — 削除済み（2026-04-02）

旧ツール群は削除済み。新しいスクリプトは最初から `tools/check/`、`tools/gen/`、`tools/run/` 等の正規ディレクトリに配置すること。
