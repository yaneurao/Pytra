<a href="../en/changelog.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# 更新履歴

## 2026-03-29

- **Go fixture 全件 PASS**: Go emitter の container 既定表現を参照型ラッパー（`*PyList[T]`, `*PyDict[K,V]`, `*PySet[T]`）に統一（P1-GO-CONTAINER-WRAPPER S1〜S3）。fixture 全 147 件 + stdlib 16/16 PASS。
- **Rust emitter 新規実装 (P7-RS-EMITTER)**: `src/toolchain2/emit/rs/` に CommonRenderer + override 構成で Rust emitter を新規実装。mapping.json 作成。fixture emit 成功。
- **TypeScript emitter 新規実装 (P8-TS-EMITTER)**: `src/toolchain2/emit/ts/` に TS emitter を新規実装。JS は TS emitter の型注釈抑制フラグで対応する設計。mapping.json 作成。fixture 142 件 emit 成功。
- **C++ emitter parity 改善 (P3-CR-CPP)**: 予約語エスケープ（`_safe_cpp_ident`）、optional dict.get、float/container printing を修正。oop 18/18, typing 22/22, signature 13/13 PASS。
- **C++ runtime 例外安全性 (P3-CR-CPP-S4)**: py_types.h の `Object<void>` コンストラクタ5箇所を `make_unique` + `release` パターンに書き換え。
- **runtime_parity_check 高速版**: `runtime_parity_check_fast.py` を新設。transpile 段を toolchain2 Python API のインメモリ呼び出しに置き換え、プロセス起動 + disk I/O を省略。
- **runtime_parity_check に `--category` オプション追加**: fixture サブディレクトリ単位（oop, control, typing 等）で部分実行可能に。
- **parity 結果の自動蓄積 + 進捗ページ自動生成 (P5-BACKEND-PROGRESS)**: parity check 実行時に `work/parity-results/` へ結果を自動蓄積（タイムスタンプ付きマージ）。`tools/gen/gen_backend_progress.py` で fixture/sample/selfhost の3マトリクスを日英同時生成。
- **mapping.json 妥当性チェッカー (P10.5-MAPPING-VALIDATE)**: `tools/check/check_mapping_json.py` を新設。全言語の mapping.json に対して必須エントリ（`env.target`）、フォーマット検証を実施。`run_local_ci.py` に組み込み。
- **spec-runtime-decorator 拡張**: `extern_var` セクション追加、パイプライン解決フロー（parser → resolve → emitter の責務境界）追記、早見表追加。
- **spec-emitter-guide 拡張**: §1.4 生成コード品質要件（例外安全性、予約語エスケープ、`rc_from_value<T>` 汎用化）、§7.1〜7.3 mapping.json の定数置換・リテラル埋め込み・`env.target` 必須エントリ。
- **spec-tools 再編**: 索引 + 3詳細ページ（daily, parity, update-rules）に分割。unregistered 7本を削除。
- **TODO 領域別分割**: `todo/index.md` を索引のみに縮退し、`cpp.md` / `go.md` / `rust.md` / `ts.md` / `infra.md` に分離。各 agent は自分の領域ファイルだけ読み書きする運用。P0 ブロッカールール撤去。
- **旧 `@abi` 参照の一掃**: spec-east / spec-dev / spec-runtime / guide / tutorial から `@abi` / `runtime_abi_v1` を削除し `@runtime` / `@extern` に統一。
- **PNG fixture パス修正**: `out/` → `test_png_out/` に変更し `os.makedirs` で自前作成。parity check の cwd 不一致を解消。

## 2026-03-28

