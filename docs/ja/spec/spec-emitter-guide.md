<a href="../../en/spec/spec-emitter-guide.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# Emitter 実装ガイドライン

このドキュメントは、新しいターゲット言語の backend（emitter）を実装するとき、および既存 emitter をメンテナンスするときに従う規約です。

## 0. パイプライン正本

**emitter の正本は `src/toolchain2/emit/<lang>/` である。**

- parity check は `runtime_parity_check_fast.py` を使う。

## 1. 原則

- emitter は **EAST3 の情報だけ** を使ってコードを生成する。モジュール名やパスのハードコード禁止。
- `pytra.std.*` / `pytra.utils.*` / `pytra.built_in.*` 等の具体的なモジュール ID を emitter にハードコードしてはならない。
- runtime 関数の呼び出し規約（builtin か extern delegate か）は `runtime_call_adapter_kind` フィールドで判定する。`runtime_module_id.startswith("pytra.std.")` のようなハードコードは禁止。
- import パス解決、@extern 委譲、runtime コピーは `loader.py` の共通関数に委譲する。
- emitter 固有のロジックは「EAST3 ノード → ターゲット言語の構文」の変換のみに限定する。

### 1.1 emitter の禁止事項

emitter は EAST3 を忠実にレンダリングする。以下は禁止:

| 禁止事項 | 理由 | 正しい対処 |
|---|---|---|
| **cast を追加する** | EAST に必要な cast がないのは resolve のバグ | resolve を修正する |
| **変数の型を変更する** | EAST の `resolved_type` が正本 | resolve を修正する |
| **for-range のループ変数の型を変更する** | EAST の型情報が正本 | resolve を修正する |
| **mapping にない名前変換をハードコードする** | `mapping.json` が正本 | mapping.json に追加する |
| **型推論を再実装する** | §12.1 参照 | EAST の型推論を修正する |
| **戻り値型が未確定の FunctionDef を受理する** | resolve が `None` または注釈から確定しているはず | resolve のバグ |
| **`in` 演算子を tuple 要素数ごとに特殊化する** | tuple は iterable。要素数ごとの runtime 実装は破綻する | iterable の汎用 `contains` で処理する（`slice.contains()`, `[]T.contains()` 等） |

emitter が許可されるのは:

| 許可事項 | 説明 |
|---|---|
| EAST ノードをターゲット言語の構文にレンダリングする | emitter の本務 |
| `mapping.json` の `calls` に従って名前を写像する | §7 参照 |
| `mapping.json` の `implicit_promotions` に従って cast 出力をスキップする | §12.4 参照。出力を省略するだけで、追加はしない |
| 特殊マーカー（`__CAST__` 等）を言語固有の構文に展開する | §5 参照 |

**EAST の情報が不足している場合は、emitter にワークアラウンドを書くのではなく、EAST（resolve/compile/optimize）を修正すること。**

### 1.5 `str()` / `int()` 等のビルトインキャストと boxing 回避

`str(x)` は EAST3 で `semantic_tag: "cast.str"` / `runtime_call: "py_to_string"` に lower される。EAST3 の `call_arg_type` は `Obj`（object 期待）になっているが、**emitter は `call_arg_type` ではなく引数の `resolved_type` を見て、具体型のまま runtime 関数を呼ぶこと。**

```python
# Python
s: str = str(42)
```

```
# EAST3
Call: str(42)
  semantic_tag: "cast.str"
  runtime_call: "py_to_string"
  arg[0].resolved_type: "int64"    ← これを使う
  arg[0].call_arg_type: "Obj"      ← これは無視
```

```cpp
// 正しい C++ — boxing なし
str s = py_to_string(int64(42));

// 間違い — 不要な boxing
str s = py_to_string(object(int64(42)));
```

大半の言語の runtime は `py_to_string` / `str()` に具体型のオーバーロードを持っている。`object` 経由で boxing する必要はない。

このルールは `str()` だけでなく `int()` / `float()` / `bool()` / `len()` 等のビルトインキャスト・関数にも適用される。`call_arg_type: Obj` は Python の動的 dispatch を表しているだけで、静的型が `resolved_type` に載っているならそれを使うこと。

### 1.2 EAST3 の前提条件

emitter に到達する EAST3 は以下を満たしていなければならない。満たさない場合は前段のバグであり、emitter で吸収してはならない。

- 全ての `FunctionDef` / `ClosureDef` の `return_type` が確定していること。`unknown` や空文字は許容しない。**戻り値型注釈がない関数は、body に `return <値>` がなければ `None` として確定する。`return <値>` があるのに注釈がない場合は resolve が `inference_failure` で停止する。**
- 全ての式ノードの `resolved_type` が確定していること（`unknown` はゼロ）。
- `range()` が生の `Call` として残っていないこと（`ForRange` / `RangeExpr` に変換済み）。

### 1.3 emitter 実装コードの記述ルール

emitter 自体のコード（`src/toolchain2/emit/` 配下の Python ファイル）は selfhost 対象である。以下を守ること。

- **値を返す関数には戻り値型の注釈を書くこと。** `-> None` は省略可能（body に `return <値>` がなければ自動的に `None`）。注釈なしで `return <値>` があると resolve が `inference_failure` で停止する。
- **`pytra.std.*` 以外の Python 標準モジュールを import しないこと。**
- **動的 import（`try/except ImportError`、`importlib`）を使わないこと。**
- **Python 標準 `ast` モジュールに依存しないこと。**

### 1.4 生成コードの品質要件

emitter が生成するコードは、ターゲット言語のイディオムに沿った品質を維持すること。

**例外安全性（C++）:**

生成コードは例外安全でなければならない。`new` が2回以上現れる式では、最初の確保が成功した後に2回目の確保が失敗した場合にリークしない構成にする。

```cpp
// NG: boxed がリークする可能性がある
auto* boxed = new PyBoxedValue<int64>(v);
cb = new ControlBlock{0, tid, boxed};  // bad_alloc → boxed がリーク

// OK: make_unique で所有権を保持し、成功後に release
auto boxed = std::make_unique<PyBoxedValue<int64>>(v);
cb = new ControlBlock{0, tid, boxed.get()};
boxed.release();
```

実用上 `bad_alloc` でリカバーすることはないが、変換器が生成するコードとして例外安全を保証する。

**予約語エスケープ:**

ユーザーの識別子（関数名、メソッド名、変数名）がターゲット言語の予約語と衝突する場合は、末尾に `_` を付与してエスケープする。

```cpp
// Python: def double(x: int) -> int: ...
// C++: double は型キーワードなのでリネーム
int64 double_(int64 x) { ... }
```

各 emitter は予約語テーブルを持ち、衝突判定を行うこと（Go: `_safe_go_ident`、C++: `_safe_cpp_ident`）。

**RC 化の汎用パターン（C++）:**

非 POD 型の値を RC で包む処理は、型ごとの専用関数（`rc_list_from_value` 等）ではなく、汎用の `rc_from_value<T>` を使う。emitter は「POD か非 POD か」だけを判定し、非 POD なら `rc_from_value(...)` で包む。

```cpp
// NG: 型ごとに関数を分ける（emitter に型別分岐が必要）
rc_list_from_value(list<str>{str("a"), str("b")})
rc_dict_from_value(dict<str, int64>{...})

// OK: 汎用1本（emitter は非POD → rc_from_value で包むだけ）
rc_from_value(list<str>{str("a"), str("b")})
rc_from_value(dict<str, int64>{...})
rc_from_value(Foo{...})
```

**冗長な出力の禁止:**

生成コードはターゲット言語のプログラマが読んで違和感がないレベルの品質を維持すること。`sample/` に出力されるコードは Pytra の展示物であり、冗長な記述は印象を損なう。

各 emitter 担当は `sample/<lang>/` の生成コードを目視確認し、以下の NG パターンを除去すること。

```cpp
// NG: POD 型リテラルに explicit cast
int64 row_sum = int64(0);
float64 x = float64(1.5);
bool flag = bool(true);

// OK: リテラルをそのまま出力
int64 row_sum = 0;
float64 x = 1.5;
bool flag = true;
```

```cpp
// NG: 不要な str() ラッパー
str name = str("hello");

// OK: 文字列リテラルをそのまま出力
str name = "hello";
```

```go
// NG: 不要な型変換
var count int64 = int64(0)

// OK: リテラルをそのまま出力
var count int64 = 0
```

```typescript
// NG: 不要な Number() ラッパー
let x: number = Number(0);

// OK: リテラルをそのまま出力
let x: number = 0;
```

```cpp
// NG: ゼロ初期化にデフォルトコンストラクタ
int64 r = int64{};
float64 x = float64{};

// OK: リテラルで初期化
int64 r = 0;
float64 x = 0.0;
```

```cpp
// NG: 冗長な括弧（演算子の優先順位で自明な場合）
int64 x = (a) + (b);
int64 y = (a + b) * c;  // + より * が先なので括弧が必要 → これは OK

// OK: 自明な括弧を除去
int64 x = a + b;

// OK: 演算順序を変えるための括弧は残す
int64 z = a * (b + c);   // 括弧なしだと a*b+c になるので必要
float64 w = a * (b * c); // 浮動小数の結合順で結果が変わり得るので残してよい
```

