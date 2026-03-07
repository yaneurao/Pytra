# 実装仕様（Pytra）

<a href="../../en/spec/spec-dev.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>


このドキュメントは、トランスパイラの実装方針・構成・変換仕様をまとめた仕様です。

- フォルダ責務の正本は [`docs/ja/spec/spec-folder.md`](./spec-folder.md) とし、本書では実装仕様そのものを扱います。

## 1. リポジトリ構成

- `src/`
  - `py2cs.py`, `py2x.py --target cpp`, `py2rs.py`, `py2js.py`, `py2ts.py`, `py2go.py`, `py2java.py`, `py2swift.py`, `py2kotlin.py`, `py2rb.py`, `py2lua.py`, `py2php.py`, `py2scala.py`, `py2nim.py`
  - `src/` 直下にはトランスパイラ本体（`py2*.py`）のみを配置する
  - `backends/common/`: 複数言語で共有する基底実装・共通ユーティリティ
  - backend 段階実装の標準ディレクトリは `src/backends/<lang>/{lower,optimizer,emitter}/` とする（正本: `spec-folder.md`）。
  - 当面は `extensions/<topic>/` を併用する（案2）。将来は `lower/optimizer/emitter` 中心へ縮退する（案3）。
  - `backends/common/profiles/` と `backends/<lang>/profiles/`: `CodeEmitter` 用の言語差分 JSON（型/演算子/runtime call/syntax）
  - `runtime/`: 各ターゲット言語のランタイム配置先（正本、`src/runtime/<lang>/pytra/`）
  - `*_module/`: 旧ランタイム配置（互換レイヤ、段階撤去対象）
  - `pytra/`: Python 側の共通ライブラリ（正式）
- `test/`: `py`（入力）と各ターゲット言語の変換結果
- `sample/`: 実用サンプル入力と各言語変換結果
- `docs/ja/`: 仕様・使い方・実装状況

### 1.1 backend 3層標準（非C++）

- 非C++ backend の標準パイプラインは `Lower -> Optimizer -> Emitter` とする。
- 現行の3層適用 backend は `rs/cs/js/ts/go/java/kotlin/swift/ruby/lua/php/scala`。
- `py2<lang>.py` は `load_east3_document -> lower_east3_to_<lang>_ir -> optimize_<lang>_ir -> transpile` の順序を固定し、層を飛び越える処理を追加しない。
- `lower/optimizer` から `emitter` を import しない。`emitter` から `lower/optimizer` を import しない。
- 再発防止の正本チェックは `python3 tools/check_noncpp_east3_contract.py` とする。

### 1.2 backend 共通 artifact / writer 契約（linked-program 期）

linked-program 導入後の backend 共通境界は次とする。

```text
linked module(EAST3)
  -> Lower
  -> Optimizer
  -> ModuleEmitter
  -> ModuleArtifact
  -> ProgramWriter
  -> output tree / manifest / runtime
```

#### `ModuleEmitter`

- 入力:
  - 1 module 分の linked `EAST3`
  - target 固有 option
- 出力:
  - `ModuleArtifact`
- 責務:
  - module 単位の最終レンダリング
  - module 内依存情報の列挙
  - emitter 固有 metadata の付与
- 禁止:
  - 出力ディレクトリ決定
  - runtime 配置
  - build manifest 生成
  - `type_id` / non-escape / ownership の再計算

#### `ModuleArtifact` 最小契約

`ModuleArtifact` は backend 共通の「1 module 分の描画結果」を表す。最低限次を持つ。

- `module_id`
  - canonical module id
- `label`
  - 出力名に使う安定ラベル
- `extension`
  - 例: `.cpp`, `.rs`, `.js`
- `text`
  - 生成ソース文字列
- `is_entry`
  - entry module かどうか
- `dependencies`
  - `module_id` 配列。module 間の依存関係のみを保持し、最終 path は持たない
- `metadata`
  - target 固有の補助情報 object

追加規則:

- `ModuleArtifact` は final output path を持たない。
- `ModuleArtifact` は target ごとの build/layout 情報を埋め込まない。
- 将来 payload 種別が増えても、互換上の最小契約は `text` を返せることとする。

#### `ProgramArtifact` 最小契約

`ProgramArtifact` は 1 program 分の writer 入力であり、最低限次を持つ。

- `target`
- `program_id`
- `entry_modules`
- `modules`
  - `ModuleArtifact[]`
- `layout_mode`
  - `single_file | multi_file`
- `link_output_schema`
  - 例: `pytra.link_output.v1`
- `writer_options`
  - writer 固有 option object

追加規則:

- `ProgramArtifact` は linked-program 段で確定した module 集合をそのまま保持する。
- `ProgramArtifact` は global semantics の canonical source を持ち込まない。global semantics の正本は `link-output.v1` と linked module 側にある。
- `ProgramArtifact` は packaging / build の入力であり、language semantics の再判断点ではない。

#### `ProgramWriter`

- 入力:
  - `ProgramArtifact`
  - `output_root`
- 出力:
  - 出力 tree
  - 必要なら build manifest
- 責務:
  - ファイル path 決定
  - multi-file / single-file layout
  - runtime 配置
  - build metadata / manifest 生成
- 禁止:
  - module text の再生成
  - module 境界の再分割
  - `type_id` / non-escape / ownership の再解釈

既定実装:

