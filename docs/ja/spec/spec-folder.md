# フォルダ責務マップ仕様（Pytra）

<a href="../../en/spec/spec-folder.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>


このドキュメントは「どのフォルダに何を置くか」を決める責務境界の正本です。  
アルゴリズム詳細は他仕様（`spec-dev.md`, `spec-east.md`, `spec-runtime.md` など）を参照し、本書は配置判断に限定します。

## 1. 適用範囲

- 対象:
  - リポジトリ直下フォルダ
  - `src/` 配下の主要責務境界
  - `docs/ja/todo/` 運用境界
- 非対象:
  - 各機能の詳細実装
  - 言語別サポート粒度の完全表

## 2. リポジトリ直下の責務

### 2.1 `src/`

- 目的: 変換器本体・共通ライブラリ・言語ランタイムの実装を保持する。
- 置くもの:
  - `py2*.py` エントリ
  - `src/toolchain/`（変換プログラム本体）
  - `src/pytra/`（変換時参照ライブラリ正本）
  - `src/runtime/generated/`（`.east` ファイル。言語非依存の中間表現。link 時に各ターゲット言語に変換）
  - `src/runtime/<lang>/`（ターゲット言語固有の手書きランタイムコード。`native/` 階層は廃止済み）
  - 非 C++ / 非 C# backend の checked-in `src/runtime/<lang>/pytra/**` は存在してはならず、再出現は contract fail とする。
  - repo 正本 layout は `src/runtime/<lang>/{generated,native}/` のみを許可する。
  - `src/backends/`
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

### 2.4 `docs/ja/`

- 目的: 仕様・運用・履歴の正本（source of truth）を保持する。
- 置くもの: `spec/`, `spec/archive/`, `plans/`, `todo/`, `language/`, `news/`
- 置かないもの: 実装コード

### 2.5 `docs/en/`

- 目的: `docs/ja/` の英訳ミラーを保持する。
- 置くもの: `docs/ja/` に対応する翻訳
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

### 3.1 `src/toolchain/frontends/` / `src/toolchain/ir/` / `src/toolchain/compiler/`（3層 + 互換）

- 目的: 入力 frontend と IR 段階処理を `toolchain` 配下へ分離し、`compiler` は互換導線へ縮退する。
- 置くもの:
  - `src/toolchain/frontends/`: 入力言語 frontend（例: `transpile_cli.py`, `python_frontend.py`, `east1_build.py`, `signature_registry.py`, `frontend_semantics.py`）
  - `src/toolchain/ir/`: EAST1/2/3 定義・lower・optimizer・pipeline（例: `core.py`, `east1.py`, `east2.py`, `east3.py`, `east3_optimizer.py`）
  - `src/toolchain/compiler/`: 互換 shim / facade（例: 旧 import 経路の受け皿、backend registry）
- 置かないもの:
  - `frontends` / `ir` 側へ移設済みロジックを `compiler` へ戻す新規実装
  - ターゲット言語固有の最終出力分岐
- 依存方向:
  - 正規方向は `toolchain.frontends -> toolchain.ir -> backends`。
  - `backends -> toolchain.frontends` は禁止。
  - `toolchain.compiler -> toolchain.frontends|toolchain.ir` は互換層として許可。
  - 暫定例外として、`toolchain.ir.core` から `toolchain.frontends.signature_registry|frontend_semantics` 参照を許容する（循環解消タスクで撤去予定）。

#### 3.1.1 旧 import 経路の禁止ルール（移行規約）

- 旧経路 `pytra.frontends` / `pytra.ir` / `pytra.compiler` への新規 import 追加は禁止する。
- 正規経路は `toolchain.frontends` / `toolchain.ir` / `toolchain.compiler` とする。
- 旧経路を延命する re-export / alias shim は追加しない（後方互換レイヤは作らない）。
- 既存参照の棚卸し・削除は段階移行で実施し、未移行参照は `rg` 検査で可視化する。
  - 推奨検査: `rg -n "pytra\\.(frontends|ir|compiler)" src tools test`
  - 変換後検査: `rg -n "toolchain\\.(frontends|ir|compiler)" src tools test`

### 3.2 `src/pytra/`（変換時参照ライブラリ）

- 目的: 変換器が参照する Python 名前空間ライブラリ（`pytra.std` / `pytra.utils` / `pytra.built_in`）を保持する。
- 置くもの:
  - `src/pytra/std/`, `src/pytra/utils/`, `src/pytra/built_in/`
