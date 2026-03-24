# パイプライン再設計案: parse / resolve / compile / optimize / emit 五段分離

最終更新: 2026-03-24
ステータス: 案（検討中）

## 1. 動機

現行パイプラインには以下の構造的問題がある。

1. **signature_registry のハードコード**: `pytra/std/*.py` の関数シグネチャを正規表現パースしてキャッシュし、型推論に注入している。stdlib が増えるたびに手動メンテナンスが必要。
2. **built-in 型のハードコード**: `len` → `int64`、`str` → `str` 等の組み込み関数の型情報がパーサー内部にハードコードされている。
3. **cross-module 型解決の設計矛盾**: EAST1→EAST2→EAST3 はモジュール単位の独立処理だが、EAST2 の型推論で他モジュールの関数シグネチャが必要。モジュール独立なのに cross-module 情報が要るという矛盾を、ハードコードテーブルで糊塗している。
4. **EAST1 の言語固有性が不明確**: EAST1 は Python パーサーの出力だが、ファイル名や段の構成からそれが読み取れない。将来の多言語 frontend 対応で混乱する。

## 2. 提案: parse / resolve / compile / optimize / emit 五段パイプライン

### 2.1 概要

```
parse:     .py → .py.east1          言語固有の構文解析（モジュール単位・完全並列）
resolve:   *.py.east1 → *.east2    型解決 + 正規化（全モジュール一括・依存順）
compile:   *.east2 → *.east3       core lowering（言語非依存）
optimize:  *.east3 → *.east3       whole-program 最適化
emit:      *.east3 → *.cpp 等      target コード生成（写像のみ）
```

通常使用は `-build` で一括実行:

```
pytra-cli2 -build --target=cpp a.py   （parse→resolve→compile→optimize→emit を一気通貫）
```

### 2.2 各段の責務

#### parse（言語固有・モジュール単位）

```
pytra-cli2 -parse a.py        →  a.py.east1
pytra-cli2 -parse math.py     →  math.py.east1
```

- 入力: ソースファイル 1 つ
- 出力: `.py.east1`（Python 固有の EAST1）
- 責務: 構文解析、ソース span / trivia 保持、型注釈の保持（未解決）
- cross-module 依存: **なし**（完全にモジュール独立）
- 並列性: **完全並列**
- 実装: `toolchain2/parse/py/`

#### resolve（言語固有→言語非依存・全モジュール一括）

```
pytra-cli2 -resolve --from=python *.py.east1  →  *.east2
```

- 入力: 全 `.py.east1`（built-in + stdlib + ユーザーコード）
- 出力: `.east2`（言語非依存の正規化済み IR）
- 責務:
  - import graph のトポロジカルソート
  - 依存順に各モジュールの型解決（先行モジュールのシグネチャを参照）
  - Python 固有の構文正規化（`range()` → `ForRange`、`int` → `int64` 等）
  - cast 挿入（`int64` → `float64` 等）
  - `--from=python` で入力言語の正規化ルールを指定
- cross-module 依存: **あり**（全モジュールが揃っている前提）
- 並列性: 内部で依存順に処理（DAG 内の独立ノードは並列可能）
- 実装: `toolchain2/resolve/py/`

#### compile（言語非依存・core lowering）

```
pytra-cli2 -compile *.east2  →  *.east3
```

- 入力: 全 `.east2`
- 出力: `.east3`（core IR）
- 責務:
  - boxing/unboxing 命令化
  - `type_id` 判定・反復計画の命令化
  - `dispatch_mode` の意味適用
  - 現行の EAST2→EAST3 lowering に相当
- cross-module 依存: **あり**
- 実装: `toolchain2/compile/`

#### optimize（言語非依存・whole-program 最適化）

```
pytra-cli2 -optimize *.east3  →  *.east3
```

- 入力: 全 `.east3`
- 出力: 最適化済み `.east3`
- 責務:
  - whole-program 解析（call graph、escape 解析、container ownership）
  - dead code 除去
  - 現行の linker optimizer に相当
- cross-module 依存: **あり**
- 実装: `toolchain2/optimize/`

#### emit（言語非依存→target・全モジュール一括）

```
pytra-cli2 -emit --target=cpp *.east3  →  *.cpp
pytra-cli2 -emit --target=rs  *.east3  →  *.rs
```

