# TODO

<a href="../docs/todo-old.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

## 2026-02-21 完了: selfhost 直変換の型正規化回帰修正

1. [x] selfhost 直変換で `list[int]` が `list<int>` と出力される回帰を修正した。
   - [x] `src/pytra/compiler/east_parts/core.py` の `_sh_ann_to_type` から正規表現依存を除去し、汎用のブラケット分解ロジックへ置換した。
   - [x] `src/runtime/cpp/pytra/compiler/east_parts/core.cpp` の同ロジックも同期修正した（`re` マッチ不要化）。
   - [x] `tools/prepare_selfhost_source.py` で `_normalize_param_annotation` の selfhost 専用 no-op 置換を削除し、本実装を使うようにした。
2. [x] selfhost 差分検証を green 化した。
   - [x] `python3 tools/check_selfhost_cpp_diff.py --selfhost-driver direct` で `mismatches=0` を確認。
3. [x] selfhost E2E 検証を追加・確認した。
   - [x] `tools/verify_selfhost_end_to_end.py` を追加（`.py -> selfhost変換 -> C++コンパイル -> 実行 -> Python標準出力比較`）。
   - [x] `python3 tools/verify_selfhost_end_to_end.py --skip-build` で `failures=0` を確認。


## 2026-02-21 完了: py2cpp Call 分岐の hook 移管

1. [x] `dict.get/list.* / set.*` 呼び出し解決を `src/py2cpp.py` の直書き分岐から `src/hooks/cpp/hooks/cpp_hooks.py` の runtime-call hook 側へ移し、`py2cpp.py` のハードコードを削減した。

## 2026-02-21 完了: パススルー記法

1. [x] トランスパイル時パススルー記法（`# Pytra::cpp` / `# Pytra::pass`）の仕様化と最小実装を完了した。
   - [x] 仕様: 適用位置、インデント維持、複数ブロック連結、既存 docstring コメント変換との優先順位を `docs-jp/spec-east.md` に明記。
   - [x] 実装: EAST 保持形式（`leading_trivia` の comment text 利用）を定義し、C++ エミッタでそのまま展開できる最小経路を追加した。
   - [x] 受け入れ条件: 最小 fixture（`test/fixtures/core/pass_through_comment.py`）で Python 実行に影響を与えず、C++ 出力に意図した行が入ることを unit test で確認。

## 2026-02-20 完了: 最優先（即時）

1. [x] 未使用シンボル削除を「1シンボルずつ」進めた。
   - [x] 対象リスト作成: `src/py2cpp.py` の候補として `_default_cpp_module_attr_call_map`, `_DEFAULT_CPP_MODULE_ATTR_CALL_MAP`, `_deep_copy_str_map`, `CPP_RESERVED_WORDS`, `_copy_str_map`, `_map_get_str`、`src/runtime/cpp/pytra/built_in/py_runtime.h` の候補として `py_runtime_stderr`, `py_runtime_stdout`, `py_runtime_path`, `py_runtime_set_path(::std::any)`, `py_runtime_set_path(list<str>)`, `py_runtime_path_storage`, `py_u8_vector`, `py_u8_matrix`, `py_runtime_set_argv(::std::any)`, `py_argparse_argument_parser` を抽出。
   - [x] 参照確認: `rg` で上記候補の参照を確認し、「未使用（空マップ生成専用 / 参照ゼロ定数 / 参照ゼロ関数）」「薄いラッパ（`dict(...)` / `dict.get` へ置換可能）」へ分類。
   - [x] 1件削除: `_default_cpp_module_attr_call_map` / `_DEFAULT_CPP_MODULE_ATTR_CALL_MAP` / `_deep_copy_str_map` / `CPP_RESERVED_WORDS` / `_copy_str_map` / `_map_get_str` / `py_runtime_stderr` / `py_runtime_stdout` / `py_runtime_path` / `py_runtime_set_path(::std::any)` / `py_runtime_set_path(list<str>)` / `py_runtime_path_storage` / `py_u8_vector` / `py_u8_matrix` / `py_runtime_set_argv(::std::any)` / `py_argparse_argument_parser` を削除し、`load_cpp_module_attr_call_map` と `load_cpp_*_ops` を簡素化。
   - [x] 1件検証: `python3 tools/check_py2cpp_transpile.py` を実行し、`checked=103 ok=103 fail=0 skipped=5` を確認。
   - [x] 1件コミット: 1シンボル削除ごとに独立コミットする（後戻り容易化）。: `a89f5a8`, `6d8261c`, `36ab6df`, `f5845ac`, `65cd733`, `938d69b`, `c4e5619`, `8a50a1d`, `e3ea881`, `f34f2d8`, `196f22e`, `1ebd94a`, `defb1f4`, `c391464`
   - [x] 影響反映: public API を消した場合は `docs-jp/spec-runtime.md` / `docs-jp/spec-dev.md` の該当記述を同コミットで更新する。: 該当 API 記述が現行ドキュメントに存在しないことを確認済み（`rg` 検索）。
2. [x] `src/runtime/cpp/pytra/built_in/py_runtime.h` の class / 関数に目的説明コメントを追加した。
   - [x] object ラッパクラス群、変換ヘルパ群、os.path/glob、dict 取得、演算互換、runtime 状態管理の各セクションに C++ コメントを追加済み。

## 2026-02-20 完了: spec-import 反映（最優先）

1. [x] import 構文の第一段階サポート範囲を実装と一致させる。
   - [x] 対応: `import M`, `import M as A`, `from M import S`, `from M import S as A`。
   - [x] 未対応: `from M import *`, 相対 import（`from .m import x`）を `input_invalid`（`kind=unsupported_import_form`）で統一する。
2. [x] `ImportBinding` を import 情報の正本として導入・統一する。
   - [x] `module_id`, `export_name`, `local_name`, `binding_kind`, `source_file`, `source_line` を保持する。
   - [x] `meta.import_modules` / `meta.import_symbols` は `ImportBinding` から導出するだけにする。
3. [x] モジュール解決を `resolve_module_name(raw_name, root_dir)` に一本化する。
   - [x] `pytra.*` を予約名前空間として最優先解決する。
   - [x] `pytra.py` / `pytra/__init__.py` の衝突は `reserved_conflict` として `input_invalid` にする。
   - [x] 未解決は `missing_module` として `input_invalid` にする。
4. [x] `ExportTable` を追加し `from M import S` の事前検証を実装する。
   - [x] 公開対象: トップレベル `FunctionDef`, `ClassDef`, `Assign/AnnAssign(Name)`。
   - [x] 未定義シンボル import は `missing_symbol` として `input_invalid` にする。
5. [x] 名前解決優先順位を固定し、同順位衝突を `duplicate_binding` で失敗させる。
   - [x] 優先順位: ローカル変数 > 関数引数 > クラスメンバ > import symbol alias > import module alias > 組み込み。
   - [x] `from M import S` のみ時に `M.T` を参照した場合は未束縛として `input_invalid` にする。
6. [x] C++ 生成規則を「常に完全修飾名へ正規化」に統一する。
   - [x] `from foo.bar import add as plus` を `foo.bar` モジュール include + `ns_of(foo.bar)::add` 呼び出しへ落とす。
   - [x] include は `ImportBinding` 由来で重複排除 + 安定ソートする。
7. [x] single-file / multi-file で同一 `module_namespace_map` を使用し、解決結果差分を禁止する。
   - [x] forward 宣言/呼び出し解決ともに同じ map を使う。
   - [x] `--dump-deps` と通常変換で依存解決結果が一致することをテストで保証する。
8. [x] import エラーの詳細フォーマットを統一する。
   - [x] `input_invalid` の detail に `kind`, `file`, `import` を必ず含める。
   - [x] `kind`: `missing_module | missing_symbol | duplicate_binding | reserved_conflict | unsupported_import_form`。
9. [x] import 最小受け入れテストマトリクスを追加する。
   - [x] 正常: 4形式（`import` / `import as` / `from import` / `from import as`）。
   - [x] 異常: `import *`, 相対 import, モジュール未存在, シンボル未存在, 同名 alias 衝突。
   - [x] single/multi と `--dump-deps` で同じ解決結果になることを自動検証する。
10. [x] 言語非依存 import IR の土台を追加する（後続 backend 共通化）。
   - [x] `QualifiedSymbolRef(module_id, symbol, local_name)` を定義し、backend 手前で `Name(alias)` を正規化する。
   - [x] backend には「解釈済み import 情報のみ」を渡し、言語側で import 意味解釈しない設計にする。

## 2026-02-20 完了: todo2 準拠タスク

1. [x] `docs-jp/todo2.md` の MUST を継続的に満たす（当時の最新版）。
   - [x] `math` は `py2cpp.py` の一般ロジックで生成し、`math` 固有分岐を `py2cpp.py` / profile / tools に追加しない。
   - [x] `src/pytra/std/math.py` -> `src/runtime/cpp/pytra/std/math.h/.cpp` の生成を `--emit-runtime-cpp` で確認済み。
   - [x] `test/fixtures/stdlib/math_extended.py` の Python/C++ 実行一致を再確認済み。
   - [x] `src/py2cpp.py` の `_default_cpp_module_attr_call_map` を空化し、`module.attr` は import 由来の汎用 namespace 解決へ統一した。
   - [x] `src/py2cpp.py` から `png`/`gif` 固有分岐（専用 bridge 生成）を削除し、`--emit-runtime-cpp` の汎用生成フローへ統一した。
   - [x] `src/py2cpp.py` から `math`/`png`/`gif` のモジュール名文字列直書きを除去した。
   - [x] `src/pytra/std/sys.py` / `src/pytra/std/typing.py` を self_hosted で変換可能な形へ修正し、`--emit-runtime-cpp` 再生成後に `sys_extended` / `typing_extended` / `any_basic_runtime` を再確認済み。
2. [x] `src/pytra/utils/std` と `src/pytra/std` の二重管理を解消する（`src/pytra/std` に統一）。
3. [x] `src/runtime/cpp/pytra/built_in/` の位置づけ（Python 組み込み型の C++ 実装）をドキュメントへ明記する。
4. [x] `src/runtime/cpp/pytra/built_in/containers.h` の分割（`str/path/list/dict/set`）を完了する。
5. [x] `py_isdigit` / `py_isalpha` を `py_runtime.h` 直下から移し、`src/runtime/cpp/pytra/built_in/str.h` 側で提供する。
6. [x] `src/pytra/utils/east.py` の要否を判断し、不要なら削除または配置見直しを行う。
7. [x] 空ディレクトリだった `src/pytra/utils/std/` を削除する。
8. [x] `src/pytra/runtime/cpp/` を `src/hooks/cpp/` へ移動する（import パス・ドキュメント・selfhost 影響を含めて整理）。
9. [x] `src/runtime/cpp/base/` を `src/runtime/cpp/pytra/built_in/` へ改名し、参照・ドキュメントを移行する。
10. [x] `src/pytra/utils/*.py` の `--emit-runtime-cpp` 生成先を `src/runtime/cpp/pytra/utils/` に統一する（`src/runtime/cpp/pytra/std/` と同じ体系）。
    - [x] `src/pytra/utils/{png,gif,assertions}.py --emit-runtime-cpp` で `src/runtime/cpp/pytra/utils/*.h/.cpp` へ生成されることを確認。
    - [x] `python3 tools/check_py2cpp_transpile.py`（`checked=103 ok=103 fail=0 skipped=5`）を再確認。
    - [x] `python3 tools/verify_image_runtime_parity.py` が `True` を返すことを確認。
11. [x] `src/runtime/cpp/py_runtime.h` から `pytra/std/math.h`, `pytra/utils/png.h`, `pytra/utils/gif.h` の直接 include を外し、import されたモジュール側でのみ include する設計へ移行する。
    - [x] `py_runtime.h` の最小依存（built_in 基盤のみ）を定義する。
    - [x] `src/py2cpp.py` 側で `math/png/gif` の include が必要ケースでのみ出力されることを確認する。
12. [x] `src/runtime/cpp/py_runtime.h` の配置を見直し、`src/runtime/cpp/pytra/built_in/` 配下へ移す。
    - [x] 既存 include パス互換（必要なら薄い forwarding header）を含めて移行方針を決める。
    - [x] `src/py2cpp.py` のヘッダ参照とテスト/ドキュメントの参照先を統一する。
    - [x] 互換 forwarding header は廃止し、`src/runtime/cpp/py_runtime.h` を削除した。
13. [x] `py_runtime.h` にある `py_sys_*` 群を `src/runtime/cpp/pytra/std/sys.h/.cpp` へ移管する。
    - [x] `py_runtime.h` から `py_sys_*` を削除し、`pytra.std.sys` import 時の `pytra::std::sys::*` へ統一した。
    - [x] `test/fixtures/stdlib/sys_extended.py` と import 系 fixture で回帰を確認する。
14. [x] `py_runtime.h` にある `perf_counter` を `src/runtime/cpp/pytra/std/time.h/.cpp` へ移管する。
    - [x] `py_runtime.h` 直下から `perf_counter` を削除する。
    - [x] `pytra.std.time` 経由のみで `perf_counter` を解決できることを確認する。

## 2026-02-20 完了: import 解決優先キュー

