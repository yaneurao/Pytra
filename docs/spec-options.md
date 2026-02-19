# トランスパイルオプション仕様（案）

この文書は、Pytra のオプション設計を整理するためのドラフトです。  
目的は「Python 互換性」と「生成コード性能」のトレードオフを、利用者が明示的に選べるようにすることです。

## 1. 設計方針

- 既定値は `native` 寄り（性能優先）とする。
- Python 互換性を重視する場合は、`balanced` / `python` プリセットや個別オプションで明示的に opt-in する。
- オプションは段階導入する。
  - Phase 1: `py2cpp.py` 先行
  - Phase 2: 共通 CLI（`src/common/transpile_cli.py`）へ集約
  - Phase 3: LanguageProfile で言語別既定値を切替可能にする

## 2. 実装済みオプション（現状）

`py2cpp.py` で有効:

- `--negative-index-mode {always,const_only,off}`
  - `always`: 負数添字を常に Python 互換で処理
  - `const_only`: 定数負数添字のみ Python 互換（現行デフォルト）
  - `off`: Python 互換処理を行わない
- `--bounds-check-mode {always,debug,off}`
  - `always`: 添字アクセスを常時チェック
  - `debug`: `NDEBUG` 無効時のみチェック
  - `off`: チェックしない（現行デフォルト）
- `--floor-div-mode {python,native}`
  - `python`: `py_floordiv` により Python 準拠
  - `native`: C++ `/` をそのまま利用（現行デフォルト）
- `--mod-mode {python,native}`
  - `python`: `py_mod` により Python 準拠
  - `native`: C++ `%` をそのまま利用（現行デフォルト）
- `--int-width {32,64,bigint}`
  - `32`/`64` は実装済み
  - `bigint` は未実装（指定時はエラー）
- `--str-index-mode {byte,codepoint,native}`
  - `byte`/`native` は利用可能
  - `codepoint` は未実装（指定時はエラー）
- `--str-slice-mode {byte,codepoint}`
  - `byte` は利用可能
  - `codepoint` は未実装（指定時はエラー）
- `--parser-backend {self_hosted,cpython}`
  - EAST 生成バックエンド選択
- `--no-main`
  - `main` 関数を生成しない
- `--dump-deps`
  - 依存情報を出力
- `--preset {native,balanced,python}`
  - 互換性/性能バランスの設定セットを一括適用
  - その後に個別指定したオプションが優先される
- `--dump-options`
  - 解決済みオプションを出力

## 3. 追加候補オプション

### 3.1 互換性/安全性

- `--any-cast-mode {checked,unchecked}`
  - `Any/object` からの取り出しを実行時検証するか

### 3.2 文字列仕様

- `--str-index-mode {byte,codepoint,native}`
  - str型の文字の実体
  - `byte`: 1 byte 単位（高速、現行実装寄り）
  - `codepoint`: Unicode 1 文字単位（Python 互換寄り）
  - `native` : ターゲット言語の string に相当するものを(wrapして)そのまま使う。
- `--str-slice-mode {byte,codepoint}`
  - slice の意味論も同様に揃える

### 3.3 数値仕様

- `--int-width=bigint`
  - 多倍長整数（Python 互換寄り、実装コスト高）
  - 現時点では未実装

### 3.4 生成コード形態

- `--emit-layout {single,split}`
  - `single`: 単一ファイルに変換される。
  - `split`: モジュール分割出力
- `--runtime-linkage {header,static,shared}`
  - ランタイム補助の組み込み形態

## 4. プリセット案

- 方針:
  - デフォルトは `native` 系を選び、C++ 変換時の性能を優先する。
  - 互換性を重視する場合は `python` 系を選ぶ。
  - `--preset` と個別オプションを併用した場合は、個別オプションを優先する。

- `--preset native`（デフォルト候補）
  - `negative-index-mode=off`
  - `bounds-check-mode=off`
  - `floor-div-mode=native`
  - `mod-mode=native`
  - `str-index-mode=native`
  - `str-slice-mode=byte`
  - `int-width=64`

- `--preset balanced`
  - `negative-index-mode=const_only`
  - `bounds-check-mode=debug`
  - `floor-div-mode=python`
  - `mod-mode=python`
  - `str-index-mode=byte`
  - `str-slice-mode=byte`
  - `int-width=64`

- `--preset python`
  - `negative-index-mode=always`
  - `bounds-check-mode=always`
  - `floor-div-mode=python`
  - `mod-mode=python`
  - `str-index-mode=codepoint`
  - `str-slice-mode=codepoint`
  - `int-width=bigint`（実装完了後）


## 5. 導入優先順位（提案）

1. `int-width=bigint` を追加し、整数モデルを明示化
2. `str-index-mode` を導入し、文字列互換性を選択可能化
3. `preset` を追加して運用コストを下げる
4. `int-overflow` 詳細動作や `emit-layout=split` を段階実装

## 6. 補足

- 既存仕様（`docs/spec-dev.md`）との整合が必要なため、導入時は必ず同時更新する。
- 破壊的変更になり得る項目（`int-width`, `str-index-mode`）は、デフォルト変更前に 1 リリース以上の移行期間を設ける。

### 6.1 仕様整合チェック手順

オプションを追加・変更したときは、次を同時に更新する。

1. `docs/spec-options.md`（オプション定義・既定値・preset）
2. `docs/spec-dev.md`（実装仕様と CLI 反映）
3. `docs/spec-east.md`（EAST 側と生成器側の責務境界）
4. `docs/how-to-use.md`（利用例）

更新後は次を確認する。

1. `python src/py2cpp.py INPUT.py --dump-options` の出力が仕様通りであること
2. `test/unit/test_py2cpp_features.py` の該当オプション回帰が通ること