一般規則:
- EAST3 の `Call(Name("<pod_type>"), [Constant(value)])` は、引数がリテラル1つの場合、型コンストラクタ呼び出しではなくリテラルそのものを出力する
- `str(literal)` は文字列リテラルとして出力する
- `bool(True)` / `bool(False)` は `true` / `false` として出力する
- 上記はターゲット言語の型推論で曖昧にならない場合のみ。型注釈が必要な言語では注釈で型を示し、リテラルは素で出力する
- POD 型のデフォルト値初期化にはリテラル（`0`, `0.0`, `false`, `""`）を使い、デフォルトコンストラクタ（`int64{}`, `float64{}`）を使わない
- 括弧は演算子の優先順位で自明な場合は出力しない。ただし演算順序を変える括弧は残す。特に浮動小数点の結合順（`a * (b * c)` vs `(a * b) * c`）で結果が変わり得る場合は括弧を残してよい
- CommonRenderer が「親の演算子優先順位 ≥ 子の演算子優先順位なら括弧を付ける」共通ロジックを持ち、各言語は自分の優先順位テーブルを渡す設計とする

### runtime_call_adapter_kind

Call ノードの `runtime_call_adapter_kind` は、runtime 関数の呼び出し規約を示す。EAST3 が `runtime_module_id` の所属グループから自動導出する。

| 値 | 意味 | 例 |
|---|---|---|
| `"builtin"` | `py_runtime` が `__pytra_` prefix で提供する関数 | `py_print`, `py_len` |
| `"extern_delegate"` | 生成された `std/<mod>.<ext>` が bare name で提供する `@extern` 委譲関数 | `perf_counter`, `sqrt` |
| `""` (空) | 未解決またはユーザー定義関数 | user-defined functions |

```python
# 禁止パターン
if runtime_mod_id.startswith("pytra.std."):  # ← ハードコード
    call_name = bare_name

# 正しいパターン
adapter = call_node.get("runtime_call_adapter_kind", "")
if adapter == "extern_delegate":
    call_name = bare_name
elif adapter == "builtin":
    call_name = "__pytra_" + bare_name
```

## 2. emitter の呼び出し構造

### 2.1 CLI エントリポイント

`pytra-cli2.py` の `-emit` / `-build` コマンドは、各言語の emitter を **subprocess** で呼び出す。直接 import しない。

```
pytra-cli2.py -build --target cpp input.py
  → parse → resolve → compile → optimize → link → manifest.json
  → subprocess: python3 -m toolchain2.emit.cpp.cli manifest.json -o out/
```

これにより `pytra-cli2.py` は使わない言語の emitter をロードしない（起動速度の維持）。

### 2.2 各言語の cli.py

各言語は `src/toolchain2/emit/<lang>/cli.py` を提供する。中身は共通ランナーに emit 関数を渡すだけ:

```python
from toolchain2.emit.common.cli_runner import run_emit_cli
from toolchain2.emit.<lang>.emitter import emit_<lang>_module

if __name__ == "__main__":
    import sys
    raise SystemExit(run_emit_cli(emit_<lang>_module, sys.argv[1:]))
```

manifest 読み、モジュールループ、引数解析は `run_emit_cli`（共通ランナー）が行う。各言語は emit 関数だけ提供する。

### 2.3 emit 関数のインターフェース

各言語の emitter は以下のシグネチャを満たす:

```python
def emit_<lang>_module(east_doc: dict[str, JsonVal]) -> str:
    """EAST3 ドキュメントからターゲット言語のコードを生成して返す。"""
    ...
```

C++ のように `module_kind` で処理を分ける必要がある言語は、`east_doc` 内の `meta` から `module_kind` を読んで内部で分岐する。cli.py や共通ランナーは `module_kind` を知らない。

### 2.4 runtime_parity_check_fast.py からの呼び出し

`tools/check/runtime_parity_check_fast.py` は `tools/` 配下（selfhost 対象外）なので、`emit_<lang>_module` を直接 import してよい。ただし共通の emit ループ（`run_emit_cli` 相当）を使い、言語固有のロジックを parity check に書かないこと。

### 2.5 禁止事項

- `pytra-cli2.py` が各言語の emitter を直接 import すること（subprocess で cli.py を呼ぶ）
- cli.py に manifest 読みやモジュールループを独自実装すること（共通ランナーを使う）
- 共通ランナーが `module_kind` を分岐すること（各言語の emit 関数の内部責務）

## 3. import パスの解決

### 禁止パターン

```python
# NG: モジュール名のハードコード
if module_id == "pytra.utils":
    zig_path = "utils/" + name + ".zig"
elif module_id.startswith("pytra.std."):
    zig_path = "std/" + tail + ".zig"
```

### 正しいパターン

```python
# OK: module_id から機械的にパスを生成
def _module_id_to_import_path(module_id: str, ext: str, root_rel_prefix: str) -> str:
    rel = module_id
    if rel.startswith("pytra."):
        rel = rel[len("pytra."):]
    return root_rel_prefix + rel.replace(".", "/") + ext
```

### import 文生成が不要な言語

Swift のように全ファイルを一括コンパイルし、同一モジュール内のシンボルが `import` なしで相互参照可能な言語では、**ソースに import 文を生成する必要がない**。

ただし `build_import_alias_map` は import 文生成のためだけでなく、**module attr call の owner 名解決**（`math.sqrt` → `pytra.std.math` → 正しい namespace/関数呼び出し）にも使われる。import 文を生成しない言語でも `build_import_alias_map` は必要。

| 言語 | import 文生成 | `build_import_alias_map` |
|---|---|---|
| JS/TS | `import { ... } from "..."` を生成 | 必要（import 生成 + alias 解決） |
| Go | import 不要（フラット配置） | 必要（alias 解決） |
| Swift | import 不要（一括コンパイル） | 必要（alias 解決） |
| Zig | `@import("...")` を生成 | 必要（import 生成 + alias 解決） |
| その他 | 言語に応じて生成 | 必要 |

### symbol import と module import の区別

`import_bindings` の `binding_kind` には `"module"` と `"symbol"` がある。これらを正しく区別すること。

```python
from re import sub       # binding_kind="symbol" — re モジュールの sub 関数
from pytra.utils import png  # binding_kind="symbol" — しかし png はサブモジュール
import math               # binding_kind="module" — math モジュール全体
```

**symbol import のインクルード/import パス生成:**

- `from re import sub` → `re` モジュールをインクルード（`std/re.<ext>`）
- `sub` はモジュール内の関数であり、**サブモジュールではない**
- `std/re/sub.<ext>` のようにシンボル名をパスに展開してはならない

```
# 正しい
from re import sub  → #include "std/re.h"      (C++)
                    → import { sub } from "./std/re.js"  (JS)

# 間違い
from re import sub  → #include "std/re/sub.h"  ← sub をサブモジュール扱い
```

**サブモジュール import の判別:**

`from pytra.utils import png` の `png` がサブモジュールかシンボルかは、linker が `module_id + "." + export_name` で runtime module が存在するか確認して判別済み。`build_import_alias_map` を使えば、emitter は判別ロジックを実装する必要がない。

### import alias の解決

`from pytra.std import os_path as path` のような alias は `build_import_alias_map` で解決:

```python
from toolchain2.emit.common.code_emitter import build_import_alias_map

alias_map = build_import_alias_map(east_doc.get("meta", {}))
# {"path": "pytra.std.os_path", "math": "pytra.std.math"}

# Attribute Call で owner_name を解決:
resolved_module = alias_map.get(owner_name, "")
if resolved_module != "":
    import_path = _module_id_to_import_path(resolved_module, ".zig", root_rel_prefix)
```

## 4. @extern 関数の委譲コード生成

spec-abi.md §3.2.1 に従い、C++ 以外の emitter は `@extern` 関数について `_native` モジュールへの委譲コードを生成する。

### 検出方法

```python
decorators = func_def.get("decorators", [])
if isinstance(decorators, list) and "extern" in decorators:
    # この関数は @extern → 委譲コードを生成
```

### 委譲コードの生成例

JS:
```javascript
import * as __native from "./std/time_native.js";
export function perf_counter() { return __native.perf_counter(); }
```

PowerShell:
```powershell
. "$PSScriptRoot/std/time_native.ps1"
function perf_counter { return (__native_perf_counter) }
```

Zig:
```zig
const __native = @import("std/time_native.zig");
pub fn perf_counter() f64 { return __native.perf_counter(); }
```

### extern() 変数（ambient global）の委譲

`@extern` 関数とは別に、`extern()` で宣言される変数（定数）がある:

```python
# math.py
pi: float = extern(math.pi)   # extern() 変数宣言
e: float = extern(math.e)
```

EAST3 では `AnnAssign` に `meta.extern_var_v1` が付与される。

emitter は `extern()` 変数を見たら、`@extern` 関数と同じく `__native` モジュールへの委譲を生成する:

```zig
// std/math.zig (generated)
const __native = @import("math_native.zig");
pub const pi: f64 = __native.pi;
pub const e: f64 = __native.e;
```

```javascript
// std/math.js (generated)
import * as __native from "./math_native.js";
export const pi = __native.pi;
export const e = __native.e;
```

対応する native ファイルにはターゲット言語の標準ライブラリの値を手書きで提供する:

