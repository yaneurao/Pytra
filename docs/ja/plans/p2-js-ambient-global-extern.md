# P2: JS/TS 向け ambient global extern 変数を導入する

最終更新: 2026-03-08

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-JS-AMBIENT-GLOBAL-EXTERN-01`

関連:
- [spec-abi.md](../spec/spec-abi.md)
- [spec-dev.md](../spec/spec-dev.md)
- [spec-import.md](../spec/spec-import.md)
- [spec-pylib-modules.md](../spec/spec-pylib-modules.md)

背景:
- JavaScript / TypeScript へ変換する際、DOM 操作の最小ケースでは `document`, `window`, `console` などの ambient global を「既に存在する外部変数」として使いたい。
- 現状の docs には `browser` / `browser.widgets.dialog` を外部参照として扱う方針があるが、DOM 用 nominal module を大きく整備し始めるとスコープが広がりすぎる。
- 一方、Python 構文上は変数に decorator を付けられないため、`@extern` を変数宣言に直接書く案は採れない。
- 既存仕様では変数 extern は `name = extern(expr)` 形式で表すため、この系に ambient global 宣言を載せるのが自然である。

目的:
- `document: Any = extern()` を「同名 ambient global 宣言」として扱えるようにする。
- `doc: Any = extern("document")` を「別名 ambient global 宣言」として扱えるようにする。
- JS/TS backend では ambient global `Any` に対する property access / method call / call expression を、そのまま生の識別子チェーンへ lower できるようにする。
- `browser` モジュール一式を拡張しなくても、最小の DOM / Web API 利用を書けるようにする。

対象:
- `src/pytra/std/__init__.py` の `extern` surface
- parser / EAST metadata / lowerer における extern variable 扱い
- JS/TS emitter の ambient global lowering
- representative smoke tests
- docs / examples

非対象:
- `browser` / `pytra.utils.browser` モジュール群の大規模設計
- DOM 型 (`Document`, `Element`, `CanvasRenderingContext`) の nominal type 導入
- C++/Rust/Go など他 target での ambient global 対応
- 一般 variable decorator 構文
- `Any` / `object` 全体の制約緩和

受け入れ基準:
- `document: Any = extern()` を含む JS/TS input が transpile できる。
- `doc: Any = extern("document")` を含む JS/TS input が transpile できる。
- `document.title`, `document.getElementById(...)`, `console.log(...)`, `window.alert(...)` のような access/call が、そのまま JS/TS へ lower される。
- JS/TS では ambient global extern variable に対して import 文を生成しない。
- non-JS/TS target では fail-closed（unsupported error）にする。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `git diff --check`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/js -p 'test_py2js_smoke.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/ts -p 'test_py2ts_smoke.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east_core.py' -k extern`

## 1. 基本方針

1. 関数の external implementation marker は従来どおり `@extern` を使う。
2. 変数の ambient global 宣言は `name: Any = extern()` / `name: Any = extern("symbol")` を canonical syntax とする。
3. `extern()` は「同名 global symbol」、`extern("symbol")` は「別名 global symbol」を意味する。
4. JS/TS backend では ambient global `Any` receiver に対する property access / method call / call expression を、そのまま raw identifier chain へ lower してよい。
5. この緩和は ambient global marker が付いた binding に限定し、一般の `Any/object` receiver 禁止ルールは維持する。

## 2. 想定 surface

同名 global:

```python
from pytra.std import extern

document: Any = extern()
console: Any = extern()
```

別名 global:

```python
from pytra.std import extern

doc: Any = extern("document")
```

想定 lowering:

```python
title = document.title
node = document.getElementById("app")
console.log(title)
```

```js
const title = document.title;
const node = document.getElementById("app");
console.log(title);
```

## 3. 段階導入

### Phase 1: syntax / metadata 固定

- `extern()` / `extern("symbol")` を ambient global variable として解釈する契約を docs に固定する。
- 既存の `extern(expr)` host fallback / runtime hook との切り分けを決定ログへ残す。

### Phase 2: parser / EAST / binding metadata

- extern variable metadata に `ambient_global_v1` を追加し、same-name / explicit-symbol を保持する。
- `Any` 以外の型でどこまで許すかを最小仕様で固定する（v1 は `Any` 限定でもよい）。

### Phase 3: JS/TS lowering

- JS/TS emitter で ambient global binding を import-free symbol として扱う。
- ambient global `Any` receiver に限り property/method/call を raw lowering する。
- 一般 `Any/object` receiver 禁止ルールは維持する。

### Phase 4: tests / docs / close

- representative smoke を追加する。
- unsupported backend error を固定する。
- docs / archive を同期する。

## 4. タスク分解

- [ ] [ID: P2-JS-AMBIENT-GLOBAL-EXTERN-01] JS/TS 向け ambient global extern 変数を導入する。
- [x] [ID: P2-JS-AMBIENT-GLOBAL-EXTERN-01-S1-01] `extern()` / `extern("symbol")` の variable ambient-global 契約を docs に固定する。
- [x] [ID: P2-JS-AMBIENT-GLOBAL-EXTERN-01-S1-02] 既存 `extern(expr)` host fallback との切り分けを決定ログへ固定する。
- [x] [ID: P2-JS-AMBIENT-GLOBAL-EXTERN-01-S2-01] parser / EAST metadata に ambient global variable marker を追加する。
- [x] [ID: P2-JS-AMBIENT-GLOBAL-EXTERN-01-S2-02] representative IR/unit test で same-name / alias case を固定する。
- [x] [ID: P2-JS-AMBIENT-GLOBAL-EXTERN-01-S3-01] JS/TS emitter で ambient global extern variable を import-free symbol へ lower する。
- [x] [ID: P2-JS-AMBIENT-GLOBAL-EXTERN-01-S3-02] ambient global `Any` receiver の property/method/call raw lowering を追加する。
- [ ] [ID: P2-JS-AMBIENT-GLOBAL-EXTERN-01-S4-01] unsupported backend guard / representative smoke を更新する。
- [ ] [ID: P2-JS-AMBIENT-GLOBAL-EXTERN-01-S4-02] docs / archive を同期して本計画を閉じる。

## 5. 決定ログ

- 2026-03-08: DOM / browser nominal module を先に大きく設計するのではなく、まず JS/TS で ambient global variable を直接宣言できる最小機能を入れる。関数は `@extern`、変数は `name = extern(...)` の既存構文系を維持する。
- 2026-03-08: `document: Any = extern()` は same-name ambient global、`doc: Any = extern("document")` は alias ambient global として扱う。`@extern` を変数へ付ける独自構文は導入しない。
- 2026-03-08: ambient global `Any` receiver の raw lowering 緩和は JS/TS に限定し、一般 `Any/object` receiver 禁止ルールは維持する。
- 2026-03-08: `extern(expr)` は従来どおり host fallback / runtime hook 初期化として残し、ambient global とは分離する。v1 の variable ambient-global は `extern()` と `extern("symbol")` だけを特例として扱う。
- 2026-03-08: parser/EAST の canonical marker は top-level `AnnAssign.meta.extern_var_v1` とし、shape は `schema_version`, `symbol`, `same_name` の 3 キーに固定する。v1 では plain `Assign` や non-`Any` 注釈へは広げない。
- 2026-03-08: JS/TS emitter は top-level ambient global extern 宣言を `ambient_global_aliases` として先に収集し、対応する `AnnAssign` 自体は emit 対象から外す。Name / call の raw lowering はこの alias table にだけ反応し、一般の `Any` receiver 緩和には広げない。
