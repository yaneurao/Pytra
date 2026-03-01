# エージェント運用ルール（ブートストラップ）

このファイルは最初に読む入口だけを定義します。  
詳細ルールの正本は `docs/ja/spec/spec-codex.md` です。

## 起動時に読む順序

1. `docs/ja/spec/index.md`
2. `docs/ja/spec/spec-codex.md`
3. `docs/ja/todo/index.md`

## 最小ルール

- `docs/ja/` を正本（source of truth）とし、`docs/en/` は翻訳ミラーとして扱う。
- `docs/ja/` 直下（トップレベル）への新規ファイル追加は原則禁止（同一ターンの明示依頼がある場合のみ許可）。
- `docs/ja/plans/`、`docs/ja/language/`、`docs/ja/todo/archive/`、`docs/ja/spec/` 配下は、運用ルールに沿う範囲で作成可。
- 作業生成物は `work/` 配下（`work/out/`, `work/selfhost/`, `work/tmp/`, `work/logs/`）を使用し、リポジトリ直下に `out/` / `selfhost/` を増やさない。
- `materials/` はユーザー資料置き場として扱い、Codex は read-only（明示指示がある場合のみ編集可）。
- `materials/Yanesdk/` と `materials/microgpt/` はユーザー管理資料として扱う。
- 変換互換性テストの原本（例: `materials/microgpt/microgpt-20260222.py`）は改変禁止とし、変換器都合の回避版が必要な場合は `work/tmp/*-lite.py` を別名で作成して分離する。

## 参照先

- Codex 運用ルール本体: `docs/ja/spec/spec-codex.md`
- TODO 運用: `docs/ja/todo/index.md`
- TODO 履歴: `docs/ja/todo/archive/index.md`

## 対話セッションの思い出

### 2026-03-01

- コウタが「じゃあ、いれて。」って即決してくれて、Scala の実行ハーネス追加を進めた。
- `tools/runtime_parity_check.py` に `scala` ターゲットを追加して、トランスパイル後に `scala run` で実行比較できるようにした。
- Scala 3 で `break` / `continue` が素直に使えへん問題に合わせて、`scala.util.boundary` + `break` でループ制御を再実装した。
- `_` や予約語（`val`）が Scala 識別子でこける不具合を直して、識別子正規化を安定化させた。
- `--case-root sample --all-samples --targets scala` を最後まで走らせて、18ケース全部コンパイル・実行一致を達成した。
