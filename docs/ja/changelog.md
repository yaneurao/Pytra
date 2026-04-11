<a href="../en/changelog.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# 更新履歴

## 2026-04-10

- **P0-ZIG-CREXC-S4 完了**: Zig / Rust の exception / try / with / raise 処理を CommonRenderer hook 経由で完全共有。言語固有コードの大半を共通化し、emitter の重複ロジックを撤去。
- **Zig toolchain_ 依存解消**: `toolchain_.frontends.runtime_symbol_index` への依存を除去。残り toolchain_ 依存は撲滅完了（Dart / Swift / Julia / Zig 全て解消）。
- **Zig 新規 fixture parity 確認**: with_statement / with_context_manager を含む新規 fixture の Zig parity を確認。
- **Nim parity 完成**: P1-NIM-EMITTER-S5/S6 完了。compile/run parity を確立し、新規 fixture の index エラーを修正。
- **Go type-id helper 依存除去**: P0-GO-TYPEID-CLN-S1~S3 完了。Go emitter から legacy type-id helper 依存を撲滅。
- **Lua emitter guide 違反修正**: P0-LUA-EMITGUIDE-S1~S3 完了。hardcode 除去、mapping-driven lowering への移行。
- **Lua full fixture parity 完了**: P1-LUA-EMITTER-S5 完了。Lua fixture 全件 parity 確認。
- **P3-COPY-ELISION-S4 Lua 実装完了**: `bytes(bytearray)` のコピー省略を Lua runtime で実装。readonly proof をモジュール横断で拡張。png/gif copy elision path 完成。

## 2026-04-09

- **P0-ZIG-CREXC-S4 継続**: Zig / Rust の handler binding / bound exception value builder / slot accessor / with fallback protocol calls を hook 化。Rust with の各種 helper（entry/exit target、exit action、bind cloning、close fallback、protocol call builder、hoist collection、enter/exit metadata helpers 等）を CommonRenderer に移行。
- **Rust panic 系 hook 化**: `panic_any` / panic capture wrapper / panic raise rendering を hook 経由に。
- **Zig block expression helper 共有**: compare block / comprehension block / guarded inline exception block / simple block expr helper を CommonRenderer に集約。

## 2026-04-08

- **全言語 lint 完全クリア達成（0 件）**: 4/4 時点の 697 件から完全解消。18 言語全てが 10/10 PASS。
- **C# / Go / Nim parity 復旧 + stdlib parity 復旧**: metadata-driven lowering への移行、runtime metadata 整合。
- **import binding 共通化**: std / helper symbol imports を mapping.json 経由で解決するよう修正。
- **fixture gaps 解消**: PS1 / Go / Nim の fixture parity gap を閉じる。
- **Zig fixture parity 復旧**: with semantics と整合。
- **P0-ZIG-CREXC S1-S3 起票・着手**: Zig / Rust の例外処理（raise / try / with）を CommonRenderer に押し戻す計画を起票。rs / zig の user-context with、raise/try の shape classification、try 処理を共通化。
- **P0-ZIG-CREXC-S4 開始**: rs / zig の exception style を emit profile で宣言。handler type/body/name access、handler dispatch loop、try match wrapper、string/user handler chain 等を hook 化。
- **Nim emitter の文字列分割回避を除去**: `"po" + "p"`, `"o" + "s"` 等の lint 回避の偽装を撲滅。mapping-driven method lowering に移行。
- **PowerShell emitter guide 整合**: with-metadata と runtime mapping に整合。
- **Rust emitter の literal coupling 除去**: emitter から文字列ハードコードを除去。
- **lint に non-emitter 誤検出除外ロジック追加**: emitter 以外の false positive を lint から除外。

## 2026-04-07

