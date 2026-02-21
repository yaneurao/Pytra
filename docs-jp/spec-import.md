# importの仕様

<a href="../docs/spec-import.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>


まず、docs-jp/spec-runtime.md も読むこと。

```Python
from X import Y
```
のような構文をどうやって py2cpp.py で変換するかについて。

アイデアとしては、Xからimportするのは確定しているので、Xのheaderをincludeするコードを生成する。

```C++
#include "X"
```
そのうちYにだけアクセスできるように(他のシンボルはシンボルテーブルに登録しない)する。
こうすることで、Yだけ読み込んだ状態になると思うが、includeしている以上、C++的にはアクセスできてしまう。
これを変換時のエラーとして扱う必要がある。

また、たまたますでに読み込まれているモジュールで宣言されている変数名と被ってしまうことがある。
例えば次の例。

```Python
from X import Y
from Z import *
```

XからはYしかimportしていないが、実は、変数zを宣言していて、from Z import * のほうでも別の変数zが宣言されているものとする。

そうすると
W = z
のように C++に変換したときに、変数名がどちらのものかわからず曖昧になる。これはコンパイルエラーになる。

そこで、各モジュールは、py2cpp.py で変換するときに、必ずnamespaceに入れて、上の例なら
```
namespace フォルダパス::X {

}
```
のようになっているといいのではないかと思うのだが…？

C++はこれでいいとして、他の言語でnamespaceがない言語ではどうすればいいのか？
namespace的なものを変数名のprefixとしてくっつけておくといいのか？

## 追記: 懸念事項

- 現行 `py2cpp` では `from module import *` は受理済み（`binding_kind=wildcard`）で、相対 import は未対応。
- `#include` だけでは C++ 上の可視性制御はできないため、`from X import Y` の制約は変換器の名前解決で保証する必要がある。
- `from X import Y` で許可するシンボル種別（関数/クラス/定数/変数）と、`X.Y` 参照の扱い（許可/不許可）を仕様で固定する必要がある。
- import 名とローカル変数名が衝突したときの優先順位（ローカル/引数/import alias/builtin）を明文化しないと、ターゲット言語ごとに挙動差が出る。

## 追記: 実装アイデア（詳細版）

### 0. 実装対象の固定（最初に仕様を止める）

- 第一段階で対応する構文は次に限定する。
- `import M`
- `import M as A`
- `from M import S`
- `from M import S as A`
- 第一段階では `from M import *` を受理し、`ImportBinding(binding_kind=wildcard)` として保持する。
- 第一段階では相対 import（`from .m import x`）も未対応として `input_invalid` を維持する。

### 1. 依存解析フェーズの入力データ構造を固定する

- EAST から import 情報を次の構造で抽出する。

```text
ImportBinding
- module_id: str              # 正規化後モジュール名（例: pytra.std.time, foo.bar）
- export_name: str            # from-import 時の元シンボル名（import M は空）
- local_name: str             # 現在スコープへ束縛される名前（alias 適用後）
- binding_kind: str           # "module" | "symbol"
- source_file: str            # 入力ファイルパス
- source_line: int            # 可能なら保持
```

- `import M as A` は `binding_kind=module, module_id=M, local_name=A`。
- `from M import S as A` は `binding_kind=symbol, module_id=M, export_name=S, local_name=A`。
- 解析結果を `meta.import_modules` / `meta.import_symbols` に加え、内部的には `ImportBinding` の配列を正本として保持する。

### 2. モジュール解決ルールを 1 か所に集約する

- モジュール解決は必ず `resolve_module_name(raw_name, root_dir)` を通す。
- 解決順は次で固定する。
- `pytra.*` は予約名前空間として最優先で解決。
- それ以外はユーザーモジュール探索（`foo/bar.py`, `foo/bar/__init__.py`）。
- どちらにも該当しない場合は `missing_modules` に記録。
- `pytra.py` / `pytra/__init__.py` が入力ルートに存在する場合は `reserved_conflicts` へ追加し `input_invalid`。

### 3. モジュール公開シンボル表（ExportTable）を作る

- `from M import S` の検証用に、各モジュールの公開シンボルを事前収集する。
- 第一段階の公開シンボル定義は次で固定する。
- トップレベル `FunctionDef.name`
- トップレベル `ClassDef.name`
- トップレベル `Assign/AnnAssign` で `Name` へ代入される識別子
- 未定義 `S` を import した場合は `input_invalid`。
- エラーメッセージには `module_id`, `symbol`, `source_file` を含める。

