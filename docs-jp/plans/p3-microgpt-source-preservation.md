# TASK GROUP: TG-P3-MICROGPT-SOURCE-PRESERVATION

最終更新: 2026-02-23

関連 TODO:
- `docs-jp/todo.md` の `ID: P3-MSP-01`
- `docs-jp/todo.md` の `ID: P3-MSP-02`
- `docs-jp/todo.md` の `ID: P3-MSP-03`

背景:
- `materials/inbox/exec-extracted.log`（2026-02-23 00:03〜00:13）には、`py2cpp` 変換を通すために `microgpt-20260222.py` を段階的に書き換えた履歴が残っている。
- 現在はユーザーが `materials/microgpt/microgpt-20260222.py` を復元済みで、変換用に改変した版は `work/tmp/microgpt-20260222-lite.py` として分離されている。
- `materials/microgpt/microgpt-20260222.py` と `work/tmp/microgpt-20260222-lite.py` の差分は、元ソースの意味変更を含む大規模改変になっている。

抽出した改変項目（ログ + 差分）:
1. 関数シグネチャへ型注釈を追加（無注釈引数拒否を回避）。
2. クラス内 1 行メソッド定義（`def ...: return ...`）を複数行へ展開。
3. トップレベル `for` や多重代入を関数化/単文化して parser 制約を回避。
4. 内包表記・`zip`・generator・`sum(...)`・f-string 書式指定を明示ループへ展開。
5. `random.choices(range(...), weights=[...])` を helper 化して呼び出し形を変更。
6. `open('input.txt')` / `urllib` / `os.path.exists` の I/O 経路を削除し、固定データへ置換。
7. `Value` / autograd / GPT ブロックを含む元アルゴリズムを、軽量な `microgpt-lite` へ再構成。

目的:
- 「変換器都合で元ソースを書き換える」運用を禁止し、必要な対応を parser/emitter/runtime 側タスクへ移す。
- `materials/microgpt/microgpt-20260222.py`（原本）を無改変のまま扱える状態を作る。

対象:
- 変換失敗要因を parser 制約 / emitter lower 不整合 / runtime API 不足へ分類する。
- 原本改変で吸収していた差分を、実装タスクとして再配分する。
- 原本ファイルを入力にした回帰導線（transpile + syntax-check）を整備する。

非対象:
- `microgpt` 学習アルゴリズム自体の最適化。
- `work/tmp/microgpt-20260222-lite.py` の機能拡張。

受け入れ基準:
- 改変項目ごとに「どのレイヤで吸収すべきか」が明文化されている。
- 原本 `materials/microgpt/microgpt-20260222.py` を直接入力したときの失敗原因が再現可能に列挙されている。
- 原本無改変のまま `py2cpp` transpile -> `g++ -fsyntax-only` を通すための実装タスクが TODO 化されている。

決定ログ:
- 2026-02-23: `materials/inbox/exec-extracted.log` と `materials/microgpt/microgpt-20260222.py` vs `work/tmp/microgpt-20260222-lite.py` 差分から、原本改変項目を抽出して本コンテキストを作成。