- **Go 例外処理完成 (P0-EXCEPTION-GO)**: typed catch、custom exception の正確な catch/rethrow、`raise ... from ...`、bare rethrow、union-return 垂直スライスを実装。builtin exception を `pytra.built_in.error` に統合。
- **C++ 例外 native lowering (P0-EXCEPTION-CPP)**: C++ backend で native exception lowering を実装。
- **Go selfhost 進捗 (P2-SELFHOST)**: lowering profile 対応、container locals の参照型ラッパー既定化、`yields_dynamic` による型アサーション判定、Go mapping dispatch + parity カバレッジ完了。P2-LOWERING-PROFILE-GO 完了。
- **CommonRenderer 拡張**: elif chain レンダリングを共通化。C++ common renderer の parity 回帰修正。
- **type_id table linker 生成 (P0-TYPE-ID-TABLE)**: linker が `pytra.built_in.type_id_table` を生成する仕様を策定・実装。ハードコード type_id の廃止方針を確定。
- **@runtime / @extern デコレータ設計完了 (P0-RUNTIME-DECORATOR)**: `@runtime("namespace")` + `@extern` + `runtime_var("namespace")` の3本立てに統一。自動導出ルール、`symbol=` / `tag=` オプション上書き、include ファイル構成を spec-runtime-decorator.md に策定。旧 `@extern_method` / `@abi` を廃止。
- **P0-CPP-INCLUDE-PATH-FIX**: C++ emitter の runtime include パス不整合を修正。
- **P0-GO-PATHLIB-FIX**: Go emitter の pathlib 署名崩れ（joinpath vararg、read_text/write_text）を修正。
- **spec 再編**: legacy 仕様 12 件をアーカイブ。spec-codex.md → spec-agent.md に改名。spec/index.md をカテゴリ別テーブルに再構成。未リンク仕様 6 件を追加。spec-opaque-type.md（`@extern class` の型契約）を新設。
- **ガイド新設**: docs/ja/guide/ に EAST・emitter・型システム・runtime・extern/FFI の 5 ページを追加。Tutorial と Specification の間に Guide セクションを配置。
- **チュートリアル拡充**: 例外処理、Python との違い、モジュール一覧（argparse/glob/re/enum/timeit）、サンプル集のページを追加。読み順を再構成。
- **AGENTS.md 分割**: planner / coder の役割別仕様に分離。最小ブートストラップ化。

## 2026-03-27

- **C++ emitter spec 準拠完了 (S1〜S15)**: fail-fast 化、mapping.json 一本化、container 参照型ラッパー（`Object<list<T>>` 等）、implicit_promotions、is_entry/main_guard_body、@property 対応、runtime パス解決の共通化。
- **Trait（pure interface・多重実装）導入**: `@trait` / `@implements` デコレータで pure interface を定義。C++ は virtual 継承 + `Object<T>` 変換コンストラクタ、Go は interface 生成で写像。trait の isinstance は compile 時検証のみ（runtime 情報不要）。
- **isinstance ナローイング**: resolve 段で `if isinstance(x, T):` 後の型環境を自動更新。if/elif、early return guard（`if not isinstance: return`）、ternary isinstance（`y = x if isinstance(x, T) else None`）、`and` 連結条件に対応。
- **三項演算子の Optional 型推論**: `expr if cond else None` → `Optional[T]`、異なる型 → `UnionType` を resolve で推論。
- **pytra.std.json parser 対応**: PEP 695 再帰的 type alias（`type JsonVal = ...`）と Union forward reference を parser で処理可能に。golden 再生成済み。
- **POD 型 isinstance**: `isinstance(x, int16)` 等の POD 型判定を exact type match で実装。spec-type_id.md §4.2 に規定。
- **link 層入力完全性検証**: link-input の未解決 import を fail-closed で報告。型スタブ生成で parse 不能モジュールを補完。
- **ClosureDef lowering**: nested FunctionDef を EAST3 で ClosureDef に lower。captures 解析（readonly/mutable）を付与。
- **Lowering プロファイル設計**: 言語能力宣言（tuple_unpack_style, container_covariance, with_style 等 16 項目）を spec-language-profile.md §7 に追加。CommonRenderer 設計を §8 に追加。
- **チュートリアル追加**: Union 型と isinstance ナローイング、Trait の解説ページを追加。英訳も実施。

## 2026-03-26

