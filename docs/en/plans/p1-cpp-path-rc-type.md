<a href="../../ja/plans/p1-cpp-path-rc-type.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p1-cpp-path-rc-type.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p1-cpp-path-rc-type.md`

# P1: C++ emitter Path が rc<Path> でなく bare 型で宣言される

最終更新: 2026-03-21

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-CPP-PATH-RC-TYPE-01`

## 背景

`Path` 型の変数が `rc<pytra::std::pathlib::Path>` ではなく `pytra::std::pathlib::Path` として
宣言されるため、デフォルトコンストラクタ（`Path()`）がないことによるコンパイルエラーになる。

```cpp
// 現状（エラー）
pytra::std::pathlib::Path value;   // no matching function for 'Path::Path()'

// あるべき姿
rc<pytra::std::pathlib::Path> value;  // rc<> はデフォルトコンストラクタを持つ
```

C++ emitter は `class_storage_hint = "ref"` のクラスを `rc<T>` として emit する。
`Path` は `__init__` / `__truediv__` で `str | Path` という union type パラメータを持つため
本来 `ref` に昇格されるべきだが、`src/runtime/east/std/pathlib.east` の
`class_storage_hint` が `"value"` のままになっている。

リンカーの escape 解析（P0-ESCAPE-TO-STORAGE-HINT）で user code のクラスは `ref` に昇格されるが、
stdlib の pre-compiled EAST（`src/runtime/east/`）については昇格が効いていない可能性がある。

## 対象

- `src/runtime/east/std/pathlib.east` — `class_storage_hint` を `"ref"` に変更
- リンカーの escape 解析が stdlib EAST にも適用されるかを検証し、必要なら修正

## 非対象

- 他の stdlib クラスへの影響調査（本タスクは Path のみを対象とする）

## 受け入れ基準

- [ ] `Path` 型の変数が `rc<pytra::std::pathlib::Path>` として emit される
- [ ] `Path.cwd()` を含む最小 repro が g++ でビルドできる

## 子タスク

- [x] [ID: P1-CPP-PATH-RC-TYPE-01] `pathlib.east` の `class_storage_hint` を `"value"` から `"ref"` に修正し、g++ ビルドを検証する

## 決定ログ

- 2026-03-21: `src/runtime/east/std/pathlib.east` の `class_storage_hint` が `"value"` であることを確認。
  `Path` は union type パラメータを持つため `"ref"` であるべき。
  stdlib pre-compiled EAST はリンカーの escape 解析の対象外になっている可能性があるため、
  まず直接修正して動作確認し、根本対応（linker による昇格）は後続タスクで検討する。
- 2026-03-21: 実装完了。`pathlib.east` 行 13639 の `"class_storage_hint": "value"` を `"ref"` に変更。
