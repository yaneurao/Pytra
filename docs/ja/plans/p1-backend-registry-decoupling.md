# P1: backend_registry 依存の除去 — コンパイラフロントエンドを backend 非依存に

最終更新: 2026-03-21

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-BACKEND-REGISTRY-DECOUPLING-01`

## 背景

P1-PIPELINE-STAGE-SEPARATION で `east2cpp.py` / `east2x.py` を新設し、emit 段階を独立エントリポイントに分離した。しかし `py2x.py` と `py2x-selfhost.py` は依然として `backend_registry.py` / `backend_registry_static.py` をモジュールレベルで import しており、compile/link だけを実行する場合でも全言語（15 backend）の emitter/lower/optimizer が読み込まれる。

### 現状の import チェーン

```
py2x.py
  → backend_registry.py
    → backends.cpp.emitter  (15+ modules)
    → backends.rs.emitter   (4 modules)
    → backends.cs.emitter   (4 modules)
    → backends.go.emitter   (4 modules)
    → backends.java.emitter (4 modules)
    → ... 合計 15 言語、~74 non-C++ backend modules

py2x-selfhost.py
  → backend_registry_static.py
    → 同上
```

### あるべき姿

```
py2x.py (compile + link のみ)
  → toolchain.frontends  (パーサー、EAST pipeline)
  → toolchain.link       (リンカー、optimizer)
  → backend_registry に依存しない

emit が必要な場合:
  → east2cpp / east2x をサブプロセスで呼ぶ
  → または --from-link-output で east2x を呼ぶ
```

## 設計

### py2x.py の変更方針

`py2x.py` が `backend_registry` から import しているシンボルは以下:

1. **compile/link パスで不要**:
   - `get_backend_spec_typed` — emit/runtime hook 用
   - `apply_runtime_hook_typed` — emit 後のファイル配置
   - `list_backend_targets` — `--target` の選択肢
   - `emit_source_typed`, `lower_ir_typed`, `optimize_ir_typed` — emit パイプライン
   - `resolve_layer_options_typed` — emitter option 解決

2. **compile/link パスで必要**（ただし backend_registry 経由でなくてよい）:
   - `default_output_path` — 出力パス生成（ターゲット拡張子のみ依存）

### 変更手順

1. `py2x.py` の C++ emit パスを `east2cpp.py` サブプロセス呼び出しに変更
2. `py2x.py` の非 C++ emit パスを `east2x.py` サブプロセス呼び出しに変更
3. `py2x.py` から `backend_registry` の import を全て除去
4. `list_backend_targets()` は `east2x.py --list-targets` またはハードコード定数で代替
5. `default_output_path()` は `py2x.py` 内に薄いヘルパーとして移動
6. `py2x-selfhost.py` からも `backend_registry_static` の import を除去し、同様にリファクタ

### py2x-selfhost.py の変更方針

selfhost バイナリの責務:
- **compile**: `.py` → EAST3（パーサー + EAST pipeline）
- **link**: EAST3 modules → linked EAST（リンカー + optimizer）
- **C++ emit**: linked EAST → C++（`east2cpp` 相当の処理を内蔵）

selfhost では C++ emit を直接実行する必要がある（サブプロセスではなくネイティブ実行）。そのため:
- compile/link 部分は `backend_registry_static` に依存しない形にリファクタ
- C++ emit 部分は `backends.cpp.emitter` のみ import（他言語 backend は不要）

## 対象

- `src/py2x.py` — `backend_registry` import の除去、emit をサブプロセス化
- `src/py2x-selfhost.py` — `backend_registry_static` import の除去、C++ emit 直接 import に変更
- `src/east2x.py` — `--list-targets` オプション追加（省略可）

## 非対象

- `backend_registry.py` / `backend_registry_static.py` 自体の廃止（`east2x.py` が使う）
- `pytra-cli.py` の変更（既に `east2cpp.py` サブプロセス化済み）
- `ir2lang.py` の変更（互換 shim として残存）

## 受け入れ基準

- [ ] `py2x.py` の import グラフに `backends.*` が一切含まれない。
- [ ] `py2x-selfhost.py` の import グラフに `backends.cpp.*` 以外の backend が含まれない。
- [ ] `python3 src/py2x.py INPUT.py --target cpp -o out.cpp` が動作する（emit はサブプロセス経由）。
- [ ] `python3 src/py2x.py INPUT.py --target rs -o out.rs` が動作する（emit はサブプロセス経由）。
- [ ] `python3 src/py2x.py INPUT.py --target cpp --link-only --output-dir out/` が動作する（backend 不要パス）。
- [ ] selfhost multi-module の compile+link 段階で非 C++ backend モジュールが import されない（link-output に含まれない）。

## 子タスク

- [ ] [ID: P1-BACKEND-REGISTRY-DECOUPLING-01-S1] `py2x.py` の C++ emit パスを `east2cpp.py` サブプロセスに変更し、`backend_registry` import を除去する。
- [ ] [ID: P1-BACKEND-REGISTRY-DECOUPLING-01-S2] `py2x.py` の非 C++ emit パスを `east2x.py` サブプロセスに変更する。
- [ ] [ID: P1-BACKEND-REGISTRY-DECOUPLING-01-S3] `py2x-selfhost.py` から `backend_registry_static` import を除去し、C++ emit のみ `backends.cpp.emitter` を直接 import する形にリファクタする。
- [ ] [ID: P1-BACKEND-REGISTRY-DECOUPLING-01-S4] selfhost multi-module の compile+link 段階で非 C++ backend が import グラフに含まれないことを検証する。

## 決定ログ

- 2026-03-21: P1-PIPELINE-STAGE-SEPARATION で emit エントリ分離は完了したが、`py2x.py` / `py2x-selfhost.py` のモジュールレベル import に `backend_registry` が残存し、compile/link だけの実行でも全 backend が読み込まれる問題を特定。`py2x.py` の emit パスをサブプロセス化し、compile/link フロントエンドを backend 非依存にするリファクタを計画。