- non-C++ backend の既定は `SingleFileProgramWriter` とする。
- C++ は `CppProgramWriter` を用い、`manifest.json` / `Makefile` / runtime tree を扱う。
- 実装同期（2026-03-07）:
  - `backend_registry.py` / `backend_registry_static.py` は backend spec を正規化するとき、`emit_module` と `program_writer` を必ず生やす。
  - `program_writer` 未指定 backend の既定は `backends/common/program_writer.py` の `write_single_file_program(...)` とする。
  - `ir2lang.py` の single-module 経路は `emit_module -> ProgramArtifact -> ProgramWriter` を通し、旧 `emit_source()` は compatibility wrapper として `ModuleArtifact.text` を返すだけに縮退した。

互換契約:

- 旧 `emit -> str` API は「`ModuleArtifact(text only)` を返す旧 emitter + `SingleFileProgramWriter`」への compatibility wrapper として扱う。
- 新規 backend / 新規経路は `emit_module + program_writer` 契約を正本とし、旧 unary emit を増やさない。

### 1.3 `src/pytra/` 公開API（実装基準）

`src/pytra/` は selfhost を含む共通 Python ライブラリの正本です。  
`_` で始まる名前は内部実装扱いとし、以下を公開APIとして扱います。

- トランスパイル対象コードでの標準モジュール直接 import は原則非推奨とし、`pytra.std.*` 明示 import を推奨します。
- 互換 shim が存在する標準モジュール（`math` / `random` / `timeit` / `enum` など）は、変換時に `pytra.std.*` へ正規化可能です。
- import は `pytra.*` とユーザー自作モジュール（`.py`）を許可します。

- `pytra.utils.assertions`
  - 関数: `py_assert_true`, `py_assert_eq`, `py_assert_all`, `py_assert_stdout`
- `pytra.std.pathlib`
  - class: `Path`
  - メンバー: `parent`, `parents`, `name`, `suffix`, `stem`, `resolve`, `exists`, `mkdir`, `read_text`, `write_text`, `glob`, `cwd`
- `pytra.std.json`
  - 関数: `loads`, `dumps`
- `pytra.std.sys`
  - 変数: `argv`, `path`, `stderr`, `stdout`
  - 関数: `exit`, `set_argv`, `set_path`, `write_stderr`, `write_stdout`
- `pytra.std.math`
  - 定数: `pi`, `e`
  - 関数: `sqrt`, `sin`, `cos`, `tan`, `exp`, `log`, `log10`, `fabs`, `floor`, `ceil`, `pow`
- `pytra.std.time`
  - 関数: `perf_counter`
- `pytra.std.timeit`
  - 関数: `default_timer`
- `pytra.std.random`
  - 関数: `seed`, `random`, `randint`
- `pytra.std.os`
  - 変数: `path`（`join`, `dirname`, `basename`, `splitext`, `abspath`, `exists`）
  - 関数: `getcwd`, `mkdir`, `makedirs`
- `pytra.std.glob`
  - 関数: `glob`
- `pytra.std.argparse`
  - クラス: `ArgumentParser`, `Namespace`
  - 関数: `ArgumentParser.add_argument`, `ArgumentParser.parse_args`
- `pytra.std.re`
  - 定数: `S`
  - クラス: `Match`
  - 関数: `match`, `sub`
- `pytra.std.enum`
  - クラス: `Enum`, `IntEnum`, `IntFlag`
- `pytra.utils.png`
  - 関数: `write_rgb_png`
- `pytra.utils.gif`
  - 関数: `grayscale_palette`, `save_gif`
- `pytra.utils.browser`
  - 変数/クラス: `document`, `window`, `DOMEvent`, `Element`, `CanvasRenderingContext`
- `pytra.utils.browser.widgets.dialog`
  - クラス: `Dialog`, `EntryDialog`, `InfoDialog`
- `pytra.compiler.east`
  - クラス/定数: `EastBuildError`, `BorrowKind`, `INT_TYPES`, `FLOAT_TYPES`
  - 関数: `convert_source_to_east`, `convert_source_to_east_self_hosted`, `convert_source_to_east_with_backend`, `convert_path`, `render_east_human_cpp`, `main`
- `pytra.compiler.east_parts.east_io`
  - 関数: `extract_module_leading_trivia`, `load_east_from_path`

### enum サポート（現状）

- 入力側は `from pytra.std.enum import Enum, IntEnum, IntFlag` を使用します（標準 `enum` は使用不可）。
- `Enum` / `IntEnum` / `IntFlag` のクラス本体は `NAME = expr` 形式のメンバー定義をサポートします。
- C++ 生成では `enum class` へ lower します。
  - `IntEnum` / `IntFlag` には `int64` との比較演算子を補助生成します。
  - `IntFlag` には `|`, `&`, `^`, `~` の演算子を補助生成します。

## 2. C# 変換仕様（`py2cs.py`）

- EAST ベースで変換します（`.py/.json -> EAST -> C#`）。
- `py2cs.py` は CLI + 入出力の薄いオーケストレータに限定します。
- C# 固有ロジックは `src/backends/cs/emitter/cs_emitter.py` に分離します。
- 言語差分は `src/backends/cs/profiles/*.json`（`types/operators/runtime_calls/syntax`）で管理します。
- `import` / `from ... import ...` は EAST `meta.import_bindings` を正本として `using` 行へ変換します。
- 主要型は `src/backends/cs/profiles/types.json` を通して変換します（例: `int64 -> long`, `float64 -> double`, `str -> string`）。

