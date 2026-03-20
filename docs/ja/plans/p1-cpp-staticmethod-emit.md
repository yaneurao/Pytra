# P1: C++ emitter @staticmethod 対応

最終更新: 2026-03-21

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-CPP-STATICMETHOD-EMIT-01`

## 背景

Python の `@staticmethod` デコレータが付いたメソッドが、C++ emitter では `static` キーワードなしで emit される。
呼び出し側は `ClassName::method()` 形式（C++ の static call）で生成されるが、定義側が `static` でないため
`cannot call member function without object` エラーになる。

C# emitter・Java emitter にはすでに `staticmethod` デコレータの検出と `static` キーワード付与が実装されている。

具体的な症状:
```cpp
// 現状（エラー）
rc<pytra::std::pathlib::Path> cwd();          // static でない
// ...
value = pytra::std::pathlib::Path::cwd();     // static call → エラー

// あるべき姿
static rc<pytra::std::pathlib::Path> cwd();
// ...
value = pytra::std::pathlib::Path::cwd();     // OK
```

## 対象

- `src/backends/cpp/emitter/stmt.py` — `emit_function` メソッド

## 非対象

- `@classmethod` の完全対応（`cls` パラメータの型付け等）
- 他バックエンドへの展開

## 受け入れ基準

- [ ] `@staticmethod` を持つメソッドが C++ で `static` として emit される
- [ ] `self` / `cls` パラメータが static メソッドのパラメータリストから除外される
- [ ] `virtual` / `override` / `const` が static メソッドに付かない
- [ ] `Path.cwd()` を含む最小 repro が g++ でビルドできる

## 子タスク

- [x] [ID: P1-CPP-STATICMETHOD-EMIT-01] `emit_function` で `@staticmethod`/`@classmethod` デコレータを検出し、`static` を emit するよう修正する

## 決定ログ

- 2026-03-21: C# emitter (`cs_emitter.py:1828`) の実装を参考に、`stmt.py` の `emit_function` に同様の分岐を追加する方針を決定。
- 2026-03-21: 実装完了。`emit_function` 冒頭で `decorators` を取得し `has_static_decorator` フラグを設定。`func_prefix = "static "` を付与。`skip_self` で `cls` も除外。`virtual`/`override`/`const` は `has_static_decorator` の `elif` 分岐により付かない。`test_py2cpp_codegen_issues.py` の classmethod テストを新出力に合わせて更新。123 tests passed。
