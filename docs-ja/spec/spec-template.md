# template 仕様（案）

この文書は、Pytra における generic / template サポート方針を定義する。  
特に、`.py` に直接書く **template 定義 + 明示インスタンス化** を正規手段として扱う。

> 2026-02-23 照合ステータス:
> - 採用: `pytra.std.typing.TypeVar` は最小 shim（`str` を返す）として提供する。
> - 保留: `@template` / `@instantiate`、compile-time branch、実体化エラー契約、生成量ガードなど template 本体仕様。
> - 非採用: §16 の「採用記法」という断定表現（現時点では記法採用を確定していないため）。

## 1. 目的

- Python 側で generic な関数/クラスを定義し、C++ を含む複数言語へ安全に変換できるようにする。
- `object` 退化を減らし、静的型を維持した生成コードを得る。
- template 非対応（または制約が強い）言語でも、型実体化コードを生成できるようにする。

## 2. 非目標

- Python の型システム（`typing`）全機能の完全再現。
- 高階型/部分特殊化/メタプログラミングの完全互換。
- 実行時型消去に依存した動的 dispatch の再現。

## 3. 基本方針

- generic の中間表現は EAST で保持する。
- template 対応が弱い言語では monomorphization（明示インスタンス化）を使う。
- 実体化は「使う型を明示して生成する」方針とし、暗黙全探索は行わない。
- template 本体をそのまま呼ぶのではなく、実体化済みシンボルを呼ぶことを必須にする。

## 4. 用語

- template 定義: 型パラメータを持つ関数/クラス定義。
- 実体化（instantiation）: 型引数を具体型に束縛して、実コードを生成すること。
- 実体化シンボル: 実体化後に呼び出し/生成に使う具体型シンボル。

## 5. `.py` での記法

### 5.1 基本API

- `pytra.std.template` を追加し、次のデコレータを提供する。
  - `@template("T", "U", ...)`
  - `@instantiate("instantiated_name", type_arg1, type_arg2, ...)`
- `@template` は「直後の 1 つの `def` / `class`」にのみ適用される。
  - 次の `def` / `class` まで有効ではない。
  - モジュール全体に波及しない。
- `@instantiate` は `@template` と同じデコレータ束で、対象定義の直前に連記する。

### 5.2 template 関数定義

```python
from pytra.std.template import template, instantiate

@template("T")
@instantiate("add_i64", int64)
@instantiate("add_f64", float64)
def add(a: T, b: T) -> T:
    return a + b
```

### 5.3 template クラス定義

```python
from pytra.std.template import template, instantiate

@template("T")
@instantiate("Vec2_f64", float64)
class Vec2:
    x: T
    y: T

    def __init__(self, x: T, y: T) -> None:
        self.x = x
        self.y = y
```

### 5.4 使用ルール

- 呼び出し/生成に使うのは `@instantiate` で定義した実体化シンボルとする。
- `add(...)` や `Vec2(...)` のような template 本体の直接利用は禁止する（`explicit` 方針）。
- `@instantiate("name", ...)` の第1引数は、生成される実体化シンボル名として扱う。

### 5.5 変換時分岐（compile-time branch）

template 本体内では、次の directive を使って「変換時」に分岐できる。

```python
# Pytra::if T == int64
...
# Pytra::elif T == str
...
# Pytra::else
...
# Pytra::endif
```

- `# Pytra::if` / `# Pytra::elif` / `# Pytra::else` / `# Pytra::endif` を 1 組で使う。
- 条件で使える左辺は template 型パラメータ（`T`, `K`, `V` など）のみ。
- 比較は `==` / `!=` のみを許可する（v1）。
- 比較対象は型トークン（`int64`, `str`, `float64` など）を使う。
  - `# Pytra::if T == "int64"` のような引用付きも互換入力として受理してよいが、正規形は非引用とする。
- 判定は各 `@instantiate` ごとに実行し、選ばれたブロックのみを残す。

## 6. 構文制約

- `@template` / `@instantiate` はモジュールトップレベルの `def` / `class` にのみ許可する。
- `@template("...")` の引数は文字列リテラル識別子のみ許可する。
- `@instantiate("name", ...)` の第1引数は文字列リテラル識別子のみ許可する。
- `@instantiate` の型引数個数は `@template` の型パラメータ個数と一致必須とする。
- `# Pytra::if` 系 directive は template 本体内でのみ許可する。
- v1 では `# Pytra::if` 系 directive のネストを禁止する。

## 7. 解決ルール

- `@instantiate("name", type_args...)` で実体化シンボルを確定する。
- 同一 template 定義内で、同一 `name` の重複は `input_invalid(kind=symbol_collision)`。
- 同一 template 定義内で、同一型引数組の重複は `input_invalid(kind=duplicate_instantiation)`。
- template 本体の直接呼び出しは `input_invalid(kind=missing_instantiation)`。
- `# Pytra::if` 系 directive は実体化ごとに評価し、1ブロックへ確定してから通常変換へ渡す。

## 8. 名前生成（mangling）

- 実体化後シンボルは型引数を含む一意名へ変換する。
- 推奨形式:
  - `__pytra__<module>__<symbol>__<type1>__...`
- 文字エンコード規則:
  - `[A-Za-z0-9_]` 以外は `_xx`（16進2桁）へ置換する。
- 同名衝突時は `input_invalid(kind=symbol_collision)`。

## 9. ターゲット別出力方針

- C++/Rust など native template が強い言語:
  - `native` 出力または `explicit` 出力を選択可能にする。
