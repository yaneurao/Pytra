# type_id 仕様（単一継承・区間判定）

<a href="../../docs/spec/spec-type_id.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

この文書は、Pytra における `type_id` の意味・生成規則・判定規則を定義する。
主目的は、`isinstance` / `issubclass` を全ターゲットで同一契約に統一し、場当たり分岐を減らすことである。

## 1. 目的

- `isinstance` / `issubclass` を `type_id` ベースで統一する。
- C++ / JS / TS / Rust などで同一の判定結果を得る。
- minify や型名変換の影響を受けない安定した実行時判定を提供する。
- `iterable` / `truthy` / `len` などの振る舞いを継承判定と分離して管理する。

## 2. 非目標

- CPython の metaclass / ABC / virtual subclass の完全再現。
- 多重継承（複数基底）を一般解としてサポートすること。
- 全ターゲット同時一括移行。

## 3. 用語

- `type_id`:
  型を一意に識別する整数 ID。実行中に不変。
- `TypeInfo`:
  `type_id` ごとのメタ情報（基底型、ID 範囲、名前など）。
- `trait_id`:
  振る舞い契約（iterable, truthy, len など）を表す識別子。継承階層とは別軸。

## 4. 基本設計

### 4.1 型階層は単一継承のみ

- 各型は `base_type_id: int | None` を持つ（0/1 個）。
- 複数基底を要求する定義は実行前にエラーとする。
- 継承は木または森（forest）とみなし、循環は禁止。
- 同一基底配下では後述の `type_id` 範囲が親子関係を完全に表現する。

### 4.2 `isinstance` と trait 判定を分離する

- `isinstance(x, T)` は名目的型関係（継承）だけで判定する。
- `iterable` / `truthy` / `len` / `str` などは trait/protocol slot で判定する。
- trait を継承判定に混ぜない（実装破綻防止）。

### 4.3 文字列名に依存しない

- 型判定に `constructor.name` や RTTI 名文字列を使わない。
- minify の影響を受ける文字列比較は禁止。

## 5. `TypeInfo` 仕様

各 `type_id` は次を持つ。

- `type_id: int`
- `name: str`（ログ/診断用途）
- `base_type_id: int | None`
- `type_id_min: int`
- `type_id_max: int`
- `mro_depth: int`（ルートとの差、任意）
- `traits: bitset | set[trait_id]`

注:
- `type_id_min` / `type_id_max` は祖先関係の O(1) 判定に使う。
- `mro_depth` は最適化やデバッグ補助情報。

## 6. 検証と割り当て

### 6.1 検証規則

- 型登録時に次を検証する。
1. `base_type_id` が未知 `type_id` でないこと。
2. `base_type_id` が自己参照や循環を形成しないこと。
3. 基底定義が単一継承制約を破っていないこと。

### 6.2 `type_id` 範囲割り当て（linker で実施）

- `type_id_min/type_id_max` は `linker`（または同等の決定的フェーズ）でのみ確定する。
- 割り当て順序:
  1. 依存を満たすトポロジカル順（基底->派生）。
  2. 同位相は FQCN の辞書順で決定。
- 割り当て手順:
  - 未訪問のルート型から DFS を開始。
  - `type_id_min = allocator.next()` と採番し、子型を連続して再帰採番。
  - 子をすべて割り当てた後、親を `type_id_max =` 子末尾の ID で確定。
- 成果:
  - 子孫が常に `parent.type_id_min <= child_id <= parent.type_id_max` を満たす。
  - `is_subtype` が区間比較のみで決まる。
- 同一入力・同一オプションなら `type_id_min/max` が決定的であること。

### 6.3 補助的な先祖確認（任意）

- 開発・デバッグ時にのみ、`base_type_id` 追跡または `ancestor_closure` を追加計算して差分監査に使ってよい。
- 本番観測は `type_id_min/max` が真実。

## 7. Runtime API 契約

最低限次の API を全ターゲットで揃える。

- `py_is_subtype(actual_type_id: int, expected_type_id: int) -> bool`
- `py_isinstance(obj: object, expected_type_id: int) -> bool`
- `py_issubclass(actual_type_id: int, expected_type_id: int) -> bool`

適用範囲:
- `--object-dispatch-mode=type_id` では上記 3 API を判定の正規経路として必須化する。
- `--object-dispatch-mode=native` では target 固有機構で同じ観測結果を満たす（必要なら互換 API 層を提供してよい）。

