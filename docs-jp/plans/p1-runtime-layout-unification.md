# TASK GROUP: TG-P1-RUNTIME-LAYOUT

最終更新: 2026-02-22

関連 TODO:
- `docs-jp/todo.md` の `ID: P1-RUNTIME-01` 〜 `P1-RUNTIME-06`

背景:
- 言語ごとに runtime 配置規約が分断され、保守責務と探索規則が揺れている。

目的:
- `src/runtime/<lang>/pytra/` へ配置規約を統一し、runtime 資産の責務境界を揃える。

対象:
- Rust: `src/rs_module/` から `src/runtime/rs/pytra/` への移行
- 他言語: `src/*_module/` 依存資産の `src/runtime/<lang>/pytra/` への移行計画
- `py2*` / hooks の解決パス統一

非対象:
- 各言語 runtime の機能追加そのもの

受け入れ基準:
- ランタイム参照先が `src/runtime/<lang>/pytra/` へ統一
- `src/*_module/` 直下への新規 runtime 追加が止まる

確認コマンド:
- `python3 tools/check_py2cpp_transpile.py`
- 言語別 smoke tests（`test/unit/test_py2*_smoke.py`）

`P1-RUNTIME-04` 移行計画（Rust以外）:

1. 現状資産（`src/*_module/`）を次の宛先へ段階移管する。
   - C#: `src/cs_module/{py_runtime.cs,pathlib.cs,png_helper.cs,gif_helper.cs,time.cs}` -> `src/runtime/cs/pytra/{built_in,std,utils}/...`
   - JS: `src/js_module/{py_runtime.js,pathlib.js,png_helper.js,gif_helper.js,math.js,time.js}` -> `src/runtime/js/pytra/{built_in,std,utils}/...`
   - TS: `src/ts_module/{py_runtime.ts,pathlib.ts,png_helper.ts,gif_helper.ts,math.ts,time.ts}` -> `src/runtime/ts/pytra/{built_in,std,utils}/...`
   - Go: `src/go_module/py_runtime.go` -> `src/runtime/go/pytra/built_in/py_runtime.go`
   - Java: `src/java_module/PyRuntime.java` -> `src/runtime/java/pytra/built_in/PyRuntime.java`
   - Swift: `src/swift_module/py_runtime.swift` -> `src/runtime/swift/pytra/built_in/py_runtime.swift`
   - Kotlin: `src/kotlin_module/py_runtime.kt` -> `src/runtime/kotlin/pytra/built_in/py_runtime.kt`
2. 移行ステップ:
   - Step A: `src/runtime/<lang>/pytra/` の雛形を作成し、既存ファイルをコピーして import/namespace 参照を壊さない最小差分で配置する。
   - Step B: 各 `py2<lang>.py` / hooks の runtime 解決パスを新配置優先に変更する（旧配置は互換 fallback）。
   - Step C: 言語別 smoke (`tools/check_py2<lang>_transpile.py`, `test/unit/test_py2<lang>_smoke.py`) を通し、旧配置参照を段階削除する。
   - Step D: 互換期間終了後に `src/*_module/` の runtime 本体を撤去し、必要なら再配置案内のみ残す。
3. 完了条件:
   - Rust以外の言語でも runtime 実体が `src/runtime/<lang>/pytra/` に揃う。
   - `py2*` / hooks の runtime 解決が新配置基準で動作し、旧 `src/*_module/` への実体依存が消える。

`P1-RUNTIME-06` 運用ルール:

1. 新規 runtime 実装（`py_runtime.*`, `pathlib.*`, `png/gif helper` など）は `src/runtime/<lang>/pytra/` 配下にのみ追加する。
2. `src/*_module/` 直下は互換レイヤ専用とし、新規実体ファイルは追加しない。
3. 互換レイヤは「移行完了後に削除する前提」の暫定資産として扱い、`todo` に撤去タスクを必ず紐付ける。
4. 例外追加が必要な場合は、同一ターンで `docs-jp/todo.md` に理由と撤去期限を記録する。

決定ログ:
- 2026-02-22: 初版作成。
- 2026-02-22: `P1-RUNTIME-04` として、Rust以外（C#/JS/TS/Go/Java/Swift/Kotlin）の `src/*_module/` -> `src/runtime/<lang>/pytra/` 移行計画（資産マップ + 段階手順）を追加。
- 2026-02-22: `P1-RUNTIME-06` として、`src/*_module/` 直下に新規 runtime 実体を追加しない運用ルールを明文化。
