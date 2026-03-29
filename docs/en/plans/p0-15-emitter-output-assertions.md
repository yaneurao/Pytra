<a href="../../ja/plans/p0-15-emitter-output-assertions.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p0-15-emitter-output-assertions.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p0-15-emitter-output-assertions.md`

# P0-15: エミッター出力変化によるテストアサーション不一致

最終更新: 2026-03-21

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-EMITTER-OUTPUT-ASSERTIONS-01`

## 背景

toolchain 変更に伴いエミッター出力が変化し、以下のテストが旧出力を期待して失敗する。

### 変化1: for ループのタプル変数 (`test_east3_cpp_bridge.py`)
```cpp
// 旧
for (::std::tuple<int64, str> __itobj : pairs) { ... }
// 新
for (const ::std::tuple<int64, str>& __itobj_1 : pairs) { ... }
```
(`const &` 参照 + 数値サフィックスが追加された)

### 変化2: タプル要素アクセス (`test_py2cpp_codegen_issues.py`)
```cpp
// 旧
auto root = ::std::get<0>(__tuple_1);
// 新
auto root = py_at(__tuple_1, 0);
```

### 変化3: 関数引数の `rc_list_ref` ラッパー (`test_py2cpp_codegen_issues.py`)
```cpp
// 旧
pytra::utils::gif::save_gif("x.gif", 1, 1, rc_list_ref(frames), ...);
// 新
pytra::utils::gif::save_gif("x.gif", 1, 1, frames, ...);
```
(引数の順序も 4,0 → 0,4 に入れ替わっている)

### 変化4: モジュール呼び出し形式 (`test_py2cpp_codegen_issues.py`)
```cpp
// 旧
rc<list<int64>> picked = pytra::std::random::choices(xs, ws);
// 新
rc<list<int64>> picked = py_to<...>(random.choices(xs, ws));
```

### 変化5: `ValueError` が raise されなくなった (`test_east3_cpp_bridge.py`)
- `test_plain_builtin_method_call_rejected_for_self_hosted_parser` が
  `ValueError not raised` で失敗

## 対象

- `tools/unittest/emit/cpp/test_east3_cpp_bridge.py` — 3 件
- `tools/unittest/emit/cpp/test_py2cpp_codegen_issues.py` — 3 件

## 受け入れ基準

- [ ] 上記 6 件のテストがパスする

## 子タスク

- [ ] [ID: P0-EMITTER-OUTPUT-ASSERTIONS-01] テストアサーションを新しいエミッター出力に合わせて更新

## 決定ログ

- 2026-03-21: エミッター側の変更は意図的なものとして扱い、テストアサーションを新出力に追従させる方針。
  変化5（ValueError not raised）は挙動変更のため、テストを新挙動に合わせるか削除を判断する。