- template 非対応または制約が強い言語:
  - `explicit` 出力を既定とする。
- どの言語でも `.py` 側の `@instantiate(...)` 記述を正本とし、外部定義ファイルには依存しない。

## 10. 型制約

- template 本体内で `Any` / `object` への暗黙退化を許可しない。
- 型引数に許可される型は EAST 正規型（`int64`, `float64`, `str`, `list[T]` など）に限定する。
- 未知型/未解決型が残る場合は `inference_failure` で停止する。

## 11. エラー契約

template 関連の失敗は次を使用する。

- `input_invalid(kind=missing_instantiation)`
- `input_invalid(kind=duplicate_instantiation)`
- `input_invalid(kind=symbol_collision)`
- `input_invalid(kind=unsupported_type_argument)`
- `input_invalid(kind=invalid_instantiation_form)`
- `input_invalid(kind=invalid_compile_time_branch)`
- `input_invalid(kind=unmatched_compile_time_branch)`
- `input_invalid(kind=unbound_template_param)`
- `unsupported_syntax`（未対応記法）

エラー詳細には最低限 `module`, `symbol`, `type_args`, `source_span` を含める。

## 12. 生成量ガード

実体化爆発を防ぐため、次のガードを設ける。

- `--max-instantiations N`（既定値を持つ）
  - 1回の変換で生成される「実体化シンボル総数」の上限を表す。
  - 直接指定した実体化だけでなく、連鎖的に発生した実体化も総数に含める。
  - 再帰の深さそのものを制限する値ではない。
- 総数が N を超える場合は `input_invalid(kind=instantiation_limit_exceeded)` で停止する。

## 13. 検証要件

最低限、次を通過すること。

- fixture 配置方針（実装着手時）:
  - `test/fixtures/template/` を新設し、template 関連 fixture を集約する。
  - 正常系は `ok_*`、異常系は `ng_*` の命名規約で管理する。
  - 最低限 `ok`（関数/クラスの実体化成功）と `ng`（`missing_instantiation` / `duplicate_instantiation` / `unsupported_type_argument`）を追加する。
- 正常系:
  - `.py` の `@instantiate(...)` で指定した型だけが生成される。
  - 生成コードが compile/run 可能である。
- 異常系:
  - `@instantiate(...)` なしの直接呼び出しが失敗する。
  - 重複実体化が `duplicate_instantiation` で失敗する。
  - 型不一致が `unsupported_type_argument` で失敗する。
  - `# Pytra::if` ブロック不整合（`endif` 欠落など）が失敗する。
- 言語間整合:
  - 同じ `.py` 入力から各ターゲットで同一の解決結果（template/type_args/instantiated_name）が得られる。

## 14. 段階導入

- Phase 1:
  - `.py` 内 `@template` / `@instantiate` と `# Pytra::if` をフロントエンドで解釈可能にする。
  - `explicit` 出力を先行実装する。
- Phase 2:
  - `native` 出力対応言語で template 直接出力を導入する。
  - `explicit` との切替を整備する。
- Phase 3:
  - 必要に応じて推論補助（実体化記述の省力化）を追加する。

## 15. 現状実装との差分（2026-02-22 時点）

- `pytra.std.typing.TypeVar` は runtime shim（`str` を返す最小実装）であり、型パラメータ機能は未提供。
- self-hosted parser は template 専用構文/API 解釈を未実装。
- 本仕様は、今後の template 実装に向けた設計基準として扱う。

## 16. `.py` 記法（候補）

候補記法は **デコレータ連記（識別子引数）** とする。

### 16.1 1型パラメータ関数の例

```python
@template("T")
@instantiate("identity_i64", int64)
@instantiate("identity_str", str)
def identity(x: T) -> T:
    return x
```

### 16.2 2型パラメータ関数の例

```python
@template("K", "V")
@instantiate("pair_i64_str", int64, str)
@instantiate("pair_f64_bool", float64, bool)
def pair(key: K, value: V) -> tuple[K, V]:
    return (key, value)
```

### 16.3 class の例

```python
@template("T")
@instantiate("Box_i64", int64)
@instantiate("Box_str", str)
class Box:
    value: T

    def __init__(self, value: T) -> None:
        self.value = value
```

- 長所:
  - 実体化定義を関数定義の直上に集約でき、実体化漏れを見つけやすい。
  - `as_name` を別引数にせず、実体化名を先頭で短く指定できる。
  - 実体化ごとの型引数が引数列で明示されるため、静的検証を実装しやすい。
- 注意:
  - 実体化が多い関数ではデコレータ行が増え、定義が縦長になりやすい。
  - 実体化名を文字列で持つため、リネーム時にIDE追従が弱い。
  - Python実行時デコレータとして解釈される場合に備え、Pytra専用のno-op実装や評価順の仕様固定が必要になる。

## 17. 採否整理（2026-02-23）

採用（既存正規仕様へ移管）:
- `TypeVar` は template 機能ではなく typing 互換 shim として提供する。
  - 移管先: `docs-ja/spec/spec-pylib-modules.md`
  - 補足: 実装は `src/pytra/std/typing.py` の `TypeVar(name: str) -> str`。

保留（草案維持）:
- §1〜§14 の template 本体仕様（構文、解決、エラー契約、実体化上限、検証要件、段階導入）。
- §16 の記法候補（デコレータ連記）は、実装方針候補として保持する。

非採用（文言/状態の修正）:
- 「`.py` 記法（採用）」という確定表現は現状実装と不整合なため非採用とし、「候補」へ変更。