規約:
- `py_isinstance` は `obj.type_id` を取得し `py_is_subtype` を呼ぶだけにする。
- 判定失敗は `false` を返し、例外は投げない。
- `expected_type_id` が未知なら開発時は fail-fast、運用時は `false` を返す。

## 8. 判定アルゴリズム

### 8.1 既定（推奨）

- 区間判定を採用する。
- 例: `return expected_min <= actual_id <= expected_max;`

### 8.2 フォールバック

- 開発時の検証では `base_type_id` 追跡（O(depth)）で同値性を再検証する。
- いずれも `--object-dispatch-mode=type_id` と一致する結果を返すこと。

## 9. ディスパッチモードとの関係

- 共通 CLI: `--object-dispatch-mode {type_id,native}`（既定: `native`）。
- 切替対象は `isinstance` / `issubclass` に加えて、boxing・iterable・`bool/len/str` を含む `Any/object` 境界全体とする。
- `--object-dispatch-mode=type_id`:
  - `Any/object` 境界の `isinstance` / `issubclass` を `type_id` API で判定する。
  - boxing / iterable / truthy などの object 境界処理も同一モードで解決する（個別混在禁止）。
- `--object-dispatch-mode=native`:
  - ターゲット固有のネイティブ機構で解決してよい。
  - ただし名前文字列依存 dispatch は禁止。
- 禁止事項: 一部機能だけ `type_id`、他を `native` にする hybrid 運用。

## 10. ターゲット別要求

### 10.1 C++

- `PyObj` が `type_id` を保持する。
- runtime に `type_id` 範囲テーブル（`name/min/max/traits`）を保持する。
- `py_is_subtype` は `type_id_min/max` で O(1) 判定。

### 10.2 JS/TS

- 各 object は `pyTypeId`（`symbol` キー推奨）を保持する。
- minify 対応のため判定は `type_id` のみで行う。
- `constructor.name` などの文字列判定を禁止する。

### 10.3 Rust

- runtime で `type_id` と範囲判定テーブルを持つ。
- `enum`/`trait` 実装都合に関係なく、外部契約は `py_is_subtype` で固定する。

## 11. Codegen 規約

- 変換器の `isinstance` lower は runtime API 呼び出しへ統一する。
- built-in 特例分岐は段階的に縮退する。
- target 固有最適化を入れても、観測可能な判定結果は API 契約に一致させる。
- `type_id` 判定 lower は原則 `EAST3` で命令化し、backend はその命令を runtime API へ写像するだけにする。
- backend（例: C++ emitter）で `type_id` 判定ロジックを直接文字列生成する経路は、移行期間の互換層を除き禁止する。

EAST3 連携規約:
- `meta.dispatch_mode`（`native | type_id`）はルートスキーマから受け取り、backend/hook で再決定しない。
- dispatch mode の意味論適用点は `EAST2 -> EAST3` の lowering 1 回のみとする。
- `type_id` 判定命令の連結・ID 確定は `spec-linker` の契約に従う。

## 12. テスト観点

1. 単一継承: `A <- B <- C` で `isinstance(C(), A)` が真。
2. 非継承型: 偽判定になる。
3. 多重継承コード（`class C(A, B)`）が生成時エラーになる。
4. 範囲判定同値性: `child.type_id` が `parent.type_id_min <= child <= parent.type_id_max` を満たす。
5. JS/TS minify 想定: 型名変更後も `type_id` 判定結果が不変。
6. trait 分離: `iterable` 実装の有無が `isinstance` 結果に影響しない。

## 13. 段階導入

1. `TypeInfo`（単一継承 + 区間）を runtime へ導入。
2. `py_isinstance` / `py_issubclass` を runtime API へ集約。
3. linker で `type_id_min/max` の決定的生成を確立。
4. built-in 直書き判定を縮退し、`isinstance` を runtime API 経由へ一本化。
5. クロスターゲット回帰テスト（対象言語一括）を固定。

## 14. 関連

- `docs-ja/spec/spec-east.md`
- `docs-ja/spec/spec-linker.md`
- `docs-ja/spec/spec-dev.md`
- `docs-ja/spec/spec-boxing.md`
- `docs-ja/spec/spec-iterable.md`
- `docs-ja/plans/p0-typeid-isinstance-dispatch.md`