```zig
// std/math_native.zig (hand-written)
const std = @import("std");
pub const pi: f64 = std.math.pi;
pub const e: f64 = std.math.e;
```

```javascript
// std/math_native.js (hand-written)
export const pi = Math.PI;
export const e = Math.E;
```

### 検出方法

```python
# 推奨: meta.extern_var_v1 で判定（構造に依存しない）
meta = stmt.get("meta", {})
extern_v1 = meta.get("extern_var_v1")
if isinstance(extern_v1, dict):
    symbol = extern_v1.get("symbol", "")  # 委譲先シンボル名
    # extern() 変数 → __native への委譲を生成
```

`meta.extern_var_v1` の構造:
```json
{"schema_version": 1, "symbol": "pi", "same_name": 1}
```

- `symbol`: 委譲先の native シンボル名
- `same_name`: target 名と symbol が一致するなら `1`

注意: value ノードは EAST3 lowering で `Unbox` にラップされる場合があるため、`value.get("kind") == "Call"` による直接検出は信頼できない。`meta.extern_var_v1` を正本とすること。

**禁止**: emitter がターゲット言語の標準ライブラリ定数（`std.math.pi`, `Math.PI` 等）をハードコードしてはならない。定数の値は native ファイルが提供する。

### native モジュールのパス

`canonical_runtime_module_id` で正規化し、`_native` suffix を付ける:

```python
from toolchain.frontends.runtime_symbol_index import canonical_runtime_module_id

clean_id = module_id.replace(".east", "")
canonical = canonical_runtime_module_id(clean_id)
# pytra.std.time → std/time_native.<ext>
parts = canonical.split(".")
if len(parts) > 1 and parts[0] == "pytra":
    native_path = "/".join(parts[1:]) + "_native.<ext>"
```

## 5. 出力ファイル名の統一規約

### モジュール → ファイル名のマッピング

全言語共通で以下のルールに従う。emitter が独自の命名規則を使ってはならない。

| module_id | 出力ファイル名 |
|---|---|
| `17_monte_carlo_pi` (entry) | `17_monte_carlo_pi.<ext>` |
| `pytra.std.time` | `std/time.<ext>` |
| `pytra.std.math` | `std/math.<ext>` |
| `pytra.utils.gif` | `utils/gif.<ext>` |
| `pytra.built_in.io_ops` | `built_in/io_ops.<ext>` |

変換ルール: `module_id` から `pytra.` prefix を除去し、`.` を `/` に置換して拡張子を付加。`emit_all_modules` が自動で行うため、emitter 側での実装は不要。

### フラット配置が必要な言語

Go のようにサブディレクトリの `.go` ファイルが別パッケージ扱いになる言語では、全ファイルを `emit/` 直下にフラット配置する必要がある。

この場合:
- `emit_all_modules` は使わず、独自ループでフラット出力する
- `copy_native_runtime` の代わりに、`built_in/` / `std/` 内のファイルを `emit/` 直下にコピーする
- ファイル名の衝突を避けるため、サブディレクトリ名を prefix として付ける（例: `std_time.<ext>`, `built_in_py_runtime.<ext>`）

```
# フラット配置の例（Go）
emit/
├── 17_monte_carlo_pi.go
├── std_time.go              # pytra.std.time
├── std_time_native.go       # 手書き native
├── std_math.go              # pytra.std.math
├── std_math_native.go
├── built_in_py_runtime.go   # 手書き built-in
└── utils_gif.go             # pytra.utils.gif
```

`loader.py` の `copy_native_runtime` に `flat=True` オプションを渡すとフラットコピーになる。`emit_all_modules` にも同様の `flat=True` オプションがある。

対象言語: Go（他にフラット配置が必要な言語があれば追加）。

### native ファイルの命名

手書きランタイムファイルは `_native` suffix を付ける:

| module_id | 生成ファイル | native ファイル |
|---|---|---|
| `pytra.std.time` | `std/time.<ext>` | `std/time_native.<ext>` |
| `pytra.std.math` | `std/math.<ext>` | `std/math_native.<ext>` |
| `pytra.built_in.io_ops` | `built_in/io_ops.<ext>` | （built_in は py_runtime に統合） |

### エントリモジュールの命名

- **標準**: module_id そのまま → `17_monte_carlo_pi.<ext>`
- **Scala のみ例外**: 全モジュールを単一ファイルにマージ

これら以外のエントリファイル名の変更は禁止。

### Java の main 分離

Java ではクラス名＝ファイル名が言語仕様で必須のため、`main()` メソッドだけを `Main.java` に分離する。ロジック本体は module_id から導出したファイル名で出力する。

```
emit/
├── 01_mandelbrot.java    # ロジック本体（関数・クラス定義）
├── Main.java             # main() のみ。本体クラスを呼び出す
├── std/time.java
└── ...
```

これにより:
- `sample/java/01_mandelbrot.java` と一致する（リネーム不要）
- `javac *.java` でコンパイルでき、`java Main` で実行できる
- `regenerate_samples.py` や `pytra-cli2.py` に Java 固有のリネームロジックが不要

## 5.1 @extern 委譲の命名統一

### 委譲先の変数名

全言語で `__native` を使う:

```javascript
// JS
import * as __native from "../std/time_native.js";
export function perf_counter() { return __native.perf_counter(); }
```

```zig
// Zig
const __native = @import("../std/time_native.zig");
pub fn perf_counter() f64 { return __native.perf_counter(); }
```

```powershell
# PowerShell
. "$PSScriptRoot/../std/time_native.ps1"
function perf_counter { return (__native_perf_counter) }
```

`__native` は予約語として扱い、ユーザーコードと衝突しないことを前提とする。PowerShell のように namespace がない言語では `__native_` prefix を関数名に付ける。

### 委譲関数の命名

- 生成される関数名は元の Python 関数名と**完全一致**させる。
- native ファイル内の実装関数名も元の Python 関数名と一致させる。
- `py_` prefix や `_native` suffix を関数名に付けてはならない（ファイル名の `_native` と関数名は別）。

```
# 正しい
def perf_counter() → std/time.js の export function perf_counter()
                   → std/time_native.js の function perf_counter()

# 間違い
def perf_counter() → function py_perf_counter()      ← prefix 禁止
                   → function perf_counter_native()   ← suffix 禁止
```

### native ファイルの import パス

`emit_context.root_rel_prefix` を使い、**同じモジュールの `_native` ファイル** を参照する:

```python
# std/time.<ext> から std/time_native.<ext> を参照
native_import_path = root_rel_prefix + "std/time_native.<ext>"
# root_rel_prefix = "../" (depth=1)  → "../std/time_native.<ext>"
# root_rel_prefix = "./"  (depth=0)  → "./std/time_native.<ext>"
```

## 6. runtime コピーと py_runtime の責務範囲

`emit_all_modules` に `lang="<lang>"` を渡せば、`src/runtime/<lang>/{built_in,std}/` から自動コピーされる。個別の `_copy_runtime` は不要。

コピーは生成済みファイルを上書きしない（@extern 委譲コードが先に生成されるため）。

### py_runtime の責務範囲

`built_in/py_runtime.<ext>` は **Python の built-in 関数に相当するヘルパーのみ** を提供する:

| 含めてよいもの | 例 |
|---|---|
| print / len / range / int / float / str / bool | Python の built-in 関数 |
| 型変換（py_to_bool 等） | Python の暗黙型変換 |
| コンテナ操作（list append 等） | Python のメソッド |
| 文字列操作（split, join 等） | str のメソッド |

| 含めてはならないもの | 理由 |
|---|---|
| `write_rgb_png` / `save_gif` / `grayscale_palette` | `pytra.utils.*` のモジュール関数。linker が必要な場合のみ生成 |
| `perf_counter` / `sqrt` / `sin` | `pytra.std.*` のモジュール関数。`_native` ファイルが提供 |
| JSON / pathlib / os 操作 | `pytra.std.*` のモジュール関数 |

`pytra.std.*` / `pytra.utils.*` の関数は、linker が依存解決した場合のみ `.east` → emitter 経由で生成される。`py_runtime` に含めると、その関数を使わないプログラムでもコンパイルエラー（未定義シンボル参照）が発生する。

### 画像 runtime（PNG/GIF）の手書き実装禁止

**`write_rgb_png` / `save_gif` / `grayscale_palette` のエンコード本体ロジック（CRC32 / Adler32 / DEFLATE / LZW / chunk 構築）をターゲット言語で手書き実装してはならない。**

これらの正本は `src/pytra/utils/png.py` / `src/pytra/utils/gif.py` であり、transpiler が各言語に変換した生成コード（`src/runtime/<lang>/generated/utils/png.*` / `gif.*`）のみを使う。

```
正本:     src/pytra/utils/png.py        ← Python ソース
生成物:   src/runtime/<lang>/generated/utils/png.<ext>  ← transpile 結果
native:   src/runtime/<lang>/native/utils/png_native.<ext>  ← I/O アダプタのみ
```

禁止される行為:
- `py_runtime` に `write_rgb_png` / `save_gif` を直接実装する
- ターゲット言語の画像ライブラリ（Go の `image/png`、Swift の `CoreGraphics` 等）を使って独自実装する
- CRC32 / DEFLATE / LZW のテーブルやアルゴリズムを手書きで移植する

