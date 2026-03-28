<a href="../../en/spec/spec-exception.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# 例外処理仕様

最終更新: 2026-03-28
ステータス: ドラフト

## 1. 目的

- Python の `raise` / `try/except/finally` を全ターゲット言語でサポートする。
- ネイティブ例外がある言語（C++ 等）ではそのまま例外機構を使う。
- ネイティブ例外がない言語（Go, Rust, Zig）では、戻り値 union によるエラー伝播に自動変換する。
- ユーザーは言語の違いを意識せず、普通の Python で `raise` / `try/except` を書く。

## 2. 非目標

- Python の例外階層の完全再現（`BaseException`, `SystemExit` 等）。
- `else` 節（`try/except/else`）のサポート（v1 では対象外）。
- 非同期例外（`asyncio.CancelledError` 等）。
- 例外の再送（bare `raise`）のサポート（v1 では対象外）。

## 3. ユーザーが書くコード

ユーザーは普通の Python として `raise` / `try/except/finally` を書く。ターゲット言語による違いは意識しない。

```python
def parse_int(s: str) -> int:
    if not s.isdigit():
        raise ValueError("invalid: " + s)
    return int(s)

def process(s: str) -> str:
    x = parse_int(s)
    return str(x * 2)

if __name__ == "__main__":
    try:
        result = process("abc")
        print(result)
    except ValueError as e:
        print("error")
    finally:
        print("done")
```

## 4. 2つの例外スタイル

言語プロファイルの `exception_style` で分岐する。

### 4.1 `native_throw`（15言語）

対象: C++, Java, C#, Kotlin, Swift, JS, TS, Dart, PHP, Ruby, Nim, Scala, Julia, Lua

- EAST3 の `Raise` / `Try` ノードをそのまま emitter に渡す。
- emitter が言語ネイティブの `throw` / `try-catch` に写像する。
- EAST3 lowering での変換は行わない。

EAST3 ノード:

- `Raise(value=Call(ValueError, ["msg"]))` → `throw ValueError("msg")`
- `Try(body=[...], handlers=[ExceptHandler(type="ValueError", name="e", body=[...])], finalbody=[...])` → `try { } catch (ValueError& e) { } finally { }`

### 4.2 `union_return`（3言語）

対象: Go, Rust, Zig

- linker が call graph を解析し、`raise` を含む関数を推移的に特定（マーカー付与）。
- EAST3 言語別 lowering が `Raise` / `Try` を `ErrorReturn` / `ErrorCheck` / `ErrorCatch` に変換する。
- emitter はこれらの専用ノードを言語固有のエラー戻り値構文に写像する。

## 5. `union_return` の変換詳細

### 5.1 例外型はクラスである

例外型は Pytra の通常のクラスとして定義する。特別な型システムは導入しない。

組み込み例外型（runtime 提供）:

```
PytraError                  # 全例外の基底
├── ValueError              # 値エラー
├── RuntimeError            # 実行時エラー
├── FileNotFoundError       # ファイル未検出
└── PermissionError         # 権限エラー
```

ユーザー定義例外:

```python
class ParseError(ValueError):
    def __init__(self, line: int, msg: str) -> None:
        self.line = line
        self.msg = msg
```

例外型は通常のクラスと同じく:
- `type_id` を持つ
- 単一継承に従う
- `isinstance` は `type_id` range check で判定する
- フィールドを持てる

### 5.2 runtime の例外型定義

3言語とも runtime に `PytraError` クラス階層を用意する。

**Go:**
```go
type PytraError struct {
    TypeId int32
    Msg    string
}

type PytraValueError struct {
    PytraError
}

type PytraRuntimeError struct {
    PytraError
}

// ユーザー定義（linker が生成）
type ParseError struct {
    PytraValueError
    Line int64
}

// isinstance は type_id range check
func pytraErrorIsInstance(err *PytraError, tidMin int32, tidMax int32) bool {
    return err.TypeId >= tidMin && err.TypeId <= tidMax
}
```