1. [x] import 解決フェーズを最優先で完了した（`selfhost` より先）。
   - [x] `import` / `from ... import ...` の収集と依存グラフ生成（`--dump-deps`）を実装済み。
   - [x] `pytra.*` とユーザーモジュールの探索パス解決、重複・循環検出を実装済み。
   - [x] `pytra.runtime.png/gif` について、hook 側の短縮名（`png_helper`/`gif_helper`）依存を削除し、正規モジュール名ベースへ統一した。
   - [x] `pytra.std.*` / `pytra.runtime.*` の include 解決を 1 対 1 規則ベースへ整理し、現行 C++ ランタイム実体があるモジュールのみ include するよう調整した。
   - [x] `module.attr` / `from-import symbol` 解決で、`pytra.*` モジュールに対する短縮名フォールバック（末尾要素一致）を使わないようにした。
   - [x] `pytra.std.math` を runtime-call map に明示し、短縮名フォールバックに依存しない解決へ寄せた。
   - [x] `from XXX import YYY` の解決を runtime include / 呼び出し解決まで一貫させ、hook 側の暫定名寄せ分岐を削除した。
   - [x] runtime 側 include パス（`pytra/std/*`, `pytra/runtime/*`）と import 正規化ルールを完全同期した。
   - [x] 複数ファイル構成で `sample/py` の import ケースを通し、`tools/check_py2cpp_transpile.py` をゲート化した（`--check-multi-file-imports`）。
   - [x] `cpp_hooks.py` から `owner_mod == "pytra.runtime.png"` などのライブラリ決め打ち分岐を削除し、`runtime_call` + `module_attr_call_map` ベース解決へ統一した。
   - [x] `cpp_hooks.py` から `write_rgb_png/save_gif` 専用レンダ関数（`_render_write_rgb_png`, `_render_save_gif`）を削除し、`py_runtime.h` 側ラッパ（`py_png_write_rgb_png`, `py_gif_save_gif`）へ移管した。

## 2026-02-19 完了: 複数ファイル構成（import 強化）先行キュー

1. [x] 「複数ファイル構成（最終ゴール）」の依存解決フェーズを先行着手した。
2. [x] `import` / `from ... import ...` の依存グラフ生成を実装した。
   - [x] `--dump-deps` で `modules/symbols/graph` を出力。
3. [x] `pytra.*` とユーザーモジュール探索パスの解決・衝突規則を実装した。
   - [x] `pytra` 名前空間予約、未解決ユーザーモジュール、循環 import を `input_invalid` で早期検出。
4. [x] モジュール単位 EAST と複数ファイル出力（`.h/.cpp`）へ移行した。

## 2026-02-19 完了: 互換オプション（出力形態）

1. [x] 既定を複数ファイル出力にする。
   - [x] `--multi-file` を既定化（`-o *.cpp` は互換のため暗黙 `--single-file`）。
2. [x] `--single-file` で従来の単一 `.cpp` へ束ねるモードを提供する。
   - [x] `--single-file` / `--multi-file` を実装。
3. [x] 既存ユーザー向け移行手順を `docs-jp/how-to-use.md` に追記する。

## 2026-02-19 完了: C++ 複数ファイル出力

1. [x] モジュールごとに `.h/.cpp` を生成し、宣言/定義を分離する。
   - [x] `--multi-file` で module ごとの `.h/.cpp` と `manifest.json` を出力。
   - [x] 生成先ディレクトリ構造（`out/include`, `out/src`）を固定。
   - [x] シンボル重複回避の命名規則（相対パス由来ラベル + sanitize）を実装。
2. [x] main モジュールから依存モジュールを include/link できるようにする。
   - [x] ユーザーモジュール呼び出しを `namespace::symbol` へ変換し、前方宣言を補完。
3. [x] ランタイム include/namespace の重複を除去する。
   - [x] `pytra_multi_prelude.h` を生成し、各 `.cpp` の runtime include を共通化。

## 2026-02-19 完了: 複数ファイル出力のビルド・実行検証

1. [x] 複数ファイル生成物を一括コンパイルするスクリプトを追加する。
   - [x] `tools/build_multi_cpp.py` を追加。
2. [x] `sample/py` 全件で Python 実行結果との一致確認を自動化する。
   - [x] `tools/verify_multi_file_outputs.py` を追加し、`sample/py` 16件で `OK=16 NG=0` を確認。
3. [x] 画像生成ケースをバイナリ一致で検証する。
   - [x] `tools/verify_multi_file_outputs.py` で `output:` 指定ファイルのバイト一致を検証。

## 2026-02-19 完了: モジュール単位 EAST 準備

1. [x] 入口ファイル + 依存モジュールを個別に EAST 化する。
   - [x] `build_module_east_map(entry_path)` を追加。
2. [x] シンボル解決情報（公開関数/クラス、import alias）をモジュールメタへ保持する。
   - [x] `build_module_symbol_index(...)` を追加。
3. [x] モジュール間で必要な型情報を共有する最小スキーマを定義する。
   - [x] `build_module_type_schema(...)` を追加。

## 2026-02-19 完了: `runtime/cpp/pytra/std/*` 自動生成移行

1. [x] `runtime/cpp/pytra/std/*` を自動生成へ移行する（`math` を含む）。
   - [x] 生成スクリプトを `pytra.runtime` だけでなく `pytra.std` モジュールにも対応させる（まず `math` から対応）。
   - [x] `src/runtime/cpp/pytra/std/math.h/.cpp` を自動生成物へ置換し、手書き実装を廃止する。
   - [x] `pathlib/time/dataclasses/sys` も同様に生成対象へ揃える。
   - [x] `python3 tools/generate_cpp_pylib_runtime.py --check` で `std/runtime` 両方の stale チェックが通ることを確認。
   - [x] 生成後に `tools/check_py2cpp_transpile.py` と `tools/verify_sample_outputs.py` で回帰確認する。
     - [x] `tools/check_py2cpp_transpile.py` は pass（`checked=103 ok=103 fail=0 skipped=5`）。
     - [x] `tools/verify_sample_outputs.py` は pass（`OK=16 NG=0`）。

## 2026-02-19-20 完了: py2cpp import + runtime 配置同期

1. [x] import と include の 1対1 対応を `py2cpp.py` に実装する（最優先）。
   - [x] `import pytra.std.X` -> `#include "pytra/std/X.h"` を出力する。
   - [x] `import pytra.runtime.X` -> `#include "pytra/runtime/X.h"` を出力する。
   - [x] `from pytra.std.X import f` / `from pytra.runtime.X import f` を同じ規則で解決する。
   - [x] 既存の `pylib.*` 直参照分岐を段階削除し、上記規則へ統一する。
2. [x] C++ ランタイム配置を include 規約に合わせる。
   - [x] `src/runtime/cpp/pytra/std/*.h|*.cpp` を配置する。
   - [x] `src/runtime/cpp/pytra/runtime/*.h|*.cpp` を配置する。
   - [x] 実装・ビルド導線の `src/runtime/cpp/std/*` / `src/runtime/cpp/pylib/*` 参照を `pytra/*` 側へ移行する。
3. [x] import 解決機能の回帰テストを追加・強化する。
   - [x] `test/unit/test_py2cpp_features.py` に `pytra.std` / `pytra.runtime` import の include 生成テストを追加する。
   - [x] `test/fixtures/stdlib` に `import pytra.std.*` / `from pytra.std.* import ...` のケースを追加する。
   - [x] `test/fixtures/stdlib` に `import pytra.runtime.*` / `from pytra.runtime.* import ...` のケースを追加する。
4. [x] ドキュメントと実装の差分を同期する。
   - [x] `docs-jp/how-to-use.md` / `docs-jp/spec-dev.md` を同期する。
   - [x] 完了項目を `docs-jp/todo-old.md` へ移す。

## 2026-02-19 移管: TODO整理（完了セクション）

## 2026-02-19 移管: CodeEmitter 化（完了小セクション）

作業ルール（step by step）:
- [x] `CodeEmitter` の変更は段階適用し、各ステップで `test/fixtures` の変換可否を確認してから次へ進む。: `tools/check_py2cpp_transpile.py` を追加
- [x] 同じく各ステップで `sample/py` 全件の変換可否を確認してから次へ進む。: `tools/check_py2cpp_transpile.py` を追加
- [x] 回帰が出た場合は次ステップへ進まず、その場で修正してから再確認する。

1. [x] `BaseEmitter` を `CodeEmitter` へ改名し、段階移行する。
   - [x] `src/common/base_emitter.py` を `src/pylib/east_parts/code_emitter.py` へ移動する。
   - [x] 互換エイリアス `BaseEmitter = CodeEmitter` を暫定で残す。
   - [x] `src/py2cpp.py` / テスト / ドキュメント参照を `CodeEmitter` 表記へ置換する。
2. [x] 言語差分を `LanguageProfile` JSON に切り出す。
   - [x] `docs-jp/spec-language-profile.md` で JSON スキーマ（v1）とロード順序を確定する。
   - [x] 型マップ（EAST 型 -> ターゲット型）を JSON で定義する。
   - [x] 演算子マップ・予約語・識別子リネーム規則を JSON で定義する。
   - [x] 組み込み関数/メソッドの runtime call map を JSON へ統合する。
3. [x] `CodeEmitter` へ `profile` 注入を実装する。
   - [x] `CodeEmitter(profile, hooks)` の初期化 API を追加する。
   - [x] `cpp_type` / call 解決 / 文テンプレートを profile 参照へ置換する。
   - [x] `src/py2cpp.py` の直書きマップを profile ロードに置換する。
5. [x] 回帰確認を追加する。
   - [x] `test/unit/test_code_emitter.py` を追加し、profile/hook の境界を検証する。
   - [x] `test/unit/test_py2cpp_features.py` と `test/unit/test_image_runtime_parity.py` を回帰する。
   - [x] selfhost 検証フロー（`tools/prepare_selfhost_source.py`）に新構造を反映する。

1. [x] selfhost 入力経路の段階回復
   - [x] `load_east` の `.json` 経路を selfhost で通す（`.py` は未実装のまま維持）。
   - [x] `.json` 経路で `test/fixtures/core/add.py` 由来 EAST を selfhost 変換できることを確認する。: `/tmp/add.east.json -> /tmp/add.selfhost.cpp` 生成成功
   - [x] `.json` 経路でのエラー分類（`input_invalid` / `not_implemented`）を固定する。: `.py` 入力は `not_implemented`、`.json` 解析失敗は `input_invalid`

0.5 [x] `test/fixtures/stdlib` compile-fail 7件を順次解消する（1件ずつ green 化）
   - [x] 現状固定: `math/os_glob/pathlib/sys/typing` は pass、`argparse/dataclasses/enum/json/re` は compile fail。
   - [x] 共通修正A: `pytra.std.*` モジュール参照が C++ 側で未解決になる経路を塞ぐ（`module.symbol` を必ず runtime 呼び出しへ lower）。
   - [x] 共通修正B: `std::any` へ退化した値に対するメソッド呼び出し生成（`obj.method(...)`）を禁止し、型付き受け口へ寄せる。
   - [x] 共通修正C: `py_assert_stdout` 依存の古い fixture 形式を現行の assertions 形式に統一する。
   - [x] `json_extended` を最優先で修正する。
     - [x] `json.loads/dumps` が `pytra.std.json` 経由で解決されることを確認する。
     - [x] `dict/list` 返却値への添字アクセスが `std::any` 退化しないようにする。
   - [x] `sys_extended` を修正する。
     - [x] `sys.argv` 参照を runtime 側アクセサへ固定する。
     - [x] `_case_main/main` 呼び出し不整合を除去する。
   - [x] `typing_extended` を修正する。
     - [x] `typing.Any` 等のシンボル参照を「実行時 no-op な型情報」として安全に lower する。
   - [x] `re_extended` を修正する。
     - [x] `re.match/search/sub/split` と match object の `group` 呼び出しを型付きで出力する。
   - [x] `argparse_extended` を修正する。
     - [x] `ArgumentParser` インスタンスが `std::any` 退化しない生成経路へ変更する。
     - [x] `add_argument/parse_args` の戻り値（namespace）アクセスを型付きで通す。
   - [x] `dataclasses_extended` を修正する。
     - [x] `repr` / 比較演算 / 例外継承周辺の不足を埋める。
   - [x] `enum_extended` を修正する。
     - [x] `IntFlag` の演算（`|`, `&`）で `std::any` 退化しないようにする。
   - [x] ゲート: 各ケース修正ごとに以下を実施する。
     - [x] `PYTHONPATH=src python3 test/fixtures/stdlib/<case>.py`
     - [x] `python3 src/py2cpp.py test/fixtures/stdlib/<case>.py -o /tmp/<case>.cpp`
     - [x] `g++` で runtime をリンクして実行し、Python 出力と一致確認
   - [x] 受け入れ条件: `test/fixtures/stdlib/*.py` が 10/10 で compile-run 一致。

0. [x] `runtime/cpp/pylib` を完全自動生成へ移行する（手書きラッパ/手書きヘッダ廃止）
   - [x] 方針確定: `src/runtime/cpp/pylib/*.h` / `*.cpp` を手書き管理しない構成へ変更する。
   - [x] `src/pytra/runtime/png.py` / `src/pytra/runtime/gif.py` から、C++ 側で直接 include/link 可能な成果物（宣言 + 定義）を生成する。
   - [x] 生成結果の公開シンボル（`pytra::pylib::png::*`, `pytra::pylib::gif::*`）を固定し、`py_runtime.h` 側の include を生成物へ切替える。
   - [x] 現在の手書き `src/runtime/cpp/pylib/png.h`, `src/runtime/cpp/pylib/png.cpp`, `src/runtime/cpp/pylib/gif.h`, `src/runtime/cpp/pylib/gif.cpp` を削除する。
   - [x] 生成スクリプト `tools/generate_cpp_pylib_runtime.py` を「ヘッダ/実装の両方を出力する」仕様へ拡張する。
   - [x] `tools/build_selfhost.py` / `tools/run_local_ci.py` / `tools/verify_*` の参照先を新生成物構成へ更新する。
   - [x] 受け入れ条件:
     - [x] `python3 tools/generate_cpp_pylib_runtime.py --check` が pass。
     - [x] `python3 tools/check_py2cpp_transpile.py` が pass。
     - [x] `python3 tools/build_selfhost.py` が pass。
     - [x] `python3 tools/verify_sample_outputs.py` が pass。: 2026-02-19 再計測で `SUMMARY OK=16 NG=0`
     - [x] `python3 tools/verify_image_runtime_parity.py` が pass。

4. [x] ローカル CI 相当手順の固定化
   - [x] 回帰コマンド群（transpile/feature/selfhost build/selfhost diff）を1コマンド実行できるスクリプト化。: `tools/run_local_ci.py`
   - [x] `docs-jp/how-to-use.md` か `docs-jp/spec-codex.md` に実行手順を追記。: `docs-jp/spec-codex.md` へ追記
   - [x] 上記スクリプトを日次作業のデフォルトゲートとして運用する。: `docs-jp/spec-codex.md` に運用ルール追記済み

