<a href="../../en/plans/p0-cpp-repo-root-and-import-alias-fix.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: REPO_ROOT 修正 + import alias 解決 + conftest extern 関数修正

最終更新: 2026-03-22

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-REPO-ROOT-IMPORT-FIX-*`

## 背景

C++ emitter の `REPO_ROOT`（`src/toolchain/emit/cpp/emitter/module.py:26`）が
ディレクトリ再構成（`backends/` → `toolchain/emit/`）後に1階層ずれている。

```python
# 現在（誤り）
REPO_ROOT = Path(__file__).resolve().parents[4]  # → /workspace/Pytra/src

# 正しい値
REPO_ROOT = Path(__file__).resolve().parents[5]  # → /workspace/Pytra
```

この誤りにより以下の連鎖的な問題が発生している:

1. `_normalize_runtime_module_name("math")` が `"pytra.std.math"` に正規化されない
   - `RUNTIME_STD_SOURCE_ROOT` が `src/src/pytra/std`（二重 `src`）で、ファイル存在チェックが失敗するため
2. import alias（`from math import sqrt as msqrt`）が C++ namespace に解決されず、`msqrt(9.0)` のまま出力される
3. `import math as m` → `m.sqrt(9.0)` が `pytra::std::math::sqrt(9.0)` に解決されない

## 問題の依存関係

```
REPO_ROOT 修正 (parents[4] → parents[5])
  ├─ import alias 解決が正しく動く ✓
  ├─ include path 生成が変わる
  │   └─ #include "utils/assertions.h" のような path が生成される
  │       └─ PYTRA_GENERATED_CPP_DIR が -I に必要
  │           └─ build_multi_cpp.py には既にあるが、一部テストで環境変数未伝播
  └─ conftest 生成 C++ で @extern 関数が自己再帰になる
      └─ conftest extern stripping で解決済み ✓
```

## 調査結果

### REPO_ROOT 修正の影響（2026-03-22 検証済み）

| 状態 | pass | fail | 備考 |
|------|------|------|------|
| REPO_ROOT 旧値（parents[4]） | 245 | 54 | 安定値 |
| REPO_ROOT 修正のみ | 214 | 85 | 30テスト退行 |
| REPO_ROOT 修正 + conftest extern fix | 211 | 88 | 退行改善せず |
| REPO_ROOT 旧値 + conftest extern fix | 234 | 65 | 安定（並行コミット影響あり） |

### 退行の根本原因

REPO_ROOT 修正により `_normalize_runtime_module_name` が正しく動作するようになると:
- `from pytra.utils.assertions import py_assert_eq` が `#include "utils/assertions.h"` を生成する
- このヘッダーは `out/_test_generated_cpp/utils/assertions.h` にあり、`-I $PYTRA_GENERATED_CPP_DIR` で解決される
- しかし一部テストパスで `PYTRA_GENERATED_CPP_DIR` が伝播しないケースがある

### conftest の @extern 問題

conftest の `_generate_runtime_cpp()` は `transpile_to_cpp(east)` を直接呼び、`@extern` 関数の body をそのまま C++ に変換する。結果:

```cpp
// 自己再帰（BUG）
float64 sqrt(float64 x) {
    return pytra::std::math::sqrt(x);  // ← 自分自身を呼ぶ
}
```

修正済み: `_build_cpp_emit_module_without_extern_decls()` で extern 関数を除去してから transpile する。

## 修正方針

### S1: include path 生成の整合性確保

`_module_name_to_cpp_include` が生成するパスが、`-I` フラグで解決可能であることを保証する。

方針:
- runtime module の include は `"std/math.h"` 形式（`-I src/runtime/east` で解決）
- generated module の include は `"built_in/type_id.h"` 形式（`-I $PYTRA_GENERATED_CPP_DIR` で解決）
- user module の include は相対パス形式

### S2: REPO_ROOT 修正の適用

S1 完了後に `parents[4]` → `parents[5]` を適用する。

### S3: import alias → namespace 解決

`_resolve_imported_symbol_cpp_target` で `_normalize_runtime_module_name` を呼び、bare module name（`math`）を canonical form（`pytra.std.math`）に正規化する。

### S4: build_multi_cpp.py の generated source リンク

extern-only でないランタイムモジュールの `.cpp` を自動リンクする。現在は `assertions.cpp` と `type_id.cpp` のみ。

## 非対象

- emitter の `@extern` 関数ネイティブ実装生成（runtime 側の手書き C++ が担当）
- multi-module emit（別計画: `p0-cpp-relative-import-*`）

## 受け入れ基準

- [ ] `REPO_ROOT` が正しい値（`parents[5]`）になっている
- [ ] `from math import sqrt as msqrt` → `pytra::std::math::sqrt(9.0)` が生成される
- [ ] `import math as m; m.sqrt(9.0)` → `pytra::std::math::sqrt(9.0)` が生成される
- [ ] `test_py2cpp_features.py` のテスト通過数が修正前以上

## 決定ログ

### 2026-03-22: 調査と暫定修正

- REPO_ROOT が parents[4] = `src/` で誤っていることを特定
- parents[5] に修正すると import alias 解決は正しく動くが、include path 生成の変更で 30 テスト退行
- conftest の extern 関数自己再帰問題を `_build_cpp_emit_module_without_extern_decls` で修正
- REPO_ROOT 修正は include path 整合性確保後に適用する方針を決定
- 暫定的に REPO_ROOT は旧値のまま、conftest extern fix のみ適用してコミット