### 4. 名前解決アルゴリズムを明示する

- 参照解決の優先順位を次で固定する（上ほど優先）。
- 現在スコープのローカル変数
- 関数引数
- クラスメンバ（`self.x` 経由）
- import された symbol alias（`from M import S as A` の `A`）
- import された module alias（`import M as A` の `A`）
- 組み込み関数
- 同一優先度内で同名衝突した場合は `input_invalid`。
- 例: 同一モジュールで `from a import x` と `from b import x` は衝突エラー。
- `from M import S` 後に `M.T` のような参照は許可しない（`M` は束縛されていないため）。

### 5. C++ 生成規則を固定する

- include 生成は `ImportBinding` から行い、重複排除 + ソートで安定化する。
- `binding_kind=symbol` の参照も、C++ 出力は常に `module_namespace::export_name` へ正規化する。
- 例:

```python
from foo.bar import add as plus
x = plus(1, 2)
```

```cpp
#include "foo/bar.h"
auto x = pytra_mod_foo__bar::add(1, 2);
```

- つまり「呼び出し位置では alias を使ってよい」が「生成コードでは必ず完全修飾名へ落とす」。
- これにより、同名関数が別モジュールにあっても C++ 側の曖昧参照を回避できる。

### 6. single-file / multi-file の整合を固定する

- namespace 決定は `module_namespace_map[module_id] -> cpp_namespace` の 1 ルートに統一する。
- single-file と multi-file で同じ `module_namespace_map` を使う。
- multi-file では forward 宣言生成時も `module_namespace_map` だけを参照し、別ロジックを持たない。
- 変換モードの違いで import 解決結果が変わらないことを要件にする。

### 7. エラー分類と報告フォーマットを固定する

- import 関連の失敗は `input_invalid` に統一する。
- detail 行に最低限次を含める。
- `kind`: `missing_module | missing_symbol | duplicate_binding | reserved_conflict | unsupported_import_form`
- `file`: 入力ファイル
- `import`: 元の import 文字列（再構築文字列で可）
- 例:
- `kind=missing_symbol file=app.py import=from foo import bar`

### 8. 最小テストマトリクス（受け入れ条件）

- 正常系:
- `import M` / `import M as A` / `from M import S` / `from M import S as A`
- 同名 symbol が別モジュールに存在しても完全修飾で衝突しないこと
- 異常系:
- `from M import *`（受理。`binding_kind=wildcard` として保持）
- `from .m import x`（第一段階では `input_invalid`）
- 存在しないモジュール/シンボル
- 同名 alias 重複
- `--dump-deps` と通常変換で同じ依存解決結果になること

## 追記: 他言語ターゲット向け方針（詳細版）

### A. 言語非依存 IR の責務を固定する

- import の意味解釈はフロントエンドで完了させ、バックエンドは解釈しない。
- バックエンドへ渡す参照は必ず次の形に正規化する。

```text
QualifiedSymbolRef
- module_id: str      # 例: foo.bar
- symbol: str         # 例: add
- local_name: str     # 例: plus（元コード上の名前）
```

- 式中の `Name("plus")` は backend 手前で `QualifiedSymbolRef(module_id="foo.bar", symbol="add")` へ解決しておく。
- これにより言語差は「どう書き出すか」だけになる。

### B. バックエンド分類ごとの写像規則

- 種別 1: namespace / module path を持つ言語（C++, Rust, C# など）
- `module_id` を言語の名前空間構文へ写像して `qualified access` を生成する。
- 例: `foo.bar.add` / `foo::bar::add` / `foo.bar::add`（言語仕様に合わせる）。
- 種別 2: ファイル分割はあるが名前空間が弱い言語
- シンボルを `module_prefix + symbol` へ mangle して衝突回避する。
- 例: `foo_bar__add(...)`。
- 種別 3: ほぼフラットなグローバル名前空間の言語
- すべての公開シンボルを mangle し、生成物内で一意性を保証する。

### C. 共通 name mangling 仕様

- 非 namespace 言語向けに共通アルゴリズムを持つ。
- `mangled = "__pytra__" + encode(module_id) + "__" + encode(symbol)`
- `encode` は `[a-zA-Z0-9_]` 以外を `_xx`（16進2桁）へ変換。
- 先頭が数字になる場合は `_` を補う。
- 同名衝突は mangle 後に再検査し、衝突時は `input_invalid`。

### D. import 制約チェックはフロントエンドで完結させる