5. [x] `unit` と `fixtures/stdlib` の同値性を揃える
   - [x] `argparse` / `dataclasses` / `enum` / `re` / `sys` / `typing` の `fixtures/stdlib/*_extended.py` を追加する。
   - [x] 既存 C++ ランタイムで実行可能な `math` / `pathlib` を `test/unit/test_py2cpp_features.py` の runtime 回帰に追加する。
   - [x] `argparse` / `dataclasses` / `enum` / `re` / `sys` / `typing` の compile-run 失敗要因を分解する。
     - [x] 共通: `pylib.*` モジュール import の C++ 側ランタイム接続が未実装（`argparse/re/sys/typing`）。
     - [x] `dataclasses`: `Exception` 継承/`repr`/rc 比較などの未対応が残る。
     - [x] `enum`: `IntFlag` 合成値の型退化（`std::any`）による演算子不整合が残る。
   - [x] 未対応モジュールを順に C++ runtime 接続する（`json -> os/glob -> argparse -> sys/typing -> re -> dataclasses -> enum`）。
     - [x] `json`:
       - [x] `fixtures/stdlib/json_extended.py` を単体 compile-run で通し、`json.loads/dumps` の最低限 API を固定する。
       - [x] `test/unit/test_py2cpp_features.py` に `json_extended` runtime 回帰を追加する。: `test_json_extended_runtime`
    - [x] `os/glob`:
      - [x] `fixtures/stdlib/os_glob_extended.py` を compile-run で通す。
      - [x] `os.path.join/splitext/dirname/basename/exists` と `glob.glob` の呼び出し解決を点検する。
      - [x] `test/unit/test_py2cpp_features.py` に `os_glob_extended` runtime 回帰を追加する。
     - [x] `argparse/sys/typing/re/dataclasses/enum`:
       - [x] 1モジュールずつ compile-run 可否を確認し、失敗要因を個別タスクへ分解する。
       - [x] 各モジュールが通るたびに `*_extended.py` を runtime 回帰へ昇格する。: `argparse/sys/typing/re/dataclasses/enum/json` を `test/unit/test_py2cpp_features.py` へ追加済み
  - [x] 接続後に `*_extended.py` を compile-run 回帰へ昇格する（`stdlib` 10/10 compile-run は達成済み、unit 回帰追加が未完）。: `python3 test/unit/test_py2cpp_features.py` 63 tests pass

## 2026-02-20 移管: `enum` サポート（完了）

1. [x] `pytra.std.enum` を追加し、`Enum` / `IntEnum` / `IntFlag` の最小互換 API を実装する。
   - [x] 値定義・比較の基本動作を実装する。
   - [x] `IntFlag` の `|`, `&`, `^`, `~` を実装する。
2. [x] EAST 変換で `Enum` 系クラス定義（`NAME = expr`）を認識できるようにする。
3. [x] `py2cpp` で `Enum` / `IntEnum` / `IntFlag` を C++ 側へ変換する最小経路を実装する。
   - [x] `Enum` 系基底クラス継承は C++ 側で省略し、静的メンバー定数として出力する。
   - [x] `Enum` / `IntEnum` / `IntFlag` を `enum class` へ lower する。
   - [x] `IntFlag` の C++ 型安全なビット演算ラッパ（`|`, `&`, `^`, `~`）を追加する。
4. [x] `test/fixtures` に `Enum` / `IntEnum` / `IntFlag` の実行一致テストを追加する。
5. [x] `docs-jp/pylib-modules.md` / `docs-jp/how-to-use.md` にサポート内容を追記する。

- [x] オプション体系（spec-options 反映）を実装完了。
  - `--mod-mode` / `--floor-div-mode` / `--bounds-check-mode` を実装。
  - `--int-width`（`32/64`）を実装し、`bigint` は planned（未実装エラー）として扱う。
  - `--str-index-mode` / `--str-slice-mode` を追加し、`codepoint` は planned（未実装エラー）として扱う。
  - `--preset {native,balanced,python}` と `--dump-options` を実装。
  - オプション処理を `src/pytra/compiler/transpile_cli.py` へ集約し、`py2cpp.py` 側の重複を削減。
  - エラー表示を `user_syntax_error` / `unsupported_by_design` / `not_implemented` などカテゴリ別に整理。
  - `docs-jp/spec-options.md` / `docs-jp/spec-dev.md` / `docs-jp/spec-east.md` / `docs-jp/how-to-use.md` を同期更新。

- [x] セルフホスティング済みトランスパイラ実行ファイル（`test/transpile/obj/pycpp_transpiler_self_new`）を使って、`test/fixtures/case05` から `test/fixtures/case100` までを `test/transpile/cpp2/` に変換し、各生成 C++ がコンパイル可能かを一括検証した。
  - 実施結果: `CASE_TOTAL=96`, `TRANSPILE_FAIL=0`, `COMPILE_OK=96`, `COMPILE_FAIL=0`

## トランスパイラ機能 TODO（今回の不足点整理）

- [x] `AugAssign`（`+=`, `-=`, `*=`, `/=`, `%=`, `//=`, `|=` など）を網羅対応する。
- [x] `**`（べき乗）を C++ 側で正しく変換する（`pow` 変換や整数演算最適化を含む）。
- [x] `bytearray(n)` / `bytes(...)` の初期化と相互変換を Python 互換に強化する。
- [x] `list.pop()` / `list.pop(index)` の両方に対応する（現在は引数なし中心）。
- [x] `math` モジュール互換を拡張する（`sin`, `cos`, `exp`, `pi` 以外も含め網羅）。
- [x] `gif` 出力ランタイム（`save_gif`, パレット関数）を `py_module` / `cpp_module` 対応で正式仕様化し、テストを追加する。
- [x] 連鎖比較（例: `0 <= x < n`）を AST から正しく展開して変換する。

## サンプル作成時に判明した追加TODO（05〜14対応）

- [x] `int / int` を含む `/` 演算で、Python互換の実数除算を保証する型昇格ルールを導入する。
- [x] `list` など空コンテナ初期化（`x = []`, `x = {}`）の型推論を強化し、`auto x = {}` の誤生成を防止する。
- [x] `bytes` / `bytearray` 系 API の変換規則を整理し、`extend(tuple)` のような利用も含めて互換を高める。
- [x] `def main()` がある入力でのエントリポイント衝突を避けるルール（自動リネームなど）を実装する。
- [x] list comprehension / nested list comprehension をサポートする（現状は手書きループへ書き換えが必要）。
- [x] 添字代入（`a[i] = v`, `a[i][j] = v`）を含む代入系の回帰テストを追加し、`// unsupported assignment` 混入を検知する。
- [x] `list.pop()` / `list.pop(index)` / `append` / `extend` など主要メソッド変換の互換テストを拡充する。

## sample/py 実行一致で追加対応が必要な項目

### py2cs.py 側

- [x] `import math` / `math.sqrt` などモジュール経由呼び出しを C# 側で正しく解決する（`math` 名未解決エラーを解消する）。
- [x] `from __future__ import annotations` を C# 変換時に無視する（`using __future__` を生成しない）。
- [x] Python 変数名が C# 予約語（例: `base`）と衝突した場合の自動リネーム規則を実装する。
- [x] `for ... in range(...)` 変換時の一時変数名衝突を防ぐ（ネスト時に `__range_*` が重複しないようにする）。
- [x] `for ... in range(...)` 変換時のループ変数再宣言衝突を防ぐ（既存ローカルと同名を再宣言しない）。
- [x] 大きな整数リテラル（例: `4294967296`）を含む代入で型変換エラーが出ないようにする（`int` / `long` の扱いを調整する）。

### py2cpp.py 側

- [x] `sample/py/04_monte_carlo_pi.py` を浮動小数点依存のサンプルから整数チェックサム系サンプルへ置き換え、言語間比較の安定性を上げる。
- [x] `for ... in range(...)` 変換時の一時変数名衝突を防ぐ（`sample/py/12_sort_visualizer.py` のコンパイル失敗を解消する）。

## sample/py/15 追加時に見えた変換器側TODO

- [x] `int(<str>)` の数値変換を `py2cpp.py` / `py2cs.py` で正しく変換する（手動パース回避）。
- [x] 文字列の 1 文字添字（`s[i]`）を Python と整合する形で C++/C# に変換する（`char`/`string` 差の吸収）。
- [x] `str` の比較（`"a" <= ch <= "z"` のような範囲比較）を C# 含め正しく変換する。
- [x] `while True: ... return ...` 形式で C# 側の「全経路 return」誤検知が出ないよう制御フロー解析を改善する。
- [x] 空リスト初期化（`x: list[T] = []`）を C# 側で `List<T>` として安定生成する（`List<object>` への退化を防止）。
- [x] メソッド呼び出し経由の型付き空コンテナ生成（`self.new_list()` 等）を常時許容し、`Only direct function calls are supported` を解消する。
- [x] `dict` 参照で C++ 側が `const` 扱いになる問題（`env[key]`）を生成側で解決し、入力コードにダミー書き込みを要求しない。
- [x] C++ の `%` はランタイム吸収せず直接生成する方針へ変更し、負数オペランドを仕様対象外として明記する。
- [x] 行連結文字列（`\n` を含む長いソース文字列）からのトークナイズが C++/C# 生成で壊れないよう文字列エスケープ処理を強化する。
- [x] 変換器都合で入力 Python を書き換えなくて済むよう、`sample/py/15` で行った回避実装をトランスパイラ側へ吸収する。

## sample/py の簡潔化候補（Python組み込み活用）

- [x] `sample/py/15_mini_language_interpreter.py`: 手動の数値文字列パースを `int(token_num.text)` に置き換える。
- [x] `sample/py/14_raymarching_light_cycle.py`: `if x > 255: x = 255` 系を `min(255, x)` に統一する（`r`, `g`, `b`, `v`）。
- [x] `sample/py/11_lissajous_particles.py`: `if v < 0: v = 0` を `max(0, v)` に置き換える。
- [x] `sample/py/09_fire_simulation.py`: 二重ループ初期化を `[[0] * w for _ in range(h)]` に置き換える。
- [x] `sample/py/13_maze_generation_steps.py`: `grid` 初期化を `[[1] * cell_w for _ in range(cell_h)]` に置き換える。
- [x] `sample/py/13_maze_generation_steps.py`: `while len(stack) > 0` を `while stack` に置き換える。
- [x] `sample/py/13_maze_generation_steps.py`: `stack[-1]` を使って末尾要素アクセスを簡潔化する。
- [x] `sample/py/12_sort_visualizer.py`: 一時変数スワップをタプル代入（`a, b = b, a`）へ置き換える。

## Go / Java ネイティブ変換の追加TODO

- [x] `py2go.py` / `py2java.py` を Python 呼び出し不要のネイティブ変換モードへ移行する。
- [x] `test/fixtures`（case01〜30）を Go/Java ネイティブ変換して、Python 実行結果と一致させる。
- [x] `sample/py` で使っている `math` モジュール呼び出し（`sqrt`, `sin`, `cos` など）を Go/Java ネイティブ変換で対応する。
- [x] `sample/py` で使っている `png.write_rgb_png` の Go/Java ランタイム実装を追加する。
- [x] `sample/py` で使っている `gif.save_gif` / `grayscale_palette` の Go/Java ランタイム実装を追加する。

## Rust 追加TODO（現時点）

- [x] `src/rs_module/py_runtime.rs` の `py_write_rgb_png` で、Python 側 `png.write_rgb_png` とバイナリ完全一致（IDAT 圧縮形式を含む）を実現する。
  - 方針変更: この厳密一致要件は今後は実施不要とし、完了扱いとする。
- [x] `py2rs.py` の `use py_runtime::{...}` 生成を使用関数ベースに最適化し、未使用 import 警告を削減する。

## 言語間ランタイム平準化 TODO

- [x] C++ のみ対応になっている `math` 拡張関数（`tan`, `log`, `log10`, `fabs`, `ceil`, `pow` など）を、Rust / C# / JS / TS / Go / Java / Swift / Kotlin の各ランタイムにも同等実装する。
- [x] C++ のみ実装が進んでいる `pathlib` 相当機能を、他ターゲット言語にも同一 API で実装する（`Path` の生成・結合・存在確認・文字列化など）。
  - [x] `pathlib` 最小共通 API を確定する（`Path(...)`, `/`, `exists`, `resolve`, `parent`, `name`, `stem`, `read_text`, `write_text`, `mkdir`, `str`）。
  - [x] `src/rs_module` / `src/cs_module` / `src/js_module` / `src/ts_module` / `src/go_module` / `src/java_module` に `pathlib` 相当ランタイムを追加する。
  - [x] `py2cpp.py` 以外の各トランスパイラで `import pathlib` と `Path` 呼び出しのマッピングを実装する。
  - [x] `sample/py` もしくは `test/fixtures` にファイルI/Oを伴う `pathlib` 利用ケースを追加し、各言語で実行確認する。
- [x] 上記の平準化後、`docs-jp/pytra-readme.md` の「対応module」を言語別の対応関数一覧で更新し、差分がある場合は理由を明記する。
  - [x] `math` / `pathlib` の言語別対応表を `docs-jp/pytra-readme.md` に追加する。
  - [x] 未対応関数が残る言語には「未対応理由・代替手段・予定」を併記する。
  - [x] `README.md` / `docs-jp/how-to-use.md` から参照される説明との整合を確認する。
- [x] `test/fixtures` に `math` / `pathlib` の共通回帰テストを追加し、全ターゲット言語で同一期待値を満たすことを CI 相当手順で確認する。
  - [x] `test/fixtures` に `math` 拡張（`tan/log/log10/fabs/ceil/pow`）の共通テストケースを追加する。
  - [x] `test/fixtures` に `pathlib` 共通テストケース（生成・結合・存在確認・読み書き）を追加する。
  - [x] 各ターゲット（C++/Rust/C#/JS/TS/Go/Java/Swift/Kotlin）への変換・実行コマンドを自動化スクリプトへ集約する。
  - [x] Python 実行結果との差分比較を自動化し、失敗ケースを一覧出力できるようにする。
  - 実行補足: 現在の開発環境では `mcs/go/javac/swiftc/kotlinc` が未導入のため、`tools/runtime_parity_check.py` は該当ターゲットを `SKIP` 表示で処理する。

