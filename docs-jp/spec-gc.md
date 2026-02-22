# GCの仕様について

<a href="../docs/spec-gc.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>


PythonからC++のコードに変換するときに、メモリ管理が必要となる。
本プロジェクトでは **参照カウント（RC: Reference Counting）方式** を採用する。

## 前提条件

- マルチスレッド対応は必須。
- 循環参照は禁止（言語仕様として禁止）。
- 弱参照はサポートしない。
- `__del__` はサポートしない。

## 採用方式

- 管理方式は **RCのみ**（tracing GCは採用しない）。
- 各ヒープオブジェクトは `ref_count` を持つ。
- `ref_count` が 0 になった時点で直ちに解放する。

## オブジェクトモデル

- GC対象は参照型オブジェクト（文字列、リスト、辞書、クラスインスタンス等）。
- 値型（`int`、`double`、`bool` など）はRC対象外。
- すべての参照型は共通ヘッダを持つ。
  - `std::atomic<uint32_t> ref_count`
  - `type_id`（デバッグ・型判定用）

## 基本操作

- `incref(obj)`:
  - `obj != nullptr` のとき `ref_count.fetch_add(1, std::memory_order_relaxed)`。
- `decref(obj)`:
  - `obj != nullptr` のとき `old = ref_count.fetch_sub(1, std::memory_order_acq_rel)`。
  - `old == 1` の場合のみ解放処理へ進む。
- 解放時:
  - オブジェクトの参照フィールドを順に `decref`（再帰的に解放伝播）。
  - 最後にオブジェクト自身を `delete`。

## 代入とコンテナ更新の規則

- 変数代入 `a = b`:
  1. `tmp = b` を取得
  2. `incref(tmp)`
  3. `old = a`
  4. `a = tmp`
  5. `decref(old)`
- フィールド代入 `obj.x = v`、配列/辞書要素更新も同じ順序を守る。
- 例外経路でも `decref` 漏れが出ないよう、生成コードは同一規則を必ず適用する。

## マルチスレッド仕様

- `ref_count` は `std::atomic` で管理する。
- RC操作（`incref/decref`）はロックなし原子的更新で行う。
- コンテナ内部状態（list/dict）の構造更新は別途ロックで保護する。
- 推奨方針:
  - オブジェクト単位 `std::mutex` または
  - ランタイム層の細粒度ロック（list用、dict用）
- 「参照カウントはatomic」「コンテナ構造はmutex」で責務を分離する。

## 生成コード側API

- `template<class T, class... Args> T* rc_new(Args&&...)`
  - `ref_count = 1` で生成。
- `void incref(PyObj* obj)`
- `void decref(PyObj* obj)`
- `template<class T> class RcHandle`
  - RAIIで `incref/decref` を自動化する補助。

## 禁止事項（トランスパイラで検出）

- 循環参照を作る代入パターンはコンパイルエラーにする。
  - 例: 親子相互参照、自己参照、閉路を作るコンテナ格納。
- 生ポインタの直接保持は禁止し、RC管理型のみ生成コードで扱う。

## デバッグ支援

- デバッグビルドで以下を有効化する。
  - `ref_count` の下限チェック（負方向破壊検知）
  - 二重解放検知
  - シャットダウン時リーク一覧出力

## 非目標（本仕様）

- tracing GC（mark-sweep, generational, incremental）
- 弱参照
- `__del__`
- 循環参照の自動回収