## 3. C++ 変換仕様（`py2x.py --target cpp`）

- Python AST を解析し、単一 `.cpp`（必要 include 付き）を生成します。
- `CppEmitter` 実装は `src/backends/cpp/emitter/cpp_emitter.py` へ分離され、`py2x.py --target cpp` は CLI / オーケストレーション層として扱います。
- 言語機能の詳細なサポート粒度（`enumerate(start)` / `lambda` / 内包表記など）は [py2cpp サポートマトリクス](../language/cpp/spec-support.md) を正として管理します。
- 生成コードは `src/runtime/cpp/` のランタイム補助実装を利用します。
- 補助関数は生成 `.cpp` に直書きせず、`runtime/cpp/pytra/built_in/py_runtime.h` 側を利用します。
- `json` に限らず、Python 標準ライブラリ相当機能は `src/pytra/std/*.py` を正本とし、`runtime/cpp` 側へ独自実装を追加しません。
  - C++ 側で必要な処理は、これら Python 正本のトランスパイル結果を利用します。
- class は `pytra::gc::PyObj` 継承の C++ class として生成します（例外クラスを除く）。
- class method 呼び出しは `src/backends/cpp/emitter/call.py` の dispatch mode（`virtual` / `direct` / `fallback`）で描画先を分離します。
  - `virtual` / `direct`: ユーザー定義 class method シグネチャが解決できる経路。
  - `fallback`: `BuiltinCall` lower 前提経路や runtime/type_id API（`IsInstance/IsSubtype/IsSubclass/ObjTypeId`）など、virtual dispatch 置換対象外の経路。
- selfhost 回帰では `sample/cpp` と `src/runtime/cpp/pytra-gen`（`built_in/type_id.cpp` 除外）に `type_id` 比較/switch dispatch を残さないことをテストで固定します（`test_selfhost_virtual_dispatch_regression.py`）。
- class member は `inline static` として生成します。
- `@dataclass` はフィールド定義とコンストラクタ生成を行います。
- `raise` / `try` / `except` / `while` をサポートします。
- list/str 添字境界チェックは `--bounds-check-mode` で制御します。
  - `off`（既定）: 通常の `[]` アクセスを生成します。
  - `always`: 実行時チェック付きの `py_at_bounds` を生成します。
  - `debug`: デバッグビルド時のみチェックする `py_at_bounds_debug` を生成します。
- `//`（floor division）は `--floor-div-mode` で制御します。
  - `native`（既定）: C++ の `/` をそのまま生成します。
  - `python`: Python 準拠の floor division になるように `py_floordiv` を生成します。
- `%`（剰余）は `--mod-mode` で制御します。
  - `native`（既定）: C++ の `%` をそのまま生成します。
  - `python`: Python 準拠の剰余意味論になるようにランタイム補助を挟みます。
- `int` 相当の出力幅は `--int-width` で制御します。
  - `64`（既定）: `int64`/`uint64` を出力します。
  - `32`: `int32`/`uint32` を出力します。
  - `bigint`: 未実装（指定時エラー）。
- 文字列添字/スライスは次で制御します。
  - `--str-index-mode {byte,native}`（`codepoint` は未実装）
  - `--str-slice-mode {byte}`（`codepoint` は未実装）
  - 現行の `byte` / `native` では、`str[i]` の返り値型は `str`（1文字）です。
  - 添字境界外挙動は `--bounds-check-mode` に従います（`off`/`always`/`debug`）。
- 生成コード最適化は `-O0`〜`-O3` で制御します。
  - `-O0`: 最適化なし（デバッグ/差分調査向け）
  - `-O1`: 軽量最適化
  - `-O2`: 中程度の最適化
  - `-O3`（既定）: 積極最適化
- 生成 C++ のトップ namespace は `--top-namespace NS` で指定できます。
  - 未指定時（既定）はトップ namespace なし。
  - 指定時は `main` をグローバルに残し、`NS::__pytra_main(...)` を呼び出します。
- list/str の負数添字（例: `a[-1]`）は `--negative-index-mode` で制御します。
  - デフォルトは `const_only`（定数の負数添字のみ Python 互換処理を有効化）。
  - `always`: すべての添字アクセスで Python 互換の負数添字処理を有効化。
  - `off`: Python 互換の負数添字処理を行わず、通常の `[]` を生成。
- PNG 画像の一致判定は、ファイルバイト列の完全一致を基準とします。
- GIF 画像の一致判定も、ファイルバイト列の完全一致を基準とします。

### 3.0 複数ファイル出力と `manifest.json` / build（実装済み）

- `py2x.py --target cpp` の既定出力モードは `--multi-file` です（明示 `--single-file` 指定で単一 `.cpp` へ切替）。
- 互換挙動として、出力先が `.cpp` で終わる場合はモード明示なしでも単一ファイル出力を選びます。
- `--multi-file` 出力では `--output-dir`（未指定時は `out`）配下へ次を生成します。
  - `include/`（モジュールごとの `*.h`）
  - `src/`（モジュールごとの `*.cpp`）
  - `manifest.json`
- `manifest.json` には少なくとも次のキーを出力します。
  - `entry`
  - `include_dir`
  - `src_dir`
  - `modules`（要素は `module`, `label`, `header`, `source`, `is_entry`）