許可される言語差分:
- I/O アダプタ（ファイル書き込み、バイト列変換）は `native/` に手書きしてよい
- 生成コードが呼ぶヘルパー関数（`write_bytes` 等）の native 実装

画像 runtime が動かない場合は、**transpile パイプライン（EAST → emitter）の修正** で対処すること。手書きで回避してはならない。

**正本ファイル（`src/pytra/utils/*.py`、`src/pytra/std/*.py`）は言語 backend 担当が変更してはならない。** これらのファイルは全言語の生成物の元になるため、変更は全言語に波及する。変更が必要な場合はプランナーまたはインフラ担当が全言語への影響を確認したうえで行う。

### built_in モジュールの emit スキップ

linker は `pytra.built_in.io_ops` / `pytra.built_in.scalar_ops` 等を link-output に含める（依存追跡のため）。しかし emitter はこれらのモジュールの **emit をスキップ** すべき。

理由: `built_in` モジュールの `@extern` 関数（`py_print`, `py_ord` 等）は `py_runtime.<ext>` が直接提供しており、`_native` ファイルへの委譲コード生成は不要。`io_ops_native` のような native ファイルも存在しない。

```python
# transpile_fn 内で built_in モジュールをスキップ
def _transpile(east_doc: dict) -> str:
    meta = east_doc.get("meta", {})
    emit_ctx = meta.get("emit_context", {}) if isinstance(meta, dict) else {}
    module_id = emit_ctx.get("module_id", "") if isinstance(emit_ctx, dict) else ""
    # built_in モジュールは py_runtime が提供するため emit 不要
    if module_id.startswith("pytra.built_in."):
        return ""  # 空文字を返すと emit_all_modules がファイル生成をスキップ
    ...
```

`emit_all_modules` は `transpile_fn` が空文字を返した場合、ファイルを生成しない。

| module_id | emit | 理由 |
|---|---|---|
| `pytra.built_in.io_ops` | **スキップ** | `py_runtime` が `py_print` 等を直接提供 |
| `pytra.built_in.scalar_ops` | **スキップ** | `py_runtime` が `py_ord` 等を直接提供 |
| `pytra.built_in.sequence` | **スキップ** | `py_runtime` が `py_range` 等を直接提供 |
| `pytra.std.time` | emit | `@extern` → `__native` 委譲コード生成 |
| `pytra.utils.png` | emit | 通常の関数コード生成 |

## 7. runtime mapping.json

各言語の runtime に `mapping.json` を配置し、EAST3 の `runtime_call` をターゲット言語の関数名に写像する。
`CodeEmitter` 基底クラスがこのファイルを読み込み、`resolve_runtime_call()` で解決する。

- 配置: `src/runtime/<lang>/mapping.json`
- 読み込み: `toolchain2/emit/common/code_emitter.py` の `load_runtime_mapping()`
- 命名ルール: `py_<type>_<method>` 形式（例: `py_str_strip`, `py_dict_get`）

**正式仕様: [spec-runtime-mapping.md](./spec-runtime-mapping.md)**

### 7.1 `calls` テーブルの用途

`calls` テーブルは関数呼び出しだけでなく、定数・変数の写像にも使われる。

| 用途 | 例（キー → 値） | 出力形式 |
|---|---|---|
| 関数呼び出し | `"py_len"` → `"py_len"` | 関数名としてそのまま出力 |
| 外部関数 | `"math.sqrt"` → `"std::sqrt"` | 外部ライブラリの関数名に置換 |
| 定数 | `"math.pi"` → `"M_PI"` | ターゲット言語の定数名に置換 |
| 特殊マーカー | `"static_cast"` → `"__CAST__"` | emitter が専用ロジックで展開 |

定数（`math.pi` → `M_PI`）は `extern_var_v1` メタデータが付いた `AnnAssign` ノードに対して解決される。emitter は `calls` テーブルの値をそのまま出力するため、ターゲット言語で有効な式でなければならない。

### 7.2 文字列リテラル定数の写像

ターゲット言語のマクロ定数ではなく、文字列リテラルそのものを埋め込みたい場合（例: `env.target` → `"cpp"`）は、値にクォートを含めて記述する:

```json
{
  "calls": {
    "env.target": "\"cpp\""
  }
}
```

emitter は `calls` の値を式としてそのまま出力するので、`"\"cpp\""` は C++/Go のソースコードに `"cpp"` として埋め込まれる。

この仕組みにより、`runtime_var` で宣言されたコンパイル時定数を mapping.json だけで言語ごとに定義できる。emitter に個別ロジックを追加する必要はない。

### 7.3 全言語必須エントリ

以下のエントリは全ての `mapping.json` に必須とする。新しい emitter を追加する際は忘れずに定義すること。

| キー | 値 | 説明 |
|---|---|---|
| `env.target` | `"\"<lang>\""` | 実行中のターゲット言語名。`pytra.std.env.target` の写像先 |

#### `env.target` とは

`pytra.std.env.target` は、現在のコードがどのターゲット言語で実行されているかを返すコンパイル時定数。ユーザーコードからは以下のように参照する:

```python
import pytra.std.env as env

if env.target == "python":
    # Python で直接実行している
    ...
elif env.target == "cpp":
    # C++ に変換されて実行している
    ...
```

emitter は mapping.json の `calls["env.target"]` を参照し、文字列リテラルとしてソースに埋め込む。runtime 関数の呼び出しは発生しない。

宣言は `include/py/pytra/std/env.py` に `runtime_var("pytra.std.env")` として置く。Python で直接実行する場合は mapping.json を経由しないため、モジュール側で `"python"` をデフォルト値として返す。

#### 各言語の定義例

```json
// src/runtime/cpp/mapping.json
"env.target": "\"cpp\""

// src/runtime/go/mapping.json
"env.target": "\"go\""

// src/runtime/rs/mapping.json
"env.target": "\"rs\""

// src/runtime/ts/mapping.json
"env.target": "\"ts\""
```

妥当性検証: `tools/check/check_mapping_json.py`（全 mapping.json に `env.target` が定義されているか等を検証）

### 7.4 型写像テーブル (`types`)

mapping.json の `types` テーブルは、EAST3 の型名をターゲット言語の型名に写像する。emitter は型名をハードコードせず、このテーブルから解決する。

```json
{
  "types": {
    "int64": "int64_t",
    "float64": "double",
    "bool": "bool",
    "str": "str",
    "Exception": "std::runtime_error",
    "Path": "PyPath"
  }
}
```

- POD 型（`int64`, `float64`, `bool`, `str` 等）もクラス型（`Exception`, `Path` 等）も同じテーブルで管理する
- `types` に一致しない型名はそのまま出力する（ユーザー定義クラス）
- `CodeEmitter` 基底クラスが `resolve_type(east3_type)` メソッドを提供する
- 各言語の `types.py` のハードコードは廃止し、mapping.json に統合する

正式仕様: [spec-runtime-mapping.md](./spec-runtime-mapping.md) §7

## 8. 共通ユーティリティ（`code_emitter.py` スタンドアロン関数）

`CodeEmitter` を継承しない emitter でも使える関数:

| 関数 | 用途 |
|---|---|
| `build_import_alias_map(meta)` | import alias → module_id マップ構築 |
| `collect_reassigned_params(func_def)` | 再代入される引数の検出（immutable 引数言語用） |
| `mutable_param_name(name)` | 引数リネーム（`data` → `data_`） |

```python
from toolchain2.emit.common.code_emitter import (
    build_import_alias_map,
    collect_reassigned_params,
    mutable_param_name,
)
```

## 8. emit_context の利用

`emit_all_modules` が各モジュールの `meta.emit_context` に設定する情報:

```python
emit_ctx = east_doc.get("meta", {}).get("emit_context", {})
module_id = emit_ctx.get("module_id", "")         # モジュール ID
root_rel_prefix = emit_ctx.get("root_rel_prefix", "./")  # ルートまでの相対パス
is_entry = emit_ctx.get("is_entry", False)         # エントリモジュールか
```

- `root_rel_prefix` はサブモジュールからの import パス解決に使う
- `is_entry` は main 関数の emit 判定に使う（下記参照）
- `module_id` は @extern 委譲先の native パス解決に使う

### is_entry と main_guard_body の扱い

リンクパイプラインは CLI で指定された 1 ファイルだけを `is_entry=True` とする。依存先モジュールは常に `is_entry=False` である。

emitter は以下のルールに従う:

- **`is_entry=True` のモジュール**: `main_guard_body`（`if __name__ == "__main__":` の本体）をターゲット言語の `main` 関数として出力する。
- **`is_entry=False` のモジュール**: `main_guard_body` が EAST に含まれていても **出力しない**。ライブラリモジュールとして扱う。
- Java のように `main` が別ファイルに分離される言語では、`is_entry=True` のモジュールに対してのみ `Main.java` を生成する（§5 参照）。
- emitter は `is_entry` を **自前で判定してはならない**。`emit_context.is_entry` を正本とする。

## 9. EAST3 ノードで emitter が対応すべきもの

