# P0 Boxing/Unboxing 境界統一（最優先）

ID: `TG-P0-BOXING`

## 背景

- `docs-jp/spec/spec-boxing.md` で、`Any/object` 境界の新しい契約（fail-fast、`obj_to_rc_or_raise`、`type_id` dispatch）を定義した。
- 現行 C++ runtime には暗黙フォールバック（`0` / `false` / `None`）と `py_obj_cast<T>` 直利用が残り、型不整合が隠蔽される経路がある。
- JS/TS は minify 時に名前情報が変化しうるため、名前依存 dispatch では安定性を保証できない。

## 目的

- `spec-boxing` を実装正本として、`Any/object` 境界の挙動を C++ と他ターゲットで統一する。
- 失敗契約を明示化し、暗黙フォールバック依存の不具合を段階的に解消する。
- この境界整理を最優先で進め、関連タスク（Any/object、multi-language runtime）への波及効果を得る。

## 非対象

- Python 完全互換（例外文言の一致や全挙動一致）を一度に達成すること。
- `std::any` 経路の全面撤廃。
- Boxing 以外の最適化（性能チューニング、コード整形のみの変更）。

## 実施項目

1. C++ runtime に `py_truthy` / `py_try_len` / `obj_to_rc` / `obj_to_rc_or_raise` / `*_or_raise` を導入する。
2. `py2cpp.py` の `Any/object -> ref class` 生成を `obj_to_rc_or_raise` 基本へ切り替える。
3. JS/TS runtime で `type_id` dispatch 強制と名前依存 dispatch 禁止を実装する。
4. 回帰テスト（runtime unit + py2cpp feature + cross-target）を追加する。

## 受け入れ基準

- `Any/object -> ref class` の成功/失敗が契約どおり（失敗は明示）に動作する。
- `if x:` / `len(x)` の動的経路が仕様どおりに動作し、未対応型を黙って `false`/`0` にしない。
- JS/TS で minify 有無に関わらず `bool/len/str` 境界が `type_id` dispatch を通る。
- selfhost/transpile の既存導線で致命回帰がない。

## 決定ログ

- 2026-02-22: `spec-boxing` の実装を TODO 最優先へ昇格。`P0-BOX-01`〜`P0-BOX-04` を追加。
- 2026-02-23: `P0-BOX-01` の初期導入を実施。`gc.h` に `PyObj` hook（`py_truthy` / `py_try_len` / `py_str`）を追加し、`py_runtime.h` に `obj_to_rc(_or_raise)` と `obj_to_*_or_raise` を追加。`py2cpp.py` は class field の Any/unknown receiver fallback を `obj_to_rc_or_raise` 経路へ切替開始（`P0-BOX-02` 継続）。