- 複数ファイル出力の C++ ビルドには `tools/build_multi_cpp.py` を使います。
  - 基本形: `python3 tools/build_multi_cpp.py out/manifest.json -o out/app.out`
  - オプション: `--std`（既定 `c++20`）、`--opt`（既定 `-O2`）
  - `manifest.modules` が配列でない、または有効 `source` が空の場合はエラー終了します。
  - `manifest.include_dir` が未指定の場合は `manifest` 同階層 `include/` を既定として扱います。
- `docs/ja/spec/spec-make.md` にある `./pytra --build` / `src/pytra-cli.py` / `tools/gen_makefile_from_manifest.py` は、2026-02-24 時点で実装済みです。

### py2cpp 共通化ガードルール

- `src/backends/cpp/cli.py` へ新規ロジックを追加する場合は、先に「C++ 固有」か「言語非依存」かを分類します。
- 言語非依存と判定した処理は `src/toolchain/compiler/`（`east_parts/` や `CodeEmitter` 含む）へ実装し、`py2x.py --target cpp` へは直接追加しません。
- `py2x.py --target cpp` に残す処理は C++ 固有責務（型写像、runtime 名解決、header/include 生成、C++ 構文最適化）に限定します。
- 例外として、後方互換の公開 API ラッパ（`load_east`, `_analyze_import_graph`, `build_module_east_map`, `dump_deps_graph_text`）のみ `py2x.py --target cpp` に残置できます。これらは共通層 API への委譲に限定します。
- 既存の `py2x.py --target cpp` 汎用 helper を修正する場合も、同時に共通層移管可否を検討し、`docs/ja/plans/p1-py2cpp-reduction.md` の決定ログへ記録します。
- 緊急 hotfix で例外的に `py2x.py --target cpp` へ汎用 helper を暫定追加する場合は、実装箇所に `TEMP-CXX-HOTFIX` コメントと対応 `ID` を残します。
- 暫定追加した helper は「追加日から 7 日以内」または「次回 PATCH リリースまで」の早い方で、`src/toolchain/compiler/` 側へ後追い抽出します。
- 後追い抽出完了まで、`docs/ja/todo/index.md` に抽出タスクを未完了で保持し、`tools/check_py2cpp_helper_guard.py` の allowlist 更新理由を `docs/ja/plans/p1-py2cpp-reduction.md` に記録します。
- 上記の責務境界は `tools/check_py2cpp_boundary.py` で検証し、`tools/run_local_ci.py` で常時実行します。
- `src/toolchain/compiler/transpile_cli.py` の汎用 helper は機能グループごとの `class + @staticmethod`（`*Helpers`）を正本とし、`py2x.py --target cpp` 側は class 単位 import + 起動時束縛で参照します。トップレベル関数は当面、既存 CLI / selfhost 互換のために併存させます。
- `ImportGraphHelpers` のうち `analyze_import_graph` / `build_module_east_map` は、実装本体を `src/toolchain/compiler/east_parts/east1_build.py` へ委譲する thin wrapper として運用します（互換公開 API のみ保持）。
- `py2x.py --target cpp` の import graph/build 入口（`_analyze_import_graph`, `build_module_east_map`）は `East1BuildHelpers` への委譲に限定し、`transpile_cli` へ実装詳細を持ち込みません。
- 回帰は `test/unit/ir/test_east1_build.py`・`test/unit/backends/cpp/test_py2cpp_east1_build_bridge.py`・`tools/check_py2cpp_transpile.py` を正本導線とし、依存解析責務の逆流を検出します。
- `P0-PY2CPP-SPLIT-01` の回帰として `python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_smoke.py'` を併用し、`py2x.py --target cpp` の責務境界（`tools/check_py2cpp_boundary.py`）が維持されていることを確認します。

### 3.1 import と `runtime/cpp` 対応

`py2x.py --target cpp` は import 文に応じて include を生成します。

- `import pytra.std.math` -> `#include "pytra/std/math.h"`
- `import pytra.std.pathlib` -> `#include "pytra/std/pathlib.h"`
- `import pytra.std.time` / `from pytra.std.time import ...` -> `#include "pytra/std/time.h"`
- `import pytra.utils.png` -> `#include "pytra/utils/png.h"`
- `import pytra.utils.gif` -> `#include "pytra/utils/gif.h"`
- GC は常時 `#include "runtime/cpp/pytra/built_in/gc.h"` を利用

`module.attr(...)` 呼び出しは、`LanguageProfile`（JSON）の設定またはモジュール名→namespace 解決で C++ 側へ解決します。

- 例: `runtime_calls.module_attr_call.pytra.std.sys.write_stdout -> pytra::std::sys::write_stdout`
- map 未定義の場合は import モジュール名から C++ namespace を導出して `ns::attr(...)` へフォールバックします
- 起動時に profile JSON を読み込み、未定義項目は共通既定値とフォールバック規則で補完します。

補足:

- import 情報の正本は EAST の `meta.import_bindings` です（`ImportBinding[]`）。
- `from module import symbol` は EAST の `meta.qualified_symbol_refs`（`QualifiedSymbolRef[]`）へ正規化し、backend 手前で alias 解決を完了させます。
- `meta.import_modules` / `meta.import_symbols` は互換用途として残し、正本から導出します。
- `import module as alias` は `alias.attr(...)` を `module.attr(...)` として解決します。
- `from module import *` は `binding_kind=wildcard` として保持し、変換を継続します。
- 相対 import（`from .mod import x`）は現状未対応です。検出時は `input_invalid` として終了します。
- `pytra` 名前空間は予約です。入力ルート配下の `pytra.py` / `pytra/__init__.py` は衝突として `input_invalid` を返します。
- ユーザーモジュール探索は「入力ファイルの親ディレクトリ基準」で行います（`foo.bar` -> `foo/bar.py` または `foo/bar/__init__.py`）。
- 未解決ユーザーモジュール import と循環 import は `input_invalid` で早期エラーにします。
- `from M import S` のみがある状態で `M.T` を参照した場合、`M` は束縛されないため `input_invalid`（`kind=missing_symbol`）として扱います。

