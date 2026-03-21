# P2: emitter にターゲット言語の予約語回避を追加

最終更新: 2026-03-21

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-RESERVED-NAME-ESCAPE`

## 背景

Python のユーザー定義識別子（`length`, `type`, `val` 等）がターゲット言語の予約語・組み込み名と衝突し、生成コードがコンパイルエラーになる。

例: sample/16 の `def length(x, y, z)` → Julia では `Base.length` をシャドウしてエラー。

EAST は言語非依存 IR であり、ターゲット言語の予約語を知るべきではない。予約語回避は emitter の責務。

## 設計

`CodeEmitter`（共通基底クラス）に:

- `_reserved_names() -> set[str]`: 各 emitter がオーバーライドしてターゲット言語の予約語 set を返す（基底では空 set）
- `_safe_name(name: str) -> str`: 予約語と衝突したら `name_` にリネーム。`name_` も衝突したら `name__`（再帰）

各 emitter は `_reserved_names()` を実装するだけで済む。`_safe_name` は識別子出力の全箇所で使用する。

### `@extern` 関数
`@extern` 関数はターゲット言語側の手書き実装と名前が一致する必要があるため、リネーム対象外。`@extern` の設計確定後に対応。

## 対象

| ファイル | 変更内容 |
|---|---|
| `src/toolchain/emit/common/emitter/code_emitter.py` | `_reserved_names()` / `_safe_name()` を追加 |
| 各 emitter | `_reserved_names()` をオーバーライドし、識別子出力で `_safe_name()` を使用 |

## 非対象

- `@extern` 関数のリネーム回避（別途対応）
- EAST / linker 側の変更

## 受け入れ基準

- [x] `CodeEmitter` に `_reserved_names()` / `_safe_name()` が実装されている
- [x] Julia emitter が `Base` の組み込み名と衝突する識別子をリネームする
- [x] sample/16 が Julia で正しくコンパイル・実行できる（`length` → `length_`）
- [x] 既存テストがリグレッションしない

## 子タスク

- [ ] [ID: P2-RESERVED-NAME-ESCAPE-01] `CodeEmitter` に `_reserved_names()` / `_safe_name()` を追加する
- [ ] [ID: P2-RESERVED-NAME-ESCAPE-02] Julia emitter に予約語リストを追加し、識別子出力で `_safe_name()` を使用する
- [ ] [ID: P2-RESERVED-NAME-ESCAPE-03] 他の主要 emitter（Dart, Zig, C++）にも予約語リストを追加する
- [ ] [ID: P2-RESERVED-NAME-ESCAPE-04] テスト検証（sample/16 Julia 通過、リグレッションなし）

## 決定ログ

- 2026-03-21: Julia backend で sample/16 が `length` の衝突で FAIL。EAST は言語非依存であるべきなので、予約語回避は emitter の責務と判断。`CodeEmitter` 基底に共通 helper を追加する方針で起票。
