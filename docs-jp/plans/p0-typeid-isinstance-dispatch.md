# P0 type_id 継承判定・isinstance 統一（最優先）

ID: `TG-P0-TYPEID-ISINSTANCE`

## 背景

- 現状の `isinstance` は target ごとに部分実装で、C++ は built-in 判定の組み合わせ、JS/TS は `pyTypeId` があっても継承判定 API が不足している。
- その結果、個別ケースのハードコード（`py_is_*` 分岐、言語別特例）が増えやすく、拡張時の保守コストが高い。
- ユーザー定義型・派生関係を跨ぐ共通判定基盤がないと、全言語 selfhost の足場が弱い。

## 目的

- `type_id` を使った `isinstance`/派生判定の共通契約を runtime と codegen で統一する。
- target 固有の場当たり分岐を縮退し、共通 API へ寄せる。
- `Any/object` 境界の型判定を再現可能・拡張可能な実装へ移行する。

## 非対象

- Python 完全互換（`abc` や metaclass を含む全型システム）を一度に達成すること。
- 既存全 runtime API の一括刷新。

## 実施項目

1. 共通判定 API を定義する（例: `py_isinstance(obj, type_id)` / `py_is_subtype(actual, expected)`）。
2. C++ runtime で `type_id` と派生関係テーブル（または同等機構）を実装する。
3. JS/TS runtime で `type_id` モード時の同等 API を実装し、継承判定を可能にする。
4. `py2cpp`（必要に応じて他言語 emitter）で `isinstance` lower を新 API 経由へ切り替える。
5. built-in 直書き分岐を段階縮退し、回帰テストで固定する。

## 受け入れ基準

- `isinstance(x, T)` が `type_id` ベースでユーザー定義型/派生型まで判定できる。
- `type_id` モードで C++ と JS/TS の判定結果が一致する。
- `py2cpp.py` の `isinstance` 特例分岐が縮退し、runtime API 経由へ集約される。
- 既存 selfhost/transpile 導線で致命回帰がない。

## 決定ログ

- 2026-02-23: 「場当たり分岐を増やさないため、`type_id` 派生判定を最優先で進める」方針を確定し、`P0-TID-01` を追加。
- 2026-02-23: Phase 1 として C++/JS/TS runtime に共通 API（`py_is_subtype` / `py_isinstance` 系）を導入し、`py2cpp` の `isinstance` lower は built-in 判定関数直呼びから `py_isinstance(..., <type_id>)` へ移行する。C++ の GC 管理クラスには `PYTRA_TYPE_ID` と constructor 内 `set_type_id(...)` を付与する。
- 2026-02-23: `py2cpp` の class storage hint 伝播は「base->child」だけでなく「ref child->base」も含める。これにより `ref` 子クラスを持つ親クラスでも `PYTRA_TYPE_ID` が定義され、`isinstance(x, Base)` の lower を `py_isinstance(x, Base::PYTRA_TYPE_ID)` で統一できる。