**Rust:**
```rust
struct PytraError {
    type_id: i32,
    msg: String,
}

struct PytraValueError {
    base: PytraError,
}

struct PytraRuntimeError {
    base: PytraError,
}

// ユーザー定義（linker が生成）
struct ParseError {
    base: PytraValueError,
    line: i64,
}

// 全例外型は PytraErrorTrait を実装
trait PytraErrorTrait {
    fn type_id(&self) -> i32;
    fn msg(&self) -> &str;
}

// isinstance は type_id range check
fn pytra_error_is_instance(err: &dyn PytraErrorTrait, tid_min: i32, tid_max: i32) -> bool {
    let tid = err.type_id();
    tid >= tid_min && tid <= tid_max
}
```

**Zig:**
```zig
const PytraError = struct {
    type_id: i32,
    msg: []const u8,
};

const PytraValueError = struct {
    base: PytraError,
};

// ユーザー定義（linker が生成）
const ParseError = struct {
    base: PytraValueError,
    line: i64,
};

fn pytraErrorIsInstance(err: *const PytraError, tid_min: i32, tid_max: i32) bool {
    return err.type_id >= tid_min and err.type_id <= tid_max;
}
```

### 5.3 linker のマーカー付与

linker が call graph を走査し、以下の関数に `meta.can_raise_v1` マーカーを付与する。

1. `Raise` 文を直接含む関数
2. マーカー付き関数を（`try/except` なしで）呼び出している関数（推移的）

```json
{
  "kind": "FunctionDef",
  "name": "parse_int",
  "meta": {
    "can_raise_v1": {
      "schema_version": 1,
      "exception_types": ["ValueError"]
    }
  }
}
```

`try/except` で全ての例外型を catch している呼び出しは、伝播しない（マーカーは付かない）。

### 5.4 戻り値型の変換

マーカー付き関数の戻り値型を `T | PytraError` に変換する。

| 元の戻り値型 | 変換後 | Go | Rust | Zig |
|---|---|---|---|---|
| `int` | `int \| PytraError` | `(int64, *PytraError)` | `Result<i64, Box<dyn PytraErrorTrait>>` | `PytraErrorOr(i64)` |
| `str` | `str \| PytraError` | `(string, *PytraError)` | `Result<String, Box<dyn PytraErrorTrait>>` | `PytraErrorOr([]const u8)` |
| `None` | `None \| PytraError` | `*PytraError` | `Result<(), Box<dyn PytraErrorTrait>>` | `PytraErrorOr(void)` |

### 5.5 EAST3 ノード変換

#### `Raise` → `ErrorReturn`

```python
raise ValueError("bad")
```

EAST3 lowering 後:

```json
{
  "kind": "ErrorReturn",
  "value": {"kind": "Call", "func": "ValueError", "args": [{"kind": "Constant", "value": "bad"}]},
  "exception_type": "ValueError"
}
```

emitter の出力:

**Go:**
```go
return _zero, &PytraValueError{PytraError{TypeId: PYTRA_TID_VALUE_ERROR, Msg: "bad"}}
```

**Rust:**
```rust
return Err(Box::new(PytraValueError { base: PytraError { type_id: PYTRA_TID_VALUE_ERROR, msg: "bad".into() } }))
```

**Zig:**
```zig
return .{ .err = PytraValueError{ .base = .{ .type_id = PYTRA_TID_VALUE_ERROR, .msg = "bad" } } };
```

#### マーカー付き関数の呼び出し（`try/except` なし） → `ErrorCheck` + 伝播

```python
x = parse_int(s)     # parse_int は can_raise
```

EAST3 lowering 後:

```json
{
  "kind": "ErrorCheck",
  "call": {"kind": "Call", "func": "parse_int", "args": [...]},
  "ok_target": {"kind": "Name", "id": "x"},
  "ok_type": "int64",
  "on_error": "propagate"
}
```

**Go:**
```go
_tmp, _err := parse_int(s)
if _err != nil {
    return _zero, _err       // そのまま上流に伝播
}
x := _tmp
```

**Rust:**
```rust
let x = parse_int(s)?;       // ? で伝播（try/except なしなので ? が使える）
```

**Zig:**
```zig
const x = try parse_int(s);  // try で伝播
```

#### `try/except` 直下のマーカー付き関数呼び出し → `ErrorCheck` + isinstance 判定