- **lint 149 件 / 14 言語 10/10 PASS 達成**: C++, JS, TS, Dart, Swift, Julia, Zig, Java, Scala, Kotlin, Ruby, Lua, PHP, Nim（ただし Nim のみ 9/10）。4/4 時点の 697 件から大幅削減。
- **PyFile 廃止**: resolver の `open()` が返す架空の型名 `PyFile` を廃止。Python の `io` モジュールに基づく `IOBase` / `TextIOWrapper` / `BufferedWriter` / `BufferedReader` に置き換え。`src/pytra/built_in/io.py` に `@extern class` で型階層を定義。
- **emitter guide §12.7 file I/O 型写像**: `open()` の mode 別 resolved_type、io.py の型階層、emitter/runtime の命名規約を文書化。emitter は型名文字列で分岐してはならない。runtime 実装名も built_in/io.py に揃える。
- **lint に PyFile 検出追加**: `class_name` カテゴリで emitter の `"PyFile"` 参照を検出。`rt:type_id` カテゴリで mapping.json types テーブルの deprecated `PyFile` キーを検出。
- **全言語横断 PyFile coupling 除去**: Java / Swift / Ruby / Lua / C++ / TS / Julia から emitter の PyFile 直参照を除去。
- **Go / Rust / C# / PHP emitter guide 整合**: 各言語で mapping-driven method lowering への移行、stale mapping entries 削除、parity 復旧。
- **Ruby / Lua hardcode 除去 + parity 復旧**: emitter hardcode 削除と stale mapping entries 整理。Ruby / Lua / PHP の parity を復旧。
- **JVM backend 継続**: Java stdlib/sample parity 復旧。Kotlin emitter 完了（sample 18/18 PASS）。
- **TODO 整理**: C++, Swift, Julia, TS, Dart, JVM の完了タスクを archive へ移動。

## 2026-04-06

- **with 文を __enter__ / __exit__ プロトコルで実装**: CommonRenderer にデフォルトの try/finally + hoist 変換を実装。C++ emitter で parity PASS 確認。plan を `p0-with-context-manager.md` に文書化。
- **with fixture 追加**: `with_statement`（`with open()` のファイル I/O）と `with_context_manager`（ユーザー定義 `__enter__` / `__exit__` の呼び出し順序 + 例外安全）。
- **parity check FAIL 時に work dir を保持**: FAIL 時は `[INFO] work dir kept for inspection: <path>` を表示して生成物を残す。PASS 時は従来通り削除。
- **progress summary 再生成バグ修正**: `_maybe_regenerate_progress()` が `backend-progress-fixture.md` の mtime をマーカーに使っていたため、parity 結果更新後に summary が再生成されないケースがあった。専用マーカー `.parity-results/.progress_generated` に変更。
- **pathlib_extended に joinpath 追加**: `Path.joinpath()` の single / multi 引数テストを追加。Julia の mapping-to-east coverage warn を解消。
- **.east* 生成物を git 管理から除去**: `test/include/east1/` の 12 ファイルと `src/runtime/east/` の 1 ファイルを `git rm --cached`。`.gitignore` に `test/include/east1/` を追加。
- **TS/JS shim cleanup 完了**: `py_runtime.ts` / `py_runtime.js` の Python ビルトイン shim（`int=Number` 等）を廃止。emitter が mapping.json 経由で解決するように移行。
- **Dart emitter guide 準拠**: toolchain_ 依存解消。module-prefix hardcode 除去、method lowering / builtin call / range / sorted / ctor を metadata ベースへ移行。With 対応。linked ctor metadata regression test 追加。
- **JVM backend 大幅進展**: Java/Scala/Kotlin の mapping.json 正規化、fixture parity 復旧。Scala/Kotlin emitter を新規実装。Java/Scala の stdlib/sample parity 復旧。Kotlin fixture/stdlib parity 確認。
- **C++ / Swift / Julia / Dart with fixture 対応**: 各言語で `with_statement` fixture の emit/compile/run を通す。
- **P2-*-LINT タスクの方針を全言語で「emitter guide 準拠」に統一**: lint 0 件が目標ではなく、emitter guide に準拠することが目標。

## 2026-04-05

