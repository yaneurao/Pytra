<a href="../../en/spec/spec-runtime-decorator.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# @runtime / @extern デコレータ仕様

最終更新: 2026-03-29
ステータス: ドラフト

## 1. 目的

- `include/` 配下の型宣言ファイルで、クラスや関数が「どこに実装があるか」を宣言する仕組みを提供する。
- `@runtime` と `@extern` の2つで、Pytra 内部の runtime 実装と外部ライブラリの実装を区別する。
- 旧デコレータ（`@extern_method`, `@extern_fn`, `@extern_class`, `@abi`）を廃止し、統一する。

## 2. 2つのデコレータ

| デコレータ | 意味 | rc | type_id | 用途 |
|---|---|---|---|---|
| `@runtime("namespace")` | Pytra runtime に実装がある | あり | あり | built_in / std のクラスと関数 |
| `@extern` | 外部（Pytra の管轄外）に実装がある | なし | なし | SDL3 等の外部ライブラリ |

### 2.1 対象

両方とも class と def に使える。

| 対象 | `@extern` | `@runtime("ns")` |
|---|---|---|
| class | opaque 型（rc なし、boxing なし） | Pytra 組み込みクラス（rc あり） |
| def | 外部関数 | Pytra runtime 関数 |

## 3. `@runtime` の仕様

### 3.1 クラス宣言

```python
@runtime("pytra.core")
class list(Generic[T]):
    def append(self, x: T) -> None: ...
    def extend(self, x: list[T]) -> None: ...
    def pop(self, index: int = -1) -> T: ...
    def sort(self) -> None: ...
    def clear(self) -> None: ...
```

- `@runtime("pytra.core")` の引数は namespace。class名と合わせて module が決まる（`pytra.core.list`）
- クラス内のメソッドは全て runtime 実装。個別にデコレータを付ける必要はない
- メソッドの symbol は `class名.メソッド名` から自動導出（`list.append`）
- tag は `stdlib.method.メソッド名` から自動導出（`stdlib.method.append`）
- runtime 関数名の変換（`list.append` → `py_list_append_mut` 等）は mapping.json の責務
- 本体は `...`（シグネチャのみ）。実装は `src/pytra/` の pure Python 本体、または各言語の runtime

### 3.2 関数宣言

```python
@runtime("pytra.built_in.sequence")
def py_range(start: int, stop: int, step: int) -> list[int]: ...
```

- namespace + 関数名で module が決まる（`pytra.built_in.sequence.py_range`）
- symbol は関数名から自動導出（`py_range`）
- 本体は `...`（シグネチャのみ）

### 3.3 自動導出ルール

`@runtime("pytra.core")` の `class list` の `extend` メソッドの場合:

| 項目 | 導出元 | 結果 |
|---|---|---|
| module | namespace + class名 | `pytra.core.list` |
| symbol | class名 + メソッド名 | `list.extend` |
| tag | `stdlib.method.` + メソッド名 | `stdlib.method.extend` |

`@runtime("pytra.built_in.sequence")` の `def py_range` の場合:

| 項目 | 導出元 | 結果 |
|---|---|---|
| module | namespace | `pytra.built_in.sequence` |
| symbol | 関数名 | `py_range` |
| tag | `stdlib.fn.` + 関数名 | `stdlib.fn.py_range` |

### 3.4 引数の渡し方

- 全引数は rc のまま渡す。arg mode 指定は不要
- runtime ヘルパーは全て rc 前提の1パターンだけ実装する
- エイリアス問題（`a.extend(a)`）があるため、rc を剥がして渡すのは禁止
- 詳細は plans/p6-extern-method-redesign.md の「rc と arg mode の設計議論」を参照

### 3.5 型の扱い

- POD 型（`int`, `float`, `bool`, `str`）の引数は値型のまま
- コンテナ型（`list[T]`, `dict[K,V]`, `set[T]`）とクラスインスタンスは rc で包まれる
- この判定は EAST3 の `resolved_type` から機械的に決まる。emitter の型写像テーブルによる

## 4. `@extern` の仕様

### 4.1 opaque クラス

```python
@extern
class Window:
    def set_title(self, title: str) -> None: ...
    def close(self) -> None: ...
```

- rc で包まない（opaque handle）
- boxing しない
- type_id を持たない
- isinstance の対象外
- 詳細は spec-opaque-type.md を参照