- 入力: 全 `.east3`
- 出力: target 言語のソースファイル群
- 責務:
  - EAST3 ノードから target 言語構文への写像（**のみ**）
  - runtime 配置・include / import 生成
  - 最適化はしない
- cross-module 依存: **あり**（import / include の解決）
- 実装: `toolchain2/emit/cpp/` 等

### 2.3 一括実行コマンド

```
# 通常使用: parse→resolve→compile→optimize→emit を一括
pytra-cli2 -build --target=cpp a.py
```

`-build` は中間ファイルを一時ディレクトリに生成し、最終出力のみを残す。個別コマンドはパイプラインの途中を覗きたいとき用。

### 2.4 ファイル命名規則

| ファイル | 意味 |
|---|---|
| `a.py` | Python ソース |
| `a.py.east1` | Python 固有の EAST1（パーサー出力） |
| `a.east2` | 言語非依存の EAST2（`.py` が消える = 言語固有の意味論が除去された） |
| `a.east3` | 最適化済みの EAST3 |

`.py.east1` → `.east2` で拡張子から `.py` が消えることが、「Python の意味論が抜けた」ことを自己説明する。

### 2.5 built-in / stdlib の統一的扱い

built-in も stdlib もユーザーコードと同じ仕組みで処理する。

```
pytra-cli2 -parse pytra/built_in.py       →  built_in.py.east1
pytra-cli2 -parse pytra/std/math.py       →  math.py.east1
pytra-cli2 -parse pytra/std/json.py       →  json.py.east1
pytra-cli2 -parse user_code.py            →  user_code.py.east1

pytra-cli2 -resolve --from=python *.py.east1  →  *.east2

pytra-cli2 -compile *.east2  →  *.east3

pytra-cli2 -optimize *.east3  →  *.east3

pytra-cli2 -emit --target=cpp *.east3  →  *.cpp
```

- `built_in.py` には `len`, `str`, `int`, `print` 等の関数宣言を記述
- `pytra/std/*.py` には stdlib の関数宣言を記述（現行と同じ）
- resolve 段が `built_in.py.east1` の `FunctionDef` ノードから戻り値型を取得
- **signature_registry のハードコードテーブルは全て不要になる**
- **built-in 型のパーサー内ハードコードも全て不要になる**
- built-in や stdlib の追加・変更は `.py` ファイルの編集のみで対応可能

## 3. 現行との対応

| 提案 | 現行の実装 | 変更点 |
|---|---|---|
| parse | `core.py` + EAST1 ビルド | CLI の分離。実装はほぼ流用可。 |
| resolve | `east2.py` + signature_registry + built-in ハードコード | signature_registry 除去。built-in ハードコード除去。cross-module 型解決を追加。 |
| compile | `east2_to_east3_lowering.py` | core lowering のみに限定。 |
| optimize | linker optimizer | whole-program 最適化のみに限定。 |
| emit | emitter 群 | 最適化責務を除去し、写像のみに限定。 |

### 3.1 現行 EAST 段との対応

| 現行 | 提案での位置 |
|---|---|
| EAST1 | parse の出力（`.py.east1`） |
| EAST2 | resolve の出力（`.east2`） |
| EAST3 | compile の出力（`.east3`） / optimize の入出力 |

EAST1 / EAST2 / EAST3 のノード定義は変更不要。実行タイミングとデータの流れが変わるのみ。

### 3.2 ディレクトリ構成

```
src/
  pytra-cli2.py               ← 新 CLI
  pytra/                      ← 共有（std, utils, built_in）
  toolchain/                  ← 現行（触らない）
  toolchain2/
    parse/py/                 ← Python → .py.east1（言語固有）
    resolve/py/               ← .py.east1 → .east2（言語固有の正規化 + cross-module 型解決）
    compile/                  ← .east2 → .east3（言語非依存の core lowering）
    optimize/                 ← .east3 → 最適化済み .east3（whole-program）
    emit/
      cpp/                    ← .east3 → .cpp（target 固有）
      rs/
      ...
```

### 3.3 テストディレクトリ構成

fixture テストと sample テストを分離する。粒度・実行時間が異なるため混在させない。

#### fixture 系（小さい・多数・高速）