```python
try:
    x = parse_int(s)
    print(x)
except ValueError as e:
    x = 0
finally:
    print("done")
```

ここが重要: `except ValueError` は `ParseError`（ValueError の派生）も catch しなければならない。そのため **type_id range check による isinstance 判定** が必須。

EAST3 lowering 後:

```json
{
  "kind": "ErrorCatch",
  "body": [
    {
      "kind": "ErrorCheck",
      "call": {"kind": "Call", "func": "parse_int", "args": [...]},
      "ok_target": {"kind": "Name", "id": "x"},
      "ok_type": "int64",
      "on_error": "catch"
    },
    {"kind": "Expr", "value": {"kind": "Call", "func": "print", "args": [{"kind": "Name", "id": "x"}]}}
  ],
  "handlers": [
    {
      "type": "ValueError",
      "type_id_min": "PYTRA_TID_VALUE_ERROR_MIN",
      "type_id_max": "PYTRA_TID_VALUE_ERROR_MAX",
      "name": "e",
      "body": [{"kind": "Assign", "target": {"kind": "Name", "id": "x"}, "value": {"kind": "Constant", "value": 0}}]
    }
  ],
  "finalbody": [
    {"kind": "Expr", "value": {"kind": "Call", "func": "print", "args": [{"kind": "Constant", "value": "done"}]}}
  ]
}
```

handler の `type_id_min` / `type_id_max` は linker が確定する。`except ValueError` は ValueError 自身と全派生クラス（ParseError 等）を catch する。

**Go:**
```go
var x int64
func() {
    defer func() { fmt.Println("done") }()

    _tmp, _err := parse_int(s)
    if _err != nil {
        // type_id range check で isinstance 判定
        if pytraErrorIsInstance(_err, PYTRA_TID_VALUE_ERROR_MIN, PYTRA_TID_VALUE_ERROR_MAX) {
            e := _err
            x = 0
            return
        }
        // ValueError 以外の例外 → 未 catch → panic
        panic(_err)
    }
    x = _tmp
    fmt.Println(x)
}()
```

**Rust:**
```rust
let x: i64;
{
    let _finally = defer(|| { println!("done"); });

    // try body をクロージャに包む（複数の ? を使うため）
    let _result = (|| -> Result<i64, Box<dyn PytraErrorTrait>> {
        let _tmp = parse_int(s)?;
        println!("{}", _tmp);
        Ok(_tmp)
    })();

    match _result {
        Ok(_tmp) => { x = _tmp; }
        Err(e) => {
            // type_id range check で isinstance 判定
            if pytra_error_is_instance(e.as_ref(), PYTRA_TID_VALUE_ERROR_MIN, PYTRA_TID_VALUE_ERROR_MAX) {
                x = 0;
            } else {
                // ValueError 以外 → 未 catch → panic
                panic!("{}", e.msg());
            }
        }
    }
}
```

**Zig:**
```zig
var x: i64 = undefined;
{
    defer std.debug.print("done\n", .{});

    const _result = blk: {
        const _tmp = parse_int(s) catch |err| break :blk err;
        std.debug.print("{}\n", .{_tmp});
        break :blk .{ .ok = _tmp };
    };

    switch (_result) {
        .ok => |_tmp| { x = _tmp; },
        .err => |err| {
            // type_id range check で isinstance 判定
            if (pytraErrorIsInstance(&err.base, PYTRA_TID_VALUE_ERROR_MIN, PYTRA_TID_VALUE_ERROR_MAX)) {
                x = 0;
            } else {
                @panic("unhandled error");
            }
        },
    }
}
```

#### try body 内に複数の can_raise 呼び出しがある場合

```python
try:
    x = parse_int(a)
    y = parse_int(b)
    print(x + y)
except ValueError as e:
    print("error")
finally:
    print("done")
```

**Go:** 各 ErrorCheck の直後に isinstance + handler を inline 展開する。

