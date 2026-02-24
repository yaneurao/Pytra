# type_id 仕様（多重継承・判定統一）

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
- MRO の全エッジケースを初回で実装すること。
- 全ターゲット同時一括移行。

## 3. 用語

- `type_id`:
  型を一意に識別する整数 ID。実行中に不変。
- `TypeInfo`:
  `type_id` ごとのメタ情報（基底型、MRO、祖先集合、名前など）。
- `trait_id`:
  振る舞い契約（iterable, truthy, len など）を表す識別子。継承階層とは別軸。

## 4. 基本設計

### 4.1 型階層は多重継承を前提にする

- 各型は `bases: list[type_id]` を持つ（0 個以上）。
- 単一継承は「`bases` の長さが 1」の特例として扱う。
- 継承グラフは DAG でなければならない（循環は禁止）。

### 4.2 `isinstance` と trait 判定を分離する

- `isinstance(x, T)` は名目的型関係（継承）だけで判定する。
- `iterable` / `truthy` / `len` / `str` などは trait/protocol slot で判定する。
- trait を継承判定に混ぜない（実装破綻防止）。

### 4.3 文字列名に依存しない

- 型判定に `constructor.name` や RTTI 名文字列を使わない。
- minify の影響を受ける文字列比較は禁止。

## 5. `TypeInfo` 仕様

各 `type_id` に対して最低限次を持つ。

- `type_id: int`
- `name: str`（ログ/診断用途）
- `bases: list[int]`
- `mro: list[int]`（先頭は自分）
- `ancestor_closure: bitset or sorted_list[int]`（自分を含む）
- `traits: bitset or set[trait_id]`

注:
- `ancestor_closure` は `py_is_subtype` の高速判定用。
- 小規模 runtime では `sorted_list` でもよい。将来 `bitset` へ置換可能。

## 6. MRO と検証

### 6.1 検証規則

- 型登録時に次を検証する。
1. `bases` に未知 `type_id` がないこと
2. 継承循環がないこと
3. 必要なら C3 線形化が成立すること

### 6.2 MRO 生成

- 既定は C3 線形化で `mro` を計算する。
- C3 が成立しない場合は型登録エラーで停止する。

### 6.3 祖先集合生成

- `mro` または基底グラフから `ancestor_closure` を前計算する。
- `ancestor_closure[type_id]` には自身を必ず含む。

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
- `expected_type_id` が未知なら fail-fast（開発時）または `false`（運用時）を選べるようにする。

## 8. 判定アルゴリズム

### 8.1 既定（推奨）

- `ancestor_closure` を使う O(1) 判定。
- 例: `return ancestor_closure[actual].contains(expected);`

### 8.2 フォールバック

- `mro` 線形走査（O(depth)）でもよい。
- 実装初期はフォールバックで開始し、後で `bitset` に移行可能。

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
- runtime に `TypeInfo` テーブルを保持する。
- `py_is_subtype` は `ancestor_closure`（または `mro`）で判定する。

### 10.2 JS/TS

- 各 object は `pyTypeId`（`symbol` キー推奨）を保持する。
- minify 対応のため判定は `type_id` のみで行う。
- `constructor.name` などの文字列判定を禁止する。

### 10.3 Rust

- runtime で `type_id` と `TypeInfo` を持つ。
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
2. 多重継承: `class C(A, B)` で双方の祖先判定が真。
3. 菱形継承: C3 MRO が成立し、重複祖先を正しく扱う。
4. 非継承型: 偽判定になる。
5. JS/TS minify 想定: 型名変更後も `type_id` 判定結果が不変。
6. trait 分離: `iterable` 実装の有無が `isinstance` 結果に影響しない。

## 13. 段階導入

1. `TypeInfo` と `py_is_subtype` を runtime へ導入。
2. `py_isinstance` / `py_issubclass` を runtime API へ集約。
3. `py2cpp` など各 emitter の `isinstance` lower を切替。
4. built-in 直書き判定を削減。
5. クロスターゲット回帰テストを固定。

## 14. 関連

- `docs-ja/spec/spec-east.md`
- `docs-ja/spec/spec-linker.md`
- `docs-ja/spec/spec-dev.md`
- `docs-ja/spec/spec-boxing.md`
- `docs-ja/spec/spec-iterable.md`
- `docs-ja/plans/p0-typeid-isinstance-dispatch.md`