```
test/
  fixture/
    source/
      py/                            ← 正例ソース（サブディレクトリ分類あり）
        collections/
          boolop_value_select.py
        core/
          add.py
        ...
      py-negative/                   ← 負例ソース（parse/resolve 失敗を期待）
        ng_kwargs.py
        dict_get_items.py
        ...
    east1/py/                        ← parse の期待出力（正例のみ）
      collections/
        boolop_value_select.py.east1
    east2/                           ← resolve の期待出力
      collections/
        boolop_value_select.east2
    east3/                           ← compile の期待出力
      collections/
        boolop_value_select.east3
    east3-opt/                       ← optimize の期待出力
      collections/
        boolop_value_select.east3
    emit/                            ← emit parity の正解 stdout（全言語共通）
      collections/
        boolop_value_select.txt
```

- `source/py/` は正例のみ。golden 生成は全件 OK になる。
- `source/py-negative/` は負例。parse/resolve が特定のエラーで失敗することを期待するテスト。
- golden ディレクトリはサブディレクトリ構造を `source/py/` と同じに維持する。

#### sample 系（大きい・18件・重い end-to-end）

```
sample/py/                           ← sample ソース（既存のまま、移動しない）
sample/golden/manifest.json          ← emit parity の正解（stdout_normalized + artifact sha256）

test/
  sample/                            ← sample の golden のみ
    east1/py/                        ← parse の期待出力
      01_mandelbrot.py.east1
    east2/                           ← resolve の期待出力
      01_mandelbrot.east2
    east3/                           ← compile の期待出力
      01_mandelbrot.east3
    east3-opt/                       ← optimize の期待出力
      01_mandelbrot.east3
```

- sample のソースは `sample/py/` を直接参照する（コピーや symlink は作らない）
- sample の emit parity 正解は `sample/golden/manifest.json` を参照する（`test/sample/emit/` は作らない）

#### データの流れ

fixture 系:
```
test/fixture/source/py/*.py      → parse    → test/fixture/east1/py/*.py.east1
test/fixture/east1/py/*.py.east1 → resolve  → test/fixture/east2/*.east2
test/fixture/east2/*.east2       → compile  → test/fixture/east3/*.east3
test/fixture/east3/*.east3       → optimize → test/fixture/east3-opt/*.east3
test/fixture/east3-opt/*.east3   → emit     → compile → run → test/fixture/emit/*.txt と一致
```

sample 系:
```
sample/py/*.py                   → parse    → test/sample/east1/py/*.py.east1
test/sample/east1/py/*.py.east1  → resolve  → test/sample/east2/*.east2
test/sample/east2/*.east2        → compile  → test/sample/east3/*.east3
test/sample/east3/*.east3        → optimize → test/sample/east3-opt/*.east3
test/sample/east3-opt/*.east3    → emit     → compile → run → sample/golden/manifest.json と一致
```

#### 設計原則

- fixture と sample は独立に実行できる（CI で分けられる）
- 各段のディレクトリは期待出力のみを持つ（`source/py/` だけが入力ソース）
- emit は golden file テスト（テキスト一致）ではなく parity テスト（実行結果一致）
  - emit の生成コードはフォーマット変更で頻繁に変わるため、テキスト一致は脆い
- emit parity の正解 stdout は全言語共通（言語別サブディレクトリなし、CRLF/LF は比較時に正規化）
- fixture の emit 正解は `test/fixture/emit/*.txt`、sample は `sample/golden/manifest.json`
- `source/py/` は将来 `source/rb/` 等に対応可能

## 4. 除去されるもの

- `src/toolchain/frontends/signature_registry.py` のハードコードテーブル全体
- `src/toolchain/frontends/frontend_semantics.py` のハードコードテーブル（semantic_tag 等）
- `core_expr_named_call_annotation.py` 等の built-in 型ハードコード
- `_NONCPP_MODULE_ATTR_RUNTIME_CALLS` 等の runtime dispatch テーブル

## 5. toolchain2/ コーディング規約

`toolchain2/` は selfhost 対象（トランスパイラ自身をトランスパイルして C++ 等で動かす）として設計する。現行 `toolchain/` の反省を踏まえ、以下を必須とする。

### 5.1 `Any` 禁止・EAST ノードは dataclass で型付け

- `dict[str, Any]` で EAST ノードを扱うことを**禁止**する。
- EAST ノードは `@dataclass` で定義し、全フィールドに具象型を付ける。
- これにより selfhost 時に C++ の struct / Rust の struct に直接写像できる。

