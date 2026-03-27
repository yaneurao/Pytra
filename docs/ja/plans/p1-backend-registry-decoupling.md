<a href="../../en/plans/p1-backend-registry-decoupling.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1: backend_registry 依存の除去 — コンパイラフロントエンドを backend 非依存に

最終更新: 2026-03-21

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-BACKEND-REGISTRY-DECOUPLING-01`

## 背景

P1-PIPELINE-STAGE-SEPARATION で `east2cpp.py` / `east2x.py` を新設し、emit 段階を独立エントリポイントに分離した。しかし `pytra-cli.py` と `pytra-cli.py` は依然として `backend_registry.py` / `backend_registry_static.py` をモジュールレベルで import しており、compile/link だけを実行する場合でも全言語（15 backend）の emitter/lower/optimizer が読み込まれる。

### 現状の import チェーン

```
pytra-cli.py
  → backend_registry.py
    → toolchain.emit.cpp.emitter  (15+ modules)
    → toolchain.emit.rs.emitter   (4 modules)
    → toolchain.emit.cs.emitter   (4 modules)
    → toolchain.emit.go.emitter   (4 modules)
    → toolchain.emit.java.emitter (4 modules)
    → ... 合計 15 言語、~74 non-C++ backend modules

pytra-cli.py
  → backend_registry_static.py
    → 同上
```

### あるべき姿

```
pytra-cli.py (compile + link のみ)
  → toolchain.frontends  (パーサー、EAST pipeline)
  → toolchain.link       (リンカー、optimizer)
  → backend_registry に依存しない

emit が必要な場合:
  → east2cpp / east2x をサブプロセスで呼ぶ
  → または --from-link-output で east2x を呼ぶ
```

## 設計

### pytra-cli.py の変更方針

`pytra-cli.py` が `backend_registry` から import しているシンボルは以下:

1. **compile/link パスで不要**:
   - `get_backend_spec_typed` — emit/runtime hook 用
   - `apply_runtime_hook_typed` — emit 後のファイル配置
   - `list_backend_targets` — `--target` の選択肢
   - `emit_source_typed`, `lower_ir_typed`, `optimize_ir_typed` — emit パイプライン
   - `resolve_layer_options_typed` — emitter option 解決

2. **compile/link パスで必要**（ただし backend_registry 経由でなくてよい）:
   - `default_output_path` — 出力パス生成（ターゲット拡張子のみ依存）

### 変更手順

1. `pytra-cli.py` の C++ emit パスを `east2cpp.py` サブプロセス呼び出しに変更
2. `pytra-cli.py` の非 C++ emit パスを `east2x.py` サブプロセス呼び出しに変更
3. `pytra-cli.py` から `backend_registry` の import を全て除去
4. `list_backend_targets()` は `east2x.py --list-targets` またはハードコード定数で代替
5. `default_output_path()` は `pytra-cli.py` 内に薄いヘルパーとして移動
6. `pytra-cli.py` からも `backend_registry_static` の import を除去し、同様にリファクタ

### pytra-cli.py の変更方針

selfhost バイナリの責務:
- **compile**: `.py` → EAST3（パーサー + EAST pipeline）
- **link**: EAST3 modules → linked EAST（リンカー + optimizer）
- **C++ emit**: linked EAST → C++（`east2cpp` 相当の処理を内蔵）

selfhost では C++ emit を直接実行する必要がある（サブプロセスではなくネイティブ実行）。そのため:
- compile/link 部分は `backend_registry_static` に依存しない形にリファクタ
- C++ emit 部分は `toolchain.emit.cpp.emitter` のみ import（他言語 backend は不要）

## 対象

- `src/pytra-cli.py` — `backend_registry` import の除去、emit をサブプロセス化
- `src/pytra-cli.py` — `backend_registry_static` import の除去、C++ emit 直接 import に変更
- `src/east2x.py` — `--list-targets` オプション追加（省略可）

## 非対象

- `backend_registry.py` / `backend_registry_static.py` 自体の廃止（`east2x.py` が使う）
- `pytra-cli.py` の変更（既に `east2cpp.py` サブプロセス化済み）
- `ir2lang.py` の変更（互換 shim として残存）

## 受け入れ基準

- [ ] `pytra-cli.py` の import グラフに `toolchain.emit.*` が一切含まれない。
- [ ] `pytra-cli.py` の import グラフに `toolchain.emit.cpp.*` 以外の backend が含まれない。
- [ ] `python3 src/pytra-cli.py INPUT.py --target cpp -o out.cpp` が動作する（emit はサブプロセス経由）。
- [ ] `python3 src/pytra-cli.py INPUT.py --target rs -o out.rs` が動作する（emit はサブプロセス経由）。
- [ ] `python3 src/pytra-cli.py INPUT.py --target cpp --link-only --output-dir out/` が動作する（backend 不要パス）。
- [ ] selfhost multi-module の compile+link 段階で非 C++ backend モジュールが import されない（link-output に含まれない）。

## 子タスク

- [ ] [ID: P1-BACKEND-REGISTRY-DECOUPLING-01-S1] `pytra-cli.py` の C++ emit パスを `east2cpp.py` サブプロセスに変更し、`backend_registry` import を除去する。
- [ ] [ID: P1-BACKEND-REGISTRY-DECOUPLING-01-S2] `pytra-cli.py` の非 C++ emit パスを `east2x.py` サブプロセスに変更する。
- [ ] [ID: P1-BACKEND-REGISTRY-DECOUPLING-01-S3] `pytra-cli.py` から `backend_registry_static` import を除去し、C++ emit のみ `toolchain.emit.cpp.emitter` を直接 import する形にリファクタする。
- [ ] [ID: P1-BACKEND-REGISTRY-DECOUPLING-01-S4] selfhost multi-module の compile+link 段階で非 C++ backend が import グラフに含まれないことを検証する。

## 決定ログ

- 2026-03-21: P1-PIPELINE-STAGE-SEPARATION で emit エントリ分離は完了したが、`pytra-cli.py` / `pytra-cli.py` のモジュールレベル import に `backend_registry` が残存し、compile/link だけの実行でも全 backend が読み込まれる問題を特定。`pytra-cli.py` の emit パスをサブプロセス化し、compile/link フロントエンドを backend 非依存にするリファクタを計画。