| ノード | 説明 | emitter の責務 |
|---|---|---|
| `VarDecl` | hoist された変数宣言 | 型付き変数宣言を生成 |
| `Swap` | `a, b = b, a` パターン（**left/right は常に Name**） | 言語固有の swap コードを生成 |
| `discard_result: true` | main_guard_body の戻り値抑制 | 戻り値を捨てるコードを生成 |
| `unused: true` | 未使用変数（Assign / VarDecl / tuple 要素） | 警告抑制コード or 宣言省略 |
| `decorators: ["extern"]` | @extern 関数 | `_native` への委譲コードを生成 |
| `decorators: ["property"]` | @property メソッド | getter アクセスに変換 |
| `mutates_self: true/false` | メソッドの self mutation | mutable/immutable self を選択 |
| `ClosureDef` | nested FunctionDef の closure 化済みノード | 言語固有の closure 構文を生成（§9.2） |
| `With` | context manager（`with expr as var:`） | 言語固有の resource 管理構文を生成（§9.3） |

### 9.1 Swap ノードの契約

Swap ノードの `left` / `right` は **常に Name ノード** である。Subscript を含む swap（`values[i], values[j] = values[j], values[i]`）は EAST3 lowering で一時変数付き Assign 列に展開済みのため、emitter に Swap として到達しない。

emitter は Swap ノードを受け取ったら、**Name 同士の単純な値交換** だけを処理すればよい。Subscript 分岐は不要。

```python
# Swap ノードの構造（保証）
{"kind": "Swap", "left": {"kind": "Name", "id": "a"}, "right": {"kind": "Name", "id": "b"}}
```

各言語での生成例:

| 言語 | 生成コード |
|---|---|
| C++ | `std::swap(a, b);` |
| Go | `a, b = b, a` |
| Rust | `std::mem::swap(&mut a, &mut b);` |
| Swift | `swap(&a, &b)` |
| その他 | `tmp := a; a = b; b = tmp` |

Subscript swap は Assign として到達するため、emitter の通常の Assign 処理で自然に処理される。

### 9.2 ClosureDef ノードの契約

`ClosureDef` は nested FunctionDef を EAST3 lowering で closure 化したノードである。キャプチャ解析は EAST3 が完了済みであり、emitter はキャプチャ解析を再実装してはならない。

```json
{
  "kind": "ClosureDef",
  "name": "inner",
  "captures": [
    {"name": "x", "mode": "readonly", "type_expr": ...},
    {"name": "y", "mode": "mutable", "type_expr": ...}
  ],
  "args": [...],
  "body": [...],
  "return_type_expr": ...
}
```

- `captures`: 外側スコープからキャプチャする変数のリスト。
  - `name`: 変数名
  - `mode`: `readonly`（値キャプチャ可）または `mutable`（参照キャプチャ必須）
  - `type_expr`: キャプチャ変数の型（構造化型表現）
- emitter の責務は `ClosureDef` を各言語の closure 構文に写像することだけである。

各言語での生成例:

| 言語 | レベル | 生成コード |
|---|---|---|
| C++ | B | `auto inner = [&y, x](args) -> T { ... };`（mutable は参照、readonly は値） |
| Go | B | `inner := func(args) T { ... }`（Go は全て暗黙参照キャプチャ） |
| Java | B | ラムダまたは anonymous class（mutable capture は配列ラッパー等で回避） |
| C# | B | `Func<...> inner = (args) => { ... };` |
| Rust | A/B | `let inner = \|args\| -> T { ... };` |
| Swift | A/B | `let inner: (Args) -> T = { args in ... }` |
| Kotlin | A/B | `val inner: (Args) -> T = { args -> ... }` |
| JS | A | `function inner(args) { ... }` または `const inner = (args) => { ... }` |
| TS | A | 同上（型注釈付き） |

レベル A（nested function をネイティブサポート）の言語では、`ClosureDef` を通常の nested function として出力してもよい。その場合 `captures` 情報は無視できる。

禁止事項:

- emitter でキャプチャ変数の解析を行うこと（EAST3 の `captures` が正本）
- emitter で capture mode を変更すること
- `ClosureDef` が到達した場合に未対応として無視すること（fail-closed で停止する）

### 9.3 With ノードの契約

`With` は Python の `with expr as var:` に対応するリソース管理ノードである。EAST では lowering せずにそのまま保持されるため、emitter が各言語の適切な構文に写像する。

```json
{
  "kind": "With",
  "context_expr": { "kind": "Call", "...": "..." },
  "var_name": "f",
  "body": [...]
}
```

- `context_expr`: context manager を生成する式（例: `open(path, "wb")`）
- `var_name`: `as` で束縛される変数名（省略時は空文字）
- `body`: with ブロックの本体

各言語での生成例:

| 言語 | 生成パターン |
|---|---|
| C++ | RAII（スコープ終了で自動解放）または `try`/デストラクタ |
| Go | `f := open(...); defer f.Close(); ...` |
| Rust | スコープ終了で `Drop`、または明示 `drop()` |
| Java | `try (var f = open(...)) { ... }` (try-with-resources) |
| C# | `using (var f = open(...)) { ... }` |
| Kotlin | `open(...).use { f -> ... }` |
| Swift | スコープ終了で `defer { f.close() }` |
| JS/TS | `try { const f = open(...); ... } finally { f.close(); }` |

写像の原則:

- 言語にリソース管理構文がある場合（Java の try-with-resources、C# の using、Go の defer 等）はそれを使う。
- リソース管理構文がない場合は `try/finally` パターンで `close()` / 解放を保証する。
- `with` ブロックの本体で例外が発生しても、リソースが解放されることを保証する。

禁止事項:

- `With` を手動 `open/close` に展開して例外安全性を失うこと。
- `With` が到達した場合に未対応として無視すること（fail-closed で停止する）。
- **正本ソース（`src/pytra/utils/*.py` 等）の `with` 文を変換器の制約に合わせて書き換えること。** emitter が `With` に対応するのが正しい対処である。

## 10. コンテナ参照セマンティクス要件

### 10.1 必須ルール

Python の `list` / `dict` / `set` は参照セマンティクスである。関数にコンテナを渡して `.append()` / `.pop()` / `[]=` 等の破壊的操作を行った場合、呼び出し元のコンテナにその変更が反映されなければならない。

全 backend は、コンテナを**参照型ラッパー**（参照カウント、GC 参照、ポインタ等）で保持しなければならない。

```python
def add_item(xs: list[int], v: int) -> None:
    xs.append(v)  # 呼び出し元の xs に反映される

items: list[int] = [1, 2, 3]
add_item(items, 4)
print(items)  # [1, 2, 3, 4]
```

### 10.2 禁止パターン

言語ネイティブの値型コンテナをラッパーなしで直接使用してはならない。

| 言語 | NG（値型） | OK（参照型ラッパー） |
|---|---|---|
| Go | `[]any` | `*PyList` / 参照ラッパー構造体 |
| Swift | `[Any]` | `class PyList` / 参照型ラッパー |
| Rust | `Vec<PyAny>`（所有権 move） | `Rc<RefCell<Vec<T>>>` / 参照ラッパー |
| C++ | `list<T>`（値型直接） | `Object<list<T>>`（参照カウント） |

値型のまま EAST3 に `mutates_params` 等のアノテーションを追加して回避してはならない。これは runtime が値型であるというターゲット固有の問題を言語非依存 IR に漏らすワークアラウンドであり、メソッド追加のたびに IR 拡張が必要になる。参照型ラッパーにすれば `append` / `extend` / `pop` / `[]=` / `clear` / `sort` / `reverse` がすべて一括で解決する。

### 10.3 参考実装

| backend | 参照型ラッパー | 実装場所 |
|---|---|---|
| C++ | `Object<list<T>>` — `ControlBlock` による参照カウント + 型付きポインタ | `src/runtime/cpp/core/object.h` |
| Zig | `Obj` — `*anyopaque` + `*usize` (rc) + `drop_fn` | `src/runtime/zig/built_in/py_runtime.zig` |
| Java/Kotlin/C#/Scala | 言語の参照型クラス（`ArrayList`, `MutableList` 等）がそのまま参照セマンティクスを満たす | 各 `src/runtime/<lang>/` |

### 10.4 値型縮退の許可条件

型既知かつ non-escape であることが証明された局所経路に限り、値型への縮退を許可する。

- `container_ref_boundary`（`Any` / `object` / `unknown` への流入経路）では参照表現を維持する。
- `typed_non_escape_value_path`（型既知 + 局所 non-escape）でのみ shallow copy 材料化を許可する。
- 判定不能時は fail-closed で参照表現に倒す。

詳細は `spec-cpp-list-reference-semantics.md` §5 および `p3-multilang-container-ref-model-rollout.md` §S1-02 を参照。

### 10.5 optimizer ヒントによる値型縮退の実装

Go / Swift / Rust のようにコンテナの参照型ラッパーを導入した backend では、既定で全コンテナを参照型として保持する。ただし EAST3 optimizer（`ContainerValueLocalHintPass`）が escape 解析を行い、値型で安全に保持できるローカル変数を `container_value_locals_v1` ヒントとして linker 経由で供給する。

emitter は linked module の `meta.linked_program_v1.container_ownership_hints_v1.container_value_locals_v1` を参照し、ヒントに含まれるローカル変数については参照ラッパーではなく言語ネイティブの値型コンテナを使ってよい。