- `from M import S` の妥当性、重複、未定義、未対応構文の判定は IR 生成前に終える。
- バックエンドは `QualifiedSymbolRef` をそのまま出力するだけにする。
- これにより「C++ では通るが別言語で落ちる」種類の差異を減らせる。

### E. バックエンドごとの最小契約テスト

- 同一入力から生成した各言語コードで、次が一致することを確認する。
- 参照先モジュールとシンボルの対応（`module_id/symbol`）
- alias 解決結果
- 衝突検出結果（成功/失敗の判定）
- テストは「構文差」ではなく「解決結果の同一性」を基準にする。

## 追記: 対応言語ごとの具体実装方針（`readme.md` / `docs-jp/pytra-readme.md` 準拠）

対応言語は `C++ / Rust / C# / JavaScript / TypeScript / Go / Java / Swift / Kotlin`。

### 1. C++（`src/py2cpp.py`）

- 実装方式:
- EAST ベースで import を解析し、`module_namespace_map` と `meta.import_symbols` を使って解決する。
- import 文自体は C++ 本体へは出力せず、`#include` と名前解決テーブルへ反映する。
- 具体実装:
- `ImportBinding` を正本にして include を生成（重複排除 + 安定ソート）。
- `from M import S as A` は `A` を直接出力せず、参照時に `ns_of(M)::S` へ正規化する。
- single-file / multi-file で同一の `module_namespace_map` を使い、解決規則差を作らない。
- エラー方針:
- 相対 import、未解決モジュール、未解決シンボル、同名重複は `input_invalid`。

### 2. Rust（`src/py2rs.py`）

- 実装方式:
- native AST 変換。現状の `Import/ImportFrom` はモジュール先頭で読み飛ばしている。
- 呼び出し解決は式側で行う（例: `math.sqrt`, `pathlib.Path`, `perf_counter`）。
- 具体実装:
- import 解析だけは先行実施し、`alias -> canonical symbol` を内部テーブル化する。
- 例:
- `from time import perf_counter as pc` は `pc()` を `perf_counter()` へ正規化して既存実装へ渡す。
- `from pathlib import Path as P` は `P(...)` を `Path(...)` 扱いへ正規化する。
- `from math import sqrt as s` は `s(x)` を `math_sqrt(...)` へ落とす。
- runtime 連携は既存通り `py_runtime` を使い、使用シンボルのみ `use py_runtime::{...}` で導入する。
- エラー方針:
- `from M import *` と相対 import は `TranspileError`（上位で `input_invalid` 同等）に統一。

### 3. C#（`src/py2cs.py`）

- 実装方式:
- import を `using` 行へ変換し、式側は `Pytra.CsModule.py_runtime.*` や `System.Math` へマップする。
- `_using_lines_from_import` と `_map_python_module` が import 入口。
- 具体実装:
- `ImportBinding` から `using` を生成する。
- `import math as m` -> `using m = System;`
- `from pathlib import Path as P` -> `using P = System.IO.Path;` ではなく、Pytra 方針に合わせ `pathlib.Path` 相当の runtime 経路へ統一する。
- `typing` は既存 `typing_aliases` 経路を維持し、from-import 名を型解決テーブルへ登録する。
- `py_module`/`pylib` 系は既存互換を維持しつつ、段階的に `pytra.*` 名へ収束させる。
- エラー方針:
- `from M import *` は展開しない。未対応構文として失敗させる。
- 同名 alias 衝突は `duplicate_binding` として即時エラー。

### 4. JavaScript（`src/py2js.py` + `src/common/js_ts_native_transpiler.py`）

- 実装方式:
- native AST 変換。`require(...)` ベースで runtime モジュールを読み込む。
- import 解決は `_transpile_import` が担当。
- 具体実装:
- `ImportBinding` から `const ... = require(...)` または分割代入を生成する。
- `import math as m` -> `const m = require(.../math.js)`
- `from time import perf_counter as pc` -> `const pc = perfCounter`
- `from pathlib import Path as P` -> `const P = pathlib.Path`
- `from pytra.utils.gif import save_gif as sg` -> `const { save_gif: sg } = require(.../gif_helper.js)`
- 未使用 import の require を抑制するため、参照カウントに基づく遅延出力（使われた binding のみ出力）を導入する。
- エラー方針:
- `_transpile_import` の unsupported 分岐を維持し、未対応 import を早期失敗させる。

### 5. TypeScript（`src/py2ts.py` + `src/common/js_ts_native_transpiler.py`）