- **containers.py に mut[T] 注釈**: `src/pytra/built_in/containers.py` をコンテナクラスのメソッドシグネチャの正本として定義。resolve が `mut[T]` 注釈を読んで `meta.mutates_receiver: true` を EAST3 に付与。
- **C++ emitter のメソッド名ハードコード解消**: `emitter.py` / `header_gen.py` の mutable メソッド名リストを `meta.mutates_receiver` ベースの判定に置き換え。lint `runtime_symbol` 0 件。
- **C++ mapping.json cleanup**: 14 件の dead エントリを分類・削除。`rt:call_coverage` 0 件。
- **C++ 新規 fixture parity 確認**: `bytes_copy_semantics`, `negative_index_comprehensive`, `callable_optional_none`, `str_find_index`, `eo_extern_opaque_basic`, `math_extended`, `os_glob_extended` で C++ parity PASS。
- **mapping.json FQCN キー統一完了**: 全言語の mapping.json calls キーを完全修飾に統一（`"sin"` → `"pytra.std.math.sin"`）。
- **旧 toolchain リネーム完了**: `toolchain` → `toolchain_`、`toolchain2` → `toolchain`。`toolchain_` は gitignore 化。
- **str_count / sorted_basic / exception_types / float_constructor fixture 追加**: 各種ビルトイン機能のテストカバレッジ強化。

## 2026-04-04

- **emitter lint に Python メソッド名ハードコード検出追加**: `runtime_symbol` カテゴリに `"append"`, `"extend"`, `"pop"`, `"clear"` 等 23 パターンを追加。emitter が `attr == "append"` のようにメソッド名を文字列で判定している箇所を検出。
- **parity check の全件 SKIP → FAIL 修正**: toolchain missing で全ターゲットが SKIP のケースを PASS ではなく FAIL に変更。Kotlin / Scala / PowerShell で false PASS が発生していた問題を解消。
- **pytra-cli.py のデフォルト出力先を work/tmp/ に変更**: `-o` 省略時に入力ファイルと同じディレクトリに east ファイルを出力する問題を修正。`test/fixture/source/` や `test/stdlib/source/` にゴミファイルが散らばる原因を根絶。
- **parity check からの lint 自動実行を廃止**: lint は手動実行（`check_emitter_hardcode_lint.py`）または `run_local_ci.py` でのみ走らせる。parity check は transpile + compile + run に集中。
- **emitter lint 常時 10 カテゴリ**: `--include-runtime` をデフォルト ON に変更し `--skip-runtime` に置き換え。キャッシュ機構を廃止。
- **callable_optional_none fixture 追加**: `callable | None` の is None ガード + invoke を検証。C++ / Rust emitter で optional callable の unwrap を修正。
- **emitter guide §12.6 callable 型写像**: 全言語の callable 型写像と `callable | None` の表現（Zig: `?fn`, Rust: `Option<Box<dyn Fn>>` 等）を文書化。
- **emitter guide §14.1 lint ドキュメント追加**: 10 カテゴリの説明、実行方法、parity check との関係を明記。
- **mapping.json 完全修飾キー計画起票**: bare symbol（`"sin"` 等）がユーザー定義関数と衝突するリスク。`"pytra.std.math.sin"` への統一を計画（P0-MAPPING-FQCN-KEY）。
- **stray east ファイル掃除**: `out/`、`src/include/`、`test/fixture/source/`、`test/stdlib/source/` に散らばった east ファイルを削除。
- **Nim PyObj boxing 方針**: spec-adt.md §3.1 に従い object variants を使うべき。PyObj 退化は禁止。
- **PowerShell emitter isinstance 方針**: emitter が型比較で定数に畳み込むのは optimizer の責務侵害。`-is` 演算子を使うべき。
- **Zig emitter 旧 toolchain 修正を差し戻し**: `src/toolchain/emit/zig/` は変更不可。toolchain2 で修正すること。
- **C++ / Rust 完了タスクをアーカイブ**: CPP-RT-TID-REMOVAL、RS-TYPE-ID-CLEANUP 他 6 件。
- **Go fixture 回帰**: 133→132 (-1) が発生。
- **Julia fixture 大幅進展**: 116→145 (+29)。ただし一時的に regression あり（146→116→145）。
- **Zig fixture/stdlib 完了**: fixture 146/146 PASS、stdlib 進行中。
- **PowerShell stdlib 進展**: 0→6 (+6)。

