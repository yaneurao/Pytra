# P0: backend から runtime module 知識を撤去する

最終更新: 2026-03-07

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01`

背景:
- `spec-runtime` は、backend / emitter が `math`, `gif`, `png` などのモジュール名やライブラリ知識を直書きしてはならないと定めている。
- しかし現状の `src/backends/` には、source-side module 名や runtime helper 名に依存した分岐が複数 backend に残っている。代表例として、`math` import を見て target 固有 built-in へ特別変換する分岐、`pytra.utils.{png,gif}` を見て helper 名へ潰す分岐、`save_gif` の引数構造を emitter 側で特別扱いする分岐がある。
- これは単なる文字列残存ではなく、責務境界の破綻である。module / symbol / signature / semantic tag は EAST3 から linker / runtime symbol index までで決定し、各 backend の CodeEmitter はそれを描画するだけでなければならない。
- linked-program 導入により global optimizer と ProgramWriter の責務整理を進めているが、その後段で backend が source-side module 名に依存したままだと、multi-target の設計負債が残る。

目的:
- backend / emitter から source-side module 名や ad-hoc helper 名に依存した分岐を撤去し、runtime symbol index / semantic tag / resolved runtime call ベースへ統一する。
- `math`, `gif`, `png` など個別ライブラリの知識を emitter から剥がし、target-specific emitter は target-side symbol の描画だけに限定する。
- backend ごとの差分は「target syntax の描画」に閉じ込め、module 解決・runtime helper 選定・ABI adapter 選定は linker / runtime index / lowerer に集約する。

対象:
- `src/backends/**`
- `src/toolchain/frontends/runtime_symbol_index.py`
- `tools/gen_runtime_symbol_index.py`
- 必要に応じて `src/toolchain/ir` の metadata / semantic tag 付与
- representative backend test / tooling test / spec docs

非対象:
- `math/gif/png` 文字列を単純な grep でゼロにすること自体
- 各 target の標準ライブラリ名 (`Math.max`, `scala.math.Pi`, `_G.math.max` など) の表記そのものを禁止すること
- runtime 実装本体の全面刷新
- linked-program / ProgramWriter 導入そのもの

受け入れ基準:
- backend が source-side module 名 (`math`, `pytra.utils`, `pytra.std.*`) を見て lowering 分岐しない。
- backend が `save_gif`, `write_rgb_png`, `pyMath*` など特定 helper の ABI を ad-hoc に解釈しない。
- runtime symbol / semantic tag / import binding 解決は data-driven に行い、backend は解決済み metadata を消費するだけになる。
- representative backend 群で、`math` 定数/関数、`png/gif` 呼び出し、module import / from import の回帰が test で固定される。
- `spec-runtime` / `spec-dev` / 必要な plan docs に、backend で禁止する知識漏れと新しい正規導線が反映される。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 -m unittest discover -s test/unit/tooling -p 'test_runtime_symbol_index.py'`
- `python3 -m unittest discover -s test/unit/common -p 'test_py2x_entrypoints_contract.py'`
- `python3 -m unittest discover -s test/unit/backends -p 'test_*.py' -k runtime`
- `rg -n "owner == \\\"math\\\"|module_id == \\\"math\\\"|module_name == \\\"math\\\"|symbol in \\{\\\"png\\\", \\\"gif\\\"\\}|save_gif|write_rgb_png|pyMath" src/backends`

## 1. 問題の分解

現状の leakage はおおむね次の 4 類型に分かれる。

1. source module 分岐
   - `owner == "math"` や `module_id == "math"` のように module 名で emitter が振る舞いを変える。
2. runtime helper 名分岐
   - `pyMathPi`, `pyMathE`, `save_gif` など特定 helper 名を emitter が知っている。
3. helper ABI 直解釈
   - `save_gif` の引数本数や keyword を emitter が自前で読み替える。
4. import 構築漏れ
   - module object / function import / constant import の解決が未抽象化で、backend が独自補完している。

この 4 類型は別々に見えて、根は同じである。  
runtime module 解決と call lowering の正本が backend 側へ漏れている。

## 2. 目標責務

目標の責務境界は次のとおり。

- EAST / linker / runtime symbol index
  - import binding から canonical runtime module / runtime symbol / semantic tag / ABI adapter 要件を確定する。
- backend lower
  - 上記 metadata を target-independent な call / import / constant node に正規化する。
- backend emitter
  - target syntax を描画する。
  - source module 名や個別 runtime helper の意味は解釈しない。

要するに、emitter は
- 「これは math.sqrt だから特別扱いする」
ではなく
- 「これは resolved runtime call `target_symbol=scala.math.sqrt`, adapter=`float64_args` なので描画する」
だけを行う。

## 3. フェーズ

### Phase 1: 棚卸しと契約固定

- backend ごとの leakage を類型別に棚卸しする。
- `spec-runtime` / `spec-dev` に「backend が解釈してよい metadata」と「解釈してはいけない source knowledge」を明記する。

### Phase 2: data-driven metadata 拡張

- runtime symbol index と import binding 解決 API を拡張し、module function / module constant / helper ABI / semantic tag を backend 外で確定できるようにする。
- `save_gif` / `write_rgb_png` のような ABI 差異は semantic tag or adapter kind として表現し、emitter に helper 固有分岐を残さない。

### Phase 3: emitter family 移行

- 共通 `CodeEmitter` 系 backend から順に移行する。
- target-specific native emitter も、module 名分岐ではなく resolved symbol / adapter を使う形へ寄せる。

### Phase 4: guard と回帰固定

- representative regression を追加し、backend に source module 名分岐が再侵入したときに検知できるようにする。
- grep ベースの粗い監査だけではなく、AST/input -> resolved metadata -> emitted text の contract test を整備する。

## 4. タスク分解

- [ ] [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S1-01] `src/backends/**` の `math/gif/png/save_gif/write_rgb_png/pyMath*` leakage を target 別・類型別に棚卸しし、 plan に記録する。
- [ ] [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S1-02] `spec-runtime` / `spec-dev` に backend 禁止事項と data-driven 正規導線を明文化する。
- [ ] [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S2-01] runtime symbol index / import binding API を拡張し、module import / function import / constant import / semantic tag を backend 外で解決できるようにする。
- [ ] [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S2-02] helper ABI 差異を adapter kind へ正規化し、`save_gif` などの引数規約を emitter 直書きから外す。
- [ ] [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S3-01] C++ / JS / CS / RS など代表 backend を、resolved runtime symbol / adapter 描画へ移行する。
- [ ] [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S3-02] Go / Swift / Kotlin / Java / Scala / Ruby / Lua / PHP / Nim を同じ契約へ追従させる。
- [ ] [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S4-01] representative backend/test/tooling 回帰と guard を追加し、知識漏れの再侵入を防ぐ。
- [ ] [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S4-02] docs 同期と full smoke を実施し、本計画を閉じる。

## 決定ログ

- 2026-03-07: `audit-runtime` 監査として `src/backends/` を `Math|math|gif|png` で棚卸ししたところ、複数 backend に source-side module 名や runtime helper 名への分岐が残っていることを確認した。これは単なる文字列残存ではなく、runtime module 解決責務が emitter へ漏れている設計問題として扱う。
- 2026-03-07: 本計画は linked-program 導入と独立に進めるが、linked-program 側で整理する `resolved metadata` 導線を前提にすると移行が簡単になる。そのため優先度は P0 を維持しつつ、既存の `P0-LINKED-PROGRAM-OPT-01` より後段に置く。