```python
@dataclass
class FunctionDef:
    name: str
    original_name: str
    args: list[Arg]
    arg_types: list[str]
    return_type: str
    body: list[Stmt]
    decorators: list[str]
    source_span: SourceSpan

@dataclass
class Call:
    func: Expr
    args: list[Expr]
    resolved_type: str
    semantic_tag: str
    runtime_module_id: str
    runtime_symbol: str
    source_span: SourceSpan
```

- `typing.Any` の import 自体を禁止する（`typing` は注釈専用 no-op として許可するが、`Any` は使わない）。
- `typing.Optional[X]` と `typing.Union[X, Y]` は使用可。パーサーが `X | None` / `X | Y` に正規化する。
- `object` 型も禁止する（Python では `Any` と同義であり、C++ 等に写像できない）。
- `dict[str, Any]` だけでなく `dict[str, object]` も同様に禁止。
- JSON シリアライズには `pytra.std.json` を使う（Python 標準 `json` は §5.2 で禁止）。
- EAST ノードの `to_dict()` 戻り値型は `dict[str, object]` ではなく `pytra.std.json.JsonVal`（`= None | bool | int | float | str | list[JsonVal] | dict[str, JsonVal]`）を使う。
- `JsonVal` は再帰的 Union 型として EAST ノードの全フィールドをカバーでき、`object` / `Any` が不要になる。
- シリアライズは `pytra.std.json.dumps(node.to_dict(), indent=2)` で完結する。
- ノード種別の判定は `isinstance()` で行い、`dict.get("kind")` パターンを使わない。
- 既存 `toolchain/` との橋渡しで `dict[str, Any]` が必要な場合は、境界の変換関数に限定し `toolchain2/` 内部に漏らさない。

### 5.2 pytra.std の機能を再実装しない

- `pytra.std.*` に既に存在する機能（`json.dumps`, `re.match`, `pathlib.Path` 等）を `toolchain2/` 内で自前実装することを禁止する。
- `pytra.std.*` のサポート範囲で足りない場合は、`pytra.std.*` 側を拡張する。`toolchain2/` 側に回避実装を書かない。

### 5.3 Python 標準モジュール直接 import 禁止

- `json`, `pathlib`, `sys`, `os`, `glob`, `re` 等の Python 標準モジュールを直接 import しない。
- `pytra.std.*` の shim を使う（例: `from pytra.std import json`, `from pytra.std.pathlib import Path`）。
- 例外: `typing` と `dataclasses` は no-op import として許可。

### 5.4 動的 import 禁止

- `try/except ImportError` フォールバック、`importlib` による遅延 import を使わない。
- import は静的に解決できる形で記述する。

### 5.5 Python `ast` モジュール禁止

- `import ast` / `from ast import ...` を使わない。
- 構文解析は selfhost 対応の自前パーサーで行う。

### 5.6 グローバル可変状態禁止

- 現行 `toolchain/` の `_SH_IMPORT_MODULES`, `_SH_IMPORT_SYMBOLS` 等のモジュールレベル可変グローバルを使わない。
- 状態はコンテキストオブジェクト（dataclass）に閉じ込め、関数引数で渡す。
- これにより並列処理が安全になり、テストも容易になる。

### 5.7 ハードコードテーブル禁止

- 関数シグネチャ、semantic_tag、runtime_call 等の情報を Python コード内にハードコードしない。
- これらは全て EAST1 から抽出し、resolve 段で解決する。
- `signature_registry.py` や `frontend_semantics.py` のようなテーブルを `toolchain2/` に持ち込まない。

### 5.8 selfhost 対象外コードの分離

- テストコード（`test/`）、ツール（`tools/`）、CLI のエントリポイント（`pytra-cli2.py`）は selfhost 非対象。
- これらでは `Any`, Python 標準モジュール, `ast`, 動的 import の使用を許可する。
- **`toolchain2/` 配下のみが selfhost 対象。** `toolchain2/` 以外のファイルから `toolchain2/` の内部モジュールを import するのは自由だが、その逆（`toolchain2/` から `pytra-cli2.py` や `toolchain/` を import すること）は禁止。

判定基準:
| ファイル | selfhost 対象 | `Any` | 動的 import | Python 標準 |
|---|---|---|---|---|
| `src/toolchain2/**/*.py` | **対象** | 禁止 | 禁止 | 禁止 |
| `src/pytra-cli2.py` | **対象** | 禁止 | 禁止 | 禁止（`pytra.std.*` を使用） |
| `src/toolchain/**/*.py` | 非対象（旧） | 許可 | 許可 | 許可 |
| `test/**/*.py` | 非対象 | 許可 | 許可 | 許可 |
| `tools/**/*.py` | 非対象 | 許可 | 許可 | 許可 |

