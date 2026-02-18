# TODO（未完了のみ）

## 画像ランタイム統一（Python正本）

1. [x] `src/pylib/png.py` を正本として、`py2cpp` 向け C++ 画像ランタイム（`src/runtime/cpp/pylib`）を段階的にトランスパイル生成へ置換する。
   - [x] `py2cpp` に `--no-main` を追加し、ライブラリ変換（`main` なし）を可能にする。
   - [x] self-hosted parser で `0x...` 整数リテラルと `^=` など拡張代入を受理する。
   - [x] self-hosted parser で `with expr as name:` を `Assign + Try(finally close)` へ lower する。
   - [x] `pylib/png.py` 変換結果で残るランタイム依存（`open`, `ValueError`, `to_bytes` など）を C++ ランタイム API へ接続する。
   - [x] 生成結果を `src/runtime/cpp/pylib/png.cpp` へ置換し、既存出力と一致確認する。
2. [x] `src/pylib/gif.py` を正本として、`py2cpp` 向け C++ 画像ランタイム（`src/runtime/cpp/pylib`）を段階的にトランスパイル生成へ置換する。
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

## selfhost 回復（優先）

1. [x] `py2cpp.py` の `BaseEmitter` 共通化後、selfhost 生成時に `common.base_emitter` の内容を C++ へ取り込む手順（または inline 展開）を実装する。
   - [x] `tools/prepare_selfhost_source.py` を追加して、`selfhost/py2cpp.py` を自己完結化する。
   - [x] `python3 src/py2cpp.py selfhost/py2cpp.py -o selfhost/py2cpp.cpp` が通る状態に戻す。
2. [ ] `BaseEmitter` の `Any/dict` 境界を selfhost で崩れない実装へ段階移行する。
   - [ ] `any_dict_get` / `any_to_dict` / `any_to_list` / `any_to_str` の C++ 生成を確認し、`object.begin/end` 生成を消す。
   - [ ] `render_cond` / `get_expr_type` / `_is_redundant_super_init_call` で `optional<dict>` 混入をなくす。
   - [ ] `test/unit/test_base_emitter.py` に selfhost 境界ケース（`None`, `dict`, `list`, `str`）を追加する。
3. [ ] `cpp_type` と式レンダリングで `object` 退避を最小化する。
   - [ ] `str|None`, `dict|None`, `list|None` の Union 処理を見直し、`std::optional<T>` 優先にする。
   - [ ] `Any -> object` が必要な経路と不要な経路を分離し、`make_object(...)` の過剰挿入を減らす。
   - [ ] `py_dict_get_default` / `dict_get_node` の既定値引数が `object` 必須になる箇所を整理する。
4. [ ] selfhost コンパイルエラーを段階的にゼロ化する。
   - [ ] `selfhost/build.all.log` の先頭 200 行を優先して修正し、`total_errors < 300` にする。
   - [ ] 同手順で `total_errors < 100` まで減らす。
   - [ ] `total_errors = 0` にする。
5. [ ] `selfhost/py2cpp.out` を生成し、最小実行を通す。
   - [ ] `./selfhost/py2cpp.out sample/py/01_mandelbrot.py test/transpile/cpp2/01_mandelbrot.cpp` を成功させる。
   - [ ] 出力された C++ をコンパイル・実行し、Python 実行結果と一致確認する。
6. [ ] selfhost 版と Python 版の変換結果一致検証を自動化する。
   - [ ] 比較対象ケース（`test/fixtures` 代表 + `sample/py` 代表）を決める。
   - [ ] `selfhost/py2cpp.out` と `python3 src/py2cpp.py` の出力差分チェックをスクリプト化する。
   - [ ] CI 相当手順（ローカル）に組み込む。

## 複数ファイル構成（最終ゴール）

1. [ ] 依存解決フェーズを追加する。
   - [ ] `import` / `from ... import ...` を収集してモジュール依存グラフを作る。
   - [ ] `pylib.*` とユーザーモジュールの探索パス解決（重複・循環検出）を実装する。
   - [ ] 依存グラフを `--dump-deps` などで可視化できるようにする。
2. [ ] モジュール単位 EAST を構築する。
   - [ ] 入口ファイル + 依存モジュールを個別に EAST 化する。
   - [ ] シンボル解決情報（公開関数/クラス、import alias）をモジュールメタへ保持する。
   - [ ] モジュール間で必要な型情報を共有する最小スキーマを定義する。
3. [ ] C++ 出力を複数ファイル化する。
   - [ ] モジュールごとに `.h/.cpp` を生成し、宣言/定義を分離する。
   - [ ] main モジュールから依存モジュールを include/link できるようにする。
   - [ ] ランタイム include/namespace の重複を除去する。
4. [ ] ビルド・実行検証を整備する。
   - [ ] 複数ファイル生成物を一括コンパイルするスクリプトを追加する。
   - [ ] `sample/py` 全件で Python 実行結果との一致確認を自動化する。
   - [ ] 画像生成ケースはバイナリ一致で検証する。
5. [ ] 互換オプションを追加する。
   - [ ] 既定を複数ファイル出力にする。
   - [ ] `--single-file`（仮称）で従来の単一 `.cpp` へ束ねるモードを提供する。
   - [ ] 既存ユーザー向け移行手順を `docs/how-to-use.md` に追記する。

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
- 更新（2026-02-18 selfhost 追加）:
  1. `tools/prepare_selfhost_source.py` を追加し、`src/common/base_emitter.py` を `selfhost/py2cpp.py` へ自動インライン展開できるようにした。
  2. `python3 src/py2cpp.py selfhost/py2cpp.py -o selfhost/py2cpp.cpp` は再び通過するようになった。
  3. 現在の主因は `Any/object` 境界由来の C++ 型不整合（`selfhost/build.all.log` で `total_errors=510`）。
