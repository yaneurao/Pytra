# Boxing/Unboxing 仕様（Any/object 境界）

<a href="../../docs/spec/spec-boxing.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

この文書は、Pytra C++ backend における `Any/object` 境界の boxing/unboxing 契約を定義する。
対象は `make_object(...)`、`obj_to_*`、`py_to_*`、および変換器が生成する `Any/object` 境界コードである。

## 1. 目的

- `Any/object -> 静的型` の変換失敗を「暗黙既定値」ではなく「明示契約」で扱う。
- truthiness / len / str をユーザー定義型まで拡張可能な形に統一する。
- 変換器（`py2cpp.py`）が `Any/object` 境界で同一規則を適用できるようにする。

## 2. 現状の問題

現状 runtime 実装には次の不整合がある。

- 未対応型の boxing が `None`（空 object）へ暗黙フォールバックする。
- `obj_to_int64` / `obj_to_float64` などが変換失敗時に `0` / `0.0` へフォールバックする。
- `py_len(object)` が未対応型で `0` を返すため、型不一致を隠蔽する。
- ユーザー定義型への unboxing API がなく、`py_obj_cast<T>` が散在し失敗契約が統一されていない。
- truthiness が built-in 分岐中心で、ユーザー定義型の拡張点が弱い。

## 3. 設計原則

1. `Any/object` 境界は fail-fast を基本とする。
2. 静的型が確定している経路では、従来どおり直接コード生成を優先する。
3. 暗黙変換ヘルパは互換目的で残してもよいが、新規生成コードでは使わない。
4. 失敗時挙動は「空値返却 API（try）」と「例外送出 API（or_raise）」で明示する。

## 4. Runtime 契約

### 4.1 Truthiness

- `PyObj` に `virtual bool py_truthy() const` を追加する。
- 既定実装は `true`。
- `obj_to_bool(const object&)` は次で統一する。
1. `null` なら `false`
2. それ以外は `v->py_truthy()`

built-in の標準実装:
- bool: 値
- int/float: 0 判定
- str/list/dict: empty 判定

### 4.2 len / str hook

- `PyObj` に次の拡張フックを追加する。
1. `virtual ::std::optional<int64> py_try_len() const`
2. `virtual str py_str() const`

規約:
- `py_len(object)` は `py_try_len()` が空の場合に `runtime_error`（将来 TypeError 相当）を送出する。
- `0` への暗黙フォールバックは行わない。
- `obj_to_str(object)` は `py_str()` を優先し、未実装時のみ既存既定表現へフォールバックする。

### 4.3 ユーザー定義型 unboxing

runtime に次を追加する。

- `template<class T> rc<T> obj_to_rc(const object& v)`
- `template<class T> rc<T> obj_to_rc_or_raise(const object& v, const char* ctx)`

契約:
- `obj_to_rc`: 失敗時に空 `rc<T>`
- `obj_to_rc_or_raise`: 失敗時に `runtime_error`

### 4.4 数値/文字列変換の厳格 API

`obj_to_int64` / `obj_to_float64` / `obj_to_str` には厳格 API を追加する。

- `obj_to_int64_or_raise`
- `obj_to_float64_or_raise`
- `obj_to_str_or_raise`（必要時）

既存の緩い API（失敗時 `0`/`0.0` など）は互換目的で当面維持するが、新規コード生成の既定にはしない。

## 5. 変換器（py2cpp）規則

`Any/object` 境界でのみ次を適用する。

- `Any/object -> ref class` 代入/return/引数: `obj_to_rc_or_raise<T>(..., "<context>")`
- optional 許容経路: `obj_to_rc<T>(...)`
- `if x:` の動的経路: `obj_to_bool(x)`（`py_truthy` 経由）
- `len(x)` の動的経路: `py_len(x)`（未対応型はエラー）

禁止事項:
- 変換器が `py_obj_cast<T>(...)->...` を直接生成して null/type 不一致を無視すること。

## 6. Dispatch 方針（多言語）

`spec-iterable.md` と同一のオプションで dispatch 方式を一括切替する。

- `--object-dispatch-mode {type_id,native}`
- 既定値: `native`

モード定義:

- `type_id`:
1. `Any/object` 境界の dispatch を全面的に `type_id` で行う。
2. Boxing/Unboxing、`bool/len/str`（および iterable を含む境界処理）を同一方式で解決する。
3. 名目的型判定は `spec-type_id` で定義した `py_is_subtype` / `py_isinstance` / `py_issubclass` 契約に従う。
4. JS/TS でも minify 有無に関わらず `type_id` dispatch を使う。
- `native`:
1. `type_id` dispatch を一切使わない。
2. C++ は `virtual` hook（必要時 `dynamic_cast`）で解決する。
3. `isinstance` / `issubclass` は target 固有機構で解決するが、`spec-type_id` と同じ観測結果を満たす。
4. JS/TS は言語ネイティブ機構で解決し、名前文字列依存 dispatch（`constructor.name` など）は禁止する。

禁止事項:

- 一部機能のみ `type_id`、他機能は `native` の混在（hybrid 運用）。

共通要件:
- `Any/object` 境界の `bool/len/str` はターゲット間で同じ失敗契約を持つ。
- 同一入力で決定的な dispatch（再現可能な挙動）を維持する。
- `meta.dispatch_mode` はルートスキーマ入力をそのまま使い、backend/hook で再決定しない。
- dispatch mode の意味論適用点は `EAST2 -> EAST3` の lowering 1 回に限定する。

## 7. 段階導入

1. Phase 1: runtime に `py_truthy` / `py_try_len` / `obj_to_rc(_or_raise)` / 厳格変換 API を追加。
2. Phase 2: `py2cpp.py` の `Any/object` 境界生成を新 API に切替。
3. Phase 3: 既存の `py_obj_cast<T>` 直書き経路を縮退。
4. Phase 4: `--object-dispatch-mode` を含む dispatch 契約を全ターゲットへ展開。

## 8. 受け入れ基準

- `Any/object -> ref class` が成功/失敗とも仕様どおり動作する。
- 失敗が `0` / `false` / `None` に暗黙吸収される経路が新規生成コードに残らない。
- `if x:` でユーザー定義 `__bool__` / `__len__`（または対応 hook）が反映される。
- `len(x)` は未対応型でエラーになり、`0` へ黙って落ちない。
- `--object-dispatch-mode=type_id` / `native` のどちらでも仕様どおりの境界挙動を維持する。
- selfhost/transpile 既存導線で致命回帰を起こさない。

## 9. テスト観点

- runtime unit:
1. `obj_to_rc` / `obj_to_rc_or_raise` 成功/失敗
2. `obj_to_bool` の built-in + ユーザー定義型
3. `py_len(object)` 未対応型でのエラー
4. 厳格 API の失敗時例外

- py2cpp feature:
1. `Any` を経由したユーザー定義型代入/return/引数
2. `if x:` / `len(x)` の境界挙動
3. 静的型確定経路で過剰な dynamic dispatch を増やさないこと

## 10. 関連

- `docs-ja/spec/spec-east.md`
- `docs-ja/spec/spec-linker.md`
- `docs-ja/spec/spec-type_id.md`
- `docs-ja/spec/spec-iterable.md`
- `docs-ja/spec/spec-dev.md`
- `docs-ja/spec/spec-runtime.md`
- `docs-ja/plans/p2-any-object-boundary.md`
- `docs-ja/plans/p3-microgpt-source-preservation.md`