```go
func() {
    defer func() { fmt.Println("done") }()

    _tmp1, _err1 := parse_int(a)
    if _err1 != nil {
        if pytraErrorIsInstance(_err1, PYTRA_TID_VALUE_ERROR_MIN, PYTRA_TID_VALUE_ERROR_MAX) {
            fmt.Println("error")
            return
        }
        panic(_err1)
    }
    x := _tmp1

    _tmp2, _err2 := parse_int(b)
    if _err2 != nil {
        if pytraErrorIsInstance(_err2, PYTRA_TID_VALUE_ERROR_MIN, PYTRA_TID_VALUE_ERROR_MAX) {
            fmt.Println("error")
            return
        }
        panic(_err2)
    }
    y := _tmp2

    fmt.Println(x + y)
}()
```

**Rust:** body 全体をクロージャに包み、`?` でエラーを外に出して一括 match。

```rust
{
    let _finally = defer(|| { println!("done"); });
    let _result = (|| -> Result<(), Box<dyn PytraErrorTrait>> {
        let x = parse_int(a)?;
        let y = parse_int(b)?;
        println!("{}", x + y);
        Ok(())
    })();
    match _result {
        Ok(()) => {}
        Err(e) => {
            if pytra_error_is_instance(e.as_ref(), PYTRA_TID_VALUE_ERROR_MIN, PYTRA_TID_VALUE_ERROR_MAX) {
                println!("error");
            } else {
                panic!("{}", e.msg());
            }
        }
    }
}
```

**Zig:** body をブロックに包み、`catch` でエラーを外に出して一括 switch。

```zig
{
    defer std.debug.print("done\n", .{});
    const _result = blk: {
        const x = parse_int(a) catch |err| break :blk .{ .err = err };
        const y = parse_int(b) catch |err| break :blk .{ .err = err };
        std.debug.print("{}\n", .{x + y});
        break :blk .{ .ok = {} };
    };
    switch (_result) {
        .ok => {},
        .err => |err| {
            if (pytraErrorIsInstance(&err.base, PYTRA_TID_VALUE_ERROR_MIN, PYTRA_TID_VALUE_ERROR_MAX)) {
                std.debug.print("error\n", .{});
            } else {
                @panic("unhandled error");
            }
        },
    }
}
```

#### 複数の except handler がある場合

```python
try:
    data = read_file(path)
except FileNotFoundError as e:
    data = ""
except PermissionError as e:
    raise RuntimeError("no access")
finally:
    cleanup()
```

handler は上から順に isinstance で判定し、最初に一致したものを実行する。

**Go:**
```go
func() {
    defer cleanup()
    _tmp, _err := read_file(path)
    if _err != nil {
        if pytraErrorIsInstance(_err, PYTRA_TID_FILE_NOT_FOUND_MIN, PYTRA_TID_FILE_NOT_FOUND_MAX) {
            data = ""
            return
        }
        if pytraErrorIsInstance(_err, PYTRA_TID_PERMISSION_ERROR_MIN, PYTRA_TID_PERMISSION_ERROR_MAX) {
            panic(&PytraRuntimeError{PytraError{TypeId: PYTRA_TID_RUNTIME_ERROR, Msg: "no access"}})
        }
        panic(_err)
    }
    data = _tmp
}()
```

**Rust:**
```rust
{
    let _finally = defer(|| { cleanup(); });
    match read_file(path) {
        Ok(_tmp) => { data = _tmp; }
        Err(e) => {
            if pytra_error_is_instance(e.as_ref(), PYTRA_TID_FILE_NOT_FOUND_MIN, PYTRA_TID_FILE_NOT_FOUND_MAX) {
                data = String::new();
            } else if pytra_error_is_instance(e.as_ref(), PYTRA_TID_PERMISSION_ERROR_MIN, PYTRA_TID_PERMISSION_ERROR_MAX) {
                panic!("RuntimeError: no access");
            } else {
                panic!("{}", e.msg());
            }
        }
    }
}
```

**Zig:**
```zig
{
    defer cleanup();
    const _result = read_file(path);
    switch (_result) {
        .ok => |_tmp| { data = _tmp; },
        .err => |err| {
            if (pytraErrorIsInstance(&err.base, PYTRA_TID_FILE_NOT_FOUND_MIN, PYTRA_TID_FILE_NOT_FOUND_MAX)) {
                data = "";
            } else if (pytraErrorIsInstance(&err.base, PYTRA_TID_PERMISSION_ERROR_MIN, PYTRA_TID_PERMISSION_ERROR_MAX)) {
                @panic("RuntimeError: no access");
            } else {
                @panic("unhandled error");
            }
        },
    }
}
```

