# TODO（未完了のみ）

## selfhost 回復（分解版）

1. [ ] `py2cpp.py` の `BaseEmitter` 共通化後、selfhost 生成時に `common.base_emitter` の内容を C++ へ取り込む手順（または inline 展開）を実装する。
2. [ ] `cpp_type` へ `str|None` 等が流入した際の `object` 退避を見直し、不要な `object` 経由変換を減らす。
3. [ ] `selfhost/py2cpp.cpp` の先頭 500 行を重点レビューし、`BaseEmitter` 起点のエラー（型境界）を 0 件にする。
4. [ ] `selfhost/py2cpp.out` を生成する。
5. [ ] `selfhost/py2cpp.out sample/py/01_mandelbrot.py` 実行を通す。
6. [ ] `selfhost/py2cpp.out` 生成結果と `python src/py2cpp.py` 生成結果の一致検証を実施する。

## 画像ランタイム統一（Python正本）

1. [ ] `src/pylib/png.py` を正本として、各言語 `*_module` の PNG 実装を段階的にトランスパイル生成へ置換する。
2. [ ] `src/pylib/gif.py` を正本として、各言語 `*_module` の GIF 実装を段階的にトランスパイル生成へ置換する。
3. [ ] 画像一致判定の既定手順を「復号後画素一致」優先へ統一し、言語別の検証スクリプトを整理する。
4. [ ] 速度がボトルネックになる箇所のみ、言語別最適化の許容範囲を文書化する。

## 複数ファイル構成（最終ゴール）

1. [ ] `py2cpp.py` にモジュール依存解決を実装し、`import pylib.png` / `import pylib.gif` をソースとして追跡できるようにする。
2. [ ] Python入力1ファイルから、必要な依存モジュールを含む「複数EAST（モジュール単位）」を構築する。
3. [ ] C++生成を単一 `.cpp` 前提から拡張し、`main` モジュール + 依存モジュールの複数 `.cpp/.h` を出力できるようにする。
4. [ ] ビルド手順を複数ファイル前提で整備し、`sample/py` 全件で Python 実行結果と一致することを確認する。
5. [ ] 互換運用として、必要時のみ単一出力へ束ねるオプションを追加する（既定は複数ファイル構成）。

## 直近メモ

- 進捗: `except ValueError:` 受理と `return`（値なし）受理を self_hosted parser に追加し、EAST 生成は通過。
- 現在の主要原因（2026-02-18 再計測）:
  1. `BaseEmitter.any_dict_get` が `optional<dict>` に対して `.find/.end` を生成してしまう。
  2. `Any -> object` 変換の影響で、`""` / `list{}` / `nullopt` を default 引数に渡す箇所が大量に不整合化している。
  3. `render_expr` 系 API が `dict|None` 固定のため、selfhost 生成側で `object/std::any` から呼び出した時に詰まる。
  4. 方針として selfhost 専用 lowering は極力増やさず、型付き helper と runtime 補助 API の拡充で汎用的に解消する。
- 更新（2026-02-18）:
  1. `BaseEmitter` 側の `any_*` を明示 `if` へ書き換え、ifexp（三項演算子）由来の不整合を削減する下準備を実施。
  2. `selfhost/py2cpp.py` と `selfhost/cpp_module/*` を `src` 最新へ同期済み。
  3. 依然として主因は `object` / `optional<dict>` / `std::any` の境界変換（代入・引数渡し・`py_dict_get_default` 呼び出し）に集中している。
