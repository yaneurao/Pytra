<a href="../../ja/plans/p0-linker-resolved-includes.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p0-linker-resolved-includes.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p0-linker-resolved-includes.md`

# P0: リンカーによる C++ include 完全確定（generated ヘッダー廃止）

最終更新: 2026-03-19

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-LINKER-RESOLVED-INCLUDES-01`

## 背景

現在の C++ runtime include 解決には 3 つの問題がある:

1. **エミッターが include を決定している**。`_collect_import_cpp_includes` が EAST body を走査し `runtime_symbol_index.json` を参照するが、リンカーは既に全モジュールの依存グラフを持っている。
2. **`runtime_symbol_index.json` が存在しないヘッダーを指している**。`src/runtime/cpp/built_in/numeric_ops.h` 等 17 件が欠落。
3. **generated ヘッダーという中間成果物が存在する**。`.east` → `.h` を事前生成し `src/runtime/cpp/generated/` に配置する仕組みがあるが、リンカーが依存先の実体位置を確定できるなら不要。

### 根本原因

include 解決がリンカーではなくエミッター + 静的 index に依存している。リンカーが全モジュールの依存と各モジュールの C++ 出力先を把握しているのだから、include パスもリンカーが確定すべき。

## 設計

### 原則

- **リンカーが依存モジュール ID を確定する**（言語非依存）。`resolved_dependencies_v1: list[str]`。
- **エミッターが依存モジュール ID を C++ include パスに変換する**（言語固有）。`_module_name_to_cpp_include` + 起動時キャッシュ。
- **ソースツリー（`src/`）にビルド生成物を置かない**。`src/runtime/cpp/generated/` の事前生成ヘッダーは撤去。
- **runtime モジュールの C++ 生成物は `out/` に動的生成する**。compile → link → emit パイプラインで runtime `.east` も処理し、`out/` に C++ ヘッダーを生成。ビルドコマンドの `-I out/` で解決。
- **`py_runtime.h` の `#include "generated/built_in/string_ops.h"` 等は、`-I out/` 配下の動的生成物を参照する形になる**。配置先パス（`generated/built_in/string_ops.h`）は確定しているので変更不要。

### `resolved_dependencies_v1` の形式（リンカーが確定）

リンカーは**言語非依存**。確定するのはモジュール ID の依存リストのみ。

```json
{
  "resolved_dependencies_v1": [
    "pytra.built_in.contains",
    "pytra.built_in.io_ops",
    "pytra.built_in.iter_ops",
    "pytra.built_in.string_ops",
    "pytra.std.time"
  ]
}
```

- 型: `list[str]`（モジュール ID の順序付きリスト）
- 重複なし、ソート済み
- 明示的 import と暗黙 runtime 依存の両方を含む

#### 依存の収集ソース

| ソース | 説明 |
|--------|------|
| `meta.import_bindings` | 明示的 import（`from pytra.std.pathlib import Path`）のモジュール ID |
| body の `Import` / `ImportFrom` ノード | `import_bindings` がない場合のフォールバック |
| body の暗黙 runtime 参照 | `py_print` → `pytra.built_in.io_ops` 等。現在 `_collect_runtime_modules_from_node` が担当している処理と同等のロジックをリンカーに移す |

#### `core` 依存は含めない

`py_runtime.h` / `process_runtime.h` 等の core ヘッダーは全モジュールに無条件で含まれるため、依存リストに列挙しない。エミッターが固定で emit する。

### エミッター側の変更（モジュール ID → C++ include パス変換）

**ファイル**: `src/toolchain/emit/cpp/emitter/runtime_paths.py` の `module_name_to_cpp_include`

#### 現在の処理

```python
def module_name_to_cpp_include(module_name_norm: str) -> str:
    module_id = canonical_runtime_module_id(module_name_norm)
    indexed = lookup_target_module_primary_compiler_header("cpp", module_id)
    # indexed = "src/runtime/cpp/built_in/contains.h" 等
    if indexed != "":
        if indexed.startswith("src/runtime/cpp/"):
            return indexed[len("src/runtime/cpp/"):]   # → "built_in/contains.h"
        ...
    return ""
```

問題: `indexed` が `src/runtime/cpp/built_in/numeric_ops.h`（存在しない）を返す場合、そのまま strip して `built_in/numeric_ops.h` を返してしまう。ファイルが存在しないので g++ が失敗する。