- 置かないもの:
  - `frontends` / `ir` / `compiler` の実体実装
  - backend 固有ロジック

### 3.3 `src/backends/`

- 目的: 言語固有の構文差分を吸収する。
- 置くもの: backendごとのhook実装
- 置かないもの: 言語非依存の意味論lowering

#### 3.3.1 backend パイプラインの標準ディレクトリ

- 各 backend の標準構成は `src/backends/<lang>/{lower,optimizer,emitter}/` とする。
- 役割は次で固定する。
  - `lower/`: `EAST3 -> <LangIR>` への言語固有 lowering
  - `optimizer/`: `<LangIR> -> <LangIR>` の言語固有最適化
  - `emitter/`: `<LangIR> -> 最終ソース文字列` の描画
- 新規実装は上記 3 層へ配置し、`emitter/` に意味論 lowering や optimizer 相当ロジックを新規追加しない。
- 既存 backend は段階移行を許容するが、移行時の到達形は同一ディレクトリ規約へそろえる。
- 非C++ backend の 3 層配線・層逆流 import の再発防止チェックは `python3 tools/check_noncpp_east3_contract.py` を正本とする。

#### 3.3.2 追加機能ディレクトリ（案2）と最終到達形（案3）

- 当面の運用は案2（core + extensions）を採用する。
  - core（必須）: `lower/`, `optimizer/`, `emitter/`
  - 拡張（任意）: `extensions/<topic>/`
- `extensions/` 配下の命名は機能名を固定語でそろえる。
  - 例: `extensions/runtime/`, `extensions/packaging/`, `extensions/integration/`
- `header/`, `multifile/`, `runtime_emit/`, `hooks/` など言語ごとの独自名ディレクトリは、新規追加を禁止し、段階的に `extensions/<topic>/` へ寄せる。
- 将来の案3移行では、`src/backends/<lang>/` から段階的に拡張機能を外出しし、最終的に `lower/optimizer/emitter` 中心の構成へ縮退する。

### 3.4 `src/backends/common/profiles/` と `src/backends/<lang>/profiles/`

- 目的: 言語差分設定を宣言的JSONとして保持する。
- 置くもの:
  - 共通既定値: `src/backends/common/profiles/core.json`
  - 言語差分: `src/backends/<lang>/profiles/{profile,types,operators,runtime_calls,syntax}.json`
- 置かないもの: 実行ロジック（Pythonコード）

### 3.5 `src/runtime/`

- 目的: ターゲット言語ランタイム実装を保持する。
- 置くもの: `src/runtime/<lang>/{generated,native}/` 実装（未移行 backend は `pytra-gen/pytra-core` を暫定許容）
- 置かないもの: トランスパイラ本体ロジック

### 3.6 `src/*_module/`（レガシー互換）

- 目的: 旧配置との互換維持
- 置くもの: 既存互換資産のみ
- 置かないもの: 新規実体実装
- 備考: 段階撤去対象。新規は canonical lane（`src/runtime/<lang>/{generated,native}/`）を使用する。

## 4. ドキュメント運用境界

### 4.1 `docs/ja/todo/index.md`

- 目的: 未完了タスクのみを管理する。
- 置くもの: 未完了ID、優先度、最小進捗メモ
- 置かないもの: 完了履歴本文

### 4.2 `docs/ja/todo/archive/`

- 目的: 完了履歴を日付単位で保持する。
- 置くもの: `YYYYMMDD.md`, `index.md`
- 置かないもの: 未完了タスク

### 4.3 `docs/ja/spec/archive/`

- 目的: 退役した旧仕様を日付付きで保管する。
- 置くもの: `YYYYMMDD-<slug>.md`, `index.md`
- 置かないもの: 現行仕様（現行仕様は `docs/ja/spec/` 直下）

## 5. 追加時チェックリスト

新規ファイル追加時は次を満たすこと。

1. 目的が既存フォルダ責務と一致する。
2. 禁止項目（置かないもの）に抵触しない。
3. 依存方向を逆流させない。
4. 責務境界を変える変更なら、本書と関連仕様を同一変更で更新する。

## 6. 関連仕様

- 実装仕様: `docs/ja/spec/spec-dev.md`
- EAST三段構成: `docs/ja/spec/spec-east.md#east-stages`
- EAST移行責務対応: `docs/ja/spec/spec-east.md#east-file-mapping`
- ランタイム仕様: `docs/ja/spec/spec-runtime.md`
- Codex運用: `docs/ja/spec/spec-codex.md`