主な補助モジュール実装:

- `src/runtime/cpp/pytra/std/math.h`, `src/runtime/cpp/pytra/std/math.cpp`
- `src/runtime/cpp/pytra/std/random.h`, `src/runtime/cpp/pytra/std/random.cpp`
- `src/runtime/cpp/pytra/std/timeit.h`, `src/runtime/cpp/pytra/std/timeit.cpp`
- `src/runtime/cpp/pytra/std/pathlib.h`, `src/runtime/cpp/pytra/std/pathlib.cpp`
- `src/runtime/cpp/pytra/std/time.h`, `src/runtime/cpp/pytra/std/time.cpp`
- `src/runtime/cpp/pytra/std/json.h`, `src/runtime/cpp/pytra/std/json.cpp`
- `src/runtime/cpp/pytra/built_in/gc.h`, `src/runtime/cpp/pytra/built_in/gc.cpp`
- `src/runtime/cpp/pytra/std/sys.h`, `src/runtime/cpp/pytra/std/sys.cpp`
- `src/runtime/cpp/pytra/utils/png.h`, `src/runtime/cpp/pytra/utils/png.cpp`
- `src/runtime/cpp/pytra/utils/gif.h`, `src/runtime/cpp/pytra/utils/gif.cpp`
- `src/runtime/cpp/pytra/utils/assertions.h`, `src/runtime/cpp/pytra/utils/assertions.cpp`
- `src/runtime/cpp/pytra/utils/browser.h`, `src/runtime/cpp/pytra/utils/browser.cpp`
- `src/runtime/cpp/pytra/utils/browser/widgets/dialog.h`, `src/runtime/cpp/pytra/utils/browser/widgets/dialog.cpp`
- `src/runtime/cpp/pytra/built_in/py_runtime.h`

`src/runtime/cpp/pytra/built_in/` の位置づけ:

- Python 組み込み型/基盤機能の C++ 実装を置く共通層です。
- 例: GC、I/O、bytes 補助、コンテナ/文字列ラッパ。
- 言語固有モジュール (`src/runtime/cpp/pytra/std/*`, `src/runtime/cpp/pytra/utils/*`) から再利用されます。
- `py_runtime.h` は `str/path/list/dict/set` を直接 include します（`containers.h` は廃止）。
- `built_in` 配下ヘッダの include guard は相対パス由来の `PYTRA_BUILT_IN_*` 命名で統一します。

`src/runtime/cpp/pytra/built_in/py_runtime.h` のコンテナ方針:

- `list<T>`: `std::vector<T>` ラッパー（`append`, `extend`, `pop` を提供）
- `dict<K, V>`: `std::unordered_map<K,V>` ラッパー（`get`, `keys`, `values`, `items` を提供）
- `set<T>`: `std::unordered_set<T>` ラッパー（`add`, `discard`, `remove` を提供）
- `str`, `list`, `dict`, `set`, `bytes`, `bytearray` は「標準コンテナ継承」ではなく、Python 互換 API を持つ wrapper として扱う。

制約:

- Python 側で import するモジュールは、原則として各ターゲット言語ランタイムにも対応実装を用意する必要があります。
- 生成コードで使う補助関数は、各言語のランタイムモジュールへ集約し、生成コードへの重複定義を避けます。
- `object` 型値（`Any` 由来を含む）への属性アクセス・メソッド呼び出しは、言語制約として未許可（禁止）とします。
  - EAST/emit 時に `object` レシーバのメソッド呼び出しを許容しない前提で実装すること。

### 3.2 関数引数の受け渡し方針

- コピーコストが高い型（`string`, `vector<...>`, `unordered_map<...>`, `unordered_set<...>`, `tuple<...>`）は、関数内で直接変更されない場合に `const T&` で受けます。
- 引数の直接変更が検出された場合は値渡し（または非 const）を維持します。
- 直接変更判定は、代入・拡張代入・`del`・破壊的メソッド呼び出し（`append`, `extend`, `insert`, `pop` など）を対象に行います。

### 3.3 画像系ランタイム（PNG/GIF）方針

