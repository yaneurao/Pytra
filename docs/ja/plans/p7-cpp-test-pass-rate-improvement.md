# P7: C++ test_py2cpp_features.py テストパス率改善

最終更新: 2026-03-22

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P7-CPP-TEST-PASS-*`

## 背景

`test_py2cpp_features.py` は C++ emitter の全機能カバレッジテスト（300テスト）。
Object<T> 移行・REPO_ROOT 修正・import alias 解決等の一連の修正で 192/107 (64%) → 268/31 (89.3%) まで改善済み。

残り ~31 件の failure カテゴリ:

| カテゴリ | 件数 | 概要 |
|---------|------|------|
| Multi-file cross-module include | ~12 | user module 間の `#include` 未生成 |
| conftest 生成 C++ Object<T> 非互換 | ~5 | re, random, pathlib 等の API 不整合 |
| Any/Object<void> runtime | ~4 | None handling, boxing logic |
| `pytra::std` namespace 衝突 | ~2 | `::` prefix で部分解決済み、残りは include 欠落 |
| テスト assertion 旧API | ~3 | nes3_list_default, validate_wildcard 等 |
| その他 | ~5 | argparse, runtime_module_class_signature 等 |

## 実施済みの修正（このセッション）

1. Object receiver guard 誤検出修正 (super/class/import/unknown)
2. ForCore/AugAssign 予約語リネーム漏れ修正
3. str.h py_to_string 二重定義修正
4. テスト subprocess PYTHONPATH 追加
5. REPO_ROOT depth 修正 (parents[4]→[5])
6. import alias → namespace 正規化 (_normalize_runtime_module_name)
7. canonical_runtime_module_id bare name 正規化
8. import binding → include 変換でサブモジュール解決
9. `::` global scope qualifier で pytra::std vs std 衝突回避
10. native C++ runtime sources リンク (time.cpp, math.cpp 等)
11. conftest extern function stripping
12. conftest namespace double-close 修正
13. Object<void>::unbox メソッド追加
14. TypeInfo deleter nullptr for non-user-class
15. scope_exit double-brace 修正
16. is_locally_declared で declared_var_types チェック追加
17. AnnAssign target pre-registration
18. テスト assertion 多数更新

## 残課題

### S1: Multi-file cross-module include (~12件)

linker の `resolved_dependencies_v1` に user module 間の依存を含める。
現状は runtime module のみ。emitter の `_includes_from_resolved_dependencies` が
user module include を生成できるようにする。

### S2: conftest 生成 C++ の Object<T> 互換 (~5件)

conftest の `transpile_to_cpp` が生成する runtime .cpp/.h が Object<T> mode の
API と一致しない（re.h の Pattern::match 引数不一致、random.h の rc<list<T>> 参照等）。
conftest の生成ロジックか、emitter の runtime 型マッピングの修正が必要。

### S3: Any/Object<void> runtime (~4件)

Object<void> の None boxing/unboxing、isinstance、比較演算の runtime 実装。
any_basic, any_none, any_list_mixed, any_dict_items が SEGV または誤出力。

### S4: その他 (~10件)

- `pytra::std` namespace 衝突の残り（include 欠落が原因）
- テスト assertion の旧 API 期待値更新
- validation regression (wildcard duplicate)

## 決定ログ

### 2026-03-22: セッション記録

- 192/107 (64%) → 268/31 (89.3%) まで改善（+76テスト、+25.3%）
- 残り31件の大部分は multi-file include (12件) と conftest/runtime (10件)
- EAST 側への要望を5点整理し、#1 (bare module 正規化) と #2 (サブモジュール解決) はlinker 修正として実施済み