## 6. 移行方針: golden file 駆動

`toolchain2/` は `toolchain/` を import しない。現行 `toolchain/` への依存はゼロとする。

移行手順（各段共通）:

1. **golden file 生成**: 現行 `toolchain/` で全 sample の出力を生成し、`test/` に golden file として保存する
2. **自前実装**: `toolchain2/` に独立実装を書く（`toolchain/` を import しない）
3. **テスト**: 自前実装の出力が golden file と一致するか検証する
4. **完了**: 一致したらその段は完成

### 6.1 golden file 生成の一元化

golden file の生成は `pytra-cli2 -golden` コマンドに一元化する。各 agent が独自スクリプトを作ることを禁止する。

```bash
# 各段の golden file 一括生成（現行 toolchain/ を使用）
pytra-cli2 -golden --stage=east1 --from=python -o test/east1/py/
pytra-cli2 -golden --stage=east2 --from=python -o test/east2/py/
pytra-cli2 -golden --stage=east3 -o test/east3/
pytra-cli2 -golden --stage=east3-opt -o test/east3-opt/
pytra-cli2 -golden --stage=emit --target=cpp -o test/emit/cpp/
```

- golden file 生成は `tools/generate_golden.py`（selfhost 非対象）に分離する。`pytra-cli2.py` の `-golden` サブコマンドは廃止予定。
- `pytra-cli2.py` は selfhost 対象とし、`toolchain/` への依存を持たない。
- `tools/generate_golden.py` は内部で現行 `toolchain/` を呼んでよい。
- 入力は `sample/py/*.py`（全 sample を自動列挙）
- 出力先を `-o` で指定。省略時はデフォルトの `test/<stage>/` に出力
- `toolchain2/` の自前実装が完成したら、golden file は回帰テスト用として維持する

例（parse 段）:

```bash
# 1. 現行 toolchain で golden file を生成
PYTHONPATH=src python3 src/toolchain/compile/cli.py sample/py/01_mandelbrot.py \
  --east-stage 1 -o test/east1/py/01_mandelbrot.py.east1

# 2. toolchain2 の自前実装で出力
PYTHONPATH=src python3 src/pytra-cli2.py -parse sample/py/01_mandelbrot.py \
  -o work/tmp/01_mandelbrot.py.east1

# 3. diff で検証
diff test/east1/py/01_mandelbrot.py.east1 work/tmp/01_mandelbrot.py.east1
```

この方式により:
- `toolchain2/` が `toolchain/` に一切依存しない
- golden file が「正解」として機能し、実装の正しさを保証する
- `toolchain/` は golden file 生成後は不要（最終的に除去可能）
- 各段を独立に開発・検証できる

## 決定ログ

### 2026-03-24: [ID: P0-PIPELINE-V2-S0] `-golden` コマンド実装

- `pytra-cli2 -golden --stage={east1,east2,east3,east3-opt} -o DIR` を実装。
- 現行 `toolchain/` を使い、`sample/py/*.py` 全18件を自動列挙して golden file を生成する。
- EAST1: `convert_path` + `normalize_east1_root_document`
- EAST2: `load_east_document`（parse + east1→east2 正規化）
- EAST3: `load_east3_document` with `east3_opt_level=0`
- EAST3-opt: `load_east3_document` with `east3_opt_level=1`
- 全4段 × 18 sample = 72 golden file の生成を確認。冪等性も検証済み。
- emit 段の golden file 生成は現時点では対応しない（S5 時に追加）。

### 2026-03-24: [ID: P0-PIPELINE-V2-S1] 自前パーサー初期実装

- `toolchain2/parse/py/` に toolchain/ 非依存の自前パーサーを実装開始。
- nodes.py: EAST1 dataclass ノード定義 (Any/object 禁止、JsonVal ベース)。
- parser.py: 行ベースパーサー (regex 不使用)。式パーサー (precedence climbing) + 文パーサー。
- 17_monte_carlo_pi.py で Module 構造の正しい生成を確認。golden file との差分残 ~15%。
- 残課題: source_span 精度、expr repr 切り出し、制御構文スパン計算。