### 4.2 外部関数

```python
@extern
def sdl_init(flags: int) -> int: ...

@extern
def sdl_create_window(title: str, w: int, h: int, flags: int) -> int: ...
```

- ターゲット言語側に実装がある関数
- Pytra はシグネチャだけ知っている
- emitter は委譲コード（ネイティブ関数への薄いラッパー）を生成する

### 4.3 `@extern` クラス内のメソッドに個別 symbol を指定する

大半のケースでは不要だが、外部ライブラリの API 名が Pytra のメソッド名と異なる場合:

```python
@extern
class Window:
    @extern(symbol="SDL_SetWindowTitle")
    def set_title(self, title: str) -> None: ...
```

## 5. `include/` ファイルの構成

```
src/include/py/pytra/
  built_in/
    containers.py     — @runtime("pytra.core") class list, dict, set, tuple
    builtins.py       — @runtime("pytra.built_in.*") def len, print, str, ...
    sequence.py       — @runtime("pytra.built_in.sequence") def py_range, ...
  std/
    pathlib.py        — @runtime("pytra.std.pathlib") class Path
    math.py           — @runtime("pytra.std.math") def sqrt, sin, cos, ...
    time.py           — @runtime("pytra.std.time") def perf_counter
    json.py           — @runtime("pytra.std.json") def loads, dumps
    sys.py            — @runtime("pytra.std.sys") ...
    os.py             — @runtime("pytra.std.os") ...
    glob.py           — @runtime("pytra.std.glob") ...
```

各ファイルはシグネチャ（型注釈）のみを持ち、実装は以下にある:
- `src/pytra/built_in/` — pure Python 実装（パイプラインで変換）
- `src/pytra/std/` — pure Python 実装（パイプラインで変換）
- `src/runtime/<lang>/` — 言語固有の native 実装（一部のみ）

## 6. 廃止されたデコレータ

| 旧 | 新 | 備考 |
|---|---|---|
| `@extern_method(module=..., symbol=..., tag=...)` | `@runtime` クラス内のメソッド（自動導出） | P0-RUNTIME-DECORATOR で廃止 |
| `@extern_fn(module=..., symbol=..., tag=...)` | `@runtime("ns") def ...` または `@extern def ...` | 同上 |
| `@extern_class(module=..., symbol=..., tag=...)` | `@runtime("ns") class ...` または `@extern class ...` | 同上 |
| `@abi(args={...})` | 廃止（arg mode 不要） | 同上 |

parser は旧デコレータを受理した場合 fail-closed で停止する。

## 7. EAST 表現

### @runtime class

```json
{
  "kind": "ClassDef",
  "name": "list",
  "decorators": ["runtime"],
  "meta": {
    "extern_v2": {
      "schema_version": 2,
      "module_id": "pytra.core.list",
      "class_symbol": "list",
      "methods": {
        "append": {"symbol": "list.append", "tag": "stdlib.method.append"},
        "extend": {"symbol": "list.extend", "tag": "stdlib.method.extend"}
      }
    }
  }
}
```

### @extern class

```json
{
  "kind": "ClassDef",
  "name": "Window",
  "decorators": ["extern"],
  "meta": {
    "opaque_v1": {"schema_version": 1}
  }
}
```

### @runtime def

```json
{
  "kind": "FunctionDef",
  "name": "py_range",
  "decorators": ["runtime"],
  "meta": {
    "extern_v2": {
      "schema_version": 2,
      "module_id": "pytra.built_in.sequence",
      "symbol": "py_range",
      "tag": "stdlib.fn.py_range"
    }
  }
}
```

### @extern def

```json
{
  "kind": "FunctionDef",
  "name": "sdl_init",
  "decorators": ["extern"],
  "meta": {
    "extern_v2": {
      "schema_version": 2,
      "symbol": "sdl_init"
    }
  }
}
```

## 8. 関連

- [spec-opaque-type.md](./spec-opaque-type.md) — opaque 型（`@extern class`）の詳細
- [spec-emitter-guide.md](./spec-emitter-guide.md) — emitter の写像規約
- [spec-runtime-mapping.md](./spec-runtime-mapping.md) — mapping.json
- [plans/p6-extern-method-redesign.md](../plans/p6-extern-method-redesign.md) — 設計議論の経緯