- `png` / `gif` は Python 側（`src/pytra/utils/`）を正本実装とします。
- 各言語の `*_module` 実装は、原則として正本 Python 実装のトランスパイル成果物を利用します。
- 全言語で `src/runtime/<lang>/pytra-core/`（手書き）と `src/runtime/<lang>/pytra-gen/`（正本由来生成物）を分離し、画像runtime本体は必ず `pytra-gen` 側へ置きます。
- `py_runtime.*` など core 側ファイルへの画像エンコード本体直書きは禁止し、必要時は `pytra-gen` API への薄い委譲のみに限定します。
- `pytra-gen` 側の画像runtimeには `source: src/pytra/utils/{png,gif}.py` と `generated-by: ...` を必須とし、手編集運用を禁止します。
- `png/gif` エンコード本体を言語別に手書き実装してはいけません。
- 言語別で許可するのは、最小の I/O アダプタ・ランタイム接続コードのみです（エンコード本体ロジックの複製は禁止）。
- 言語間一致は「生成ファイルのバイト列完全一致」を主判定とします。
- `src/pytra/utils/png.py` は `binascii` / `zlib` / `struct` に依存しない pure Python 実装（CRC32/Adler32/DEFLATE stored block）を採用します。
- 受け入れ基準:
  - 置換作業中は、同一入力に対して `src/pytra/utils/*.py` 出力と各言語ランタイム出力のバイト列が一致することを必須とします。
  - C++ では `tools/verify_image_runtime_parity.py` を実行して PNG/GIF の最小ケース一致を確認します。

### 3.3.1 std/utils 正本運用ガード（手書き禁止）

- `src/pytra/std/*.py` および `src/pytra/utils/*.py` を runtime 機能の唯一正本とする。
- `src/runtime/<lang>/pytra-core/**` および `src/runtime/<lang>/pytra/**` へ、正本と同等のロジックを手書き実装してはならない。
- 正本由来コードは必ず `src/runtime/<lang>/pytra-gen/**` に生成し、`source:` / `generated-by:` トレースを保持する。
- 例外（既存負債）は `tools/runtime_std_sot_allowlist.txt` に明示し、無記録の追加は禁止する。
- 検証の正本は `python3 tools/check_runtime_std_sot_guard.py` とし、`tools/run_local_ci.py` で常時実行する。

### 3.4 Python 補助ライブラリ命名

- 旧 `pylib.runtime` 互換名は廃止済みで、`pytra.utils.assertions` を正とします。
- テスト補助関数（`py_assert_*`）は `from pytra.utils.assertions import ...` で利用します。

### 3.5 画像ランタイム最適化ポリシー（py2cpp）

- 対象: `src/runtime/cpp/pytra/utils/png.cpp` / `src/runtime/cpp/pytra/utils/gif.cpp`（自動生成）。
- 前提: `src/pytra/utils/png.py` / `src/pytra/utils/gif.py` を正本とし、意味差を導入しない。
- 生成手順:
  - `python3 src/py2x.py src/pytra/utils/png.py --target cpp -o /tmp/png.cpp`
  - `python3 src/py2x.py src/pytra/utils/gif.py --target cpp -o /tmp/gif.cpp`
  - 生成物は `src/runtime/cpp/pytra/utils/png.cpp` / `src/runtime/cpp/pytra/utils/gif.cpp` に直接出力される。
  - これら 2 ファイルの本体ロジックを手書きで追加してはならない。
  - C++ namespace は生成元 Python ファイルのパスから自動導出する（ハードコードしない）。
    - 例: `src/pytra/utils/gif.py` -> `pytra::utils::gif`
    - 例: `src/pytra/utils/png.py` -> `pytra::utils::png`
- 許容する最適化:
  - ループ展開・`reserve` 追加・一時バッファ削減など、出力バイト列を変えない最適化。
  - 例外メッセージ変更を伴わない境界チェックの軽量化。
- 原則禁止:
  - 画像出力仕様を変える最適化（PNG chunk 構成、GIF 制御ブロック、色テーブル順など）。
  - Python 正本と異なる既定値・フォーマット・丸め方への変更。
- 受け入れ条件:
  - 変更後に `python3 tools/verify_image_runtime_parity.py` が `True` を返すこと。
  - `test/unit/common/test_image_runtime_parity.py` と `test/unit/backends/cpp/test_py2cpp_features.py` を通過すること。

## 4. 検証手順（C++）

1. Python 版トランスパイラで `test/fixtures` を `test/transpile/cpp` へ変換
2. 生成 C++ を `test/transpile/obj/` にコンパイル
3. 実行結果を Python 実行結果と比較
4. セルフホスティング検証時は自己変換実行ファイルで `test/fixtures` -> `test/transpile/cpp2` を生成
5. `test/transpile/cpp` と `test/transpile/cpp2` の一致を確認

### 4.1 selfhost 検証のゴール条件

- 必須条件:
  - `selfhost/py2cpp.py` から生成した `selfhost/py2cpp.cpp` がコンパイル成功する。
  - その実行ファイルで `sample/py/01_mandelbrot.py` を C++ へ変換できる。
- 推奨確認:
  - `src/backends/cpp/cli.py` 生成版と `selfhost` 生成版の C++ ソース差分を確認する（差分自体は許容）。
  - 変換後 C++ をコンパイル・実行し、Python 実行結果と一致することを確認する。

### 4.2 一致判定条件（selfhost / 通常比較）

- ソース一致:
  - 生成 C++ の全文一致は「参考指標」であり、必須条件ではない。
- 実行一致:
  - 同じ入力に対して、Python 実行結果と生成 C++ 実行結果が一致することを必須とする。
- 画像一致:
  - PNG/GIF ともに、出力ファイルのバイト列完全一致を必須とする。

## 5. EASTベース C++ 経路