#### 修正後の処理

起動時に一度だけ `runtime_symbol_index.json` の全 C++ モジュールを走査し、モジュール ID → include パスの解決済みキャッシュを構築する。以後の `module_name_to_cpp_include` 呼び出しはキャッシュ参照のみ。

```python
# 起動時に一度だけ実行
_RESOLVED_INCLUDE_CACHE: dict[str, str] = {}

def _build_include_cache() -> dict[str, str]:
    """runtime_symbol_index の全 C++ モジュールを走査し、
    モジュール ID → include パスのキャッシュを構築する。"""
    cache: dict[str, str] = {}
    for module_id, info in all_cpp_modules():
        for header_path in info["compiler_headers"]:
            if Path(header_path).exists():
                cache[module_id] = _strip_prefix(header_path)
                break
            # native が存在しない → generated/ を探す
            rel = _strip_runtime_cpp_prefix(header_path)
            gen_path = "src/runtime/cpp/generated/" + rel
            if Path(gen_path).exists():
                cache[module_id] = "generated/" + rel
                break
    return cache

def module_name_to_cpp_include(module_name_norm: str) -> str:
    module_id = canonical_runtime_module_id(module_name_norm)
    return _RESOLVED_INCLUDE_CACHE.get(module_id, "")
```

ファイル存在チェックはキャッシュ構築時（プロセス起動時 1 回）のみ。エミッターの `module_name_to_cpp_include` 呼び出し（モジュールごとに複数回）はキャッシュ辞書の参照だけ。

#### `_collect_import_cpp_includes` の変更

**ファイル**: `src/toolchain/emit/cpp/emitter/module.py`

`resolved_dependencies_v1` があれば、body 走査と import 解析をスキップし、リンカーが確定した依存モジュール ID リストを `module_name_to_cpp_include` で変換するだけにする。

### リンカー側の変更

**ファイル**: `src/toolchain/link/global_optimizer.py`

`optimize_linked_program` 内で `_build_resolved_dependencies(module)` を呼び出し、各モジュールについて:

1. `meta.import_bindings`（または body の `Import`/`ImportFrom`）から依存モジュール ID を収集。
2. body を走査し暗黙 runtime 依存（`py_print` → `pytra.built_in.io_ops` 等）を収集。現在 `_collect_runtime_modules_from_node`（エミッター側）がやっている処理をリンカーに移植。
3. 重複除去・ソートし `resolved_dependencies_v1: list[str]` として `linked_program_v1` メタデータに格納。

### エミッター側の変更

**ファイル**: `src/toolchain/emit/cpp/emitter/module.py`

`_collect_import_cpp_includes` を修正:
- `linked_program_v1.resolved_includes_v1` が存在すれば、それをそのまま返す。
- 存在しなければ従来のフォールバック（後方互換）。

### 撤去済み

| 対象 | 状態 |
|------|------|
| `src/runtime/cpp/generated/` ディレクトリ全体 | 撤去済み。ビルド生成物はソースツリーに置かない。 |
| `tools/runtime_generation_manifest.json` の C++ ターゲット | 撤去済み。 |

### ビルド時の動的生成

runtime モジュールの C++ ヘッダーは `out/` に動的生成する。`py_runtime.h` の `#include "generated/built_in/string_ops.h"` は `-I out/` で `out/generated/built_in/string_ops.h` に解決される。ビルドコマンドに `-I out/` を追加する。

### runtime モジュールの扱い

現在 runtime モジュール（`pytra.built_in.*`, `pytra.std.*`）は `src/runtime/east/{bucket}/{name}.east` として事前に EAST3 JSON 化されている。これらは:

- **compile 段**: 既に `.east` 化済み（変更なし）
- **link 段**: ユーザーモジュールと一緒に `LinkedProgram` に含まれる（現在も同様）
- **emit 段**: リンカーが確定した include パスでエミッターが `#include` を emit

runtime モジュールの C++ 出力は、マルチファイルモード（`write_multi_file_cpp`）ではモジュールごとに `.h` + `.cpp` として出力される。シングルファイルモードでは inline で含まれる。いずれの場合もリンカーが出力先を知っているので、include パスを確定できる。

## 対象ファイル