## EAST / CppEmitter 簡素化 TODO

- [x] `east.py` 側で式を低レベル化し、`CppEmitter` の `Call` 分岐を削減する。
  - [x] `math.*`, `Path.*`, `len`, `print`, `str`, `int`, `float`, `bool`, `bytes`, `bytearray` を `BuiltinCall` 系ノードへ正規化する。
  - [x] `CppEmitter` は `BuiltinCall` 名と引数をそのまま C++ ランタイム呼び出しへマッピングする。
- [x] `Compare` の `in` / `not in` を専用ノード化し、コンテナ種別分岐を `east.py` 側で確定する。
  - [x] `Contains(container, key, negated)` ノードを追加する。
  - [x] `dict` と `list/set/tuple/str` の判定分岐を `east.py` 側に寄せる。
- [x] `slice` を専用ノード化し、`CppEmitter` の `Subscript` 条件分岐を削減する。
  - [x] `SliceExpr(value, lower, upper)` ノードを追加する。
  - [x] `Subscript` は単一添字アクセスに限定して表現する。
- [x] `JoinedStr`（f-string）を `Concat` 系へ事前展開し、文字列化規則を `east.py` で確定する。
  - [x] `FormattedValue` の型に応じた `to_string` 方針を EAST ノードに埋め込む。
  - [x] `CppEmitter` 側は連結出力のみを行う。
- [x] 代入ノードに宣言情報を持たせ、`CppEmitter` 側のスコープ推測ロジックを削減する。
  - [x] `Assign` / `AnnAssign` に `declare` / `decl_type` を追加する。
  - [x] `AugAssign` の未宣言時挙動を `east.py` で正規化する。
- [x] クラスノード情報を拡張し、`emit_class` の推測処理を削減する。
  - [x] `ClassDef` に `base`, `field_types`, `field_defaults`, `constructor_signature` を持たせる。
  - [x] dataclass/`__init__` の constructor 生成方針を EAST 側で確定する。
- [x] `For` 系の正規化を強化し、`CppEmitter` の `for` 出力を単純化する。
  - [x] `ForRange` と `ForEach` を完全分離し、`target_type` を持たせる。

## 保留（Go / Java は EAST 化まで凍結）

- Go/Java で、Python 側に型注釈がある変数・引数・戻り値を `any` / `Object` へ退化させず、可能な限り静的型（`int`/`float64`/`string`/`bool`/`[]byte`/`byte[]`/コンテナ型）へ落とす。
- `src/common/go_java_native_transpiler.py` の型注釈解釈を拡張し、`list[T]` / `dict[K,V]` / `set[T]` / `tuple[...]` を内部型タグへ保持する。
- 関数シグネチャ生成で、引数・戻り値の型注釈を Go/Java の静的型へ優先反映する（未注釈時のみ `any` / `Object`）。
- ローカル変数宣言で、型注釈付き代入 (`AnnAssign`) を `var/object` ではなく具体型で宣言する。
- コンテナ操作（`append`, `pop`, `pyGet`, `pySet`）のコード生成を型付きコンテナ前提で整合させる。
- `sample/py/15` 相当の複合ケースで Go/Java 生成コードの型退化が再発しないことを確認する。
- Go/Java の `bytes` / `bytearray` 型注釈を優先して `[]byte` / `byte[]` へ反映し、`any` / `Object` ベース実装は型未確定ケースのみに限定する。
- 型注釈 `bytes` / `bytearray` を内部型タグで区別し、宣言時に Go:`[]byte` / Java:`byte[]` で出力する。
- `bytes(...)` / `bytearray(...)` / `pyToBytes` 周辺の生成コードで不要な `any` / `Object` キャストを削減する。
- 添字アクセス・代入・`append` / `extend` / `pop` の `[]byte` / `byte[]` パスを優先する分岐を追加する。
- `sample/py` の PNG/GIF 系ケースで、バイト列が終始 `[]byte` / `byte[]` で通ることを確認する。
  - [x] `range_mode` と境界条件の確定を `east.py` 側で完了させる。
- [x] `CppEmitter` を「文字列出力専用」へ段階移行し、挙動回帰を防ぐ。
  - [x] 各段階で `test/fixtures` の `test/transpile/cpp` 実行結果一致を確認する。
  - [x] 各段階で `sample/py` の PNG/GIF 一致（バイナリ比較）を確認する。

## EAST C++可読性改善 TODO

- [x] `east/py2cpp.py` の括弧出力を簡素化し、不要な多重括弧（`if ((((...)))` など）を削減する。
  - [x] 演算子優先順位テーブルを導入し、必要な箇所だけ括弧を残す。
- [x] `r; g; b;` のような無意味な式文を出さない。
  - [x] 未初期化宣言のみ必要な場合は `int64 r;` の宣言で完結させる。
- [x] `for (i += (1))` 形式を C++らしい表記（`++i` など）へ寄せる。
  - [x] `step == 1` / `-1` の場合は `++i` / `--i` を使う。
  - [x] その他の step のみ `i += step` を維持する。

## EAST py2cpp sample対応 TODO（完了）

- [x] `sample/py` の `list.append(...)` / `frames.append(...)` を C++ `vector::push_back` へ正しく変換する。
  - [x] `Call(Attribute(..., "append"))` の lowered 情報を優先し、`append` を生のまま出力しない。
  - [x] `list[uint8]` / `list[list[uint8]]` / `list[Token]` など複数型で回帰テストする。
- [x] `perf_counter()` を C++ で解決する（`time` ランタイム呼び出しへマップ）。
  - [x] `east/cpp_module/py_runtime.h` もしくは適切な `cpp_module/time.h` 経由で利用可能にする。
  - [x] `sample/py` の計測系ケース（04,05,06,08,10,12,13）でコンパイル通過を確認する。
- [x] `range(...)` は `py2cpp.py` で処理せず、EAST 構築時点で消し切る。
  - [x] list comprehension 等の lowered 出力で `range` を未定義関数として出さない（生の `Call(Name("range"))` を残さない）。
  - [x] `for in range` 以外の利用（式位置・代入・引数渡し）がある場合も、EAST専用ノードへ lower して後段へ渡す。
  - [x] `py2cpp.py` 側に `range` 意味解釈を追加しない（残っていたらバグとして検出する）。
- [x] `min` / `max` の出力を `std::min` / `std::max`（型整合付き）へ統一する。
  - [x] `int`/`int64` 混在でテンプレート推論エラーが出ないよう型キャスト規則を追加する。
  - [x] `sample/py/14` での `min(255, ...)` / `max(0, ...)` を回帰テストする。
- [x] タプル分解代入の宣言不足を修正する（未宣言変数に代入だけが出る問題）。
  - [x] `a, b, c = f(...)` で `a,b,c` が未宣言なら型付き宣言を生成する。
  - [x] `sample/py/16` の `normalize(...)` 展開で `fwd_x` 等の未宣言エラーが消えることを確認する。
- [x] 上記対応後、`sample/py` 全16件で `east/py2cpp.py` 変換→コンパイル→実行を再実施し、実行時間一覧を更新する。

## self_hosted AST/Parser 段階移行 TODO


### ケース順移行（test/fixtures/case01 から順に）

- [x] `case01_add` を `self_hosted` で通す（EAST生成 + C++実行一致）。
- [x] `case02_sub_mul` を `self_hosted` で通す。
- [x] `case03_if_else` を `self_hosted` で通す。
- [x] `case04_assign` を `self_hosted` で通す。
- [x] `case05_compare` を `self_hosted` で通す。
- [x] `case06_string` を `self_hosted` で通す。
- [x] `case07_float` を `self_hosted` で通す。
- [x] `case08_nested_call` を `self_hosted` で通す。
- [x] `case09_top_level` を `self_hosted` で通す。
- [x] `case10_not` を `self_hosted` で通す。

### 切替完了条件


## 生成画像不一致 調査ベース TODO（2026-02-17）
## 移管済み（docs-jp/todo.md から） 2026-02-18

- [x] 比較・論理・算術の混在式で意味が変わらないことを `test/fixtures` で回帰確認する。
- [x] Python docstring を C++ の裸文字列文として出さず、コメントへ変換するか出力しない。
- [x] 関数先頭の単独文字列式（docstring）を `east.py` 側で専用メタ情報へ分離する。
- [x] `py2cpp.py` は `//` コメント出力に統一する（必要時のみ）。
- [x] 式文としての識別子単体出力を禁止するガードを `py2cpp.py` に追加する。
- [x] API 由来が追えるように、必要箇所に薄いコメントを付ける（例: `png.write_rgb_png` 対応）。
- [x] `write_rgb_png` / `save_gif` / `grayscale_palette` などランタイムブリッジ関数に限定して付与する。
- [x] コメントが過剰にならないよう最小限に制御する。
- [x] 生成コードのレイアウトを「意味単位」（初期化・計算・出力）で整える。
- [x] 連続宣言ブロック、連続代入ブロック、I/O 呼び出しブロックの間にのみ空行を入れる。
- [x] `sample/01` を可読性改善のゴールデンとして差分レビュー可能な形にする。
- [x] 方針変更: `python_ast` backend は廃止し、`self_hosted` 単独運用とする。
- [x] `src/common/east.py` に `parser_backend` 切替インターフェースを導入する。
- [x] CLI 引数で `--parser-backend` を受け付ける。
- [x] デフォルトは `self_hosted` とする。
- [x] 変換結果メタに backend 名を記録する。
- [x] `self_hosted` の最小字句解析器を追加する（コメント/改行/インデント含む）。
- [x] `INDENT` / `DEDENT` / `NEWLINE` / `NAME` / `NUMBER` / `STRING` / 記号をトークン化する。
- [x] `#` コメントを収集し、行番号つきで保持する。
- [x] tokenize 失敗時のエラー位置・ヒントを EAST エラー形式で返す。
- [x] `self_hosted` の最小構文木（内部ノード）を定義する。
- [x] まず `Module`, `FunctionDef`, `Assign`, `AnnAssign`, `Return`, `Expr`, `If`, `For`, `Call`, `Name`, `Constant`, `BinOp`, `Compare` を対象にする。
- [x] 各ノードに `lineno/col/end_lineno/end_col` を持たせる。
- [x] `self_hosted` 用パーサ本体（再帰下降）を追加する。
- [x] 式の優先順位テーブルを実装する（`* / %`, `+ -`, 比較, `and/or`）。
- [x] `for ... in range(...)` と通常 `for ... in iterable` を識別する。
- [x] 関数定義と型注釈（`x: int` / `-> int`）を解釈する。
- [x] 既存 EAST ビルド処理に `self_hosted` ノード経路を追加する。
- [x] 既存の型推論・lowering（`ForRange`, `Contains`, `SliceExpr` など）を共通で再利用できる形にする。
- [x] `self_hosted` 単独運用で EAST の形が安定するように正規化する。
- [x] コメント引き継ぎを実装する（`#` / docstring）。
- [x] `#` コメントを `leading_comments` として関数/文に紐づける。
- [x] `Expr(Constant(str))` の docstring と重複しないよう統合規則を決める。
- [x] `src/py2cpp.py` で `leading_comments` を `// ...` 出力する。
- [x] `case11_fib` を `self_hosted` で通す。
- [x] `case12_string_ops` を `self_hosted` で通す。
- [x] `case13_class` 〜 `case16_instance_member`（クラス系）を `self_hosted` で通す。
- [x] `case17_loop` 〜 `case24_ifexp_bool`（ループ/例外/内包/ifexp）を `self_hosted` で通す。
- [x] `case25_class_static` 〜 `case33_pathlib_extended`（拡張ケース）を `self_hosted` で通す。
- [x] `test/fixtures` 全ケースで `self_hosted` EAST が意味的に安定していることを確認する。
- [x] `src/py2cpp.py` で `--parser-backend self_hosted` 時に `test/fixtures` 全ケースが実行一致する。
- [x] デフォルト backend を `self_hosted` に変更する。
- [x] `save_gif(..., delay_cs=..., loop=...)` の keyword 引数を `py2cpp.py` の非lowered `Call` 経路でも確実に反映する。
- [x] 現状 `sample/cpp/*` で `save_gif(..., palette)` のみになり `delay_cs` が既定値 `4` に落ちる問題を修正する。
- [x] `sample/05,06,08,10,11,14` で GIF の GCE delay 値が Python 実行結果と一致することを確認する。
- [x] 浮動小数点式の再結合（演算順序変更）を抑制し、Python と同じ評価順を優先する。
- [x] `a * (b / c)` が `a * b / c` に変わらないように、`render_expr` の括弧方針を見直す。
- [x] `sample/01_mandelbrot` と `sample/03_julia_set` で PNG の raw scanline が一致することを確認する。
- [x] PNG 出力の差分を「画素差」と「圧縮差」に切り分けた上で、仕様として扱いを明文化する。
- [x] `sample/02_raytrace_spheres` は画素一致・IDAT 圧縮差のみであることを docs に追記する。
- [x] 必要なら C++ 側 `src/cpp_module/png.cpp` を zlib 圧縮実装へ寄せ、IDAT 近似一致または完全一致方針を決める。
- [x] GIF の `sample/12_sort_visualizer` / `sample/16_glass_sculpture_chaos` のフレーム画素差を解消する。
- [x] `render()` 内の float→int 変換境界（bar幅/補間/正規化）の評価順を Python と一致させる。
- [x] フレームデータ（LZW 展開後）が全フレーム一致することを確認する。
- [x] 画像一致検証を自動化する。
- [x] `sample/py` 全件について、`stdout` 比較に加えて PNG raw / GIF フレーム一致を検証するスクリプトを追加する。
- [x] 差分時は「最初の不一致座標・チャネル・元式」を出力できるようにする。
- [x] 方針を明文化する: Pythonのユーザー定義クラスは参照セマンティクスを原則とし、値型化は「意味保存が証明できる場合のみ」許可する。
- [x] `case34_gc_reassign` を回帰ゴールデンに設定し、`a = b` 後に同一オブジェクト共有（コピーで2個化しない）を必須条件にする。
- [x] 値型化の適用条件を仕様化する（例: インスタンスフィールドなし、`__del__` なし、インスタンス同一性に依存する操作なし、代入/引数渡しで共有観測されない）。
- [x] EAST 解析段階で「値型化候補クラス」と「参照必須クラス」を分類するメタ情報を追加する。
- [x] `src/py2cpp.py` にクラスごとのストレージ戦略選択（`rc<T>` / `T`）を実装し、混在ケースで正しく `.` と `->` を切り替える。
- [x] `case15_class_member` は以前どおり `Counter c = Counter();` へ戻す（最適化適用例）。
- [x] `case34_gc_reassign` は `rc<Tracked>` のまま維持する（最適化非適用例）。
- [x] 新規テストを追加する: 同一性依存ケース（代入共有、関数引数経由の更新共有、コンテナ格納後の共有）では必ず参照型を選ぶことを検証する。
- [x] 新規テストを追加する: 値型化候補（実質 stateless クラス）では出力C++が値型になり、実行結果がPython一致することを検証する。
- [x] selfhost一次ゴールを固定する: `python3 src/py2cpp.py selfhost/py2cpp.py -o selfhost/py2cpp.cpp` が成功する。
- [x] self-hosted parser で関数定義シグネチャの `*`（keyword-only 引数マーカー）を解釈可能にする。
- [x] `*` 対応後、`selfhost/py2cpp.py` の EAST 生成が最後まで通ることを確認する。
- [x] 関数定義シグネチャでの未対応要素（`/`, `*args`, `**kwargs`）の扱いを仕様化する（受理/拒否とエラーメッセージ）。
- [x] `src/common/east.py` の対応箇所へ最小コメントを追加し、どのシグネチャ構文をサポートするか明記する。
- [x] self_hosted parser の `STR` 解析で prefix 付き文字列（`f/r/b/u/rf/fr`）を正しく扱えるようにする。
- [x] self_hosted parser の `f-string` を `JoinedStr/FormattedValue` に落とす（最低限 `{expr}` と `{{` `}}`）。