## 2026-04-03

- **emitter 呼び出し構造の統一**: 共通ランナー `cli_runner.py` を新設。17 言語の cli.py を共通ランナーに移行（Rust のみ独自維持）。`pytra-cli.py` は subprocess で cli.py を呼ぶ形に統一し、emitter 直接 import を廃止。
- **parity check emit ロジック共通化**: `runtime_parity_check_fast.py` の 18 言語 if/elif チェーンを `importlib` 動的 import + 共通ループに置換。新言語追加時に parity check 修正不要に。
- **`resolved_type: "object"` 全面禁止**: EAST3 validator で `resolved_type: "object"` を fail-fast。trait `cls: object` → `@template T`、`dict.get()` 型推論バグを修正し残存 6 ノードをゼロに。
- **IsInstance ノードから PYTRA_TID_* 廃止**: `expected_type_name` を直接持つ形に移行。C++ emitter の逆引きテーブルも削除。全言語の emitter が native isinstance（`x is Type`, `instanceof`, `holds_alternative` 等）を使える。
- **`--east3-opt-level` → `--opt-level` 改名**: negative_index_mode / bounds_check_mode のデフォルトを opt-level で決定する設計に統合。
- **@extern class opaque 型**: spec-opaque-type.md を確定。`class_storage_hint: "opaque"` + `meta.opaque_v1` を compile/resolve で付与。`eo_` prefix の emit-only fixture 規約を新設。
- **builtin_name 廃止**: EAST3 から `builtin_name` フィールド生成を削除。mapping.json キーを `runtime_call` に統一。
- **runtime_call カバレッジ lint**: `check_runtime_call_coverage.py` を新設し `emitter-hardcode-lint.md` に `rt: call_cov` カテゴリとして統合。
- **emitter lint 常時 10 カテゴリ**: `--include-runtime` をデフォルト ON に変更。parity check からの自動 lint 呼び出しは廃止（手動 or run_local_ci のみ）。
- **全件 SKIP を FAIL に**: parity check で toolchain missing により全ターゲットが SKIP のケースを PASS ではなく FAIL に変更。
- **tools/unregistered/ 削除**: 旧ツール 110 ファイルを削除。`run_local_ci.py` から参照を除去。
- **check_todo_priority.py 削除**: 優先順位チェッカーを削除（実用性なし）。
- **Julia / Zig / PowerShell / Swift / Dart backend TODO 新設**: 各言語に toolchain2 emitter 実装タスクを起票。
- **Kotlin / Scala を JVM backend TODO に統合**: `java.md` で一括管理。

## 2026-04-02

