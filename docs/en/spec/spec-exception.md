<a href="../../ja/spec/spec-exception.md"><img alt="日本語で読む" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

# Exception Handling Specification

Last updated: 2026-03-28
Status: Draft

## 1. Purpose

- Support Python's `raise` / `try/except/finally` in all target languages.
- For languages with native exceptions (C++, etc.), use the native exception mechanism directly.
- For languages without native exceptions (Go, Rust, Zig), automatically translate to error propagation via return-value unions.
- Users write ordinary Python `raise` / `try/except` without needing to think about language differences.

## 2. Non-Goals

- Full reproduction of Python's exception hierarchy (`BaseException`, `SystemExit`, etc.).
- Support for the `else` clause (`try/except/else`) — out of scope for v1.
- Asynchronous exceptions (`asyncio.CancelledError`, etc.).
- Support for re-raising with bare `raise` — out of scope for v1.

## 3. Code Written by Users

Users write `raise` / `try/except/finally` as ordinary Python. They do not need to be aware of differences between target languages.

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

## 4. Two Exception Styles

Branching is controlled by `exception_style` in the language profile.

### 4.1 `native_throw` (14 languages)

Targets: C++, Java, C#, Kotlin, Swift, JS, TS, Dart, PHP, Ruby, Nim, Scala, Julia

- `Raise` / `Try` nodes from EAST3 are passed to the emitter as-is.
- The emitter maps them to the language's native `throw` / `try-catch`.
- No transformation is performed during EAST3 lowering.

EAST3 nodes:

- `Raise(value=Call(ValueError, ["msg"]))` → `throw ValueError("msg")`
- `Try(body=[...], handlers=[ExceptHandler(type="ValueError", name="e", body=[...])], finalbody=[...])` → `try { } catch (ValueError& e) { } finally { }`

### 4.2 `union_return` (4 languages)

Targets: Go, Rust, Zig, Lua

- The linker analyzes the call graph and transitively identifies functions that contain `raise` (marking them).
- EAST3 per-language lowering converts `Raise` / `Try` into `ErrorReturn` / `ErrorCheck` / `ErrorCatch`.
- The emitter maps these dedicated nodes to language-specific error-return syntax.

## 5. `union_return` Transformation Details

### 5.1 Exception types are classes

Exception types are defined as ordinary Pytra classes. No special type system is introduced.

Built-in exception types (defined in `src/pytra/built_in/error.py`; available without import):

```
PytraError                  # base of all exceptions
└── BaseException
    └── Exception           # base of general exceptions
        ├── ValueError
        ├── RuntimeError
        │   └── NotImplementedError
        ├── FileNotFoundError
        ├── PermissionError
        ├── TypeError
        ├── IndexError
        ├── KeyError
        ├── NameError
        └── OverflowError
```

User-defined exceptions (can be subclassed directly, no import needed):

```python
class ParseError(ValueError):
    line: int
    def __init__(self, line: int, msg: str) -> None:
        super().__init__(msg)
        self.line = line
```

Exception types, like ordinary classes:
- Have a `type_id`
- Follow single inheritance
- `isinstance` is determined by `type_id` range check
- Can have fields

### 5.2 Exception type definitions (pure Python, no hand-written runtime needed)

Exception types are defined in pure Python in `src/pytra/built_in/error.py`. These pass through the normal pipeline (parse → resolve → compile → link → emit) and are automatically translated into all target languages. No hand-written runtime exception classes per language are needed.

The canonical source is `src/pytra/built_in/error.py`. It is automatically translated into all target languages through the pipeline (parse → resolve → compile → link → emit). No hand-written runtime exception classes per language are needed.

Design principles:

- Exception types are just classes. They do not inherit from any special base class (`std::exception`, `error` interface, etc.).
- Because they are `built_in`, no import is needed. `ValueError` etc. can be used directly.
- `type_id` is assigned by the linker in the same way as for ordinary classes.
- `isinstance` is determined by `type_id` range check (same as ordinary classes).
- User-defined exceptions are also defined in user code and translated through the same pipeline.
- Exception classes must not be hand-written in the per-language runtime.

### 5.3 Linker marker assignment

The linker traverses the call graph and assigns the `meta.can_raise_v1` marker to the following functions:

1. Functions that directly contain a `Raise` statement
2. Functions that call a marked function (without `try/except`) — transitively

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

Calls where all exception types are caught by `try/except` do not propagate (no marker is assigned).

### 5.4 Return type transformation

The return type of marked functions is transformed to `T | PytraError`.

