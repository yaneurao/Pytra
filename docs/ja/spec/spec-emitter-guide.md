# Emitter 実装ガイドライン

このドキュメントは、新しいターゲット言語の backend（emitter）を実装するとき、および既存 emitter をメンテナンスするときに従う規約です。

## 1. 原則

- emitter は **EAST3 の情報だけ** を使ってコードを生成する。モジュール名やパスのハードコード禁止。
- `pytra.std.*` / `pytra.utils.*` / `pytra.built_in.*` 等の具体的なモジュール ID を emitter にハードコードしてはならない。
- import パス解決、@extern 委譲、runtime コピーは `loader.py` の共通関数に委譲する。
- emitter 固有のロジックは「EAST3 ノード → ターゲット言語の構文」の変換のみに限定する。

## 2. エントリポイント（`*.py`）の標準形

全 non-C++ emitter のエントリポイントは以下の形に統一する:

```python
#!/usr/bin/env python3
"""<Lang> backend: manifest.json → <Lang> multi-file output."""

from __future__ import annotations
import sys

from toolchain.emit.<lang>.emitter import transpile_to_<lang>
from toolchain.emit.loader import emit_all_modules


def main() -> int:
    argv = sys.argv[1:]
    if len(argv) == 0 or argv[0] in ("-h", "--help"):
        print("usage: toolchain.emit.<lang> MANIFEST.json --output-dir DIR")
        return 0

    input_path = ""
    output_dir = "work/tmp/<lang>"
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok == "--output-dir" and i + 1 < len(argv):
            output_dir = argv[i + 1]
            i += 2
            continue
        if not tok.startswith("-") and input_path == "":
            input_path = tok
        i += 1

    if input_path == "":
        print("error: input manifest.json is required", file=sys.stderr)
        return 1

    return emit_all_modules(input_path, output_dir, ".<ext>", transpile_to_<lang>, lang="<lang>")


if __name__ == "__main__":
    sys.exit(main())
```

### is_submodule / emit_main が必要な場合

`transpile_fn` のシグネチャは `(dict) -> str` で固定。追加パラメータが必要な場合はラッパーで対処:

```python
def _transpile_<lang>(east_doc: dict) -> str:
    meta = east_doc.get("meta", {})
    emit_ctx = meta.get("emit_context", {}) if isinstance(meta, dict) else {}
    is_entry = emit_ctx.get("is_entry", False) if isinstance(emit_ctx, dict) else False
    return transpile_to_<lang>(east_doc, is_submodule=not is_entry)
```

`emit_context` から `is_entry` / `module_id` / `root_rel_prefix` を取得する。ハードコード不可。

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

### import alias の解決

`from pytra.std import os_path as path` のような alias は `build_import_alias_map` で解決:

```python
from toolchain.emit.common.emitter.code_emitter import build_import_alias_map

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

EAST3 では `AnnAssign` の value が `Call(func=Name("extern"), args=[...])` として表現される。

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
# AnnAssign/Assign の value が extern() 呼び出しかチェック
value = stmt.get("value", {})
if isinstance(value, dict) and value.get("kind") == "Call":
    func = value.get("func", {})
    if isinstance(func, dict) and func.get("id") == "extern":
        # extern() 変数 → __native への委譲を生成
        # value.args[0] は Python フォールバック（ターゲット言語では無視）
```

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
- **Java のみ例外**: `Main.java`（Java 言語仕様でクラス名 = ファイル名が必須）
- **Scala のみ例外**: 全モジュールを単一ファイルにマージ

これら以外のエントリファイル名の変更は禁止。

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

## 7. 共通ユーティリティ（`code_emitter.py` スタンドアロン関数）

`CodeEmitter` を継承しない emitter でも使える関数:

| 関数 | 用途 |
|---|---|
| `build_import_alias_map(meta)` | import alias → module_id マップ構築 |
| `collect_reassigned_params(func_def)` | 再代入される引数の検出（immutable 引数言語用） |
| `mutable_param_name(name)` | 引数リネーム（`data` → `data_`） |

```python
from toolchain.emit.common.emitter.code_emitter import (
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
- `is_entry` は main 関数の emit や emit_main フラグに使う
- `module_id` は @extern 委譲先の native パス解決に使う

## 9. EAST3 ノードで emitter が対応すべきもの

| ノード | 説明 | emitter の責務 |
|---|---|---|
| `VarDecl` | hoist された変数宣言 | 型付き変数宣言を生成 |
| `Swap` | `a, b = b, a` パターン | swap コードを生成 |
| `discard_result: true` | main_guard_body の戻り値抑制 | 戻り値を捨てるコードを生成 |
| `unused: true` | 未使用変数 | 警告抑制コード or 宣言省略 |
| `decorators: ["extern"]` | @extern 関数 | `_native` への委譲コードを生成 |
| `decorators: ["property"]` | @property メソッド | getter アクセスに変換 |
| `mutates_self: true/false` | メソッドの self mutation | mutable/immutable self を選択 |

## 10. チェックリスト

新しい emitter を実装するときのチェックリスト:

- [ ] エントリポイント `src/toolchain/emit/<lang>.py` が `emit_all_modules(lang="<lang>")` を使う
- [ ] `transpile_fn` のシグネチャが `(dict) -> str`
- [ ] import パスに `pytra.std.*` 等のハードコードがない
- [ ] `build_import_alias_map` で alias を解決している
- [ ] `emit_context.root_rel_prefix` でサブモジュールの相対パスを生成している
- [ ] `@extern` 関数の `_native` 委譲コードを生成している
- [ ] `VarDecl` / `Swap` / `discard_result` / `unused` / `mutates_self` を処理している
- [ ] immutable 引数言語は `collect_reassigned_params` + `mutable_param_name` を使っている
- [ ] 個別の `_copy_runtime` がない（`lang=` で自動コピー）
- [ ] 出力先のデフォルトが `work/tmp/<lang>`（`out/` 禁止）