- **C++ monostate → optional\<variant\>**: `T1 | T2 | None` の型写像を `std::variant<..., std::monostate>` から `std::optional<std::variant<...>>` に変更。Rust `Option<enum>` と対応統一。
- **C++ bounds check / negative index を EAST optimizer に移管**: 旧 emitter オプション `--negative-index-mode` / `--bounds-check-mode` を optimizer のメタデータ（`subscript_access_v1`）に移管。C++ sample 01 mandelbrot 12.8s → 0.82s。
- **png.py / gif.py の extend 最適化**: `_png_append` / `_gif_append` の append ループを `extend` に変更。全言語の PNG/GIF 生成が高速化。
- **bytes_copy_semantics fixture 追加**: `bytes(bytearray)` のコピーセマンティクス検証。Lua の不正な zero-copy 最適化を検出。
- **negative_index fixture 追加**: `negative_index_comprehensive`（list/str/bytes/bytearray の負数インデックス）、`negative_index_out_of_range`（`a[-100]` の IndexError）。
- **emitter guide §12.4 Optional/union 型写像**: 3 分類と言語別写像ルールを新設。monostate 方式と optional+variant 方式の両方を文書化。
- **emitter guide §12.5 数値 cast → §12.6 callable 型写像**: callable | None の各言語での表現を文書化。
- **spec-adt.md monostate → optional 整合**: 旧 monostate 例を修正、p6-plan に経緯注釈。
- **emitter hardcode lint runtime キャッシュ**: `--include-runtime` 結果を `.parity-results/emitter_lint_runtime.json` に保存し、通常実行で復元。
- **lint total_cats 分母バグ修正**: `len(CATEGORIES)` → `len(mat)` でカテゴリ数の不一致を解消。
- **fixture リネーム**: `any_basic` → `union_basic`、`any_dict_items` → `union_dict_items`、`any_list_mixed` → `union_list_mixed`、`any_none` → `optional_none`。
- **Java / C# 完了タスクをアーカイブ**: Java TYPE-ID-CLEANUP / NEW-FIXTURES / LINT-V2、C# TYPE-ID-CLEANUP。
- **README バッジ順統一**: JVM 3 言語（Java / Scala / Kotlin）を隣接配置。全テーブルの列順を統一。

## 2026-04-01

- **emitter hardcode lint runtime キャッシュ機構**: `--include-runtime` 実行結果をキャッシュし、通常実行で復元する仕組みを追加。
- **正本ファイル変更禁止ルール**: `src/pytra/utils/*.py` / `src/pytra/std/*.py` は言語 backend 担当が変更してはならない旨を spec-agent.md と emitter guide に明記。
- **EAST3 copy elision メタデータ計画**: `bytes(bytearray)` のコピー省略を EAST/linker メタデータで制御する計画を起票。
- **C++ prefix_match lint 修正**: `runtime_paths.py` の `pytra.std.` フォールバックを削除。C++ lint 全 8 カテゴリ 🟩。

## 2026-03-31

