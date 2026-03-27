<a href="../../en/plans/p7-east3-default-arg-expansion.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P7: EAST3 lowering でデフォルト引数を呼び出し側に展開

最終更新: 2026-03-22

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P7-DEFAULT-ARG-EXPANSION`

## 背景

Python ではデフォルト引数を省略して関数を呼べる:

```python
def save_gif(path, w, h, frames, palette, delay_cs=4, loop=0): ...
save_gif(path, w, h, frames, palette)  # delay_cs=4, loop=0 は省略
```

EAST3 はこの呼び出しを 5 引数のまま出力するため、全 emitter がデフォルト値を補完する必要がある。EAST3 lowering で `arg_defaults` を参照して省略された引数を call site に展開すれば、emitter は何もしなくてよい。

## 設計

EAST3 lowering の Call ノード処理で:
1. callee の FunctionDef を参照し、`arg_defaults` を取得
2. 呼び出し側の引数数が仮引数数より少ない場合、不足分をデフォルト値で補完
3. 補完後の Call ノードは全引数を明示的に持つ

## 対象

- `src/toolchain/compile/east2_to_east3_lowering.py` または新規パス

## 子タスク

- [ ] [ID: P7-DEFAULT-ARG-EXPANSION-01] EAST3 lowering で省略されたデフォルト引数を call site に展開する
- [ ] [ID: P7-DEFAULT-ARG-EXPANSION-02] ユニットテストを追加する

## 決定ログ

- 2026-03-22: Zig 担当が save_gif 呼び出しでデフォルト引数が展開されない問題を報告。全 backend 共通の改善として起票。