## 移管: 2026-02-18（docs-jp/todo.md から完了済みを移動）

### Any/object 方針への移行（完了）

- [x] `src/cpp_module/py_runtime.h` に `using object = rc<PyObj>;` を導入する。
- [x] `Any -> object` 変換のためのボックス型を実装する。
- [x] `PyIntObj` / `PyFloatObj` / `PyBoolObj` / `PyStrObj`
- [x] `PyListObj` / `PyDictObj`（`list<object>` / `dict<str, object>` ベース）
- [x] `make_object(...)` / `obj_to_int64` / `obj_to_float64` / `obj_to_bool` / `obj_to_str` を実装する。
- [x] `py_is_none(object)` を実装し、null `object` 判定を統一する。
- [x] `py_to_string(object)` を実装する。

### py2cpp 側 Any lowering（完了）

- [x] `src/py2cpp.py` の `cpp_type()` で `Any` / `object` を `object` 型へ解決する。
- [x] `dict[str, Any]` を `dict<str, object>` に変換する。
- [x] `list[Any]` を `list<object>` に変換する。
- [x] `Any` 代入時に `make_object(...)` を生成する。
- [x] `Any` 利用演算時に明示的 unbox (`obj_to_*`) を生成する。
- [x] `Any is None` / `Any is not None` を `py_is_none` ベースへ統一する。

### selfhost 回復（部分完了）

- [x] `selfhost/py2cpp.cpp` を再生成し、現時点のコンパイルエラー件数を計測する。
  - 計測値: `305` errors（`g++ -std=c++20 -O2 -I src selfhost/py2cpp.cpp ...`）

### 内包表現・lambda 追加回帰（完了）

- [x] `test/fixtures/collections` に内包表現の追加ケースを増やす。
- [x] 二重内包（nested comprehension）
- [x] `if` 句を複数持つ内包
- [x] `range(start, stop, step)` を使う内包
- [x] `test/fixtures/core` に lambda の追加ケースを増やす。
- [x] `lambda` 本体が `ifexp` を含むケース
- [x] 外側変数 capture + 複数引数
- [x] 関数引数として lambda を渡すケース
- [x] 上記を `test/unit/test_py2cpp_features.py` の C++ 実行回帰に追加する。

### ドキュメント更新（完了）

- [x] `docs-jp/spec-east.md` に `Any -> object(rc<PyObj>)` 方針を明記する。
- [x] `docs-jp/spec.md` に `Any` の制約（boxing/unboxing, None 表現）を追記する。
- [x] `readme.md` に `Any` 実装状況（移行中）を明記する。

## 移管: 2026-02-18（todo.md から完了済みを移動・2）

### selfhost 回復（完了分）

- [x] `selfhost/py2cpp.py` のパース失敗を最小再現ケースへ分離する（`except ValueError:` 近傍）。
- [x] `src/common/east.py` self_hosted parser に不足構文を追加する。
- [x] 2. の再発防止として unit test を追加する。
- [x] `PYTHONPATH=src python3 src/py2cpp.py selfhost/py2cpp.py -o selfhost/py2cpp.cpp` を成功させる。
- [x] `selfhost/py2cpp.cpp` をコンパイルし、エラー件数を再計測する。
- [x] コンパイルエラー上位カテゴリを3分類し、順に削減する。
- [x] `src/py2cpp.py` 実行結果との一致条件を定義し、比較確認する。
- [x] `selfhost/` には `src` 最新をコピーしてよい前提で、`selfhost/py2cpp.py` と `selfhost/cpp_module/*` を同期する（`cp -f src/py2cpp.py selfhost/py2cpp.py` / `cp -f src/cpp_module/* selfhost/cpp_module/`）。
- [x] `g++` ログ取得を `> selfhost/build.all.log 2>&1` に統一し、`stderr` 空でも原因追跡できるようにする。

### object 制約の実装反映（汎用）

- [x] EAST で `object` レシーバの属性アクセス・メソッド呼び出しを検出し、`unsupported_syntax` を返す。
- [x] `py2cpp.py` の emit 時にもガードを追加し、`object` レシーバの呼び出し漏れを最終防止する。
- [x] `test/fixtures/signature/` に `object` レシーバ呼び出し禁止の NG ケースを追加する。
- [x] `test/unit` に NG ケースが失敗することを確認する回帰テストを追加する。

### 追加回帰（super）

- [x] `super()` の回帰 fixture を追加する（`test/fixtures/oop/super_init.py`）。
- [x] EAST parser 側で `super().__init__()` を含むコードが parse できる unit test を追加する。
- [x] C++ 変換して実行まで通る runtime test を追加する（`test/unit/test_py2cpp_features.py`）。

### EAST へ移譲（py2cpp 簡素化・第2段）

- [x] `src/common/east_parts/core.py` で `Call(Name(...))` の `len/str/int/float/bool/min/max/Path/Exception` を全て `BuiltinCall` 化し、`py2cpp` の生分岐を削減する。
- [x] `src/common/east_parts/core.py` で `Attribute` 呼び出しの `owner_t == "unknown"` フォールバック依存を減らし、型確定時は EAST で runtime_call を確定させる。
- [x] `src/py2cpp.py` の `render_expr(kind=="Call")` から、EAST で吸収済みの `raw == ...` / `owner_t.startswith(...)` 分岐を段階削除する。
- [x] `test/unit/test_py2cpp_features.py` に `BuiltinCall` 正規化の回帰（`dict.get/items/keys/values`, `str` メソッド, `Path` メソッド）を追加する。
- [x] `test/unit` 一式を再実行し、`test/fixtures` 一括実行で退行がないことを確認する。

### BaseEmitter 共通化（言語非依存 EAST ユーティリティ）

- [x] `src/common/base_emitter.py` に言語非依存ヘルパ（`any_dict_get`, union型分解、`Any` 判定）を移し、`CppEmitter` の重複を削減する。
- [x] ノード補助（`is_name/is_call/is_attr` などの軽量判定）を `BaseEmitter` に追加し、各エミッタの分岐可読性を上げる。
- [x] 型文字列ユーティリティ（`is_list_type/is_dict_type/is_set_type`）を `BaseEmitter` へ寄せる。
- [x] `py2cpp.py` で `BaseEmitter` の新規ユーティリティ利用へ置換し、挙動差分がないことを回帰テストで確認する。
- [x] 次段として `py2rs.py` / `py2cs.py` でも流用可能な API 形に揃え、適用候補箇所を `todo.md` に追記する。

## 移管: 2026-02-18（todo.md から完了済みを移動・3）

### selfhost 回復（完了分）

- [x] self_hosted parser で `return`（値なし）を文として受理する。
- [x] `return`（値なし）の再発防止 unit test（`test/unit/test_east_core.py`）を追加する。
- [x] `BaseEmitter` に `any_to_dict/any_to_list/any_to_str` ヘルパを追加する（自己変換時の型崩れ分析の土台）。
- [x] `py_runtime.h` に `optional<dict<...>>` 向け `py_dict_get/py_dict_get_default` 補助オーバーロードを追加する。

## 移管: 2026-02-18（C++ runtime wrapper 方針の整合）

- [x] `py_runtime.h` の `str/list/dict/set` を STL 継承ベースから「非継承 wrapper（composition）」へ移行する。
- [x] 非継承 `str` で range-for が自然に書けるよう、`begin()/end()`（必要なら iterator wrapper）を整理する。
- [x] `py2cpp.py` の生成コードから STL 依存の前提（継承由来の暗黙利用）を除去し、wrapper API のみで成立させる。
- [x] `test/fixtures/strings/str_for_each.py` を含む文字列走査ケースで、生成 C++ が簡潔な `for (str c : s)` を維持することを回帰確認する。
- [x] `docs-jp/spec-dev.md` / `docs-jp/how-to-use.md` / `docs-jp/spec-east.md` の wrapper 記述を実装実態と一致させる（移行完了時に再更新）。

## 移管: 2026-02-18（selfhost 回復 1-3）

- [x] `selfhost/py2cpp.cpp` で `object -> optional<dict<...>> / list<object> / str` 代入が失敗している箇所を、`any_to_dict/any_to_list/any_to_str` を通る形へ統一する。
- [x] `py_dict_get_default(...)` 呼び出しの曖昧解決（`bool` 既定値など）を解消するため、`dict_get_bool/str/list/node` など型付き helper 呼び出しへ置換する。
- [x] `emit_stmt` / `emit_assign` / `render_expr` の `dict|None` 固定引数を段階的に `Any` 受け + 内部 `dict` 化へ寄せ、selfhost 生成コードの `std::any` 入力と整合させる。

## 移管: 2026-02-18（todo.md から完了済みを移動・4）

### 画像ランタイム統一（Python正本）

- [x] `src/pylib/png.py` を正本として、`py2cpp` 向け C++ 画像ランタイム（`src/runtime/cpp/pylib`）を段階的にトランスパイル生成へ置換する。
  - [x] `py2cpp` に `--no-main` を追加し、ライブラリ変換（`main` なし）を可能にする。
  - [x] self-hosted parser で `0x...` 整数リテラルと `^=` など拡張代入を受理する。
  - [x] self-hosted parser で `with expr as name:` を `Assign + Try(finally close)` へ lower する。
  - [x] `pylib/png.py` 変換結果で残るランタイム依存（`open`, `ValueError`, `to_bytes` など）を C++ ランタイム API へ接続する。
  - [x] 生成結果を `src/runtime/cpp/pylib/png.cpp` へ置換し、既存出力と一致確認する。
- [x] `src/pylib/gif.py` を正本として、`py2cpp` 向け C++ 画像ランタイム（`src/runtime/cpp/pylib`）を段階的にトランスパイル生成へ置換する。
  - [x] `_lzw_encode` のネスト関数を除去し、self-hosted parser で変換可能な形へ整理する。
  - [x] `py2cpp --no-main src/pylib/gif.py` で C++ ソース生成できるところまで到達する。
  - [x] 生成結果で残るランタイム依存（`open`, `ValueError`, `to_bytes` など）を C++ ランタイム API へ接続する。
  - [x] 生成結果を `src/runtime/cpp/pylib/gif.cpp` へ置換し、既存出力と一致確認する。
- [x] 画像一致判定の既定手順を「バイナリ完全一致」へ統一し、`py2cpp` 向けの検証スクリプトを整理する。
  - [x] `pylib` と `runtime/cpp/pylib` の PNG/GIF 出力一致を確認する自動テスト（最小ケース）を追加する。
  - [x] 置換作業中の受け入れ基準を「Python正本と同じ入力で同一出力」へ固定する。
- [x] 速度がボトルネックになる箇所のみ、`py2cpp` 向け最適化の許容範囲を文書化する。

### import 強化

- [x] `from XXX import YYY` / `as` を EAST メタデータと `py2cpp` の両方で解決し、呼び出し先ランタイムへ正しく接続する。
- [x] `import module as alias` の `module.attr(...)` を alias 解決できるようにする。
- [x] `from pytra.runtime.png import write_rgb_png` / `from pytra.runtime.gif import save_gif` / `from math import sqrt` の回帰テストを追加する。
- [x] `import` 関連の仕様追記（対応範囲・`*` 非対応）を `docs-jp/spec-east.md` / `docs-jp/spec-user.md` / `docs-jp/spec-dev.md` に反映する。

### selfhost 回復（完了済み分）

- [x] `py2cpp.py` の `BaseEmitter` 共通化後、selfhost 生成時に `common.base_emitter` の内容を C++ へ取り込む手順（または inline 展開）を実装する。
  - [x] `tools/prepare_selfhost_source.py` を追加して、`selfhost/py2cpp.py` を自己完結化する。
  - [x] `python3 src/py2cpp.py selfhost/py2cpp.py -o selfhost/py2cpp.cpp` が通る状態に戻す。


## 移管: 2026-02-21（todo.md 再整理前スナップショット）

> 再整理前の docs-jp/todo.md 原本を退避。完了済みタスクの履歴を保持するために移管。