- **Ruby / Lua / PHP / Nim backend 担当を新設**: TODO と plans を起票。各言語の emitter 実装 → lint → selfhost のタスクを積んだ。
- **C# emitter selfhost 手前まで完了**: fixture 131/131 + sample 18/18 + stdlib 16/16 PASS。lint 全カテゴリ 0 件。dotnet fallback を parity check に追加。
- **C# / Java emitter 新規実装進行中**: Java は S1/S2 完了。
- **spec-python-compat: bool は int のサブタイプではない**: isinstance(True, int) は Pytra では False。全プリミティブ型は leaf 型。
- **spec-emitter-guide §15 FAQ 拡充**: unsigned right shift（`>>` → `>>>`）、パッケージマネージャ依存禁止、型チェックスキップ禁止、yields_dynamic cast ガイダンスを追加。
- **spec-emitter-guide §13 selfhost parity**: `run_selfhost_parity.py` を正本ツールとして追加。selfhost の完了条件（emit → build → golden → fixture parity → sample parity）を明記。
- **spec-emitter-guide §1.1 禁止事項追加**: `in` 演算子の tuple 要素数ごとの特殊化を禁止。iterable の汎用 contains で処理すること。
- **EAST3 narrowing Cast ノード**: Rust 担当が isinstance narrowing 後に Cast ノードを挿入する EAST3 修正を実施。emitter workaround を削除。
- **EAST tuple unpack バグ修正**: 括弧付き左辺 `(x,y,z)=` / `[x,y,z]=` と comprehension + unpack の 3 パターンを修正。
- **spec-east.md §4.1 Python → EAST ノード変換表**: 代入/unpack、ループ、関数/クロージャ、制御構文、式、クラス、import、コンテナ操作の全カテゴリで変換表を追加。
- **C++ callable 型サポート**: `callable[[Args],Ret]` → `std::function<R(Args...)>` 変換を実装。
- **C++ in/not in の range 算術展開**: `x in range(start, stop, step)` を算術判定式に直接展開。
- **C++ variant 移行計画**: union type を `std::variant` で表現し `object` / box / unbox を廃止する計画を策定。`work/tmp/variant_test.cpp` で基本動作・再帰型・RC共有を実証。Phase 1 (variant 出力) の S1 完了。
- **C++ selfhost S0-S4 完了**: 全モジュール emit 成功、golden 配置。S5 (build) 以降は残。
- **C++ lint 全カテゴリ PASS**: P1-CPP-LINT-CLEANUP 全5件解消。skip_modules から pytra.std. 全 skip を撤廃。
- **C++ g_type_table 撤去**: ControlBlock に deleter ポインタを持たせる設計に変更。fixture 131/131 + sample 18/18 PASS。
- **C++ 整数リテラル冗長キャスト除去**: CommonRenderer に `literal_nowrap_ranges` テーブルを追加。profile 駆動で bare literal / typed wrap を切り替え。
- **Rust in 演算子を iterable 汎用化**: 要素数ごとの `PyContains` を廃止、slice.contains() に統一。
- **EAST3 optimizer に in リテラル展開**: 少数リテラルの `in` を `||` チェーンに展開する pass を追加。
- **Rust 継承 ref 一貫性 + super() 解決**: 基底クラスの ref 昇格、super() の型解決を EAST2/EAST3 で実装。
- **Rust fixture 132/132 + sample 18/18 PASS**: emitter 新規実装、mapping.json、stdlib argparse parity PASS。
- **Rust selfhost mod 構造計画**: flat include! → Rust mod + use 構造への移行を設計。
- **linker に receiver_storage_hint**: peer module のクラス情報を Attribute/Call ノードに付与。
- **pytra-cli.py から C++/Rust emit を subprocess 委譲**: selfhost で不要な言語の emitter が依存グラフに入らなくなった。
- **parity changelog 自動記録**: PASS 件数の変化を progress-preview/changelog.md に自動追記。emitter lint の変化も同じ仕組みで記録。
- **emitter lint に skip_pure_python カテゴリ**: pure Python モジュールの skip を検出。cli.py を除外リストに追加。
- **fixture 追加**: tuple_unpack_variants, typed_container_access, in_membership_iterable, callable_higher_order, object_container_access。
- **spec-setup.md 新設**: clone 直後の golden / runtime east 生成手順を一箇所にまとめた。
- **spec-adt.md 新設**: union type の言語別変換方針。17言語の変換表、再帰型の扱い、RC 管理ルール、object 退化全面禁止。
- **出力先整理**: sample → sample-preview、progress → progress-preview、runtime east を gitignore 化。
- **自動生成間隔変更**: progress 3分、emitter lint 10分、selfhost 15分、benchmark 3分。
- **TODO archive 整理**: 日付別ファイル統合（20260330-go.md, 20260330-p10reorg.md, 20260321b.md を統合）。
- **P7-GO-SELFHOST-RUNTIME 起票**: Go selfhost バイナリの実稼働に必要な3つのギャップを特定。
- **全言語 selfhost TODO に parity ステップ追加**: `run_selfhost_parity.py` の fixture/sample parity を全言語の TODO に積んだ。
- **Dockerfile に TypeScript compiler 追加**: `npm install -g typescript`。npm 依存排除（tsc + node）。

## 2026-03-30