#### try/finally（except なし）

```python
try:
    x = parse_int(s)
finally:
    cleanup()
```

except handler がないので、エラーは伝播する。

**Go:**
```go
func() {
    defer cleanup()
    _tmp, _err := parse_int(s)
    if _err != nil {
        return _zero, _err   // 呼び出し元が can_raise なら伝播
        // panic(_err)        // 呼び出し元が can_raise でなければ panic
    }
    x = _tmp
}()
```

**Rust:**
```rust
{
    let _finally = defer(|| { cleanup(); });
    let x = parse_int(s)?;    // 伝播
}
```

**Zig:**
```zig
{
    defer cleanup();
    const x = try parse_int(s);  // 伝播
}
```

### 5.6 `finally` の扱い

| 言語 | `finally` の写像 |
|---|---|
| Go | `defer func() { ... }()` |
| Rust | `defer` ガード（`Drop` impl または `scopeguard::defer!`） |
| Zig | `defer { ... }` |

`finally` は `ErrorCatch` ノードの `finalbody` として保持し、emitter が各言語の defer 機構に写像する。正常終了でもエラー終了でも必ず実行される。

### 5.7 マーカーが付かない関数

`can_raise_v1` マーカーがない関数では:
- `Raise` / `Try` ノードは EAST3 に存在しない（ユーザーが書いていない）。
- 戻り値型は変更されない。
- emitter は通常のコード生成を行う。

### 5.8 catch されない例外の最終処理

エラーが `main` まで伝播した場合:
- Go: `panic(err)`
- Rust: `panic!("{}", err.msg())`
- Zig: `@panic("unhandled error")`

プログラムは異常終了する。

### 5.9 isinstance の判定方式（重要）

`except ValueError as e:` は `ValueError` 自身だけでなく、**ValueError の全派生クラス**（`ParseError` 等）も catch する。

判定方式は通常のクラス isinstance と同じ **type_id range check**:

```
err.type_id >= PYTRA_TID_VALUE_ERROR_MIN && err.type_id <= PYTRA_TID_VALUE_ERROR_MAX
```

- `type_id_min` / `type_id_max` は linker が確定する（spec-type_id.md §6.2）。
- 例外型も通常のクラスと同じ type_id ツリーに含まれる。
- 特別な例外用判定機構は作らない。既存の type_id 基盤をそのまま流用する。

## 6. `native_throw` の emitter 写像

### 6.1 `Raise`

| 言語 | 写像 |
|---|---|
| C++ | `throw ValueError("msg")` |
| Java | `throw new ValueError("msg")` |
| C# | `throw new ValueError("msg")` |
| Kotlin | `throw ValueError("msg")` |
| Swift | `throw ValueError.init("msg")` |
| JS/TS | `throw new ValueError("msg")` |
| Dart | `throw ValueError("msg")` |
| PHP | `throw new ValueError("msg")` |
| Ruby | `raise ValueError.new("msg")` |
| Nim | `raise newException(ValueError, "msg")` |
| Scala | `throw new ValueError("msg")` |
| Julia | `throw(ValueError("msg"))` |
| Lua | `error({type="ValueError", msg="msg"})` |

### 6.2 `Try/Except/Finally`

| 言語 | 写像 |
|---|---|
| C++ | `try { } catch (ValueError& e) { }` + デストラクタ |
| Java | `try { } catch (ValueError e) { } finally { }` |
| C# | `try { } catch (ValueError e) { } finally { }` |
| Kotlin | `try { } catch (e: ValueError) { } finally { }` |
| Swift | `do { try ... } catch let e as ValueError { }` + `defer` |
| JS/TS | `try { } catch (e) { if (e instanceof ValueError) { } } finally { }` |
| Dart | `try { } on ValueError catch (e) { } finally { }` |
| PHP | `try { } catch (ValueError $e) { } finally { }` |
| Ruby | `begin ... rescue ValueError => e ... ensure ... end` |
| Nim | `try: ... except ValueError as e: ... finally: ...` |
| Scala | `try { } catch { case e: ValueError => } finally { }` |
| Julia | `try ... catch e; if e isa ValueError ... end; finally ... end` |
| Lua | `local ok, err = pcall(function() ... end); if not ok then ... end` |

