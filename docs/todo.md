# TODO（未完了のみ）

## 画像ランタイム統一（Python正本）

1. [ ] `src/pylib/png.py` を正本として、`py2cpp` 向け C++ 画像ランタイム（`src/runtime/cpp/pylib`）を段階的にトランスパイル生成へ置換する。
   - [x] `py2cpp` に `--no-main` を追加し、ライブラリ変換（`main` なし）を可能にする。
   - [x] self-hosted parser で `0x...` 整数リテラルと `^=` など拡張代入を受理する。
   - [x] self-hosted parser で `with expr as name:` を `Assign + Try(finally close)` へ lower する。
   - [x] `pylib/png.py` 変換結果で残るランタイム依存（`open`, `ValueError`, `to_bytes` など）を C++ ランタイム API へ接続する。
   - [x] 生成結果を `src/runtime/cpp/pylib/png.cpp` へ置換し、既存出力と一致確認する。
2. [ ] `src/pylib/gif.py` を正本として、`py2cpp` 向け C++ 画像ランタイム（`src/runtime/cpp/pylib`）を段階的にトランスパイル生成へ置換する。
   - [x] `_lzw_encode` のネスト関数を除去し、self-hosted parser で変換可能な形へ整理する。
   - [x] `py2cpp --no-main src/pylib/gif.py` で C++ ソース生成できるところまで到達する。
   - [x] 生成結果で残るランタイム依存（`open`, `ValueError`, `to_bytes` など）を C++ ランタイム API へ接続する。
   - [x] 生成結果を `src/runtime/cpp/pylib/gif.cpp` へ置換し、既存出力と一致確認する。
3. [x] 画像一致判定の既定手順を「バイナリ完全一致」へ統一し、`py2cpp` 向けの検証スクリプトを整理する。
   - [x] `pylib` と `runtime/cpp/pylib` の PNG/GIF 出力一致を確認する自動テスト（最小ケース）を追加する。
   - [x] 置換作業中の受け入れ基準を「Python正本と同じ入力で同一出力」へ固定する。
4. [x] 速度がボトルネックになる箇所のみ、`py2cpp` 向け最適化の許容範囲を文書化する。

## import 強化（完了）

1. [x] `from XXX import YYY` / `as` を EAST メタデータと `py2cpp` の両方で解決し、呼び出し先ランタイムへ正しく接続する。
2. [x] `import module as alias` の `module.attr(...)` を alias 解決できるようにする。
3. [x] `from pylib.png import write_rgb_png` / `from pylib.gif import save_gif` / `from math import sqrt` の回帰テストを追加する。
4. [x] `import` 関連の仕様追記（対応範囲・`*` 非対応）を `docs/spec-east.md` / `docs/spec-user.md` / `docs/spec-dev.md` に反映する。

## selfhost 回復（後回し）

1. [ ] `py2cpp.py` の `BaseEmitter` 共通化後、selfhost 生成時に `common.base_emitter` の内容を C++ へ取り込む手順（または inline 展開）を実装する。
2. [ ] `cpp_type` へ `str|None` 等が流入した際の `object` 退避を見直し、不要な `object` 経由変換を減らす。
3. [ ] `selfhost/py2cpp.cpp` の先頭 500 行を重点レビューし、`BaseEmitter` 起点のエラー（型境界）を 0 件にする。
4. [ ] `selfhost/py2cpp.out` を生成する。
5. [ ] `selfhost/py2cpp.out sample/py/01_mandelbrot.py` 実行を通す。
6. [ ] `selfhost/py2cpp.out` 生成結果と `python src/py2cpp.py` 生成結果の一致検証を実施する。

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
  2. `selfhost/py2cpp.py` と `selfhost/runtime/cpp/*` を `src` 最新へ同期済み。
  3. 依然として主因は `object` / `optional<dict>` / `std::any` の境界変換（代入・引数渡し・`py_dict_get_default` 呼び出し）に集中している。