# TODO（未完了のみ）

## 最優先（2026-02-20 追加: todo2 優先TODO 反映）

- [x] `src/pytra/std/*.py` を `--emit-runtime-cpp` で再生成し、`src/runtime/cpp/pytra/std/` への反映を自動生成起点に統一する。
  - [x] 対象: `math.py`, `json.py`, `pathlib.py`, `re.py`, `sys.py`, `typing.py`, `dataclasses.py`, `time.py`, `glob.py`, `os.py`。
  - [x] 進捗: `math/json/pathlib/re/sys/typing/dataclasses/time/glob/os` は self_hosted parser で EAST 変換可能。
  - [x] 進捗: `os.py --emit-runtime-cpp` の生成物（`src/runtime/cpp/pytra/std/os.cpp`）は単体コンパイル可能化した（`py_os_*` マップ + runtime helper 追加）。
  - [x] ブロッカー解消:
    - `pathlib.py` 再生成物の C++ 単体コンパイル失敗を解消（`class_storage_hint` 明示上書き + `pytra.std.pathlib` 実装整理 + `PyFile` の text `read/write` 拡張）。
    - `os.py` 再生成物の C++ 単体コンパイル失敗を解消（`src/runtime/cpp/pytra/std/os.cpp` は `g++ -std=c++17 -Isrc -Isrc/runtime/cpp -c` で通過）。
  - [x] 受け入れ条件:
    - [x] `python3 src/py2cpp.py src/pytra/std/math.py --emit-runtime-cpp` 後に `src/runtime/cpp/pytra/std/math.h`, `src/runtime/cpp/pytra/std/math.cpp` が更新される。
    - [x] `python3 test/fixtures/stdlib/math_extended.py` と対応 C++ 実行結果が一致する。
    - [x] `python3 src/py2cpp.py src/pytra/std/pathlib.py --emit-runtime-cpp` 後の `src/runtime/cpp/pytra/std/pathlib.cpp` が単体コンパイルできる（`g++ -std=c++17 -Isrc -Isrc/runtime/cpp -c`）。
    - [x] `python3 src/py2cpp.py src/pytra/std/os.py --emit-runtime-cpp` 後の `src/runtime/cpp/pytra/std/os.cpp` が単体コンパイルできる（`g++ -std=c++17 -Isrc -Isrc/runtime/cpp -c`）。
    - [x] 上記 10 モジュールを再生成後に `g++ -std=c++20 -Isrc -Isrc/runtime/cpp -c src/runtime/cpp/pytra/std/<module>.cpp` で全件単体コンパイル通過。

- [x] `test_py2cpp_features -k extended_runtime` の残り失敗 3 件を解消する。
  - [x] `argparse_extended_runtime`: `pytra::std::argparse` 解決（include/namespace と `dict.get` キー型）を修正する。
  - [x] `sys_extended_runtime`: `set_argv` / `set_path` への `std::any` 退化引数を型付きで渡すように修正する。
  - [x] `os_glob_extended_runtime`: `pytra.std.glob` の自己再帰生成を runtime call map（`py_glob_glob`）で解消する。

- [x] `enumerate()` 変換を拡張し、`start` 引数つきケースを回帰テストで固定する。
  - [x] 追加ケース: `enumerate(xs)`, `enumerate(xs, 1)`, `enumerate(xs, 5)`, タプル分解あり/なし（非分解は `pair` 受け取り）。
  - [x] 受け入れ条件: `test/fixtures` 側の Python/C++ 出力一致テストが green。

- [x] 内包表記とラムダのテストを増やし、コード生成崩れを早期検知できるようにする。
  - [x] 追加ケース: list/set/dict comprehension（if あり/なし）、lambda の即時呼び出し、lambda を変数へ代入して呼び出し。
  - [x] 進捗: `lambda_immediate` / `comprehension_ifexp` / `comprehension_dict_set` fixture を追加し、対応 unit test を追加した。
  - [x] ブロッカー解消: `dict/set` comprehension の型不整合（`dict<int,...>` が `dict<str, object>` へ崩れる）を修正した（EAST 側 target 型束縛 + C++ 側 dict key 型キャスト）。
  - [x] 受け入れ条件: 追加 fixture の Python/C++ 一致と `tools/check_py2cpp_transpile.py` green（`checked=106 ok=106 fail=0 skipped=5`）を確認済み。

- [x] `import_pytra_runtime_png.png` 誤生成の原因を特定し、再発防止テストを追加する。
  - [x] 原因候補を特定: `tools/runtime_parity_check.py` が repo 直下 `cwd` で fixture 実行しており、画像出力が作業ツリーへ漏れる。
  - [x] 暫定対策: `runtime_parity_check` を一時作業ディレクトリ実行へ変更し、`cwd` 由来の出力漏れを抑止。
  - [x] 再現条件（入力ファイル・コマンド・期待値）メモ:
    - 入力: `test/fixtures/imports/import_pytra_runtime_png.py`
    - コマンド: `python3 tools/runtime_parity_check.py import_pytra_runtime_png --targets cpp`
    - 期待値: repo 直下に `import_pytra_runtime_png.png` が生成されない。
  - [x] 受け入れ条件: `test/unit/test_image_runtime_parity.py::test_runtime_parity_check_does_not_leak_png_to_repo_root` を追加して確認。

## 最優先（2026-02-20 追加: py2cpp コード生成不具合）

- [x] `py2cpp.py` の分岐内初回代入（関数スコープ変数）が C++ でブロックスコープ宣言になってしまう問題を修正する。
  - [x] 原因調査:
    - `emit_assign`（`src/py2cpp.py`）が `is_declared` 判定を現在スコープ基準で行うため、`if/else` 内初回代入が `str x = ...;` として各ブロックに閉じる。
    - その後の `return x + y` はブロック外参照となり、未宣言エラーを誘発する。
  - [x] 最小再現の生成テストを追加:
    - `test/unit/test_py2cpp_codegen_issues.py::Py2CppCodegenIssueTest::test_branch_first_assignment_is_hoisted_before_if`
    - `test/unit/test_py2cpp_codegen_issues.py::Py2CppCodegenIssueTest::test_optional_tuple_destructure_keeps_str_type`
  - [x] 修正:
    - 関数単位で「分岐後にも参照されるローカル」を事前収集し、`if/else` の外側で宣言、分岐内は代入のみを出力する。
    - `TupleAssign` で `tuple[...]|None` からの代入時に `optional` を展開してから `std::get<>` する。
    - 事前宣言変数への代入で型情報を見失わないよう `declared_var_types` のフォールバックを追加する。
  - [x] 受け入れ条件:
    - 上記 2 テストが green であること（skip なし）。: `python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py'` で `2/2 OK`。
    - `runtime/cpp/pytra/std/json.cpp` 末尾 `dumps()` と同種のスコープ崩れが再発しないことを確認する。: `--emit-runtime-cpp` 再生成 + `g++ -c src/runtime/cpp/pytra/std/json.cpp` を確認済み。

## 優先方針（2026-02-19 更新）

- まず `import` 解決（依存グラフ・探索パス・`from ... import ...` を含む）を先に完了させる。
- `selfhost` は import 解決完了後に回す（手戻り抑制のため）。

## 直近実行キュー（細分化）

1. [ ] selfhost `.py` 経路の段階回復
   - [x] `load_east` スタブ置換のために必要な EAST 変換依存（parser/east_io）を最小単位で棚卸しする。
     - 依存本体: `src/pytra/compiler/east_parts/core.py::{EastBuildError, convert_path, convert_source_to_east_with_backend}`
     - 主要 shim 依存: `pytra.std.argparse`, `pytra.std.json`, `pytra.std.re`, `pytra.std.pathlib`, `pytra.std.sys`, `pytra.std.dataclasses`, `pytra.std.typing`
     - selfhost 非対応要素: `src/pytra/compiler/east.py` facade の bootstrap path 操作（`import sys as _bootstrap_sys` と `sys.path.insert`）
   - [x] `tools/prepare_selfhost_source.py` に取り込み可能な関数群を「安全（selfhost通過済み）」と「要分割」に分ける。
     - 安全（通過済み）: `CodeEmitter` 本体、`transpile_cli` の関数群（`parse_py2cpp_argv` など）、main差し替え
     - 要分割: `src/pytra/compiler/east.py` facade 経由の import 連鎖、`east_parts.core` 全量取り込み（サイズ過大かつ selfhost 変換コスト高）
   - [x] `sample/py/01_mandelbrot.py` を selfhost 経路で `-o` 生成できるところまで回復する。
     - [x] 暫定ブリッジ `tools/selfhost_transpile.py` を追加し、`.py -> EAST JSON -> selfhost` で `test/fixtures/core/add.py` の生成を確認。
     - [x] 同ブリッジ経路で `sample/py/01_mandelbrot.py` の `-o` 生成を確認。
     - [x] `src/py2cpp.py` の runtime モジュール解決を `pytra.compiler.*` まで拡張し、`_runtime_module_tail_from_source_path` / include / namespace の経路に `compiler/` を追加した。
      - [x] `src/pytra/compiler/east_parts/core.py --emit-runtime-cpp` 生成物（`runtime/cpp/pytra/compiler/east_parts/core.cpp`）を単体コンパイル可能化する。
        - [x] 下準備: `dict.update` 未対応は `src/runtime/cpp/pytra/built_in/dict.h` 拡張で解消した。
        - [x] 下準備: Python 例外継承 (`class X(Exception)`) は C++ 側継承省略へ統一してビルド阻害を回避した。
        - [x] ブロッカーA: `Call(...).attr()` が `ns::func(...)::attr()` へ誤解決されるケースは、`re.strip_group(...)` 導入と call/attribute 解決見直しで解消した。
      - [x] ブロッカーB: `core.py` 内の mutable 引数/ローカルが `const` 扱いで生成される経路を解消した（`list.append`/`dict[...] =` が通る）。
      - [x] ブロッカーC: self_hosted parser 本体の不整合（keyword-only 呼び出し、tuple 要素アクセス、`lstrip(" ")` 等）を潰し、`core.cpp` 単体 `g++ -c` を通した。
     - [x] pure selfhost（中間 Python 呼び出しなし）で `.py -> -o` を通す。
      - [x] `selfhost/py2cpp.out` 側に `load_east(.py)` の実処理を実装し、`not_implemented` を返さないようにする。
         - [x] `load_east(.py)` を `load_east_from_path(..., parser_backend="self_hosted")` ベースに置換する。
         - [x] selfhost 最小モードの `load_east(.json)` を復活させ、`tools/check_selfhost_cpp_diff.py --selfhost-driver bridge` を再び通す（`std::any` 退化を回避した実装にする）。
           - [x] `.json` 読み込み自体は復活し、`bridge-json-unavailable` skip は解消した（2026-02-20）。
           - [x] `tools/check_selfhost_cpp_diff.py --selfhost-driver bridge` の既定ケースで `mismatches=0` を達成する。: `test/fixtures/core/add.py`, `test/fixtures/control/if_else.py`, `test/fixtures/collections/comprehension_filter.py`, `sample/py/01_mandelbrot.py` で `mismatches=0` を確認済み（2026-02-20）。
           - [x] 暫定措置: `check_selfhost_cpp_diff --mode allow-not-implemented --selfhost-driver bridge` では `[input_invalid]` を skip 扱いにした（本タスク完了時に戻す）。
           - [x] `src/pytra/std/json.py` を C++ へ安全に生成できるサブセットへ段階分割し、`runtime/cpp/pytra/std/json.cpp` の selfhost ビルドエラー（`ord/chr` / 文字列 `.begin()` / optional tuple 展開など）を解消する。: `json.cpp` 単体コンパイル通過、`json_extended` の Python/C++ 出力一致を確認済み（2026-02-20）。
         - [x] 置換後に `--help` / `.json` 入力の既存経路が壊れないことを確認する。: `./selfhost/py2cpp.out --help` と `./selfhost/py2cpp.out <EAST.json> -o out.cpp` を確認済み（2026-02-20）。
         - [x] `.py` / `.json` 入力のエラー分類を `user_syntax_error` / `input_invalid` / `not_implemented` で再点検する。: 2026-02-21 時点で `.py` / `.json` とも実処理に到達し、`--help` は `0` を確認。
       - [x] `src/py2cpp.py` の EAST 読み込み import を `pytra.compiler.east` facade から `pytra.compiler.east_parts.core` へ切り替えた（selfhost 時の動的 import 依存を削減）。
       - [x] `tools/build_selfhost.py` の現行失敗要因を段階解消する（`literal.join` 生成崩れ、`AUG_OPS/BIN_OPS` 未束縛、`parse_py2cpp_argv` 返り値の tuple 退化）。: 2026-02-20 時点で `python3 tools/build_selfhost.py` が再び green（`selfhost/py2cpp.out` 生成成功）。
         - [x] `CppEmitter._module_source_path_for_name` の selfhost 変換で `Path` が `float64` 退化する経路を除去する（`Path /` と `str + Path` を使わない）。: `Path` 合成を文字列経由へ変更し、`py_div(Path, str)` 発生を除去。
         - [x] `CppEmitter._module_function_arg_types` の `load_east` 依存を selfhost 最小モードで無効化する（`not_implemented` のままでもビルド通過を優先）。: runtime `.py` の関数シグネチャ抽出を source 解析経由のみに固定。
         - [x] `parse_py2cpp_argv` の返り値が tuple 退化する経路を修正し、`_dict_str_get(parsed, ...)` 呼び出しを常に `dict[str, str]` で通す。
         - [x] `", ".join(...)` / `" && ".join(...)` など literal `.join` が C++ 側で `char[]` 扱いになる箇所を全置換する（`sep` 変数経由または `py_join` 経由）。: `src/py2cpp.py` の結合処理を `_join_str_list(...)` 経由へ統一。
         - [x] `BIN_OPS` / `AUG_OPS` / `CMP_OPS` の global 参照が selfhost で未束縛になる経路を切り分け、`CodeEmitter` 側 accessor 経由へ寄せる。: selfhost source 準備時に `BIN_OPS/CMP_OPS/AUG_OPS/AUG_BIN` を再束縛し、`dict_get_node` の `dict[str,str]` 取得経路を runtime へ追加。
       - [x] `src/pytra/compiler/east_parts/core.py` の selfhost 非対応構文（bootstrap/path 操作）を切り離して取り込み可能にする。
         - [x] bootstrap 専用コードを `src/pytra/compiler/east.py` facade 側へ隔離し、`east_parts.core` から除去する。
         - [x] `east_parts.core` の import を `pytra.std.*`（または同等 shim）に固定する。
         - [x] `core.py` 先頭の self_hosted parser 未対応パターン（行内 `#` コメント / class docstring）を除去した。
         - [x] `core.py` 内のネスト `def`（例: `_tokenize` 内 `scan_string_token`）を self_hosted parser で扱える形へ段階分解する。: `PYTHONPATH=src python3 -c 'from pytra.compiler.east_parts.core import convert_path; from pytra.std.pathlib import Path; convert_path(Path(\"src/pytra/compiler/east_parts/core.py\"))'` で `OK` を確認（2026-02-20）。
         - [x] `tools/prepare_selfhost_source.py` の取り込み対象へ `east_parts.core` を段階追加する。: 現行は `runtime/cpp/pytra/compiler/east_parts/core.cpp` を selfhost ビルドへ同時リンクする経路で稼働。
       - [x] `tools/selfhost_transpile.py` を使わず `./selfhost/py2cpp.out sample/py/01_mandelbrot.py -o /tmp/out.cpp` が成功することを確認する。
       - [x] 上記生成物を `g++` でビルドして、実行結果が Python 実行と一致することを確認する。: `sample/py/04_monte_carlo_pi.py` を selfhost 変換後にコンパイル実行し、`pixels` / `checksum` が Python 実行結果と一致（2026-02-21）。