```
# linked module metadata の構造
meta.linked_program_v1.container_ownership_hints_v1:
  container_value_locals_v1:
    "<module_id>::<function_name>":
      version: "1"
      locals: ["xs", "buf"]    # 値型で安全な変数名リスト
```

実装例（Go emitter 擬似コード）:

```
# ヒントなし（既定）: 参照ラッパーを使用
xs := NewPyList()       # *PyList（参照型）

# ヒントあり: 値型で直接保持
xs := make([]int64, 0)  # []int64（値型スライス）
```

注意事項:

- ヒントが存在しない変数は**必ず参照型**で保持する（fail-closed）。
- ヒントは list のみが対象（dict / set は将来拡張）。

## 10.2 type_id テーブルの扱い

linker が生成する仮想モジュール `pytra.built_in.type_id_table` は、通常の EAST3 モジュールとして link-output に含まれる。

emitter の責務:

- isinstance はターゲット言語のネイティブ型判定機能（`instanceof`, `holds_alternative`, `match` 等）を使う（[spec-adt.md](./spec-adt.md) §3 参照）。
- `PYTRA_TYPE_ID` / `pytra_isinstance` / `type_id_table` は廃止予定。新規 emitter では使わない。

isinstance のサブタイプ規則:

- **`bool` は `int` のサブタイプではない。** `isinstance(True, int)` は Pytra では `False`。Python との非互換だが、型判定の実装を全言語で簡素化するため採用しない（[spec-python-compat.md](./spec-python-compat.md) 参照）。
- `IntEnum` / `IntFlag` の派生クラスは通常の class 継承として扱う（`isinstance(Color.RED, IntEnum)` → `True`）。ただし `isinstance(Color.RED, int)` → `False`。
- 全プリミティブ型（`bool`, `int`, `str`, `float`, `list`, `dict`, `set`, `None`）は leaf 型であり、相互にサブタイプ関係を持たない。

禁止事項:

- `PYTRA_TYPE_ID` フィールドを生成コードに埋め込んではならない。
- `pytra_isinstance(x, TID)` のような type_id ベースの判定を生成してはならない。ネイティブ機能を使う。
- runtime ヘッダーに type_id テーブルのサイズや値をハードコードしてはならない。

詳細は `spec-type_id.md` §7 を参照。

## 11. `yields_dynamic` 契約

コンテナ要素を抽出するメソッド呼び出し（`dict.get`, `dict.pop`, `dict.setdefault`, `list.pop`）では、Python 意味論上の型（`resolved_type`）は具象型（例: `int64`）だが、非テンプレート言語（Go, Java 等）の runtime 実装は動的型（`any` / `interface{}` / `Object`）を返す場合がある。

- このような Call ノードには EAST3 で `yields_dynamic: true` が付与される。
- `resolved_type` が既に動的型（`Any`, `object`, `unknown`）の場合は付与されない。
- emitter は `yields_dynamic: true` を見て型アサーション / ダウンキャストの要否を判断する。
- 生成済みターゲット言語式の文字列パターンマッチで判断してはならない。
- 対応する `semantic_tag` は `container.dict.get`, `container.dict.pop`, `container.dict.setdefault`, `container.list.pop` である。

詳細は `spec-east.md` §7 の「`yields_dynamic` について」を参照。

## 12. EAST3 型情報の利用規約

### 12.1 emitter は型推論を再実装しない

EAST3 の `resolved_type` / `decl_type` / `type_expr` は型推論パイプラインが確定した正本である。emitter がこれらの値を信頼できない場合は EAST3 側の型推論を修正すべきであり、emitter 側にワークアラウンドを追加してはならない。

禁止パターン:

```python
# NG: emitter 側で math モジュールの戻り型を再判定
if owner_name in _IMPORT_ALIAS_MAP and _IMPORT_ALIAS_MAP[owner_name].endswith("math"):
    return "double"  # ← EAST3 の resolved_type を使え

# NG: emitter 側で VarDecl の型を後続 Assign から先読み
for stmt in body[i+1:]:
    if stmt.get("target", {}).get("id") == var_name:
        real_type = stmt.get("decl_type")  # ← EAST3 の VarDecl.type を使え
```

### 12.2 resolved_type / decl_type の保証

EAST3 パイプラインは以下を保証する。emitter はこれらを前提として実装してよい。

| フィールド | 保証 |
|---|---|
| `Call.resolved_type` | stdlib 関数（`math.sin` 等）は具象型が設定される。`from pytra.std import math` スタイルの import を含む |
| `cast(T, value)` | `resolved_type` にキャスト先の型名 `T` が設定される。emitter は `resolved_type` を見てターゲット言語のキャストを生成する |
| `list[T].pop()` | 要素型 `T` が `resolved_type` に設定される（`object` ではない） |
| コンテナメソッド戻り値 | `list.append()` / `list.extend()` → `None`、`dict.get()` / `dict.pop()` → 値型。generic パラメータから導出される |
| `VarDecl.type` | 型注釈がない変数でも、代入式の型推論結果から具象型が設定される。`object` になるのは本当に動的型の場合のみ |
| `Assign.decl_type` | `declare: true` の Assign では、value 式の `resolved_type` から導出された型が設定される |
| tuple destructuring | `x, y = stack[-1]` で `stack: list[tuple[int, int]]` の場合、`x` / `y` の `resolved_type` は `int64` に解決される |
| `FunctionDef.returns` | `return_type` が設定されていれば `returns` にも同じ値が反映される。emitter は forward declaration 等で `returns` を参照してよい |
| `VarDecl.name` | 常に非空文字列。`None` や空文字の VarDecl は生成されない |
| tuple 要素の `unused` | `root, _ = s.split(".")` のように body 内で参照されない要素には `unused: true` が付与される。Assign 単体だけでなく Tuple target の個々の要素にも適用 |

注意:
- Call ノードの `func`（関数名/属性アクセスの式ノード）の `resolved_type` は callable 型であり、`unknown` のまま残り得る。emitter は `func.resolved_type` ではなく **`Call.resolved_type`（呼び出し結果の型）** を使うこと。
- `FunctionDef` の戻り値型は `return_type` が正本。`returns` は `return_type` からの同期コピーであり、両方が設定されている場合は `return_type` を優先する。

### 12.3 `Any` / `Obj` / `unknown` の型写像

EAST の `Any` / `Obj` / `unknown` は各言語の動的型に写像する:

| EAST 型 | Go | C++ | Rust | Java | C# |
|---|---|---|---|---|---|
| `Any` | `any` | `std::any` or `Object<void>` | `Box<dyn Any>` | `Object` | `object` |
| `Obj` | `any` | `Object<void>` | `Box<dyn Any>` | `Object` | `object` |
| `unknown` | `any` | `auto` | `_` (推論) | `Object` | `var` |

`unknown` が emitter に到達した場合：
- emitter は上記の動的型にフォールバックしてよい。
- ただし、`unknown` の頻出は EAST3 型推論のバグである可能性が高い。issue として報告すべきであり、emitter 側に恒久的なワークアラウンドを追加すべきではない。

### 12.4 Optional / union の型写像

EAST の `type_expr` は `OptionalType` と `UnionType` を明確に区別する（[spec-east.md](./spec-east.md) §6.4）。emitter はこの区別を認識し、ターゲット言語に適した表現を選択する。

#### 3 分類

| EAST `type_expr` | 意味 |
|---|---|
| `OptionalType(inner=T)` | `T \| None` |
| `UnionType(general)` | `T1 \| T2`（None なし） |
| `OptionalType(inner=UnionType)` | `T1 \| T2 \| None` |

#### 言語別の写像（仕様目標）

[spec-adt.md §3](./spec-adt.md) で定義する各言語の変換先を目標とする。

| EAST | C++ | Rust | Go | Java | C# | TS |
|---|---|---|---|---|---|---|
| `OptionalType(T)` | `std::optional<T>` | `Option<T>` | `*T` / nil | `T` (nullable) | `T?` | `T \| null` |
| `UnionType(general)` | `std::variant<T1, T2>` | `enum { T1(T1), T2(T2) }` | `any` | `Object` | `object` | `T1 \| T2` |
| `OptionalType(UnionType)` | 下記参照 | `Option<enum>` | `any` | `Object` | `object?` | `T1 \| T2 \| null` |

#### 現行実装との乖離

| 言語 | `UnionType(general)` の仕様目標 | 現行実装 | 備考 |
|---|---|---|---|
| C++ | `std::variant<T1, T2>` | `std::variant<T1, T2>` | 実装済み |
| TS | `T1 \| T2` | `T1 \| T2` | 実装済み（ネイティブ union） |
| Rust | `enum { T1(T1), T2(T2) }` | `PyAny` / `Box<dyn Any>` | 型安全 enum 未実装 |
| Go | `any` | `any` | 仕様どおり |
| Java | `Object` | `Object` | 仕様どおり |
| C# | `object` | `object` | 仕様どおり |

#### C++ の `OptionalType(inner=UnionType)` 写像

`T1 | T2 | None` のように union に None が混在する場合、C++ では 2 つの方式が使える:

- **monostate 方式**: `std::variant<T1, T2, std::monostate>` — フラットで型が短い。`is None` は `std::holds_alternative<std::monostate>(x)`。
- **optional+variant 方式**: `std::optional<std::variant<T1, T2>>` — EAST の型構造に対応する。`is None` は `!x.has_value()`。

