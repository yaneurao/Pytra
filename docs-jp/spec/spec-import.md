# importの仕様

<a href="../../docs/spec/spec-import.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>


まず、docs-jp/spec/spec-runtime.md も読むこと。

## Yanesdk 重複配置の扱い（運用ルール）

- `materials/refs/Yanesdk/yanesdk/yanesdk.py` を正本とする。
- `materials/refs/Yanesdk/docs/*/yanesdk.py` は重複コピーとして扱い、import 解決・回帰判定の基準にしない。
- `py2cpp` の smoke 検証では、library は正本 1 本、game は `materials/refs/Yanesdk/docs/*/*.py`（`yanesdk.py` を除外）を対象にする。
- 重複コピー側に残る文末 `;` などの文法誤りは、self_hosted parser では入力エラー（`input_invalid`）とする。

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

## 追記: 対応言語ごとの具体実装方針（`readme.md` / `docs-jp/plans/pytra-wip.md` 準拠）

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
- EAST 変換。`py2rs.py` は薄い CLI、実出力は `src/hooks/rs/emitter/rs_emitter.py` が担当。
- import 解決は EAST `meta.import_bindings` を正本として `use ...;` 行へ変換する。
- 具体実装:
- `binding_kind=module/symbol` を使って `use crate::a::b` / `use crate::a::b::sym` を生成する。
- `as` 付き import は Rust 側でも `as` へ正規化する。
- `typing` / `__future__` は import 出力対象から除外する。
- エラー方針:
- `from M import *` と相対 import は `TranspileError`（上位で `input_invalid` 同等）に統一。

### 3. C#（`src/py2cs.py`）

- 実装方式:
- EAST 変換。`py2cs.py` は薄い CLI、実出力は `src/hooks/cs/emitter/cs_emitter.py` が担当。
- import 解決は EAST `meta.import_bindings` を正本として `using` 行へ変換する。
- 具体実装:
- `binding_kind=module/symbol` を使って `using ns;` / `using alias = ns.sym;` を生成する。
- `typing` / `__future__` / `browser*` は using 出力対象から除外する。
- C# 固有の文・式変換は profile/hook（`src/profiles/cs/*`, `src/hooks/cs/*`）で管理する。
- エラー方針:
- `from M import *` は展開しない。frontend の禁止構文として失敗させる。
- 相対 import や未解決 import は frontend 側の `input_invalid` 方針に従う。

### 4. JavaScript（`src/py2js.py` + `src/hooks/js/emitter/js_emitter.py`）

- 実装方式:
- EAST 変換。`py2js.py` は薄い CLI に限定し、出力処理は `JsEmitter` が担当。
- import 解決は EAST `meta.import_bindings` を正本として処理する。
- 具体実装:
- 通常モジュールは `import ... from "./a/b/c.js"` 形式へ変換する。
- `browser` / `browser.widgets.dialog` は外部参照として扱い、import 本体を生成しない。
- `from browser import window as win` は `win` を `window` 参照へ解決する。
- エラー方針:
- 既存の禁止構文（例: `from M import *`）は frontend/EAST 側のエラー方針に従う。

### 5. TypeScript（`src/py2ts.py` + `src/hooks/ts/emitter/ts_emitter.py`）

- 実装方式:
- EAST 変換。`py2ts.py` は薄い CLI、実出力は `TSEmitter`（preview）が担当。
- import 解決は EAST `meta.import_bindings` を正本とし、現状は JS 互換出力をそのまま利用する。
- 具体実装:
- profile/hook は `src/hooks/ts/`（内部では JS profile を再利用）。
- 出力は TypeScript 拡張子だが、現段階では JavaScript 互換コードを優先する。
- エラー方針:
- `py2js` と同一。未対応 import は frontend/EAST 側で停止する。

### 6. Go（`src/py2go.py` + `src/hooks/go/emitter/go_emitter.py`）

- 実装方式:
- EAST 変換。`py2go.py` は薄い CLI、実出力は Go preview emitter が担当。
- 具体実装:
- import 解決は EAST `meta.import_bindings` を正本として処理する（内部の lower は C# ベース preview を使用）。
- 生成コードは最小 `main` + 中間コードコメント形式で、段階移行中の暫定実装。
- エラー方針:
- 未対応構文は frontend/EAST 側で停止し、Go 出力へ進ませない。

### 7. Java（`src/py2java.py` + `src/hooks/java/emitter/java_emitter.py`）

- 実装方式:
- EAST 変換。`py2java.py` は薄い CLI、実出力は Java preview emitter が担当。
- 具体実装:
- import 解決は EAST `meta.import_bindings` を正本として処理する（内部の lower は C# ベース preview を使用）。
- 生成コードは最小 `Main` クラス + 中間コードコメント形式で、段階移行中の暫定実装。
- エラー方針:
- 未対応構文は frontend/EAST 側で停止し、Java 出力へ進ませない。

### 8. Swift（`src/py2swift.py` + `src/hooks/swift/emitter/swift_emitter.py`）

- 実装方式:
- EAST 変換。`py2swift.py` は薄い CLI、実出力は Swift preview emitter が担当。
- 具体実装:
- import 解決は EAST `meta.import_bindings` を正本として処理する（内部の lower は C# ベース preview を使用）。
- 生成コードは最小 `main` + 中間コードコメント形式で、段階移行中の暫定実装。
- エラー方針:
- 未対応構文は frontend/EAST 側で停止し、Swift 出力へ進ませない。

### 9. Kotlin（`src/py2kotlin.py` + `src/hooks/kotlin/emitter/kotlin_emitter.py`）

- 実装方式:
- EAST 変換。`py2kotlin.py` は薄い CLI、実出力は Kotlin preview emitter が担当。
- 具体実装:
- import 解決は EAST `meta.import_bindings` を正本として処理する（内部の lower は C# ベース preview を使用）。
- 生成コードは最小 `main` + 中間コードコメント形式で、段階移行中の暫定実装。
- エラー方針:
- 未対応構文は frontend/EAST 側で停止し、Kotlin 出力へ進ませない。

### 10. 言語別実装の統合順序（推奨）

- Step 1: C++ 実装（EAST）で `ImportBinding` / `QualifiedSymbolRef` を完成させる。
- Step 2: JS/TS（共通基盤）へ同じ解決器を移植する。
- Step 3: Swift/Kotlin は JS 経由なので追従確認のみで済ませる。
- Step 4: Go/Java（共通基盤）へ alias 正規化のみ先行導入する。
- Step 5: Rust/C# は既存実装を壊さない範囲で import 前処理テーブルを導入する。