- `src/toolchain/compiler/east.py`: Python -> EAST JSON（正本）
- `src/toolchain/compiler/east_parts/east_io.py`: `.py/.json` 入力から EAST 読み込み、先頭 trivia 補完（正本）
- `src/backends/common/emitter/code_emitter.py`: 各言語エミッタ共通の基底ユーティリティ（ノード判定・型文字列補助・`Any` 安全変換）
- `src/backends/cpp/cli.py`: EAST JSON -> C++
- `src/runtime/cpp/pytra/built_in/py_runtime.h`: C++ ランタイム集約
- 責務分離:
  - `range(...)` の意味解釈は EAST 構築側で完了させる
  - `src/backends/cpp/cli.py` は正規化済み EAST を文字列化する
  - 言語非依存の補助ロジックは `CodeEmitter` 側へ段階的に集約する
- 出力構成方針:
  - 最終ゴールは「モジュール単位の複数ファイル出力（`.h/.cpp`）」とする。
  - 単一 `.cpp` 出力は移行期間の互換経路として扱う。

### 5.1 CodeEmitter テスト方針

- `src/backends/common/emitter/code_emitter.py` の回帰は `test/unit/common/test_code_emitter.py` で担保します。
- 主対象:
  - 出力バッファ操作（`emit`, `emit_stmt_list`, `next_tmp`）
  - 動的入力安全化（`any_to_dict`, `any_to_list`, `any_to_str`, `any_dict_get`）
  - ノード判定（`is_name`, `is_call`, `is_attr`, `get_expr_type`）
  - 型文字列補助（`split_generic`, `split_union`, `normalize_type_name`, `is_*_type`）
- `CodeEmitter` に機能追加・仕様変更した場合は、同ファイルへ対応テストを追加してから利用側エミッタへ展開します。

### 5.2 EASTベース Rust 経路（段階移行）

- `src/py2rs.py` は CLI + 入出力の薄いオーケストレータに限定する。
- Rust 固有の出力処理は `src/backends/rs/emitter/rs_emitter.py`（`RustEmitter`）へ分離する。
- `src/py2rs.py` は `src/backends/common/` / `src/rs_module/` に依存しない（`src/runtime/rs/pytra/` 基準で統一済み）。
- 言語固有差分は `src/backends/rs/profiles/` と `src/backends/rs/` に分離する。
- 変換可否のスモーク確認は `tools/check_py2rs_transpile.py` を正本とする。
- `--east-stage` の既定は `3`、`--east-stage 2` は移行互換モード（警告付き）として扱う。
- 現時点の到達点は「変換成功（transpile success）を優先」であり、Rust コンパイル互換・出力品質は段階的に改善する。

### 5.3 EASTベース JavaScript 経路（段階移行）

- `src/py2js.py` は CLI + 入出力の薄いオーケストレータに限定する。
- JavaScript 固有の出力処理は `src/backends/js/emitter/js_emitter.py`（`JsEmitter`）へ分離する。
- `src/py2js.py` は `src/backends/common/` に依存しない。
- 言語固有差分は `src/backends/js/profiles/` と `src/backends/js/` に分離する。
- `browser` / `browser.widgets.dialog` は外部提供ランタイム（ブラウザ環境）として扱い、`py2js` 側では import 本体を生成しない。
- 変換可否のスモーク確認は `tools/check_py2js_transpile.py` を正本とする。
- `--east-stage` の既定は `3`、`--east-stage 2` は移行互換モード（警告付き）として扱う。

### 5.4 責務境界（CodeEmitter / EAST parser / compiler共通層）

- `CodeEmitter` の責務:
  - 入力済み EAST（ノード + `meta`）を受け取り、言語 profile/hooks を適用してコード文字列を生成する。
  - スコープ管理・式/文の共通 lower・テンプレート展開など、出力生成に閉じた処理のみを持つ。
  - ファイルシステム走査、import グラフ解析、プロジェクト全体依存解決は持たない。
  - `meta.dispatch_mode` は入力値を読むだけにし、mode 再決定や意味論差し替えを行わない。
  - `CodeEmitter` は `EAST3` 以降の「構文写像専任」とし、意味論 lower（`EAST2 -> EAST3` 相当）は担当しない。
  - 禁止事項: dispatch mode の意味適用、`type_id`/boxing/built-in の意味論決定、backend/hook 側での再解釈。
- EAST parser（`src/toolchain/compiler/east.py`）の責務:
  - 単一入力（`.py`）を字句解析/構文解析し、単一モジュール EAST を生成する。
  - `range` などの言語非依存正規化と、単一ファイル内で完結する型/symbol 補助情報の付与に専念する。
  - 複数モジュール横断の import グラフ解析や module index 構築は持たない。
  - ルート契約（`east_stage`, `schema_version`, `meta.dispatch_mode`）を満たす EAST 文書を生成/保持する。
- compiler 共通層（`src/toolchain/compiler/` 配下で段階抽出）の責務:
  - FS 依存の import 解決、module EAST map 構築、symbol index / type schema 構築、deps dump を担当する。
  - 各 `py2*.py` CLI はこの共通層で解析を完了し、その結果を `CodeEmitter` に渡す構成とする。
  - `--object-dispatch-mode` はコンパイル開始時に 1 回だけ確定し、段間で `meta.dispatch_mode` として保持する。
  - dispatch mode の意味論適用は `EAST2 -> EAST3` lowering のみで実施し、backend/hook では再判断しない。

## 6. LanguageProfile / CodeEmitter

- `CodeEmitter` は言語非依存の骨組み（ノード走査、スコープ管理、共通補助）を担当します。
- 言語固有差分は `LanguageProfile` JSON に定義します。
  - 型マップ
  - 演算子マップ
  - runtime call マップ
  - 構文テンプレート