現行 C++ emitter は monostate 方式を採用している。どちらの方式でも正当であり、emitter の判断に委ねる。

#### None 値の写像

| 言語 | None 値 |
|---|---|
| C++ | `std::nullopt` または `std::monostate{}` （emitter の方式に依存） |
| Rust | `None` |
| Go | `nil` |
| TS/JS | `null` |
| Java | `null` |
| C# | `null` |

#### 必須ルール

- `OptionalType` を `UnionType(options=[T, None])` のまま emit してはならない。EAST 側で正規化済みであり、emitter が再分類する必要はない。
- `UnionType(union_mode=dynamic)` を general union と同じ写像で処理してはならない。`Any` / `object` を含む union は §12.3 の動的型写像に従う。

### 12.5 数値 cast の出力判定

EAST は数値型の混合演算で常に明示的な cast ノードを挿入する（spec-east2.md §2.5）。emitter はこの cast を出力するかどうかを `mapping.json` の `implicit_promotions` テーブルで判定する。

- `implicit_promotions` に一致する cast → 出力をスキップ（ターゲット言語が暗黙変換する）
- 一致しない cast → 明示的なキャストコードを出力

```python
# CodeEmitter 基底クラスのメソッド
if self.is_implicit_cast(from_type, to_type):
    return expr  # cast なしで出力
else:
    return cast_expr(to_type, expr)  # 明示 cast を出力
```

Go / Rust は `implicit_promotions` が空なので全 cast を出力する。C++ / Java / C# は C の integer promotion に相当するペアを定義する。

**emitter が独自に cast 除去判定を書いてはならない。`mapping.json` のテーブルが正本。**

正式仕様: [spec-runtime-mapping.md §7](./spec-runtime-mapping.md)

## 13. parity check の実施

### 初回セットアップ（git clone 直後）

golden ファイルと runtime east キャッシュは git 管理していない。clone 直後の生成手順は **[開発環境セットアップ](./spec-setup.md)** を参照。

### 正本ツール

**`tools/check/runtime_parity_check_fast.py` が全言語共通の parity check 正本ツール** である。以下は全て禁止:

- 言語別の parity check スクリプト（`check_cs_fixture_emit.py` 等）
- 言語別の smoke テストスクリプト（`test_cs_emitter_smoke.py` 等）
- 言語別の fixture emit チェッカー

全て `runtime_parity_check_fast.py --targets <lang>` で代替できる。独自スクリプトを作ると結果が `.parity-results/` に蓄積されず、進捗マトリクスに反映されない。

transpile 段を toolchain2 Python API のインメモリ呼び出しで実行し、プロセス起動 + disk I/O を省略する。

```bash
# sample parity
PYTHONPATH=src:tools/check python3 tools/check/runtime_parity_check_fast.py \
  --targets <lang> --case-root sample
```

### fixture parity check

`test/fixture/source/py/` の全テストケース（146+ 件）も同じツールで全言語検証できる。`ng_*`（negative test）は自動スキップされる。`--category` でカテゴリ単位の部分実行も可能。

```bash
# fixture parity（カテゴリ指定）
PYTHONPATH=src:tools/check python3 tools/check/runtime_parity_check_fast.py \
  --targets <lang> --category oop

# fixture parity（全件）
PYTHONPATH=src:tools/check python3 tools/check/runtime_parity_check_fast.py \
  --targets <lang>
```

### stdlib parity check

`test/stdlib/source/py/` の stdlib モジュールテストも同じツールで検証できる。モジュールごとにフォルダが分かれている。

```bash
# stdlib parity（全件）
PYTHONPATH=src:tools/check python3 tools/check/runtime_parity_check_fast.py \
  --targets <lang> --case-root stdlib
```

### 3 つの parity 全てが必要

emitter 開発時は **fixture, sample, stdlib の 3 つ全て** で parity check を実行すること。最適化レベルはデフォルト（1）を使う。**`--opt-level` 等の最適化オプションは指定しないこと。**

```bash
# fixture — 言語機能の網羅テスト
PYTHONPATH=src:tools/check python3 tools/check/runtime_parity_check_fast.py \
  --targets <lang>

# sample — 実アプリケーション
PYTHONPATH=src:tools/check python3 tools/check/runtime_parity_check_fast.py \
  --targets <lang> --case-root sample

# stdlib — Python 標準ライブラリ互換モジュール
PYTHONPATH=src:tools/check python3 tools/check/runtime_parity_check_fast.py \
  --targets <lang> --case-root stdlib
```

**selfhost マトリクスの Python 行は、fixture + sample + stdlib の全てが PASS して初めて PASS になる。** 1 つでも FAIL があれば FAIL 表示。

実行結果は `.parity-results/` に自動蓄積され、`tools/gen/gen_backend_progress.py` の進捗マトリクスに反映される。

### sample benchmark

sample の実行時間は parity check の sample 実行時に自動計測され、`.parity-results/<target>_sample.json` の `elapsed_sec` に記録される。parity check 末尾で `tools/gen/gen_sample_benchmark.py` が自動実行され、`sample/README-ja.md` / `sample/README.md` の benchmark テーブルが更新される（前回生成から10分以上経過時のみ）。

### skip リストの廃止

`_LANG_UNSUPPORTED_FIXTURES` によるスキップは廃止済み。全 fixture を全言語で実行し、FAIL なら FAIL として `.parity-results/` に記録し、進捗マトリクスに反映する。スキップで問題を隠さない。

### 検証内容

`runtime_parity_check.py` は以下を自動で行う:

1. Python でケースを実行し、stdout と artifact（`sample/out/*.png`, `*.gif`, `*.txt`）を記録
2. ターゲット言語で transpile → compile → run
3. stdout の正規化比較（`elapsed_sec` 等のタイミング行は除外）
4. artifact のサイズ + CRC32 比較

### emit-only fixture（`eo_` プレフィックス）

ファイル名が `eo_` で始まる fixture は **emit-only**。Python 実行もターゲット実行も行わず、emit（transpile）が成功することだけを検証する。

用途: `@extern class` のように実体がなく Python でも実行できないが、emit できることを保証したいケース。

```
test/fixture/source/py/oop/eo_extern_opaque_basic.py  ← emit-only
test/fixture/source/py/oop/class_instance.py           ← 通常（run parity）
```

### 既存ツールとの関係

| ツール | 用途 | 正本か |
|---|---|---|
| `tools/check/runtime_parity_check.py` | 全言語 parity check（stdout + artifact） | **正本** |
| `tools/run/run_selfhost_parity.py` | selfhost バイナリによる parity check | **正本**（selfhost 検証） |
| `tools/benchmark_sample_cpp_rs.py` | C++/Rust 実行時間ベンチマーク | 別責務（parity ではない） |
| `tools/gen/regenerate_samples.py` | sample/py → sample/<lang> の再生成 | 再生成専用（実行しない） |

emitter 開発時の parity 検証は `runtime_parity_check.py` を使うこと。selfhost 検証は `run_selfhost_parity.py` を使うこと。独自スクリプトの作成は禁止。

### parity テストの完了条件

**「emit 成功」だけでは parity 完了ではない。** 以下の全てが通ることが完了条件:

1. **emit**: ターゲット言語のソースコードが生成される（エラーなし）
2. **compile**: 生成されたコードがコンパイルに通る（Go: `go build`, C++: `g++`, Rust: `rustc` 等）
3. **run**: コンパイルしたバイナリが実行できる（クラッシュしない）
4. **stdout 一致**: 実行結果の stdout が Python 実行結果と一致する（`elapsed_sec` 等は除外）
5. **artifact 一致**: 生成されたファイル（PNG/GIF/TXT）のサイズ + CRC32 が Python と一致

emit だけ成功してもプレースホルダーコード（`nil /* list comprehension */` 等）が混入している可能性がある。必ず compile + run + stdout 一致まで確認すること。

### selfhost parity

selfhost は「自分自身（toolchain2）をターゲット言語に transpile し、そのバイナリで fixture/sample を変換して parity PASS する」ことが最終目標。検証ツールは `tools/run/run_selfhost_parity.py`。

```bash
# C++ selfhost で fixture parity
python3 tools/run/run_selfhost_parity.py \
  --selfhost-lang cpp --emit-target cpp --case-root fixture

# Go selfhost で sample parity
python3 tools/run/run_selfhost_parity.py \
  --selfhost-lang go --emit-target go --case-root sample

# Python selfhost（既存 parity 結果を集約）
python3 tools/run/run_selfhost_parity.py --selfhost-lang python
```

selfhost の完了条件は以下の全てが通ること:

1. **emit**: toolchain2 全 .py がターゲット言語に emit できる
2. **build**: 生成コードがコンパイル・リンクできる
3. **golden**: emit 結果が golden と一致する（回帰テスト）
4. **fixture parity**: selfhost バイナリで fixture を変換し、Python 実行結果と stdout + artifact が一致
5. **sample parity**: 同上（sample）

golden（emit 成功の回帰テスト）だけでは selfhost 完了ではない。selfhost バイナリが実際に正しいコードを出力することを `run_selfhost_parity.py` で確認すること。

## 14. チェックリスト