3. [ ] CodeEmitter hook 移管の再開（selfhostを壊さない手順）
   - [x] `CodeEmitter` に hooks 辞書呼び出しを導入する前に、selfhost非対応構文（`callable` など）を使わない制約版APIを定義する。
     - [x] hook シグネチャを `dict[str, Any]` / `list[str]` のみで完結させる（`callable` 注釈禁止）。
     - [x] 制約版 API の最小仕様を `docs-jp/spec-language-profile.md` へ追記する。
   - [x] `cpp_hooks.py` は最初に `png/gif` のみ移管し、`py2cpp.py` の既存分岐を1件ずつ削る。: `src/py2cpp.py` から `png/gif` 固有分岐が消えており、`src/hooks/cpp/hooks/cpp_hooks.py` 側へ集約済み（2026-02-21）。
     - [x] `png.write_rgb_png` の解決ロジックを `cpp_hooks.py` へ移し、`py2cpp.py` 側の分岐を削除する。: `CodeEmitter.hook_on_render_call` に実配線を追加し、`_render_special_runtime_call` 系分岐を削除済み。
     - [x] `gif.save_gif` の解決ロジックを `cpp_hooks.py` へ移し、`py2cpp.py` 側の分岐を削除する。: `runtime_call`/`Name`/`Attribute` の解決は `build_cpp_hooks()` 注入の `on_render_call` 側へ統一済み。
     - [x] 補足: `cpp_hooks.py` 側の `on_render_call` 追加は着手済み。`pytra.*` 名へ正規化する処理を追加済み。selfhost を壊さない hook 呼び出し経路（高階関数を使わない方式）を先に確定する。
    - [x] 置換ごとに `tools/check_py2cpp_transpile.py` を実行し、差分を確認する。: 2026-02-20 時点で `checked=119 ok=119 fail=0 skipped=5` を確認。
   - [x] 各ステップで `tools/build_selfhost.py` と `tools/check_py2cpp_transpile.py` の両方を必須ゲートにする。
     - [x] 上記 2 コマンド失敗時はコミット禁止ルールを `docs-jp/spec-codex.md` に明記する。

## CodeEmitter 化（JSON + Hooks）

4. [ ] フック注入 (`EmitterHooks`) を実装する。
   - [x] `on_render_call`, `on_render_binop`, `on_emit_stmt` など最小フック面を定義する。
   - [ ] `render_expr(Call/BinOp/Compare)` の巨大分岐を hooks + helper へ段階分離する。: `BinOp` + `Call(Name/Attribute)` は helper 分離済み
    - [x] `render_expr(IfExp/List/Tuple/Set/Dict/Subscript)` を `hook_on_render_expr_kind(kind, node)` へ委譲できる形へ整理する。: `render_expr` 先頭で kind フックを共通呼び出しする形へ移行済み。
    - [x] `JoinedStr/Lambda/Comp` 系を `hook_on_render_expr_complex(node)` へ分離する。: 入口フックを実装し、`JoinedStr/Lambda/ListComp/SetComp/DictComp` で委譲可能化。
   - [x] `emit_stmt(If/While/For/AnnAssign/AugAssign)` の分岐を hooks + template helper へ段階分離する。: `If/While` は `_emit_if_stmt` / `_emit_while_stmt`、`For` はヘッダ template 化、`AnnAssign/AugAssign` は文面 template 化、`hook_on_emit_stmt_kind` 入口で kind 単位の差し替えが可能。
    - [x] `emit_stmt(Return/Expr/Assign/Try)` を `hook_on_emit_stmt_kind(kind, stmt)` 前提で分割する。
    - [x] `emit_stmt` 本体を「dispatch + fallback」のみ（50行以下目標）へ縮退する。
   - [ ] profile で表現しにくいケースのみ hooks 側へ寄せる（`py2cpp.py` に条件分岐を残さない）。
   - [x] C++ 向け hooks 実装を `src/hooks/cpp/hooks/cpp_hooks.py` として分離する。

## py2cpp 縮退（行数削減）

1. [ ] `src/py2cpp.py` の未移行ロジックを `CodeEmitter` 側へ移し、行数を段階的に削減する。
   - [x] 目標値を固定する（`src/py2cpp.py` 実コード 1500 行以下を当面目標）。
   - [x] ベースライン行数を計測し、`docs-jp/todo.md` に記録する（毎回更新）。: 2026-02-19 時点 `src/py2cpp.py` は `4305` 行（`wc -l`）
   - [ ] `render_expr` の `Call` 分岐（builtin/module/method）を機能単位に分割し、`CodeEmitter` helper へ移す。: `BuiltinCall` / Name/Attribute は helper 分離済み
     - [ ] `dict.get/list.* / set.*` 呼び出し解決を runtime-call map + hook へ移して `py2cpp.py` 直書きを削減する。
     - [x] `BuiltinCall` の `list.* / set.* / dict.*` 分岐を `CppEmitter` 専用 helper（`_render_runtime_call_*_ops`）へ切り出し、`_render_builtin_call` 本体の分岐密度を下げた（2026-02-21）。
     - [x] 文字列系 runtime-call（`py_strip` / `py_replace` / `py_join` など）も helper（`_render_runtime_call_str_ops`）へ切り出し、`_render_builtin_call` をさらに縮退した（2026-02-21）。
     - [x] `Path`/`png`/`gif` の module method 解決を `cpp_hooks.py` 側へ寄せる。: `png/gif` は `Call` + `Attribute`、`Path` は `Attribute(name/stem/parent)` を hooks 移管済み。
   - [x] `render_expr` の `Call` で残っている module method / object method / fallback 呼び出しを 3 helper に分離する。
   - [x] `render_expr` の `Call` で runtime-call 解決前後の前処理（kw 展開・owner 抽出）を helper 化する。
   - [x] `render_expr` の `Call` 分岐を 200 行未満に縮退する（目標値を明示）。: 現在は helper 呼び出し中心で 20 行前後
   - [ ] `render_expr` の算術/比較/型変換分岐を独立関数へ分割し、profile/hook 経由で切替可能にする。: `BinOp` / `Compare` / `UnaryOp` は専用 helper に分離済み
     - [x] `IfExp` の cast 適用ロジックを helper 化する。
     - [ ] `Constant(Name/Attribute)` の基本レンダを `CodeEmitter` 共通へ移す。: `Name` は `CodeEmitter.render_name_ref(...)` へ移管済み（`Constant`/`Attribute` は未移管）。
   - [x] `Compare` 分岐を helper へ切り出す（`Contains` / chain compare / `is` 系）。
   - [x] `UnaryOp` と `BoolOp` の条件式特化ロジックを helper へ切り出す。: `UnaryOp` は `_render_unary_expr` へ分離、`BoolOp` は既存 `render_boolop` を継続利用
   - [x] `Subscript` / `SliceExpr` / `Concat` を helper 化し、`render_expr` 直書きを削減する。: `Subscript`/`SliceExpr` は `_render_subscript_expr` へ分離（`Concat` は既存 helper 経路）
   - [ ] `emit_stmt` の制御構文分岐をテンプレート化して `CodeEmitter.syntax_*` へ寄せる。: `If/While` は専用 helper に分離済み
     - [x] `syntax.if/elif/else`, `syntax.while`, `syntax.for_range`, `syntax.for_each` の最小テンプレート定義を profile へ追加する。: `src/py2cpp.py` で `if/while/for` ヘッダを `syntax_line(...)` 経由へ切替済み（2026-02-20）。
     - [ ] C++ 固有差分（brace省略や range-mode）だけ hook 側で上書きする。
   - [x] `For` / `AnnAssign` / `AugAssign` を helper 化して `emit_stmt` 本体を縮退する。: `For` は既存 `emit_for_each`/`emit_for_range`、`AnnAssign`/`AugAssign` は helper 分離済み
   - [ ] `FunctionDef` / `ClassDef` の共通テンプレート（open/body/close）を `CodeEmitter` 側に寄せる。: `open/close` helper は移管済み。`body` 側は `emit_scoped_stmt_list` / `emit_with_scope` / `emit_scoped_block` を導入し、`If/While/ForRange/FunctionDef` へ適用済み。`ClassDef` 本体適用を継続する。
2. [ ] 未使用関数の掃除を継続する（詳細タスクは「最優先（即時）」へ移動）。
   - [x] `extract_module_leading_trivia` ラッパーを削除。
   - [x] `_stmt_start_line` / `_stmt_end_line` / `_has_leading_trivia` を削除。
   - [x] `py2cpp.py` 内の補助関数で参照ゼロのものを追加洗い出しして削除する。: `_safe_nested_dict` / `_safe_nested_str_map` / `_safe_nested_str_list` / `_load_cpp_runtime_call_map_json` を削除

## selfhost 回復（後段）

1. [ ] `CodeEmitter` の `Any/dict` 境界を selfhost で崩れない実装へ段階移行する。
   - [x] `any_dict_get` / `any_to_dict` / `any_to_list` / `any_to_str` の C++ 生成を確認し、`object.begin/end` 生成を消す。
   - [x] `render_cond` / `get_expr_type` / `_is_redundant_super_init_call` で `optional<dict>` 混入をなくす。
     - [x] `get_expr_type` は `resolved_type` の動的値フォールバックを追加し、selfhost 変換時の空文字化を抑制した（2026-02-20）。
     - [x] `_is_redundant_super_init_call` は `dict` 正規化と `kind` 取得の共通化（`_node_kind_from_dict`）で `Any/object` 境界でも安定化した（2026-02-20）。
     - [x] `render_cond` の同等整理（`optional<dict>` 境界の削減）を実施した。: `repr` の動的値フォールバックと外側括弧除去を追加し、`test/unit/test_code_emitter.py` で回帰固定（2026-02-20）。
     - [x] `render_expr` の先頭正規化で `expr_node` 再代入パターンを除去し、`object -> dict` を1回に固定する。: `kind` 取得を `_node_kind_from_dict` に統一し、手書き fallback 再代入を削減（2026-02-20）。
     - [x] `*_dict_stmt_list` 系引数を `expr.get(..., [])` ではなく `expr.get(...)` + helper 正規化へ統一する。: `dict.get(..., [])` 残存3件（`details`/`graph_adj`）を helper 経由へ置換（2026-02-20）。
   - [x] `test/unit/test_code_emitter.py` に selfhost 境界ケース（`None`, `dict`, `list`, `str`）を追加する。
   - [x] `emit_leading_comments` / `emit_module_leading_trivia` で `Any` 経由をやめ、list[dict] 前提に統一する。
   - [x] `py2cpp.py` の `kind` 判定を `_node_kind_from_dict` / `_dict_any_kind` 経由へ統一し、`dict.get("kind")` 直参照を排除した（2026-02-20）。
   - [x] 回帰防止として `test/unit/test_py2cpp_codegen_issues.py` に「`get(\"kind\")` 直参照禁止」テストを追加した（2026-02-20）。
   - [x] `hook_on_*` 系の `hooks` コンテナ型を selfhost で安定化する。
     - [x] `CodeEmitter` 側の hook 呼び出しを object receiver メソッド参照（`self.hooks.on_*`）から排除する。
     - [x] `selfhost/py2cpp.cpp` で `hooks` が `object` へ退化しないよう、`dict[str, Any]` を維持する初期化経路へ統一する。: `CodeEmitter.hooks` を `dict[str, Any]` へ固定し、`selfhost/py2cpp.cpp` で `inline static dict<str, object> hooks;` を確認（2026-02-20）。
     - [x] `fn(self, ...)` 呼び出しが C++ 側で無効式になる問題を、selfhost 生成時 hook no-op 化で解消した。: `tools/prepare_selfhost_source.py` による置換後 `selfhost/py2cpp.cpp` で `hook_on_*` は `nullopt` 返却のみ（2026-02-20）。
   - [x] `*_dict_get*` の default 引数を `str` / `int` / `list` 別 helper に分離し、`object` 強制変換を減らす。
     - [x] `any_dict_get_bool` / `any_dict_get_list` / `any_dict_get_dict` を追加する。
     - [x] `py_dict_get_default(..., list<object>{})` を全箇所削減する（selfhost compile logで追跡）。: `src/py2cpp.py` / `selfhost/py2cpp.cpp` を grep して残存なし（2026-02-20）。
   - [x] `split_*` / `is_*_type` の引数型を `str` に固定し、`py_slice(object,...)` 生成を消す。
