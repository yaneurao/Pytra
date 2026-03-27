<a href="../../en/plans/p2-cross-backend-common-test-suite.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P2: 全 backend 共通テストスイートの整備

最終更新: 2026-03-23

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-COMMON-TEST-*`

## 背景

現在 C++ backend のみ 300+ テスト（`test_py2cpp_features.py`）が存在し、他言語は smoke テスト（7〜48 テスト）に留まる。C++ テストの大部分は「Python ソースを変換し、コンパイル + 実行して正しい出力が出るか」という言語非依存のロジックであり、全 backend で共有できる。

## 前提条件（更新 2026-03-23）

- `runtime_parity_check.py` が fixture 対応済み（`--case-root fixture --all-samples`）
- `test/fixtures/` の 128 fixture が全言語の parity check 対象として使用可能
- emitter guide §13 に parity check の正本ツールとして明記済み

## 設計方針（更新）

### 正本ツール

**`tools/runtime_parity_check.py` が全 backend 共通テストの実行基盤** である。pytest ラッパーは作成しない。

```bash
# 全 fixture × 全言語の共通テスト
python3 tools/runtime_parity_check.py \
  --case-root fixture --all-samples \
  --targets cpp,rs,cs,js,ts,go,java,kotlin,swift,ruby,lua,php,scala,nim

# 全 sample × 全言語の parity check
python3 tools/runtime_parity_check.py \
  --case-root sample --all-samples \
  --targets cpp,rs,cs,js,ts,go,java,kotlin,swift,ruby,lua,php,scala,nim
```

### 言語ごとの unsupported feature 管理

`runtime_parity_check.py` に言語ごとの skip リストを追加し、未サポート機能の fixture を宣言的にスキップする。

```python
# runtime_parity_check.py
_LANG_UNSUPPORTED_FIXTURES: dict[str, set[str]] = {
    "zig": {"enum_basic", "dataclass_basic", "match_exhaustive", "try_raise"},
    "lua": {"type_annotation_strict", "enum_basic"},
    ...
}
```

これにより：
- `toolchain_missing`（ツールチェインなし）とは別に `unsupported_feature` カテゴリで skip される
- 各言語の機能対応状況が一覧できる
- 新 fixture 追加時に未対応言語が自動的に skip される

### fixture の分類

`test/fixtures/` の既存 fixture は機能カテゴリ別にサブディレクトリで整理済み：

| サブディレクトリ | ケース数 | カテゴリ |
|---|---|---|
| `core/` | 算術・代入・比較・関数・クラス | 基本機能 |
| `collections/` | list/dict/set 操作・内包表記 | コンテナ |
| `control/` | if/for/while/match/try | 制御フロー |
| `strings/` | 文字列操作 | 文字列 |
| `typing/` | 型注釈・Any・union | 型システム |
| `oop/` | 継承・super・dataclass | OOP |
| `imports/` | import/from-import/alias | モジュール |
| `stdlib/` | math/pathlib/time 等 | 標準ライブラリ |
| `signature/` | 関数シグネチャ・ng_* | 署名チェック |

## 移行計画（更新）

### S1: 共通テスト基盤 — 完了

`runtime_parity_check.py` の `--case-root fixture --all-samples` で 128 fixture を全言語で実行可能。`ng_*` は自動スキップ。

### S2: 言語ごとの unsupported fixture skip 登録

全言語で fixture parity を実行し、失敗を分類：
- transpile_failed → EAST3 / emitter のバグ → issue 起票
- compile_failed → runtime / 生成コードのバグ → issue 起票
- unsupported_feature → `_LANG_UNSUPPORTED_FIXTURES` に登録

### S3: `test_py2cpp_features.py` からの共通テスト分離

C++ 固有テスト（namespace、include path、Object\<T\>、bounds_check_mode 等）のみに絞り、言語非依存テストは fixture + `runtime_parity_check.py` に委譲。

## 非対象

- pytest ラッパーの作成（`runtime_parity_check.py` で十分）
- パフォーマンステスト（`benchmark_sample_cpp_rs.py` が担当）
- selfhost テスト（別テストスイート）

## 受け入れ基準

- [x] `runtime_parity_check.py` で 128 fixture が全言語で実行可能
- [ ] 言語ごとの unsupported fixture が `_LANG_UNSUPPORTED_FIXTURES` で宣言的に管理されている
- [ ] `test_py2cpp_features.py` から共通化済みテストが除去され、C++ 固有テストのみになっている

## 決定ログ

- 2026-03-22: 起票。pytest parametrize + `compile_and_run` ヘルパー方式で計画。
- 2026-03-23: `runtime_parity_check.py` の fixture 対応完了により S1 を代替達成。pytest ラッパーは不要と判断し、`runtime_parity_check.py` を正本として計画を更新。
