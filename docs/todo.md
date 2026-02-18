# TODO（未完了のみ）

## CodeEmitter 化（JSON + Hooks）

作業ルール（step by step）:
- [x] `CodeEmitter` の変更は段階適用し、各ステップで `test/fixtures` の変換可否を確認してから次へ進む。: `tools/check_py2cpp_transpile.py` を追加
- [x] 同じく各ステップで `sample/py` 全件の変換可否を確認してから次へ進む。: `tools/check_py2cpp_transpile.py` を追加
- [x] 回帰が出た場合は次ステップへ進まず、その場で修正してから再確認する。

1. [x] `BaseEmitter` を `CodeEmitter` へ改名し、段階移行する。
   - [x] `src/common/base_emitter.py` を `src/common/code_emitter.py` へ移動する。
   - [x] 互換エイリアス `BaseEmitter = CodeEmitter` を暫定で残す。
   - [x] `src/py2cpp.py` / テスト / ドキュメント参照を `CodeEmitter` 表記へ置換する。
2. [x] 言語差分を `LanguageProfile` JSON に切り出す。
   - [x] `docs/spec-language-profile.md` で JSON スキーマ（v1）とロード順序を確定する。
   - [x] 型マップ（EAST 型 -> ターゲット型）を JSON で定義する。
   - [x] 演算子マップ・予約語・識別子リネーム規則を JSON で定義する。
   - [x] 組み込み関数/メソッドの runtime call map を JSON へ統合する。
3. [x] `CodeEmitter` へ `profile` 注入を実装する。
   - [x] `CodeEmitter(profile, hooks)` の初期化 API を追加する。
   - [x] `cpp_type` / call 解決 / 文テンプレートを profile 参照へ置換する。
   - [x] `src/py2cpp.py` の直書きマップを profile ロードに置換する。
4. [ ] フック注入 (`EmitterHooks`) を実装する。
   - [x] `on_render_call`, `on_render_binop`, `on_emit_stmt` など最小フック面を定義する。
   - [ ] `render_expr(Call/BinOp/Compare)` の巨大分岐を hooks + helper へ段階分離する。: `BinOp` + `Call(Name/Attribute)` は helper 分離済み
   - [ ] `emit_stmt(If/While/For/AnnAssign/AugAssign)` の分岐を hooks + template helper へ段階分離する。: `If/While` は `_emit_if_stmt` / `_emit_while_stmt` へ分離済み
   - [ ] profile で表現しにくいケースのみ hooks 側へ寄せる（`py2cpp.py` に条件分岐を残さない）。
   - [x] C++ 向け hooks 実装を `src/runtime/cpp/hooks/cpp_hooks.py` として分離する。
5. [x] 回帰確認を追加する。
   - [x] `test/unit/test_code_emitter.py` を追加し、profile/hook の境界を検証する。
   - [x] `test/unit/test_py2cpp_features.py` と `test/unit/test_image_runtime_parity.py` を回帰する。
   - [x] selfhost 検証フロー（`tools/prepare_selfhost_source.py`）に新構造を反映する。

## py2cpp 縮退（行数削減）

1. [ ] `src/py2cpp.py` の未移行ロジックを `CodeEmitter` 側へ移し、行数を段階的に削減する。
   - [ ] `render_expr` の `Call` 分岐（builtin/module/method）を機能単位に分割し、`CodeEmitter` helper へ移す。: Name/Attribute 分岐は `_render_call_name_or_attr` へ分離済み
   - [ ] `render_expr` の算術/比較/型変換分岐を独立関数へ分割し、profile/hook 経由で切替可能にする。: `BinOp` は専用 helper に分離済み
   - [ ] `emit_stmt` の制御構文分岐をテンプレート化して `CodeEmitter.syntax_*` へ寄せる。: `If/While` は専用 helper に分離済み
2. [ ] 未使用関数の掃除を継続する。
   - [x] `extract_module_leading_trivia` ラッパーを削除。
   - [x] `_stmt_start_line` / `_stmt_end_line` / `_has_leading_trivia` を削除。
   - [ ] `py2cpp.py` 内の補助関数で参照ゼロのものを追加洗い出しして削除する。

## selfhost 回復（優先）

1. [ ] `CodeEmitter` の `Any/dict` 境界を selfhost で崩れない実装へ段階移行する。
   - [ ] `any_dict_get` / `any_to_dict` / `any_to_list` / `any_to_str` の C++ 生成を確認し、`object.begin/end` 生成を消す。
   - [ ] `render_cond` / `get_expr_type` / `_is_redundant_super_init_call` で `optional<dict>` 混入をなくす。
   - [ ] `test/unit/test_code_emitter.py` に selfhost 境界ケース（`None`, `dict`, `list`, `str`）を追加する。
2. [ ] `cpp_type` と式レンダリングで `object` 退避を最小化する。
   - [ ] `str|None`, `dict|None`, `list|None` の Union 処理を見直し、`std::optional<T>` 優先にする。
   - [ ] `Any -> object` が必要な経路と不要な経路を分離し、`make_object(...)` の過剰挿入を減らす。
   - [ ] `py_dict_get_default` / `dict_get_node` の既定値引数が `object` 必須になる箇所を整理する。
3. [ ] selfhost コンパイルエラーを段階的にゼロ化する。
   - [ ] `selfhost/build.all.log` の先頭 200 行を優先して修正し、`total_errors < 300` にする。
   - [ ] 同手順で `total_errors < 100` まで減らす。
   - [ ] `total_errors = 0` にする。
4. [ ] `selfhost/py2cpp.out` を生成し、最小実行を通す。
   - [ ] `./selfhost/py2cpp.out sample/py/01_mandelbrot.py test/transpile/cpp2/01_mandelbrot.cpp` を成功させる。
   - [ ] 出力された C++ をコンパイル・実行し、Python 実行結果と一致確認する。
5. [ ] selfhost 版と Python 版の変換結果一致検証を自動化する。
   - [ ] 比較対象ケース（`test/fixtures` 代表 + `sample/py` 代表）を決める。
   - [x] `selfhost/py2cpp.out` と `python3 src/py2cpp.py` の出力差分チェックをスクリプト化する。: `tools/check_selfhost_cpp_diff.py`
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
  1. `BaseEmitter`（移行後 `CodeEmitter`）側の `any_*` を明示 `if` へ書き換え、ifexp（三項演算子）由来の不整合を削減する下準備を実施。
  2. `selfhost/py2cpp.py` と `selfhost/runtime/cpp/*` を `src` 最新へ同期済み。
  3. 依然として主因は `object` / `optional<dict>` / `std::any` の境界変換（代入・引数渡し・`py_dict_get_default` 呼び出し）に集中している。
- 更新（2026-02-18 selfhost 追加）:
  1. `tools/prepare_selfhost_source.py` を追加し、`src/common/code_emitter.py` を `selfhost/py2cpp.py` へ自動インライン展開できるようにした。
  2. `python3 src/py2cpp.py selfhost/py2cpp.py -o selfhost/py2cpp.cpp` は再び通過するようになった。
  3. 現在の主因は `Any/object` 境界由来の C++ 型不整合（`selfhost/build.all.log` で `total_errors=538`）。
  4. 先頭エラー群は `CodeEmitter` 基底の `any_dict_get/profile_get/syntax_line` 由来で、selfhost 変換時に `dict` が `object` として扱われる点がボトルネック。