2. [ ] `cpp_type` と式レンダリングで `object` 退避を最小化する。
   - [x] `str|None`, `dict|None`, `list|None` の Union 処理を見直し、`std::optional<T>` 優先にする。: 重複 Union（例: `list[int64]|None|None`）も `optional<...>` に正規化するよう更新し、`test/unit/test_cpp_type.py` を追加（2026-02-20）。
   - [ ] `Any -> object` が必要な経路と不要な経路を分離し、`make_object(...)` の過剰挿入を減らす。
   - [ ] `py_dict_get_default` / `dict_get_node` の既定値引数が `object` 必須になる箇所を整理する。
   - [ ] `py2cpp.py` で `nullopt` を default 値に渡している箇所を洗い出し、型ごとの既定値へ置換する。
   - [ ] `std::any` を経由する経路（selfhost 変換由来）をログベースでリスト化し、順次削除する。
     - [x] `tools/summarize_selfhost_errors.py` 出力の `cannot convert std::any` 発生行をホットスポット表に集約する。: `python3 tools/summarize_selfhost_errors.py selfhost/py2cpp.compile.log selfhost/py2cpp.cpp` で `std_any_hotspots` 集計を表示可能にした（2026-02-21）。
     - [ ] 上位3関数ごとにパッチを分けて改善し、毎回 `check_py2cpp_transpile.py` を通す。
3. [ ] selfhost コンパイルエラーを段階的にゼロ化する。
   - [x] `selfhost/build.all.log` の先頭 200 行を優先して修正し、`total_errors < 300` にする。: 2026-02-18 再計測で `total_errors=82`
   - [x] 同手順で `total_errors < 100` まで減らす。: 2026-02-18 再計測で `total_errors=82`
   - [x] `total_errors <= 50` にする。: 2026-02-19 再計測で `total_errors=25`
   - [x] `total_errors <= 20` にする。: 2026-02-19 再計測で `total_errors=17`
   - [x] `total_errors = 0` にする。: 2026-02-19 再計測で C++ `error:` は 0（残りは単体リンク時の `ld` エラー）
   - [x] 段階ゲート A: `total_errors <= 450` を達成し、`docs-jp/todo.md` に主因更新。: 2026-02-18 再計測で `total_errors=322`
   - [x] 段階ゲート B: `total_errors <= 300` を達成し、同時に `test_code_emitter` 回帰を固定化。: 2026-02-18 再計測で `total_errors=233`、`test/unit/test_code_emitter.py` は 12/12 pass
   - [x] 段階ゲート C-1: `total_errors <= 100` を維持する。: 2026-02-19 再計測で `total_errors=72`
   - [x] 段階ゲート C-2: `tools/check_selfhost_cpp_diff.py` の最小ケースを通す。: `--mode allow-not-implemented` で `mismatches=0`
4. [ ] `selfhost/py2cpp.out` を生成し、最小実行を通す。
   - [x] `tools/build_selfhost.py` を追加し、runtime `.cpp` を含めて `selfhost/py2cpp.out` を生成できるようにする。
   - [x] `selfhost/py2cpp.out` は `__pytra_main(argv)` を実行する状態まで接続する（no-op ではない）。
   - [x] `./selfhost/py2cpp.out sample/py/01_mandelbrot.py test/transpile/cpp2/01_mandelbrot.cpp` を成功させる。
     - [x] 引数パース互換（`INPUT OUTPUT` 形式）と `-o` 形式の両方で通ることを確認する。
       - [x] `argv[0]` 混入で `unexpected extra argument` になる不具合を修正し、`-o` 形式で `not_implemented` まで到達することを確認する（2026-02-19）。
      - [x] `parse_py2cpp_argv` が `INPUT OUTPUT` 形式（`-o` 省略）を受理するように実装した（2026-02-19）。
      - [x] 失敗時に `user_syntax_error` / `input_invalid` / `not_implemented` の分類が維持されることを確認する。: selfhost 実行で `.py` と `.json` の分類を確認済み（2026-02-19）。
   - [x] `./selfhost/py2cpp.out --help` を通す。
   - [x] `./selfhost/py2cpp.out INPUT.py -o OUT.cpp` を通す。
   - [x] 出力された C++ をコンパイル・実行し、Python 実行結果と一致確認する。: `sample/py/04_monte_carlo_pi.py` を selfhost 変換後にコンパイル実行し、`pixels` / `checksum` が Python 実行結果と一致（2026-02-21）。
   - [x] `test/fixtures/core/add.py`（軽量ケース）でも selfhost 変換を実行し、最小成功ケースを確立する。: C++ 実行出力 `True` が `PYTHONPATH=src python3 test/fixtures/core/add.py` と一致（2026-02-21）。
   - [ ] `tools/prepare_selfhost_source.py` の selfhost 専用スタブ整理を継続する。
     - [x] `load_east` を `.json` `input_invalid` / `.py` `not_implemented` に分割した（selfhost 最小モード）。
     - [x] selfhost parser 非対応のネスト関数を含む補助関数（import graph / multi-file）の一部をスタブへ置換した。
     - [x] `Path`/`json` 操作の型退化で C++ 生成が崩れる箇所を段階的に縮退し、`tools/build_selfhost.py` を再 green 化する。: `src/py2cpp.py` の `_python_module_exists_under` / `_runtime_cpp_header_exists_for_module` を selfhost-safe に修正し、`prepare_selfhost_source.py` の対応スタブ（Path 周辺3関数）を除去しても build green を維持（2026-02-21）。
       - [x] 未使用になった `load_east` スタブ置換ヘルパ（`_replace_load_east_for_selfhost`）を削除し、現行実装と乖離した残骸を整理した（2026-02-21）。
      - [x] `tools/build_selfhost.py` は再度 green（`selfhost/py2cpp.out` 生成成功）へ回復した。2026-02-21 時点で `.py` 入力も実処理で変換可能。
      - [x] 暫定運用: `tools/build_selfhost.py` は `cpp/pytra/compiler/*` をリンク対象から除外し、未使用の compiler runtime 由来リンク失敗を回避している（`.py` 入力実装時に再有効化）。
5. [x] selfhost 版と Python 版の変換結果一致検証を自動化する。
   - [x] 比較対象ケース（`test/fixtures` 代表 + `sample/py` 代表）を決める。: `test/fixtures/core/add.py`, `test/fixtures/control/if_else.py`, `sample/py/01_mandelbrot.py`
   - [x] `selfhost/py2cpp.out` と `python3 src/py2cpp.py` の出力差分チェックをスクリプト化する。: `tools/check_selfhost_cpp_diff.py`
   - [x] CI 相当手順（ローカル）に組み込む。: `tools/run_local_ci.py`

## 複数ファイル構成（最終ゴール）

1. [x] 依存解決フェーズを追加する。
   - [x] `import` / `from ... import ...` を収集してモジュール依存グラフを作る。: `--dump-deps` の `graph` 出力で可視化
     - [x] 相対 import（`from .mod import x`）の解決ルールを仕様化する。: 現状は未対応として `input_invalid` 扱い
     - [x] 循環 import 検出時のエラー分類を `input_invalid` で統一する。
   - [x] `pytra.*` とユーザーモジュールの探索パス解決（重複・循環検出）を実装する。
     - [x] 同名モジュール衝突時の優先順位（ユーザー/`pytra`）を仕様化して実装する。: `pytra` 名前空間予約（ユーザー側 `pytra.py` / `pytra/__init__.py` 禁止）
   - [x] 依存グラフを `--dump-deps` などで可視化できるようにする。: `src/py2cpp.py --dump-deps`
## 直近メモ

- 進捗: `except ValueError:` 受理と `return`（値なし）受理を self_hosted parser に追加し、EAST 生成は通過。
- 現在の主要原因（2026-02-18 再計測）:
  1. `BaseEmitter.any_dict_get` が `optional<dict>` に対して `.find/.end` を生成してしまう。
  2. `Any -> object` 変換の影響で、`""` / `list{}` / `nullopt` を default 引数に渡す箇所が大量に不整合化している。
  3. `render_expr` 系 API が `dict|None` 固定のため、selfhost 生成側で `object/std::any` から呼び出した時に詰まる。
  4. 方針として selfhost 専用 lowering は極力増やさず、型付き helper と runtime 補助 API の拡充で汎用的に解消する。
- 更新（2026-02-18）:
  1. `BaseEmitter`（移行後 `CodeEmitter`）側の `any_*` を明示 `if` へ書き換え、ifexp（三項演算子）由来の不整合を削減する下準備を実施。
  2. `selfhost/py2cpp.py` と `selfhost/runtime/cpp/*` を `src` 最新へ同期済み。
  3. 依然として主因は `object` / `optional<dict>` / `std::any` の境界変換（代入・引数渡し・`py_dict_get_default` 呼び出し）に集中している。
- 更新（2026-02-18 selfhost 追加）:
  1. `tools/prepare_selfhost_source.py` を追加し、`src/pytra/compiler/east_parts/code_emitter.py` を `selfhost/py2cpp.py` へ自動インライン展開できるようにした。
  2. `python3 src/py2cpp.py selfhost/py2cpp.py -o selfhost/py2cpp.cpp` は再び通過するようになった。
  3. 現在の主因は `Any/object` 境界由来の C++ 型不整合（2026-02-18 再計測で `total_errors=82`）。
  4. 先頭エラー群は `emit_stmt`/`emit_stmt_list` の文リスト型、`render_boolop` 周辺の `Any` 取り回し、`self` 記号解決の C++ 生成不整合が中心。
  5. 解析補助:
     - `python3 tools/summarize_selfhost_errors.py selfhost/py2cpp.compile.log`
     - `python3 tools/selfhost_error_hotspots.py selfhost/py2cpp.cpp selfhost/py2cpp.compile.log`
  6. 2026-02-18 時点の上位ホットスポット（`selfhost_error_hotspots.py`）:
     - `render_expr`: `69`
     - `emit_class`: `17`
     - `emit_assign`: `15`
- 更新（2026-02-19 selfhost 進捗）:
  1. `tools/prepare_selfhost_source.py` -> `src/py2cpp.py selfhost/py2cpp.py` は継続して通過。
  2. selfhost C++ の型エラー（`error:`）は解消済み。単体リンク失敗は runtime `.cpp` 同時リンクで解消。
  3. 現在の selfhost 実行時は `load_east` スタブのため、`.py` 入力は `[not_implemented]`、`.json` 入力は `[input_invalid]` を返す（設計通りの暫定動作）。
  4. `--help` は selfhost 実行で終了コード `0` で表示されるように修正済み（`parse_py2cpp_argv` の `continue` 依存を回避）。
  5. `a in {"x","y"}` の selfhost C++ 生成は一時オブジェクト生成の都合で不安定なため、CLI 解析経路では `a == "x" or a == "y"` を採用。
  6. `tools/check_selfhost_cpp_diff.py` に `--mode allow-not-implemented`（既定）を追加し、現段階の selfhost 未実装ケースを skip 集計できるようにした。
  7. `py_runtime.h` の `optional<dict<...>>` 向け `py_dict_get` が temporary 参照返却警告を出していたため、値返しへ変更して selfhost ビルド警告を解消。
  8. `tools/run_local_ci.py` を追加し、`check_py2cpp_transpile` / unit tests / selfhost build / selfhost diff（allow-not-implemented）を1コマンドで実行できるようにした。
  9. selfhost の `load_east` に `.json` 入力経路を追加し、当時は C++ runtime 経由で EAST JSON を直接読み込めるようにした（現在は pure Python 実装の正本化方針へ移行中）。
  10. `CppEmitter` 生成時の `CodeEmitter` 基底初期化を `load_cpp_profile()` 付きに修正し、selfhost での `dict key not found: syntax` を解消した。
  11. `tools/selfhost_transpile.py` を追加し、`.py` 入力を一時 EAST JSON 化して selfhost バイナリに渡す暫定運用を可能にした。
  12. selfhost JSON 直入力時の改行崩れ（`\\n` がそのまま出る問題）を修正し、通常の改行付き C++ 出力へ回復した。
  13. selfhost 生成 C++ で関数本体が空になる問題（`emit_stmt_list` の基底 no-op 束縛）を解消し、`return`/式文が出力されるようにした。
  14. selfhost 生成 C++ の `print(...)` 残留を暫定修正し、フォールバックでも `py_print(...)` を出力するようにした。
  15. `tools/check_selfhost_cpp_diff.py --selfhost-driver bridge` の `sample/py/01_mandelbrot.py` 差分を解消（引数順崩れ/`png.write_rgb_png` 残留/浮動小数リテラル差分を修正）。
  16. `test/fixtures/collections/comprehension_filter.py` の selfhost 差分を解消（内包表現 `if` 条件崩れと `list[bool]` 初期化型崩れを修正）。
- 更新（2026-02-21 selfhost 進捗）:
  1. `selfhost/py2cpp.out` で `.py` / `.json` の両入力が実処理で通ることを確認（`--help` は終了コード `0` 維持）。
  2. `tools/check_selfhost_cpp_diff.py --selfhost-driver bridge` は既定ケースで `mismatches=0` を再確認。
  3. selfhost 直実行で `test/fixtures` は expected-fail 除外 `91/91` 変換成功（enum 4件の class 解析失敗を解消）。
  4. `./selfhost/py2cpp.out sample/py/01_mandelbrot.py -o /tmp/out.cpp` と `INPUT OUTPUT` 形式の両方で生成成功を確認。
  5. `sample/py/04_monte_carlo_pi.py` で selfhost 出力差分（`row_sum += ...` が再宣言化）を修正し、`CodeEmitter.any_dict_get_int` の bool 分岐を selfhost 安全な if 文へ変更した。
  17. `tools/check_selfhost_cpp_diff.py --selfhost-driver bridge` の既定ケースで `mismatches=0` を確認。
  2. `g++` コンパイルエラーは `total_errors=72`（`<=100` 維持）を確認。
  3. 現在の上位は `__pytra_main`（import/runtime 参照境界）と `emit_class` / `emit_assign` の `Any` 境界由来の型不整合。