新しい emitter を実装するときのチェックリスト:

- [ ] `src/toolchain2/emit/<lang>/emitter.py` に `emit_<lang>_module()` が定義されている
- [ ] import パスに `pytra.std.*` 等のハードコードがない
- [ ] `build_import_alias_map` で alias を解決している
- [ ] `emit_context.root_rel_prefix` でサブモジュールの相対パスを生成している
- [ ] `@extern` 関数の `_native` 委譲コードを生成している
- [ ] `VarDecl` / `Swap` / `discard_result` / `unused` / `mutates_self` を処理している
- [ ] immutable 引数言語は `collect_reassigned_params` + `mutable_param_name` を使っている
- [ ] 個別の `_copy_runtime` がない（`lang=` で自動コピー）
- [ ] 画像 runtime（PNG/GIF）を手書き実装していない（§6 生成コードのみ使用）
- [ ] 出力先のデフォルトが `work/tmp/<lang>`（`out/` 禁止）
- [ ] コンテナ（list/dict/set）が参照型ラッパーで保持されている（§10）
- [ ] `yields_dynamic: true` の Call ノードで型アサーションを生成している（§11）
- [ ] emitter 側に型推論のワークアラウンド（math 戻り型判定、VarDecl 先読み等）がない（§12）
- [ ] `runtime_parity_check_fast.py --targets <lang>` で fixture 検証している（§13）
- [ ] `runtime_parity_check_fast.py --targets <lang> --case-root sample` で sample 検証している（§13）
- [ ] `runtime_parity_check_fast.py --targets <lang> --case-root stdlib` で stdlib 検証している（§13）
- [ ] `check_emitter_hardcode_lint.py --lang <lang>` で emitter lint 0 件を確認している（§14.1）

### 14.1 emitter ハードコード lint

emitter が EAST3 の情報を使わずにモジュール名・runtime 関数名・クラス名等を文字列で直書きしている箇所を検出する lint。

```bash
# 自分の言語のみ（軽量、数秒）
python3 tools/check/check_emitter_hardcode_lint.py --lang <lang>

# 全言語 + runtime ソース走査（重い、1-2 分）
python3 tools/check/check_emitter_hardcode_lint.py --include-runtime
```

結果は `docs/ja/progress-preview/emitter-hardcode-lint.md` に書き出される（gitignore 対象、ディスク上のみ）。

**lint は parity check とは別に手動で実行する。** parity check は transpile + compile + run の検証に集中し、lint は含まない。lint の一括実行は `run_local_ci.py` でも行える。

10 カテゴリ:

| カテゴリ | 内容 |
|---|---|
| module name | モジュール名の文字列直書き |
| runtime symbol | runtime 関数名の直書き |
| target const | ターゲット定数の直書き |
| prefix match | `pytra.std.` 等のプレフィックス分岐 |
| class name | クラス名の直書き |
| Python syntax | Python 構文文字列の判定 |
| type_id | type_id 定数の直書き |
| skip pure py | mapping.json の skip_modules に pure Python モジュール |
| rt: type_id | runtime ソースの type_id 残骸（`--include-runtime` 時のみ） |
| rt: call_cov | mapping.json の calls と EAST3 golden の突き合わせ |

## 15. 言語別 FAQ

新しい emitter を実装する際によくある疑問と回答。

### isinstance はどう実装する？

emitter はターゲット言語のネイティブ型判定機能を使う。`PYTRA_TYPE_ID` / `pytra_isinstance` / `type_id_table` は廃止予定であり、新規 emitter では使ってはならない（[spec-adt.md](./spec-adt.md) §3, §6 参照）。

| 言語 | isinstance の実現 |
|---|---|
| C++ | `std::holds_alternative<T>(v)` (variant 移行後) |
| Rust | `if let Enum::Variant(x) = v` / `match` |
| Go | `switch v := x.(type)` |
| TS/JS | `instanceof` / `typeof` |
| C# | `x is Type t` |
| Java | `x instanceof Type t` |
| Swift | `if case let .variant(x) = v` |

isinstance のサブタイプ規則は変わらない:
- **`bool` は `int` のサブタイプではない。** `isinstance(True, int)` は Pytra では `False`（[spec-python-compat.md](./spec-python-compat.md) 参照）。
- 全プリミティブ型は leaf 型であり、相互にサブタイプ関係を持たない。

### enum / IntEnum はどう出力する？

定数群（`public static final long RED = 1;` 等）として出力する。ターゲット言語の enum 型（Java `enum`、C# `enum`、Rust `enum`）にマッピングしない。理由:
- `IntEnum` は算術演算（`Color.RED + 1`）が合法であり、言語の enum 型だと面倒になる
- EAST3 で enum は通常のクラス + 定数フィールドとして表現されている
- fixture を早く通すことを優先する

### property / super / trait はどう出力する？

ターゲット言語の素直な継承・interface に寄せる:
- `@property` → getter メソッド（Java: `getX()` / C#: プロパティ）
- `super().__init__()` → 親クラスのコンストラクタ呼び出し
- `@trait` → interface（Java: `interface` / C#: `interface` / Go: `interface`）
- `@implements` → implements / コンストラクタで interface 実装

EAST3 のノードをそのまま写像すること。emitter が独自の継承解決ロジックを持ってはならない。

### コンテナ（list/dict/set）は値型？参照型？

参照型ラッパーを既定とする（§10 参照）。言語ごとの表現:
- C++: `Object<list<T>>`
- Go: `*PyList[T]`
- Java: `PyList<T>`（参照型が既定）
- C#: `PyList<T>`（参照型が既定）
- Rust: `Rc<RefCell<Vec<T>>>`
- TS/JS: 配列はそのまま（JS の配列は参照型）

### 戻り値型の注釈がない関数はどう扱う？

`-> None` は省略可能。body に `return <値>` がなければ resolve が `None` と推論する。emitter に到達する時点では `return_type` は必ず確定している（§1.2 参照）。

### `dict.get()` や `list.pop()` の戻り値が Any/object のとき、どう cast する？

EAST3 の `yields_dynamic: true` フラグを見て型アサーションを生成するだけ（§11 参照）。emitter が「この呼び出しは Any を返すから cast が必要」と自前で判断してはならない。`yields_dynamic` が付いていなければ cast は不要。付いていれば `resolved_type` へのダウンキャストを出力する。

```java
// yields_dynamic: true, resolved_type: int64 の場合
// Java: (long) dict.get(key)
// Go: dict.Get(key).(int64)
// TS: dict.get(key) as number
```

### Python の `>>` が符号付き右シフトになる言語はどうする？

Python の `>>` は常に符号なし右シフトとして動作する（Python の整数は任意精度なので符号ビットの問題がない）。しかし JS/TS では `>>` は符号付き右シフトであり、CRC32 計算等で誤動作する。

正しい対処: **emitter 側で `>>` を符号なし右シフトに変換する。** 正本ソース（`src/pytra/`）を書き換えてはならない。

| 言語 | 対処 |
|---|---|
| JS/TS | EAST3 の `RShift` → `>>>` に変換。`>>=` → `>>>=` |
| Java | `>>` → `>>>` に変換（Java にも `>>>` がある） |
| C++/Go/Rust/C# | `>>` がそのまま動く（整数型のサイズが固定なので問題ない場合が多い。必要に応じて unsigned cast） |

実例: TS emitter が `src/pytra/utils/png.py` の CRC32 計算で `>>` → `>>>` に変換して解決した（2026-03-30）。

### コンパイラの型チェックやリンタをスキップしてよいか？

**禁止。** parity check は「生成コードが正しく動くか」の検証であり、型チェックやリンタをスキップすると不正なコードが PASS してしまう。

- `tsc --noCheck` 禁止（TS の型エラーを検出できなくなる）
- `rustc --allow` で警告を抑制するのは許可するが、エラーを抑制するのは禁止
- `g++ -fpermissive` 禁止
- `go build` のエラーを無視するのは禁止

型チェックやコンパイルでエラーが出るなら、emitter の出力を修正すること。チェックをスキップして parity PASS を稼ぐのは本末転倒。

### npm / pip / cargo 等のパッケージマネージャ依存は禁止？

**禁止。** 生成コードも runtime もビルドツールも、外部パッケージマネージャへの依存を持ってはならない。

- `npm install` / `npx` 禁止。`tsc` と `node` はシステムにグローバルインストール済みのものを使う
- `pip install` 禁止。Python 標準ライブラリと `pytra.std.*` のみ使用可
- `cargo add` 禁止。Rust 標準ライブラリのみ
- 生成コードが外部クレート / npm パッケージ / pip パッケージに依存する場合は設計が間違っている

parity check も同様。`runtime_parity_check_fast.py` は `tsc` + `node`、`g++`、`go`、`rustc` 等のシステムツールのみ使用する。

### sample の生成コードが汚い。どこまで品質を気にすべき？

`sample/<lang>/` は Pytra の展示物。§1.4 の NG パターンを全て排除し、ターゲット言語のプログラマが読んで違和感がないレベルを目指すこと。具体的には:
- `int64(0)` → `0`（不要な POD cast 除去）
- `(a) + (b)` → `a + b`（冗長な括弧除去）
- `int64{}` → `0`（デフォルトコンストラクタではなくリテラル）
