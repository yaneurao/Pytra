# P1: `type X = T` 型エイリアスサポート

最終更新: 2026-03-18

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-TYPE-ALIAS-SUPPORT-01`

## 背景

`src/runtime/cpp/generated/std/argparse.h` に以下のような長い型が多数出現している：

```cpp
::std::optional<dict<str, ::std::variant<str, bool, ::std::monostate>>>
```

Python ソース（`src/pytra/std/argparse.py`）では `str | bool | None` という簡潔な型を使っているが、
C++ 出力では完全展開された型式になるため可読性が著しく低下している。

Python 3.12 で導入された `type` 文（PEP 695）を Pytra でサポートすることで、

```python
# argparse.py
type ArgValue = str | bool | None
```

↓ emitter が透過的に変換

```cpp
// argparse.h
using ArgValue = ::std::variant<str, bool, ::std::monostate>;
```

とすることで、ソースと生成コードの対応が一対一になり可読性が大きく改善される。

## 現状の問題

現在の emitter は `ArgValue = str | bool | None` をモジュールレベルの変数代入として扱い、
```cpp
TypeAlias ArgValue;  // runtime 変数
static void __pytra_module_init() { ArgValue = str | bool | ::std::nullopt; }
```
という誤った出力を生成する。

## 対象

- `src/toolchain/compile/core_module_parser.py` — `type X = T` 文のパース・IR ノード化
- `src/toolchain/compile/core.py` — TypeAlias IR ノード定義
- `src/toolchain/emit/cpp/emitter/cpp_emitter.py` — `using X = <cpp_type>;` の emit
- `src/toolchain/emit/cpp/emitter/` — 型式レンダリング時の alias 逆引き
- `src/pytra/std/argparse.py` — `type ArgValue = str | bool | None` を追加して動作確認
- `src/runtime/cpp/generated/std/argparse.h`（再生成で改善を確認）

## 非対象

- `X: TypeAlias = T` 形式（typing.TypeAlias アノテーション）— 後続タスクで対応可
- ネストしたスコープ（関数内・クラス内）の type alias — まずモジュールレベルのみ
- 非 C++ バックエンド — まず C++ のみ。他言語は後続タスクで対応
- Generic type alias（`type Stack[T] = list[T]`）— PEP 695 の型パラメータは対象外

## 修正方針

### ステップ 1: パーサー（core_module_parser.py）

セルフホストパーサーが `type X = T` 文を認識するよう拡張する。
実行環境の Python バージョンに依存せず、Pytra 独自のパースルールとして実装する。

認識した型エイリアスを EAST IR の `TypeAlias` ノードとして出力する：
```json
{ "kind": "TypeAlias", "name": "ArgValue", "type_expr": "str|bool|None" }
```

### ステップ 2: IR ノード（core.py）

`TypeAlias` ステートメントノードを追加する。

### ステップ 3: C++ emitter

モジュールヘッダ生成時に `TypeAlias` ノードを `using X = <cpp_type>;` として emit する。

型式レンダリング（`_cpp_type_text` 等）に alias 逆引き機能を追加する：
- モジュール内で定義された alias の型式を正規化した形で保持
- 型式を render する際に alias が存在すればその名前を使用
- alias の適用はモジュールスコープ内の参照に限定（他モジュールには展開形を使用）

### ステップ 4: 動作確認

`src/pytra/std/argparse.py` に `type ArgValue = str | bool | None` を追加し、
再生成後の `argparse.h` で `using ArgValue = ...;` と alias 参照が正しく出ることを確認する。

## 受け入れ基準

- `type ArgValue = str | bool | None` を含む Python ソースから `using ArgValue = ::std::variant<str, bool, ::std::monostate>;` が生成される。
- 同モジュール内の関数シグネチャで `ArgValue` が展開形の代わりに使用される。
- `argparse.h` の可読性が改善されている（長い variant 型が alias 名に置き換わる）。
- fixture 145/145・sample 18/18 pass、selfhost diff mismatches=0。
- 既存の非 alias ソースへの影響なし。

## 決定ログ

- 2026-03-18: ユーザー指摘。argparse.h の `::std::optional<dict<str, ::std::variant<str, bool, ::std::monostate>>>` が可読性を著しく損なっている。
- 2026-03-18: 選択肢（A: 自動 typedef / B: 固定挿入 / C: Python type alias）の中から C を採用。ソースと出力の透明な対応が最も設計として正しい。
- 2026-03-18: Python 3.12 `type` 文（PEP 695）を対象に決定。Pytra はセルフホストパーサーを持つため実行環境の Python バージョンは制約にならない。`X: TypeAlias = T` 形式は後続タスクとする。
- 2026-03-18: 実装完了。`argparse.py` への直接追加は Python 3.11（実行環境）が PEP 695 構文を parse できないため見送り。`pytra.std.re` への新パターン追加・`core_module_parser.py` / `cpp_emitter.py` / `header_builder.py` / `type_bridge.py` / `module.py` を修正。バージョン: shared 0.121.0 / cpp 0.585.0。fixture 145/145・sample 18/18 pass、selfhost mismatches=0。