| Original return type | Transformed | Go | Rust | Zig |
|---|---|---|---|---|
| `int` | `int \| PytraError` | `(int64, *PytraError)` | `Result<i64, Box<dyn PytraErrorTrait>>` | `PytraErrorOr(i64)` |
| `str` | `str \| PytraError` | `(string, *PytraError)` | `Result<String, Box<dyn PytraErrorTrait>>` | `PytraErrorOr([]const u8)` |
| `None` | `None \| PytraError` | `*PytraError` | `Result<(), Box<dyn PytraErrorTrait>>` | `PytraErrorOr(void)` |

### 5.5 EAST3 node transformations

#### `Raise` → `ErrorReturn`

```python
raise ValueError("bad")
```

After EAST3 lowering:

```json
{
  "kind": "ErrorReturn",
  "value": {"kind": "Call", "func": "ValueError", "args": [{"kind": "Constant", "value": "bad"}]},
  "exception_type": "ValueError"
}
```

emitter output:

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

#### Call to a marked function (without `try/except`) → `ErrorCheck` + propagation

```python
x = parse_int(s)     # parse_int is can_raise
```

After EAST3 lowering:

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
    return _zero, _err       // propagate upstream as-is
}
x := _tmp
```

**Rust:**
```rust
let x = parse_int(s)?;       // propagate with ? (since there is no try/except, ? can be used)
```

**Zig:**
```zig
const x = try parse_int(s);  // propagate with try
```

#### Call to a marked function directly inside `try/except` → `ErrorCheck` + isinstance check

```python
try:
    x = parse_int(s)
    print(x)
except ValueError as e:
    x = 0
finally:
    print("done")