### 2026-03-24: [ID: P0-PARSE-S1] fixture golden 一致 進捗

- fixture 132件中: exact_match=14, parse_err=5, diff=113
- 完了した修正: キー順序、trivia/leading_comments、main リネーム、ClassDef 構造、
  ForRange target/span、numeric promotion casts、listcomp/slice/decorator 構文対応、
  set リテラル、論理行マージ、import symbol runtime 情報。
- pytra.std.re / pytra.std.json を使用 (§5.2 準拠)。
- parse_err 残 5件: lambda, generator expression, *args, f-string format, re.sub 引数。
- diff 残 113件: 主にセマンティクス差分 (import symbol runtime 解決の詳細、OOP 型推論)。

### 2026-03-24: [ID: P0-RESOLVE-S1/S2/S3] resolve 実装完了

- `toolchain2/resolve/py/resolver.py` に east1→east2 resolver を実装。
- 現時点の resolve はメタデータ正規化のみ: east_stage=2, schema_version=1, dispatch_mode="native"。
- fixture 132 件・sample 18 件の全件が golden と完全一致を確認。
- `pytra-cli2 -resolve` サブコマンドを実装し、CLI 経由での resolve を可能にした。
- toolchain/ への依存ゼロ。§5 コーディング規約 (Any/object 禁止、pytra.std.* のみ) を遵守。
- 将来の cross-module 型解決・import graph ソート・構文正規化は、golden file が変更された段階で追加実装する。

### 2026-03-24: [ID: P0-COMPILE-S1/S2/S3] compile (east2→east3) 実装完了

- `toolchain2/compile/` に east2→east3 core lowering を実装。
- ファイル構成: `jv.py` (JsonVal ヘルパー)、`source_span.py` (span 正規化)、`type_summary.py` (型要約・nominal ADT)、`lower.py` (メイン lowering + 全ノード変換)、`passes.py` (17 のポスト lowering パス)。
- toolchain/ の全 17 パスを toolchain2/ へ移植: source_span rename, For/ForRange→ForCore, type_expr_summary_v1, isinstance/issubclass lowering, nominal ADT metadata, call metadata, vararg desugaring, yield lowering, listcomp lowering, default arg expansion, tuple target expansion, enumerate lowering, block scope hoist, integer promotion, type propagation, yields_dynamic, swap detection, mutates_self, unused var detection, main guard discard。
- fixture 132 件・sample 18 件の全 150 件が golden と完全一致を確認。
- `pytra-cli2 -compile` サブコマンドを実装。
- toolchain/ への依存ゼロ。§5 コーディング規約 (Any/object 禁止、JsonVal ベース) を遵守。

### 2026-03-24: [ID: P0-OPTIMIZE-S1/S2/S3] optimize (east3→east3) 実装完了

- `toolchain2/optimize/` に EAST3 optimizer を実装。
- ファイル構成: `optimizer.py` (PassContext/PassResult/PassManager フレームワーク)、`utils.py` (共有ユーティリティ)、`passes/` (15 パスを個別ファイルに分離)。
- toolchain/ の全 15 ローカルパスを toolchain2/ へ移植: NoOpCastCleanup, LiteralCastFold, IdentityPyToElision, NumericCastChainReduction, RangeForCanonicalization, ExpressionNormalization, EmptyInitShorthand, SafeReserveHint, TypedEnumerateNormalization, TypedRepeatMaterialization, DictStrKeyNormalization, TupleTargetDirectExpansion, LifetimeAnalysis, UnusedLoopVarElision, StrengthReductionFloatLoop。
- fixture 132 件・sample 18 件の全 150 件が golden と完全一致を確認。
- `pytra-cli2 -optimize` サブコマンドを実装。
- toolchain/ への依存ゼロ。§5 コーディング規約 (Any/object 禁止、JsonVal ベース、pytra.std.* のみ) を遵守。
- `copy.deepcopy` は pytra.std にないため、JSON 値の再帰コピー関数 (`deep_copy_json`) で代替。

## 7. 未決事項

- `--from=python` 以外の frontend が現実的に必要になる時期
- `.east1` / `.east2` / `.east3` のシリアライズ形式（JSON 維持 or バイナリ形式導入）
- optimize 段をスキップするオプション（`-build --no-optimize` 等）の提供
- `-build` 時の中間ファイル配置（一時ディレクトリ or `work/` 配下）