- JSON だけで表現しにくい例外ケースは `hooks` で処理します。
- 詳細スキーマは `docs/ja/spec/spec-language-profile.md` を正本とします。
- `render_expr` の hook 優先順位は「`on_render_expr_<kind>` -> `on_render_expr_kind` -> `on_render_expr_leaf/complex` -> emitter 既定実装」を共通規約とします。
- kind 専用 hook 名は EAST kind の snake_case 変換で決めます（例: `IfExp -> on_render_expr_if_exp`）。
- `py2ts.py` は現状 JavaScript emitter 経由のプレビュー実装のため、TypeScript でも同じ `render_expr` hook 順序・命名規約を適用します。

### 6.1 backend runtime metadata 契約

- backend / emitter / hook が runtime 呼び出し判定に使ってよい入力は、`runtime_module_id`, `runtime_symbol`, `semantic_tag`, `runtime_call`, `resolved_runtime_call`, `resolved_runtime_source`、および lowerer/linker が付与した adapter kind / import binding metadata に限ります。
- backend / emitter / hook が source-side knowledge を見て分岐してはなりません。
  - 例: `module_id == "math"`, `owner == "math"`, `module_name == "pytra.utils"`, `resolved_runtime.endswith(".pi")`
  - 例: `pyMathPi`, `pyMathE`, `save_gif`, `write_rgb_png`, `grayscale_palette` の helper 名で意味論を決める
  - 例: `save_gif` の positional arity / default / keyword (`delay_cs`, `loop`) を emitter が直解釈する
- target 固有 backend がしてよいのは、解決済み metadata を target syntax へ描画することだけです。
  - 例: `runtime_symbol=sin` を `scala.math.sin` へ描画する
  - 例: resolved import を `using` / `use` / `import` / `#include` へ並べる
- target helper 名が最終出力に現れること自体は許可されます。ただし、それは index/lowerer が決めた target symbol を描画した結果であり、source-side module 名や helper ABI の再解釈であってはなりません。
- emitter source に上記の禁止知識が再侵入していないことは、source-scan guard と representative backend smoke で継続監査します。

## 7. 実装上の共通ルール

- `src/backends/common/` には言語非依存で再利用される処理のみを配置します。
- 言語固有仕様（型マッピング、予約語、ランタイム名など）は `src/backends/common/` に置きません。
- ランタイム実体は `src/runtime/<lang>/pytra/` に配置し、`src/*_module/` 直下へ新規実体を追加しません。
- `py2x.py --target cpp` と `py2rs.py` で共通化できる処理は、各エミッタへ直接足さずに `CodeEmitter` 側へ先に寄せます。
- 言語固有分岐は `hooks` / `profiles` 側へ分離し、`py2*.py` は薄いオーケストレータを維持します。
- runtime module / helper ABI / source-side stdlib 名の解決は `profiles` / `runtime symbol index` / lowerer 側で完結させ、emitter 本体に `math` / `png` / `gif` / `save_gif` / `write_rgb_png` などの分岐を増やしません。
- CLI の共通引数（`input`/`output`/`--negative-index-mode`/`--parser-backend` など）は `src/toolchain/compiler/transpile_cli.py` へ集約し、各 `py2*.py` の `main()` から再利用します。
- selfhost 対象コードでは、動的 import（`try/except ImportError` による分岐 import や `importlib`）を避け、静的 import のみを使用します。
- selfhost 対象コード（`src/` 配下のトランスパイラ本体・backend・IR 実装）では、Python 標準 `ast` モジュール（`import ast` / `from ast ...`）への依存を禁止します。
- 構文解析/依存抽出が必要な場合は EAST ノードと既存 IR 情報を使って実装し、`ast` へのフォールバックを追加しません。
- 例外として `tools/` と `test/` の検査・テストコードは selfhost 非対象のため `ast` 利用を許可します。
- class 名・関数名・メンバー変数名には、日本語コメント（用途説明）を付与します。
- 標準ライブラリ対応の記載は、モジュール名だけでなく関数単位で明記します。
- ドキュメント未記載の関数は未対応扱いです。

## 8. 各ターゲットの実行モード注記

- `py2rs.py`: ネイティブ変換モード（Python インタプリタ非依存）
- `py2js.py`: EAST ベース変換モード（ブラウザ runtime 外部参照）
- `py2ts.py`: EAST ベースプレビューモード（JS 互換出力）
- `py2go.py` / `py2java.py`: EAST ベースプレビューモード（専用 Emitter へ段階移行中）
- `py2swift.py` / `py2kotlin.py`: EAST ベースプレビューモード（専用 Emitter へ段階移行中）

### 8.1 `--east-stage` 運用（実装同期）

- `py2x.py --target cpp` と非 C++ 8変換器（`py2rs.py`, `py2cs.py`, `py2js.py`, `py2ts.py`, `py2go.py`, `py2java.py`, `py2kotlin.py`, `py2swift.py`）は、既定を `--east-stage 3` に統一する。
- `py2x.py --target cpp` は `--east-stage 3` のみ受理し、`--east-stage 2` 指定時はエラー停止する。
- 非 C++ 8変換器のみ、`--east-stage 2` を移行互換モードとして受理し、`warning: --east-stage 2 is compatibility mode; default is 3.` を出力する。
- 回帰導線は `tools/check_py2cpp_transpile.py` と `tools/check_noncpp_east3_contract.py` を正本とする。