- 実装方式:
- JS と同一ロジック（runtime 拡張子のみ `.ts`）。
- 具体実装:
- import 解決は JS と同じ `ImportBinding` を使う。
- 出力文は `require` を維持し、実行ランタイム（tsx）互換を優先する。
- 型情報を壊さないため、必要に応じて import alias に最小型注釈を付ける（将来拡張）。
- エラー方針:
- JS と同一。未対応 import は変換エラーで停止。

### 6. Go（`src/py2go.py` + `src/common/go_java_native_transpiler.py`）

- 実装方式:
- native AST 変換。Go 側 import 文は runtime テンプレートに内包し、Python import 文は本体で出力しない。
- 関数/メソッド解決は `_transpile_call` が担当（`math.*`, `pathlib.Path`, `perf_counter`, `save_gif` など）。
- 具体実装:
- import 文を捨てる前に `ImportBinding` だけ収集し、alias 正規化へ使う。
- `from time import perf_counter as pc` は `pc()` を `pyPerfCounter()` へ解決。
- `from pathlib import Path as P` は `P("x")` を `pyPathNew(...)` へ解決。
- `from math import sqrt as s` は `s(x)` を `math.Sqrt(pyToFloat(x))` へ解決。
- `png/gif` は `pyWriteRGBPNG` / `pySaveGIF` / `pyGrayscalePalette` へ統一解決する。
- エラー方針:
- alias 重複や未定義 symbol を Go 生成前に検出し、`input_invalid` で落とす。

### 7. Java（`src/py2java.py` + `src/common/go_java_native_transpiler.py`）

- 実装方式:
- Go と同一の共通トランスパイラを使用。Java 側 runtime は `PyRuntime.java`。
- Python import は Java import 文へ直接は展開せず、`PyRuntime.*` 呼び出しへ落とす。
- 具体実装:
- Go と同様に `ImportBinding` で alias 正規化を先に実施。
- `from time import perf_counter as pc` -> `PyRuntime.pyPerfCounter()`
- `from pathlib import Path as P` -> `PyRuntime.pyPathNew(...)`
- `from math import sin as s` -> `PyRuntime.pyMathSin(...)`
- module attribute 呼び出しは `PyRuntime` の明示メソッドへ寄せ、曖昧な `Object` メソッド呼び出しを禁止する。
- エラー方針:
- 解決不能メソッドは現状 `TranspileError("cannot resolve method call: ...")`。import 解決段階で事前検出してメッセージを統一する。

### 8. Swift（`src/py2swift.py` + `src/common/swift_kotlin_node_transpiler.py`）

- 実装方式:
- Node バックエンド方式。Python -> JS へ変換し、JS を Base64 埋め込みした Swift を生成する。
- import 意味論は Swift 側ではなく JS 変換側（`JsTsNativeTranspiler`）が正本。
- 具体実装:
- Swift 固有では import 解決ロジックを持たない。
- 変換時は JS 生成段階で `ImportBinding` を解決し、その結果を埋め込む。
- Swift runtime は「埋め込み JS を実行する責務」のみに限定する。
- エラー方針:
- import エラーは JS 変換時点で停止し、Swift 側へは進ませない（エラー源を一意化）。

### 9. Kotlin（`src/py2kotlin.py` + `src/common/swift_kotlin_node_transpiler.py`）

- 実装方式:
- Swift と同じ Node バックエンド方式（内部 JS を Kotlin へ埋め込み実行）。
- import 意味論の正本は JS 変換側。
- 具体実装:
- Kotlin 側は class 名生成と実行エントリのみを担当し、import 解決を持たない。
- JS 側で解決済みの `ImportBinding` 結果をそのまま埋め込む。
- Kotlin runtime は `PyRuntime.runEmbeddedNode(...)` 呼び出し専用に保つ。
- エラー方針:
- Swift と同様に JS 変換で import エラーを止め、Kotlin 生成は行わない。

### 10. 言語別実装の統合順序（推奨）

- Step 1: C++ 実装（EAST）で `ImportBinding` / `QualifiedSymbolRef` を完成させる。
- Step 2: JS/TS（共通基盤）へ同じ解決器を移植する。
- Step 3: Swift/Kotlin は JS 経由なので追従確認のみで済ませる。
- Step 4: Go/Java（共通基盤）へ alias 正規化のみ先行導入する。
- Step 5: Rust/C# は既存実装を壊さない範囲で import 前処理テーブルを導入する。