- **パイプライン再設計完了**: parse → resolve → compile → optimize → link → emit の 6 段パイプライン（`pytra-cli2`）が全段動作。toolchain2 は toolchain に一切依存しない独立実装。
- **Go backend 新パイプライン移行**: Go emitter + runtime を新パイプラインで実装。sample 18/18 emit 成功。旧 Go emitter/runtime を削除。
- **C++ emitter 新規実装**: `toolchain2/emit/cpp/` に新パイプライン用 C++ emitter を実装。fixture 132/132, sample 18/18 emit 成功。
- **CodeEmitter 基底クラス**: `mapping.json` による runtime_call 写像を全 emitter で共有。ハードコード除去。
- **仕様整合 (Codex-review)**: resolve/parser/validator/linker/emitter の仕様違反 20 件以上を修正。
- **spec-east1.md / spec-east2.md**: EAST1（型未解決）と EAST2（型確定）の出力契約を正式定義。
- **spec-builtin-functions.md**: built-in 関数の宣言仕様。POD/Obj 型分類、dunder 委譲、extern_fn/extern_var/extern_class/extern_method。
- **spec-runtime-mapping.md**: mapping.json のフォーマット仕様。implicit_promotions テーブル。
- **integer promotion**: C++ usual arithmetic conversion に準拠した数値昇格 cast を resolve で挿入。
- **bytearray 対応**: `pytra/utils/png.py` / `gif.py` を `list[int]` → `bytearray` に書き換え。Go で `[]byte` に写像。

## 2026-03-25

- **P0 全完了**: parse/resolve/compile/optimize/link/emit の全段が golden file テストと一致。
- **test/ ディレクトリ再編**: fixture/sample/include/pytra/selfhost の 5 カテゴリに整理。
- **golden file 自動再生成**: `tools/gen/regenerate_golden.py` で全段 golden を一括再生成。
- **Go emitter**: お手本 emitter として実装。fixture 132/132, sample 18/18 emit 成功。
- **Go runtime + parity**: sample 18/18 で `go run` + stdout 一致。Go は Python の 63x 高速。
- **Go runtime 分解**: `pytra_runtime.go` 全部入り → `built_in/` + `std/` + `utils/` に分離。

## 2026-03-24

- **パイプライン再設計着手**: parse/resolve/compile/optimize/emit の 5 段（後に link 追加で 6 段）パイプラインを設計。
- **toolchain2/ 新規作成**: 現行 toolchain/ とは独立した新パイプライン実装。selfhost 対象（Any/object 禁止、pytra.std のみ）。
- **pytra-cli2**: 新 CLI。-parse/-resolve/-compile/-optimize/-link/-emit/-build サブコマンド。
- **EAST1 golden file**: spec-east1 準拠で golden を strip（型情報除去）。150 件。
- **built-in 関数宣言**: `src/include/py/pytra/built_in/builtins.py` + `containers.py`。v2 extern（extern_fn/extern_var/extern_class/extern_method）。
- **stdlib 宣言**: `src/include/py/pytra/std/` に math/time/glob/os/sys 等の v2 extern 宣言。

## 2026-03-23

- Dart emitter デッドコード除去（14 関数削除）。ランタイムヘルパー重複排除。18/18 parity。
- Nim emitter spec-emitter-guide 準拠改善。`build_import_alias_map` 導入、`yields_dynamic` 対応。
- 全 backend 共通テストスイート整備。`runtime_parity_check.py` で fixture 131 件を全言語実行可能に。
- EAST3 型推論バグ修正 4 件（Nim 担当報告: Swap, returns, VarDecl, list[unknown]）。
- ContainerValueLocalHintPass を全 backend 共通化。
- Swap ノードを Name 限定に制約し、Subscript swap を Assign 展開。
- tuple 分割代入の `_` 要素に `unused: true` 付与。
- cast() の resolved_type 修正 + list.pop() の generic 解決。
- C++ multi-file emit の runtime east パス解決修正。
- C++ test_py2cpp_features.py テストパス率 64% → 95%。

## 2026-03-22

- REPO_ROOT 修正 + import alias 解決 + conftest extern 関数修正。
- `build_multi_cpp.py` の generated source を include 追跡ベースの自動リンクに変更。
- Object<T> 移行フェーズ 1〜4 完了（ControlBlock, emitter, list/dict, 旧型撤去）。

## 2026-03-21