## 7. CommonRenderer の例外処理サポート

### 7.1 `native_throw` 共通処理

CommonRenderer が `Raise` / `Try` ノードの走査骨格を提供し、言語固有の構文トークンだけ override する。

```
CommonRenderer.emit_raise(node):
    expr = self.emit_expr(node.value)
    return self.profile.throw_keyword + " " + expr + self.stmt_end()

CommonRenderer.emit_try(node):
    emit "try" + block_open
    emit body
    for handler in handlers:
        emit catch_clause(handler.type, handler.name)
        emit handler.body
    if finalbody:
        emit finally_clause
        emit finalbody
```

### 7.2 `union_return` 共通処理

CommonRenderer が `ErrorReturn` / `ErrorCheck` / `ErrorCatch` ノードの走査骨格を提供する。

```
CommonRenderer.emit_error_return(node):
    err_expr = self.emit_expr(node.value)
    return self.format_error_return(err_expr)  # 言語 override

CommonRenderer.emit_error_check(node):
    call_expr = self.emit_expr(node.call)
    ok_var = node.ok_target
    return self.format_error_check(call_expr, ok_var)  # 言語 override

CommonRenderer.emit_error_catch(node):
    # body 内の ErrorCheck + handlers + finalbody の走査骨格
    ...
```

言語 override:

| メソッド | Go | Rust | Zig |
|---|---|---|---|
| `format_error_return(err)` | `return _zero, err` | `return Err(err)` | `return err` |
| `format_error_check(call, var)` | `_tmp, _err := call; if _err != nil { return _zero, _err }; var := _tmp` | `let var = call?;` | `const var = try call;` |
| `format_ok_return(val)` | `return val, nil` | `Ok(val)` | `return val` |

## 8. EAST 表現

### 8.1 `native_throw` 用ノード（既存）

- `Raise`: `value`（例外値の式）
- `Try`: `body`, `handlers`（`ExceptHandler[]`）, `finalbody`
- `ExceptHandler`: `type`（例外型名）, `name`（束縛変数名）, `body`

### 8.2 `union_return` 用ノード（新規）

- `ErrorReturn`: `value`（例外値の式）, `exception_type`（例外型名）
- `ErrorCheck`: `call`（呼び出し式）, `ok_target`（成功時の代入先）, `ok_type`（成功時の型）, `on_error`（`"propagate"` or `"catch"`）
- `ErrorCatch`: `body`（`ErrorCheck` を含む文列）, `handlers`（`ErrorHandler[]`）, `finalbody`
- `ErrorHandler`: `type`（例外型名）, `name`（束縛変数名）, `body`

### 8.3 不変条件

- `exception_style == "native_throw"` の場合、`ErrorReturn` / `ErrorCheck` / `ErrorCatch` は EAST3 に存在しない。
- `exception_style == "union_return"` の場合、`Raise` / `Try` は EAST3 に存在しない（lowering で全て変換済み）。
- `can_raise_v1` マーカーがない関数の戻り値型は変更されない。

## 9. 検証

- fixture: `try/except/raise` を含むテストケースを追加
- `native_throw` 言語: `throw` / `try-catch` が正しく生成されること
- `union_return` 言語: `ErrorCheck` の伝播が正しく動作し、`ErrorCatch` で catch されること
- `finally` が全言語で確実に実行されること
- マーカーの推移的伝播が正しいこと（call graph 解析）

## 10. 関連

- [spec-language-profile.md §7.16](./spec-language-profile.md) — `exception_style` プロファイル
- [spec-east.md §10](./spec-east.md) — 対応文（`Raise`, `Try`）
- [spec-emitter-guide.md](./spec-emitter-guide.md) — emitter の写像規約
- [spec-linker.md](./spec-linker.md) — linker の call graph 解析
