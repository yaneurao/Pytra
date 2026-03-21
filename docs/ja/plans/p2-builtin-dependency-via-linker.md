# P2: built-in 依存を EAST1 → linker 経由で解決し、emitter の決め打ちバンドルを廃止

最終更新: 2026-03-21

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-BUILTIN-VIA-LINKER`

## 背景

現状、`len()`, `print()`, `range()` 等の built-in 関数は各 emitter がランタイムファイル（`py_runtime.dart`, `py_runtime.jl`, `py_runtime.zig` 等）を決め打ちでバンドルしている。

この設計には以下の問題がある:

1. **emitter 間の不統一**: emitter ごとに「何を含めるか」がバラバラ
2. **不要コードの混入**: 使われていない built-in も全て含まれる
3. **linker の依存グラフが不完全**: `pytra.std.*` / `pytra.utils.*` は linker で解決されるのに、`pytra.built_in.*` だけ別経路
4. **built-in 追加時の修正コスト**: 新しい built-in を追加するたびに全 emitter を修正する必要がある

## 設計

### EAST1 パーサーの責務

`len()`, `print()` 等の built-in 呼び出しを検出したら、`import_bindings` に暗黙的な依存を記録する:

```python
# len(x) を検出 → import_bindings に追加
{"module_id": "pytra.built_in.sequence", "binding_kind": "implicit_builtin", ...}
```

「`len` はどのモジュールに属するか」は Python の意味論であり、EAST1 パーサーの責務。EAST2 以降に Python 固有知識を持ち込んではならない。

### linker の責務

既存の `_resolve_runtime_east_path` + `_RUNTIME_MODULE_BUCKETS` がそのまま使える:
- `import_bindings` に `pytra.built_in.sequence` → `built_in/sequence.east` を解決
- link-output manifest にモジュールとして含める

### emitter の責務

- manifest に含まれるモジュールだけを emit する
- `py_runtime.*` の決め打ちバンドルを廃止する

## 対象

| 変更対象 | 内容 |
|---|---|
| EAST1 パーサー（`core_*` 系） | built-in 呼び出し検出時に `import_bindings` へ暗黙依存を記録 |
| 全 emitter（C++ 含む）の `*.py` エントリ | `py_runtime.*` / ヘッダーの決め打ちコピー/include を除去 |
| `built_in/*.east` | 必要に応じて分割・整理 |

## 非対象

- built-in の実装内容の変更

## 受け入れ基準

- [x] EAST1 パーサーが built-in 呼び出しに対応する `import_bindings` を生成する
- [x] linker が `pytra.built_in.*` の依存を link-output manifest に含める
- [ ] 全 emitter（C++ 含む）が manifest 内のモジュールのみを emit し、決め打ちバンドルを行わない（`@extern` 関数の扱い確定後）
- [x] 既存テストがリグレッションしない

## 子タスク

- [x] [ID: P2-BUILTIN-VIA-LINKER-01] EAST1 パーサーに built-in → module 対応テーブルを追加し、`import_bindings` に暗黙依存を記録する
- [x] [ID: P2-BUILTIN-VIA-LINKER-02] linker が `pytra.built_in.*` を link-output manifest に含めることを検証する
- [ ] [ID: P2-BUILTIN-VIA-LINKER-03] 全 emitter（C++ 含む）から `py_runtime.*` / ヘッダーの決め打ちバンドルを除去する（`@extern` 関数の扱い確定後）
- [x] [ID: P2-BUILTIN-VIA-LINKER-04] 既存テストのリグレッションがないことを検証する

## 決定ログ

- 2026-03-21: linker のサブモジュール import 解決（P2-LINKER-SUBMODULE-IMPORT）の議論中に、built-in 関数の依存解決が linker を経由せず各 emitter で決め打ちバンドルされている設計問題を確認。Python の意味論（built-in がどのモジュールに属するか）は EAST1 パーサーの責務であり、EAST2 以降に持ち込むべきではないと判断。起票。