- EAST1 パーサーから `noncpp_runtime_call` / `noncpp_module_id` を除去（EAST1 責務逸脱の解消）。
- py_runtime.h を 6 ファイルに分解・ファサード化。
- runtime .east を link パイプラインに自動統合。
- object = tagged value 統一。tagged union を PyTaggedValue (object+tag) に統一。
- 旧 object API 一掃（make_object, obj_to_rc_or_raise 等）。
- escape 解析結果を class_storage_hint に反映。union type パラメータを ref (gc_managed) に強制。
- self-contained C++ output: extern モジュールの宣言ヘッダー自動生成。

## 2026-03-20 | v0.15.0

- backend として PowerShell をサポート。ネイティブ PowerShell コードを直接生成。
- Zig backend: pathlib native 実装 + 汎用 native re-export 機構 → 18/18 parity 達成。
- Go/Lua fixture parity 改善（第 2 弾）。
- Ruby emitter: fixture parity 改善（Is/IsNot, lambda, str iteration, dunder methods, runtime 拡張）。
- C# emitter: @extern 委譲コード生成 + ビルドパイプライン修正。

## 2026-03-18 | v0.14.0

- 再帰的 union type（tagged union）をサポート。spec-tagged-union.md 策定。
- nominal ADT: parser → EAST3 lowering → C++ backend まで一貫実装。
- Match/case の exhaustiveness check（closed nominal ADT family）。
- 非 C++ backend は nominal ADT lane を fail-closed。

## 2026-03-14〜17

- EAST core モジュール分割（core.py 8000 行 → 20+ ファイルに分解）。
- IR core decomposition: builder, expr, stmt, call metadata, type parser 等を個別モジュールに。
- backend registry selfhost parity 強化。local CI reentry guard。

## 2026-03-11〜13 | v0.13.0

- NES(ファミコン)のエミュレーターを Python + SDL3 で作成。C++ に変換できるよう Pytra 側を改良中。
- Linker 仕様策定（spec-linker.md）。compile / link パイプライン計画。
- 全 backend 共通の smoke テスト基盤整備。`test_py2x_smoke_common.py` を正本化。
- non-C++ backend health gate を family 単位で集約。

## 2026-03-10 | v0.12.0

- Runtime 整理の大工事。C++ generated runtime ヘッダー生成パイプライン整備。
- `src/runtime/cpp/{generated,native}` の責務分離を確立。
- runtime .east ファイルを正本化し、C++ ヘッダーを自動生成する仕組みを構築。

## 2026-03-09 | v0.11.0

- object 境界を見直し。selfhost stage2 parity (pass=18 fail=0) 達成。
- チュートリアル整備（tutorial/README.md, how-to-use.md）。

## 2026-03-08 | v0.10.0

- `@template` を使えるようになった。linked runtime helper 向け v1。
- 各言語の runtime を整備中。Debian 12 parity bootstrap。
- 全 target sample parity の完了条件を定義。

## 2026-03-07 | v0.9.0

- 大規模リファクタリング完了。全言語で再び使えるようになった。
- `@extern` と `@abi` を使えるようになり、変換後のコードを他言語からも呼び出せるようになった。
- selfhost stage1 build + direct .py route が green。

## 2026-03-06 | v0.8.0

- ABI 境界を定義しなおして大規模リファクタリング実施中。
- spec-abi.md 策定（@extern / @abi の固定 ABI 型）。
- C++ 変換器以外は一時的に壊れていた。

## 2026-03-04 | v0.7.0

- 変換対象として PHP を追加。Nim 正式対応作業中。

## 2026-03-02 | v0.6.0

- 変換対象として Scala を追加。

## 2026-03-01 | v0.5.0

- 変換対象として Lua を追加。

## 2026-02-28 | v0.4.0

- 変換対象として Ruby を追加。

## 2026-02-27 | v0.3.0

- EAST（中間表現）を段階処理（EAST1→EAST2→EAST3）へ整理。
- C++ CodeEmitter の大規模分割・縮退。

## 2026-02-25 | v0.2.0

- 全言語（C++, Rust, C#, JS, TS, Go, Java, Kotlin, Swift）について元ソースコードに近い形で出力されるようになった。

## 2026-02-23 | v0.1.0

- Pytra 初版リリース。Python の元ソースコードに極めて近いスタイルで、読みやすい C++ コードを生成できるようになった。