- **Go fixture 全件 PASS**: Go emitter の container 既定表現を参照型ラッパー（`*PyList[T]`, `*PyDict[K,V]`, `*PySet[T]`）に統一。fixture 全 147 件 + stdlib 16/16 PASS。
- **Rust emitter fixture 132/132 PASS**: arg_usage による mut 制御、narrowing workaround。
- **TypeScript emitter S5〜S7 完了**: fixture 146/146、sample 18/18、JS 147/147 PASS。ESM 移行、PNG エンコーダをトランスパイル対象に変更。
- **C++ emitter P3-CR-CPP 全完了**: S1〜S8 全完了。isinstance 一本化（S6）、rc_from_value 統一（S7）、予約語エスケープ（S8）。
- **runtime_parity_check 高速版**: transpile 段を toolchain2 API のインメモリ呼び出しに置き換え。`--category` オプション追加。
- **parity 結果の自動蓄積 + 進捗ページ自動生成**: `.parity-results/` に結果蓄積、`gen_backend_progress.py` で fixture/sample/stdlib/selfhost/emitter lint の5マトリクス + サマリを日英同時生成。
- **stdlib テスト分離**: `test/stdlib/source/py/<module>/` にモジュール別テストを配置。parity check に `--case-root stdlib` 追加。
- **mapping.json に types テーブル追加**: 型写像を mapping.json に統合。`CodeEmitter.resolve_type()` 共通 API。
- **emitter ハードコード違反チェッカー**: 7カテゴリ（module_name, runtime_symbol, target_const, prefix_match, class_name, Python_syntax, type_id）の grep ベース検出。
- **TODO 領域別分割**: cpp/go/rust/ts/cs/java/infra に分離。P0 ブロッカールール撤去。
- **golden ファイルを git 追跡から除外**: ~400MB の JSON を gitignore。`regenerate_golden.py` で再生成。
- **spec-runtime-decorator 拡張**: extern_var 追加、パイプライン解決フロー、早見表。
- **sample benchmark 自動計測**: parity check で elapsed_sec を自動記録、sample/README の表を自動更新。
- **integer_promotion fixture 追加**: 全整数型の widening / sign extension / mixed arithmetic テスト。
- **pytra.std.env 追加**: `env.target` コンパイル時定数。mapping.json で言語名に置換。
- **gc_reassign fixture 修正**: `__del__` を pass に変更（GC タイミング依存の stdout を排除）。

## 2026-03-29

- **Go fixture 全件 PASS**: Go emitter の container 既定表現を参照型ラッパー（`*PyList[T]`, `*PyDict[K,V]`, `*PySet[T]`）に統一（P1-GO-CONTAINER-WRAPPER S1〜S3）。fixture 全 147 件 + stdlib 16/16 PASS。
- **Rust emitter 新規実装 (P7-RS-EMITTER)**: `src/toolchain2/emit/rs/` に CommonRenderer + override 構成で Rust emitter を新規実装。mapping.json 作成。fixture emit 成功。
- **TypeScript emitter 新規実装 (P8-TS-EMITTER)**: `src/toolchain2/emit/ts/` に TS emitter を新規実装。JS は TS emitter の型注釈抑制フラグで対応する設計。mapping.json 作成。fixture 142 件 emit 成功。
- **C++ emitter parity 改善 (P3-CR-CPP)**: 予約語エスケープ（`_safe_cpp_ident`）、optional dict.get、float/container printing を修正。oop 18/18, typing 22/22, signature 13/13 PASS。
- **C++ runtime 例外安全性 (P3-CR-CPP-S4)**: py_types.h の `Object<void>` コンストラクタ5箇所を `make_unique` + `release` パターンに書き換え。
- **runtime_parity_check 高速版**: `runtime_parity_check_fast.py` を新設。transpile 段を toolchain2 Python API のインメモリ呼び出しに置き換え、プロセス起動 + disk I/O を省略。
- **runtime_parity_check に `--category` オプション追加**: fixture サブディレクトリ単位（oop, control, typing 等）で部分実行可能に。
- **parity 結果の自動蓄積 + 進捗ページ自動生成 (P5-BACKEND-PROGRESS)**: parity check 実行時に `.parity-results/` へ結果を自動蓄積（タイムスタンプ付きマージ）。`tools/gen/gen_backend_progress.py` で fixture/sample/selfhost の3マトリクスを日英同時生成。
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

- **パイプライン再設計完了**: parse → resolve → compile → optimize → link → emit の 6 段パイプライン（`pytra-cli`）が全段動作。toolchain2 は toolchain に一切依存しない独立実装。
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
- **pytra-cli**: 新 CLI。-parse/-resolve/-compile/-optimize/-link/-emit/-build サブコマンド。
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
