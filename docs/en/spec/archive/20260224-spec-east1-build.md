# アーカイブ: spec-east1-build.md

- 元ファイル: docs/ja/spec/spec-east1-build.md
- 退役日: 2026-02-24
- 退役理由: EAST1 build責務境界を spec-east.md へ統合したため。
- 現行の参照先: docs/ja/spec/spec-east.md

---

# EAST1 Build 分離仕様（`east1_build.py`）

最終更新: 2026-02-24

この文書は `EAST1` の build 入口責務を明確化する。  
上位仕様は `docs/ja/spec/spec-east123.md`、移行順は `docs/ja/spec/spec-east123-migration.md` に従う。

## 1. 背景

- `.py -> EAST` の実パーサ本体は `src/pytra/compiler/east_parts/core.py` にある。
- `src/pytra/compiler/east_parts/east1.py` は stage 付与（`east_stage=1`）中心で、`.py -> EAST1` build の責務境界が見えにくい。
- `EAST3` は `east3.py`（入口）と `east3_lowering.py`（変換本体）に分離されているため、`EAST1` 側も同様に入口と実装を分離する。

## 2. 目的

1. `.py -> EAST1` build の入口責務を `east1_build.py` に集約する。  
2. `core.py` の parser 内部実装と公開 build API を分離する。  
3. `transpile_cli.py` の責務を「互換ラッパ中心」へ縮退する。  

## 3. 非対象

- self-hosted parser ロジック（`_sh_*` 群）の全面移動
- EAST ノード仕様変更
- `EAST1 -> EAST2` / `EAST2 -> EAST3` の意味論変更

## 4. 提案構成

```text
src/pytra/compiler/east_parts/
  core.py             # parser 内部実装（現状維持）
  east1_build.py      # .py/.json 入力 -> EAST1 build 入口（新規）
  east1.py            # EAST1 stage helper（stage 付与・薄い公開 API）
  east2.py
  east3.py
  east3_lowering.py
```

## 5. 責務境界

### 5.1 `east1_build.py` の責務

- 入力（`.py` / `.json`）から `dict(kind=Module)` を得る build 入口を提供する。
- parser backend 選択（`self_hosted` など）と build 失敗時のエラー整形を担当する。
- `east_stage=1` の付与までを担う（または `east1.py` helper を呼ぶ）。
- `EAST1 -> EAST2` 変換は **行わない**。

### 5.2 `east1.py` の責務

- `EAST1` stage 契約 helper の提供に限定する。
- 入口 API は薄い委譲にとどめ、build 本体ロジックを持たない。

### 5.3 `core.py` の責務

- self-hosted parser の実装詳細（字句/構文処理、`_sh_*` 群）に専念する。
- CLI 文脈を持たない低レイヤとして維持する。

## 6. API 案（最小）

`src/pytra/compiler/east_parts/east1_build.py`:

```python
def build_east1_document(
    input_path: Path,
    parser_backend: str = "self_hosted",
    *,
    make_user_error_fn: Any = None,
) -> dict[str, object]
```

補助（必要なら）:

```python
def build_east1_from_source(
    source_text: str,
    filename: str,
    parser_backend: str = "self_hosted",
) -> dict[str, object]
```

## 7. 実装ステップ（無挙動変更）

1. `east1_build.py` を追加し、`transpile_cli.load_east_document()` の `.py` build 部分を関数化して移す。  
2. `transpile_cli.py` は `east1_build.py` 呼び出しへ置換し、既存エラー契約を維持する。  
3. `east1.py` は `normalize_east1_root_document` と薄い wrapper のみに整理する。  
4. 既存 `EAST2` 経路（`normalize_east1_to_east2_document`）には触れず、出力差分ゼロを確認する。  

## 8. 受け入れ基準

1. `.py -> EAST1` build 入口が `east1_build.py` に存在する。  
2. `transpile_cli.py` に parser build 本体ロジックが残らない（委譲中心）。  
3. `load_east_document_compat` のエラー分類/文言契約（`input_invalid` 系の互換）が維持される。  
4. `EAST1` build は `east_stage=1` 付与までに限定し、`EAST1 -> EAST2` は行わない。  
5. `EAST1 -> EAST2` / `EAST2 -> EAST3` 契約テストが退行しない。  

## 9. 最低確認コマンド

```bash
python3 -m pytest -q test/unit/test_east3_lowering.py
python3 -m pytest -q test/unit/test_east3_cpp_bridge.py
python3 tools/check_py2cpp_transpile.py
python3 tools/check_py2js_transpile.py
python3 tools/check_py2ts_transpile.py
python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented
```

## 10. リスクと対策

1. リスク: エラー文言/分類が変わる。  
   対策: `make_user_error` 経路を `east1_build.py` に注入し、現行 payload 形式を維持する。

2. リスク: `transpile_cli.py` と `east1_build.py` で責務が再重複する。  
   対策: `transpile_cli.py` は wrapper、build 条件分岐は `east1_build.py` へ一本化する。

3. リスク: `core.py` からの大規模移動で selfhost 回帰が出る。  
   対策: 初期段階は「委譲追加のみ」で開始し、`core.py` 実装は移動しない。

## 11. 命名補足

- `.py -> EAST1` は `lowering` より `build` / `parse` が適切。
- 本提案では `east1_lowering.py` ではなく `east1_build.py` を採用する。