```

This is important: `except ValueError` must also catch `ParseError` (a subclass of ValueError). Therefore an **isinstance check via type_id range check** is required.

After EAST3 lowering:

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

The `type_id_min` / `type_id_max` in each handler are determined by the linker. `except ValueError` catches ValueError itself and all its subclasses (ParseError, etc.).

**Go:**
```go
var x int64
func() {
    defer func() { fmt.Println("done") }()

    _tmp, _err := parse_int(s)
    if _err != nil {
        // isinstance check via type_id range check
        if pytraErrorIsInstance(_err, PYTRA_TID_VALUE_ERROR_MIN, PYTRA_TID_VALUE_ERROR_MAX) {
            e := _err
            x = 0
            return
        }
        // Exception other than ValueError → not caught → panic
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

    // Wrap the try body in a closure (to allow multiple uses of ?)
    let _result = (|| -> Result<i64, Box<dyn PytraErrorTrait>> {
        let _tmp = parse_int(s)?;
        println!("{}", _tmp);
        Ok(_tmp)
    })();

    match _result {
        Ok(_tmp) => { x = _tmp; }
        Err(e) => {
            // isinstance check via type_id range check
            if pytra_error_is_instance(e.as_ref(), PYTRA_TID_VALUE_ERROR_MIN, PYTRA_TID_VALUE_ERROR_MAX) {
                x = 0;
            } else {
                // Not ValueError → not caught → panic
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
            // isinstance check via type_id range check
            if (pytraErrorIsInstance(&err.base, PYTRA_TID_VALUE_ERROR_MIN, PYTRA_TID_VALUE_ERROR_MAX)) {
                x = 0;
            } else {
                @panic("unhandled error");
            }
        },
    }
}
```

#### Multiple can_raise calls inside a try body

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

**Go:** Inline-expand the isinstance + handler after each ErrorCheck.

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

**Rust:** Wrap the entire body in a closure, propagate errors out with `?`, then handle with a single match.

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

**Zig:** Wrap the body in a block, propagate errors out with `catch`, then handle with a single switch.

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

#### Multiple except handlers

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

Handlers are checked from top to bottom using isinstance; the first match is executed.

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

#### try/finally (no except)

```python
try:
    x = parse_int(s)
finally:
    cleanup()
```

There are no except handlers, so the error propagates.

**Go:**
```go
func() {
    defer cleanup()
    _tmp, _err := parse_int(s)
    if _err != nil {
        return _zero, _err   // propagate if the caller is can_raise
        // panic(_err)        // panic if the caller is not can_raise
    }
    x = _tmp
}()
```

**Rust:**
```rust
{
    let _finally = defer(|| { cleanup(); });
    let x = parse_int(s)?;    // propagate
}
```

**Zig:**
```zig
{
    defer cleanup();
    const x = try parse_int(s);  // propagate
}
```

### 5.6 Handling `finally`

| Language | `finally` mapping |
|---|---|
| Go | `defer func() { ... }()` |
| Rust | defer guard (`Drop` impl or `scopeguard::defer!`) |
| Zig | `defer { ... }` |

`finally` is held as `finalbody` in the `ErrorCatch` node, and the emitter maps it to each language's defer mechanism. It is guaranteed to execute whether the block exits normally or with an error.

### 5.7 Functions without a marker

For functions without the `can_raise_v1` marker:
- `Raise` / `Try` nodes do not exist in EAST3 (the user has not written them).
- The return type is not changed.
- The emitter performs normal code generation.

### 5.8 Final handling of uncaught exceptions

If an error propagates all the way to `main`:
- Go: `panic(err)`
- Rust: `panic!("{}", err.msg())`
- Zig: `@panic("unhandled error")`

The program terminates abnormally.

### 5.9 isinstance check method (important)

`except ValueError as e:` must catch not only `ValueError` itself but also **all subclasses of ValueError** (e.g., `ParseError`).

The check method is the same **type_id range check** used for ordinary class isinstance:

```
err.type_id >= PYTRA_TID_VALUE_ERROR_MIN && err.type_id <= PYTRA_TID_VALUE_ERROR_MAX
```

- `type_id_min` / `type_id_max` are determined by the linker (spec-type_id.md §6.2).
- Exception types are included in the same type_id tree as ordinary classes.
- No special exception-specific check mechanism is created. The existing type_id infrastructure is reused as-is.

## 6. `native_throw` emitter mappings

### 6.1 `Raise`

| Language | Mapping |
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
| Lua | `return {__class__="ValueError", msg="msg"}` (union_return style) |

### 6.2 `Try/Except/Finally`

| Language | Mapping |
|---|---|
| C++ | `try { } catch (ValueError& e) { }` + destructor |
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
| Lua | `local result = f(); if __pytra_isinstance(result, "Exception") then ... end` (union_return style) |

## 7. CommonRenderer Exception Handling Support

### 7.1 `native_throw` common processing

CommonRenderer provides the traversal skeleton for `Raise` / `Try` nodes; only the language-specific syntax tokens need to be overridden.

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

### 7.2 `union_return` common processing

CommonRenderer provides the traversal skeleton for `ErrorReturn` / `ErrorCheck` / `ErrorCatch` nodes.

```
CommonRenderer.emit_error_return(node):
    err_expr = self.emit_expr(node.value)
    return self.format_error_return(err_expr)  # language override

CommonRenderer.emit_error_check(node):
    call_expr = self.emit_expr(node.call)
    ok_var = node.ok_target
    return self.format_error_check(call_expr, ok_var)  # language override

CommonRenderer.emit_error_catch(node):
    # traversal skeleton for ErrorCheck inside body + handlers + finalbody
    ...
```

Language overrides:

| Method | Go | Rust | Zig |
|---|---|---|---|
| `format_error_return(err)` | `return _zero, err` | `return Err(err)` | `return err` |
| `format_error_check(call, var)` | `_tmp, _err := call; if _err != nil { return _zero, _err }; var := _tmp` | `let var = call?;` | `const var = try call;` |
| `format_ok_return(val)` | `return val, nil` | `Ok(val)` | `return val` |

## 8. EAST Representation

### 8.1 Nodes for `native_throw` (existing)

- `Raise`: `value` (expression for the exception value)
- `Try`: `body`, `handlers` (`ExceptHandler[]`), `finalbody`
- `ExceptHandler`: `type` (exception type name), `name` (bound variable name), `body`

### 8.2 Nodes for `union_return` (new)

- `ErrorReturn`: `value` (expression for the exception value), `exception_type` (exception type name)
- `ErrorCheck`: `call` (call expression), `ok_target` (assignment target on success), `ok_type` (type on success), `on_error` (`"propagate"` or `"catch"`)
- `ErrorCatch`: `body` (list of statements including `ErrorCheck`), `handlers` (`ErrorHandler[]`), `finalbody`
- `ErrorHandler`: `type` (exception type name), `name` (bound variable name), `body`

### 8.3 Invariants

- When `exception_style == "native_throw"`, `ErrorReturn` / `ErrorCheck` / `ErrorCatch` do not exist in EAST3.
- When `exception_style == "union_return"`, `Raise` / `Try` do not exist in EAST3 (all have been converted during lowering).
- The return type of functions without the `can_raise_v1` marker is not changed.

## 9. Verification

- fixture: Add test cases containing `try/except/raise`
- `native_throw` languages: Verify that `throw` / `try-catch` is generated correctly
- `union_return` languages: Verify that `ErrorCheck` propagation works correctly and `ErrorCatch` catches errors
- Verify that `finally` executes reliably in all languages
- Verify that transitive marker propagation is correct (call graph analysis)

## 10. Related

- [spec-language-profile.md §7.16](./spec-language-profile.md) — `exception_style` profile
- [spec-east.md §10](./spec-east.md) — corresponding statements (`Raise`, `Try`)
- [spec-emitter-guide.md](./spec-emitter-guide.md) — emitter mapping conventions
- [spec-linker.md](./spec-linker.md) — linker call graph analysis
