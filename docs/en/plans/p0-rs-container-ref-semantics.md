<a href="../../ja/plans/p0-rs-container-ref-semantics.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p0-rs-container-ref-semantics.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p0-rs-container-ref-semantics.md`

# P0: Rust backend コンテナ参照セマンティクス導入

最終更新: 2026-03-23

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-RS-CONTAINER-REF-*`

仕様:
- `docs/ja/spec/spec-emitter-guide.md` §10（コンテナ参照セマンティクス要件）

## 背景

現在の Rust emitter は `list[T]` → `Vec<T>`, `dict[K,V]` → `BTreeMap<K,V>` と値型で直接生成している。Rust の所有権モデルにより、関数に `Vec<T>` を渡すと所有権が move し、呼び出し元のコンテナは使用不能になる。

spec-emitter-guide §10.1 は「関数にコンテナを渡して破壊的操作を行った場合、呼び出し元のコンテナにその変更が反映されなければならない」と定めており、§10.2 で `Vec<PyAny>`（所有権 move）を禁止パターンとして明示している。

## 非対象

- `dict` / `set` の参照ラッパー化（list のみが §10.5 ヒント対象。dict/set は将来拡張）
- EAST3 側への変更（§10.2 で明示禁止: ターゲット固有の問題を IR に漏らさない）
- C++ / Zig / Go など他言語の参照ラッパー（各 backend が独立で対応済み or 対応予定）

## 受け入れ基準

1. `list[T]` がデフォルトで `Rc<RefCell<Vec<T>>>` ラッパー（`PyList<T>`）で保持される
2. `container_value_locals_v1` ヒントに含まれるローカル変数は `Vec<T>` 値型に縮退できる
3. ヒントに含まれない変数は fail-closed で参照型
4. `.append()` / `.push()` / `[idx]` / `len()` / for ループが参照ラッパー経由で動作する
5. 既存 5 pass ケース（01-04 PNG + 17 テキスト）がリグレッションしない

## 設計

### PyList\<T\> ラッパー

```rust
// py_runtime.rs に追加
use std::rc::Rc;
use std::cell::RefCell;

#[derive(Clone, Debug)]
pub struct PyList<T> {
    inner: Rc<RefCell<Vec<T>>>,
}
```

`Clone` で参照カウントのみコピー（shallow clone）。Python の代入・引数渡しセマンティクスと一致。

### API 設計

| Python | PyList メソッド |
|--------|----------------|
| `xs.append(v)` | `xs.borrow_mut().push(v)` |
| `xs[i]` | `xs.borrow()[i as usize]` |
| `xs[i] = v` | `xs.borrow_mut()[i as usize] = v` |
| `len(xs)` | `xs.borrow().len()` |
| `for x in xs` | `for x in xs.borrow().iter()...` |
| `xs.pop()` | `xs.borrow_mut().pop()` |
| `xs + ys` | 新 PyList（両方の要素をコピー）|

emitter の生成コードから直接 `.borrow()` / `.borrow_mut()` を呼ぶのは冗長なため、`PyList` にメソッドを実装して隠蔽する:

```rust
impl<T: Clone> PyList<T> {
    pub fn new() -> Self { ... }
    pub fn from_vec(v: Vec<T>) -> Self { ... }
    pub fn push(&self, val: T) { self.inner.borrow_mut().push(val); }
    pub fn get(&self, idx: i64) -> T { ... }
    pub fn set(&self, idx: i64, val: T) { ... }
    pub fn py_len(&self) -> usize { self.inner.borrow().len() }
    pub fn iter_snapshot(&self) -> Vec<T> { self.inner.borrow().clone() }
    pub fn pop(&self) -> Option<T> { self.inner.borrow_mut().pop() }
}
```

### §10.5 ヒント読み取り

```python
# emitter transpile() 内
linked_meta = meta.get("linked_program_v1", {})
ownership_hints = linked_meta.get("container_ownership_hints_v1", {})
cvl = ownership_hints.get("container_value_locals_v1", {})
# cvl["module_id::fn_name"] = {"version": "1", "locals": ["xs", "buf"]}
```

ヒントに含まれるローカル変数は `Vec<T>` で直接生成。含まれない変数は `PyList<T>` で生成。

### emitter 変更概要

| 箇所 | 現在 | 変更後 |
|------|------|--------|
| `_rust_type("list[T]")` | `Vec<T>` | `PyList<T>`（ヒントなし）/ `Vec<T>`（ヒントあり）|
| `vec![...]` リテラル | `vec![a, b, c]` | `PyList::from_vec(vec![a, b, c])` |
| `.append(v)` | `.push(v)` | `.push(v)` (PyList メソッドに委譲) |
| `xs[i]` | `xs[i as usize]` | `xs.get(i)` |
| `xs[i] = v` | `xs[i as usize] = v` | `xs.set(i, v)` |
| `len(xs)` | `xs.len()` | `xs.py_len()` |
| `for x in xs` | `xs.iter().copied()` | `xs.iter_snapshot().into_iter()` |
| `Vec::with_capacity(n)` | そのまま | `PyList::with_capacity(n)` |

## フェーズ

### フェーズ 1: runtime に PyList\<T\> 追加

`src/runtime/rs/built_in/py_runtime.rs` に `PyList<T>` 構造体 + メソッドを追加する。

### フェーズ 2: emitter の list 型マッピング変更

emitter が `list[T]` を `PyList<T>` で生成するように変更。`vec![]` → `PyList::from_vec(vec![])`, `.push()` は変更不要（PyList が同名メソッドを提供）、添字アクセスを `.get()` / `.set()` に。

### フェーズ 3: §10.5 ヒント対応

`container_value_locals_v1` を読み取り、ヒントありの変数は `Vec<T>` のまま生成。

### フェーズ 4: テスト・検証

既存 5 pass ケースのリグレッションなし + コンテナ共有パターンの検証。

## 決定ログ

- 2026-03-23: 計画書起票。spec-emitter-guide §10 違反として P0 で積む。
- 2026-03-23: S1 完了（PyList<T> runtime 実装）。S2 着手 → emitter の `list[T]` → `PyList<T>` 変更は Vec 引数との型境界が多すぎ、関数シグネチャ・slice・for ループ・添字アクセス等の全箇所で型不一致が発生。現在の sample は全て local non-escape のため §10.4 に基づき `_use_pylist=False`（値型縮退）で暫定対応。PyList 有効化は emitter のリスト添字/slice/for ループ生成を全面的に `PyList` API に移行してから。