| ファイル | 変更内容 |
|---------|---------|
| `src/toolchain/link/global_optimizer.py` | `_build_resolved_includes` 追加、`resolved_includes_v1` をメタデータに格納 |
| `src/toolchain/emit/cpp/emitter/module.py` | `resolved_includes_v1` 優先読み取り |
| `tools/runtime_symbol_index.json` | `compiler_headers` を実体パスに修正（S2 完了後は段階的に不要化） |
| `src/runtime/cpp/generated/` | 段階的に撤去 |
| `tools/runtime_generation_manifest.json` | C++ ターゲット撤去 |
| `tools/gen_runtime_from_manifest.py` | `cpp_program_to_header` 撤去 |

## 非対象

- 非 C++ バックエンドの include 解決
- `py_runtime.h` の include 構造リファクタリング（native runtime 層は本タスクのスコープ外）

## 受け入れ基準

- [ ] リンカーが `resolved_dependencies_v1`（モジュール ID リスト）を構築し、メタデータに格納している。
- [ ] C++ エミッターが `resolved_dependencies_v1` を読み、モジュール ID → C++ include パス変換を経て `#include` を emit する。
- [ ] `from pytra.std.pathlib import Path` を含むコードが `g++ -Isrc -Isrc/runtime/cpp` でコンパイルできる。
- [x] `src/runtime/cpp/generated/` の事前生成ヘッダーを撤去済み。
- [ ] `check_py2x_transpile --target cpp` 149/149 pass。

## 子タスク

- [ ] [ID: P0-LINKER-RESOLVED-INCLUDES-01-S1] `global_optimizer.py` に `_build_resolved_dependencies` を実装。`import_bindings` + 暗黙 runtime 依存を収集し `resolved_dependencies_v1: list[str]` をメタデータに格納。
- [ ] [ID: P0-LINKER-RESOLVED-INCLUDES-01-S2] `module.py` の `_collect_import_cpp_includes` を修正。`resolved_dependencies_v1` があれば各モジュール ID を `_module_name_to_cpp_include` で C++ パスに変換するだけにする。
- [ ] [ID: P0-LINKER-RESOLVED-INCLUDES-01-S3] `runtime_symbol_index.json` の `compiler_headers` を実体パスに修正する（generated のみのモジュール 17 件）。
- [ ] [ID: P0-LINKER-RESOLVED-INCLUDES-01-S4] `from pytra.std.pathlib import Path` の最小 repro が `g++` でビルドできることを検証する。
- [x] [ID: P0-LINKER-RESOLVED-INCLUDES-01-S5] `src/runtime/cpp/generated/` と manifest の C++ ターゲットを撤去する。
6. [ ] [ID: P0-LINKER-RESOLVED-INCLUDES-01-S6] compile → link → emit パイプラインで runtime `.east` の C++ ヘッダーを `out/` に動的生成し、`-I out/` でビルドが通ることを検証する。

## 決定ログ

- 2026-03-19: Pytra-NES チームから `#include "built_in/numeric_ops.h"` / `#include "std/pathlib.h"` が見つからないバグ報告。
- 2026-03-19: shim wrapper で対処 → ユーザーから「リンカーで確定すべき」と指摘。
- 2026-03-19: generated ヘッダーに forward declaration 追加 → ユーザーから「リンカーが位置まで確定しているなら generated ヘッダー自体不要」と指摘。include 解決の責務をリンカーに統一し、generated ヘッダーを廃止する設計で計画書を更新。
- 2026-03-19: `resolved_includes_v1`（C++ パスリスト）→ ユーザーから「リンカーが .h パスを知るのはおかしい。リンカーは言語非依存であるべき」と指摘。リンカーは `resolved_dependencies_v1`（モジュール ID リスト）のみを確定し、モジュール ID → C++ パス変換はエミッター側（`_module_name_to_cpp_include`）が担う設計に修正。
- 2026-03-19: ユーザーから「ソースツリー（`src/`）にビルド生成物を置くのがおかしい。`out/` に動的生成すべき」と指摘。`src/runtime/cpp/generated/` を撤去。runtime モジュールの C++ ヘッダーは compile → link → emit パイプラインで `out/` に動的生成し、`-I out/` で解決する設計に修正。手書き `py_runtime.h` の `#include "generated/built_in/string_ops.h"` は配置先パスが確定しているので変更不要。
