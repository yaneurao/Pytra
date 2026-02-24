# フォルダ責務マップ仕様（Pytra）

<a href="../../docs/spec/spec-folder.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>


このドキュメントは「どのフォルダに何を置くか」を決める責務境界の正本です。  
アルゴリズム詳細は他仕様（`spec-dev.md`, `spec-east.md`, `spec-runtime.md` など）を参照し、本書は配置判断に限定します。

## 1. 適用範囲

- 対象:
  - リポジトリ直下フォルダ
  - `src/` 配下の主要責務境界
  - `docs-ja/todo/` 運用境界
- 非対象:
  - 各機能の詳細実装
  - 言語別サポート粒度の完全表

## 2. リポジトリ直下の責務

### 2.1 `src/`

- 目的: 変換器本体・共通ライブラリ・言語ランタイムの実装を保持する。
- 置くもの:
  - `py2*.py` エントリ
  - `src/pytra/`（共通Python正本）
  - `src/runtime/<lang>/pytra/`（ターゲット言語ランタイム）
  - `src/hooks/`, `src/profiles/`
- 置かないもの:
  - 運用ログ、検証一時生成物、手順ドキュメント

### 2.2 `test/`

- 目的: 回帰テストと検証用fixtureを保持する。
- 置くもの: unit/integration、fixture、検証補助
- 置かないもの: 本番実装コード

### 2.3 `sample/`

- 目的: 公開サンプル入力・出力・成果物比較導線を提供する。
- 置くもの: `sample/py`, `sample/<lang>`, `sample/images`, `sample/golden`
- 置かないもの: 開発中の未整理実験コード

### 2.4 `docs-ja/`

- 目的: 仕様・運用・履歴の正本（source of truth）を保持する。
- 置くもの: `spec/`, `spec/archive/`, `plans/`, `todo/`, `language/`, `news/`
- 置かないもの: 実装コード

### 2.5 `docs/`

- 目的: `docs-ja/` の英訳ミラーを保持する。
- 置くもの: `docs-ja/` に対応する翻訳
- 置かないもの: 日本語正本への先行変更

### 2.6 `materials/`

- 目的: ユーザー提供資料・参照データを保持する。
- 置くもの: `materials/refs/`, `materials/inbox/`, `materials/archive/`
- 置かないもの: 変換器都合で改変した原本

### 2.7 `work/`

- 目的: Codex 作業用の一時領域を隔離する。
- 置くもの: `work/out/`, `work/selfhost/`, `work/tmp/`, `work/logs/`
- 置かないもの: 正本データ

### 2.8 `out/`, `selfhost/`, `archive/`（互換運用）

- 目的: 既存運用の互換維持（段階整理対象）。
- 置くもの: 既存スクリプトが出力する成果物
- 置かないもの: 新規運用の恒久保存先
- 備考: 新規の一時出力は `work/` を優先する。

## 3. `src/` 配下の責務

### 3.1 `src/pytra/compiler/east_parts/`

- 目的: EAST1/EAST2/EAST3 の段階処理と共通エミッタ基盤を提供する。
- 置くもの:
  - `east1.py`, `east2.py`, `east3.py`, `east3_lowering.py`
  - `east_io.py`, `core.py`, `code_emitter.py`
- 置かないもの:
  - ターゲット言語固有の最終出力分岐
- 依存方向:
  - `pytra.*` 共通層への依存を許可
  - `hooks/<lang>` への直接依存は原則禁止

### 3.2 `src/hooks/`

- 目的: 言語固有の構文差分を吸収する。
- 置くもの: backendごとのhook実装
- 置かないもの: 言語非依存の意味論lowering

### 3.3 `src/profiles/`

- 目的: 言語差分設定を宣言的JSONとして保持する。
- 置くもの: `types/operators/runtime_calls/syntax` マップ
- 置かないもの: 実行ロジック（Pythonコード）

### 3.4 `src/runtime/`

- 目的: ターゲット言語ランタイム実装を保持する。
- 置くもの: `src/runtime/<lang>/pytra/` 実装
- 置かないもの: トランスパイラ本体ロジック

### 3.5 `src/*_module/`（レガシー互換）

- 目的: 旧配置との互換維持
- 置くもの: 既存互換資産のみ
- 置かないもの: 新規実体実装
- 備考: 段階撤去対象。新規は `src/runtime/<lang>/pytra/` を使用する。

## 4. ドキュメント運用境界

### 4.1 `docs-ja/todo/index.md`

- 目的: 未完了タスクのみを管理する。
- 置くもの: 未完了ID、優先度、最小進捗メモ
- 置かないもの: 完了履歴本文

### 4.2 `docs-ja/todo/archive/`

- 目的: 完了履歴を日付単位で保持する。
- 置くもの: `YYYYMMDD.md`, `index.md`
- 置かないもの: 未完了タスク

### 4.3 `docs-ja/spec/archive/`

- 目的: 退役した旧仕様を日付付きで保管する。
- 置くもの: `YYYYMMDD-<slug>.md`, `index.md`
- 置かないもの: 現行仕様（現行仕様は `docs-ja/spec/` 直下）

## 5. 追加時チェックリスト

新規ファイル追加時は次を満たすこと。

1. 目的が既存フォルダ責務と一致する。
2. 禁止項目（置かないもの）に抵触しない。
3. 依存方向を逆流させない。
4. 責務境界を変える変更なら、本書と関連仕様を同一変更で更新する。

## 6. 関連仕様

- 実装仕様: `docs-ja/spec/spec-dev.md`
- EAST三段構成: `docs-ja/spec/spec-east.md#east-stages`
- EAST移行責務対応: `docs-ja/spec/spec-east.md#east-file-mapping`
- ランタイム仕様: `docs-ja/spec/spec-runtime.md`
- Codex運用: `docs-ja/spec/spec-codex.md`
