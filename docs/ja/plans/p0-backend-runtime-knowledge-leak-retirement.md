# P0: backend から runtime module 知識を撤去する

最終更新: 2026-03-08

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

- [x] [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S1-01] `src/backends/**` の `math/gif/png/save_gif/write_rgb_png/pyMath*` leakage を target 別・類型別に棚卸しし、 plan に記録する。
- [x] [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S1-02] `spec-runtime` / `spec-dev` に backend 禁止事項と data-driven 正規導線を明文化する。
- [x] [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S2-01] runtime symbol index / import binding API を拡張し、module import / function import / constant import / semantic tag を backend 外で解決できるようにする。
- [x] [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S2-02] helper ABI 差異を adapter kind へ正規化し、`save_gif` などの引数規約を emitter 直書きから外す。
- [x] [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S3-01] C++ / JS / CS / RS など代表 backend を、resolved runtime symbol / adapter 描画へ移行する。
- [x] [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S3-02] Go / Swift / Kotlin / Java / Scala / Ruby / Lua / PHP / Nim を同じ契約へ追従させる。
- [ ] [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S4-01] representative backend/test/tooling 回帰と guard を追加し、知識漏れの再侵入を防ぐ。
- [ ] [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S4-02] docs 同期と full smoke を実施し、本計画を閉じる。

## 5. S1-01 棚卸し結果

### 5.1 影響 backend

- 2026-03-08 時点で leakage が確認できた backend は `cpp`, `cs`, `go`, `kotlin`, `lua`, `php`, `rs`, `ruby`, `scala`, `swift` の 10 件。
- 今回の grep / 目視棚卸しでは、`java`, `js`, `nim`, `ts` は同類の direct hit がなく、fail-closed test や source-scan guard が先行している。

### 5.2 類型別 inventory

- `source-module branching`
  - `src/backends/cpp/emitter/cpp_emitter.py:1362` は `owner_name == "math"` を見て数値返り値型を決めている。
  - `src/backends/cs/emitter/cs_emitter.py:449-460` は `module_id == "math"` と `module_id == "pytra.utils" && export_name in {"png","gif"}` を見て alias 先を直決めしている。
  - `src/backends/lua/emitter/lua_native_emitter.py:485-603` は `math` import / from-import と `pytra.utils.{png,gif}` import を emitter 側で module object に再構築している。
  - `src/backends/rs/emitter/rs_emitter.py:1755-1767,1796-1823` は `pytra.utils.{png,gif}` leaf 判定と `module_id == "math"` skip を持つ。
  - `src/backends/scala/emitter/scala_native_emitter.py:833-864` は `module_name == "math"` と helper allowlist で target symbol を決めている。
  - `src/backends/kotlin/emitter/kotlin_native_emitter.py:633-637` と `src/backends/swift/emitter/swift_native_emitter.py:623-627` は `resolved_runtime.endswith(".pi" | ".e")` を見て attribute 描画を変えている。

- `runtime-helper branching`
  - `src/backends/go/emitter/go_native_emitter.py:651-655,788-797` は `pyMathPi` / `pyMathE` / `pyMath*` を helper 名で分岐している。
  - `src/backends/kotlin/emitter/kotlin_native_emitter.py:765-776`、`src/backends/php/emitter/php_native_emitter.py:318-326,681-685`、`src/backends/ruby/emitter/ruby_native_emitter.py:515-518`、`src/backends/swift/emitter/swift_native_emitter.py:742-753` も同様に `pyMath*` helper 名を正本として扱う。
  - `src/backends/scala/emitter/scala_native_emitter.py:863-864,1014-1023,1457-1464,1566-1572` は `scala.math.*` / `scala.math.Pi` / `scala.math.E` を helper/target symbol 名で分岐している。
  - `src/backends/cs/emitter/cs_emitter.py:2469-2474` は `pytra.utils.{png,gif}` leaf から `png_helper` / `gif_helper` 呼び出しを組み立てている。

- `helper-ABI interpretation`
  - `src/backends/go/emitter/go_native_emitter.py:677-711` は `save_gif` の positional arity、既定値、`delay_cs` / `loop` keyword を emitter 側で解釈している。
  - `src/backends/scala/emitter/scala_native_emitter.py:936-964` も `save_gif` の positional/default/keyword ABI を emitter 側で組み替えている。
  - `src/backends/rs/emitter/rs_emitter.py:1761-1767` は image helper 引数の ref adapter を module leaf 判定で適用しており、helper 固有 ABI が emitter に残っている。

- `import-construction leak`
  - `src/backends/go/emitter/go_native_emitter.py:622-635`、`src/backends/kotlin/emitter/kotlin_native_emitter.py:606-616`、`src/backends/php/emitter/php_native_emitter.py:254-267`、`src/backends/ruby/emitter/ruby_native_emitter.py:210-220`、`src/backends/swift/emitter/swift_native_emitter.py:596-606` は dotted runtime 名から `py{Module}{Symbol}` を組み立てている。
  - `src/backends/lua/emitter/lua_native_emitter.py:506-603` は `math` / `pytra.utils.*` import を runtime helper table へ再構築しており、import 解決責務が emitter に漏れている。
  - `src/backends/cs/emitter/cs_emitter.py:446-465` と `src/backends/rs/emitter/rs_emitter.py:1770-1823` も import binding を target import へ直結する前に source-side module 名で前処理している。

### 5.3 representative regression / guard

- 既存の positive/fail-closed 回帰としては、`test/unit/backends/cpp/test_py2cpp_features.py` の `math` import / alias / `png` / `gif`、`test_py2cpp_codegen_issues.py` の `save_gif` keyword order、`test/unit/backends/go/test_py2go_smoke.py` / `kotlin` / `swift` の `pyMath*` routing と source-scan guard、`test/unit/backends/php/test_py2php_smoke.py` と `test/unit/backends/scala/test_py2scala_smoke.py` の `save_gif` default + keyword order が代表ケースになる。
- tooling 側では `test/unit/tooling/test_runtime_symbol_index.py` が `math` / `png` canonical 解決、`test/unit/tooling/test_check_emitter_runtimecall_guardrails.py` が `write_rgb_png` の dispatch-table leakage を検知している。

### 5.4 主要ギャップ

- `Go` と `Scala` は `save_gif` keyword/default を emitter 側で直解釈しており、次フェーズの adapter-kind 正規化対象として最優先。
- `Go` / `Kotlin` / `Swift` は `pyMath*` helper 名依存を guard で抑えたい意図はあるが、実装本体には helper branching が残っている。
- `Java` は source-scan guard が強い一方で unresolved `save_gif` fail-closed が薄い。`JS` / `TS` / `Nim` / `C#` / `Rust` も positive `png/gif` success-path coverage が相対的に薄い。
- tooling には `gif` symbol lookup の direct assert と `pyMath` naming 専用 guard がまだない。

## 決定ログ

- 2026-03-07: `audit-runtime` 監査として `src/backends/` を `Math|math|gif|png` で棚卸ししたところ、複数 backend に source-side module 名や runtime helper 名への分岐が残っていることを確認した。これは単なる文字列残存ではなく、runtime module 解決責務が emitter へ漏れている設計問題として扱う。
- 2026-03-07: 本計画は linked-program 導入と独立に進めるが、linked-program 側で整理する `resolved metadata` 導線を前提にすると移行が簡単になる。そのため優先度は P0 を維持しつつ、既存の `P0-LINKED-PROGRAM-OPT-01` より後段に置く。
- 2026-03-08: [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S1-01] inventory の結果、直接 leakage は 10 backend に残っていた。中でも `Go` / `Scala` の `save_gif` ABI 直解釈、`Lua` / `C#` / `Rust` の source-module import 補完、`Go` / `Kotlin` / `PHP` / `Ruby` / `Swift` / `Scala` の `pyMath*` or `scala.math.*` helper branching を代表退役対象として固定する。
- 2026-03-08: [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S1-02] `spec-runtime` には backend が見てよい runtime metadata と、source import 名 / helper 名 / helper ABI を見てはいけない禁止事項を追記した。`spec-dev` には backend 実装規約として同じ禁止事項を転記し、target helper 名は「描画結果として現れてよいが、分岐条件にしてはならない」と明文化した。
- 2026-03-08: [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S2-01] `runtime_symbol_index` は annotated const (`math.pi`, `math.e`) と symbol-level `semantic_tag` を持つよう拡張し、`resolve_import_binding_doc(...)` で canonical runtime module / resolved binding kind / runtime symbol / semantic tag を返せるようにした。selfhost parser は legacy `meta.import_bindings` を維持したまま、`meta.import_resolution.bindings` にのみ richer metadata を載せるので、既存 backend 互換を壊さず次段の emitter 移行準備ができた。
- 2026-03-08: [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S2-02] `pytra.utils.gif.save_gif` には `image.save_gif.keyword_defaults` adapter kind を symbol metadata / import resolution / call node に通し、Go/Scala emitter は shared `runtime_call_adapters.normalize_rendered_runtime_args(...)` を使うようにした。これで `delay_cs` / `loop` の default と keyword order を emitter 直書きから外し、helper ABI 差異を central helper へ寄せた。
- 2026-03-08: [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S3-01] common `CodeEmitter` に canonical runtime metadata 付き import binding 取得を追加し、`load_import_bindings_from_meta(...)` も `resolved_binding_kind` / `runtime_module_id` / `runtime_symbol` を正本として読むようにした。これで representative backend は source-side `math` / `pytra.utils` 名ではなく、resolved runtime module ベースで import / alias / owner 解決を共有できる。
- 2026-03-08: [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S3-01] `JS` は `import_resolution.bindings` から canonical runtime module path を構築し、`from pytra.utils import gif` を module import として扱えるようにした。`resolved_runtime_call` は semantic tag suffix と照合して fail-closed を維持しつつ許可したので、`math.sqrt` や `gif.save_gif` の resolved runtime path を source module 名分岐なしで描画できる。
- 2026-03-08: [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S3-01] `C#` は canonical runtime module id から alias 先を決める helper へ切り替え、関数/定数 import は expr metadata (`runtime_module_id` / `runtime_symbol`) から `Pytra.CsModule.math.*` / `gif_helper.*` を直接描画するようにした。`Rust` は canonical runtime module id から `use crate::pytra::...` を作るようにし、image helper ref adapter も canonical runtime module 判定で適用する。
- 2026-03-08: [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S3-01] regression として `test_code_emitter.py` に canonical import binding 読み込み、`test_py2js_smoke.py` / `test_py2cs_smoke.py` / `test_py2rs_smoke.py` に runtime import resolution の success-path を追加した。これで `math` module alias、`from math import pi`、`from pytra.utils import gif`、`from pytra.utils.gif import save_gif` の representative route を固定した。
- 2026-03-08: [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S3-02] `Kotlin` / `Swift` / `PHP` / `Ruby` / `Nim` は `pyMath*` helper 名や `owner == "math"` を分岐条件に使う経路をやめ、expr metadata の `runtime_module_id` / `runtime_symbol` から canonical runtime module を見て `math` 定数・関数を描画する形へ揃えた。`Nim` の `sqrt` / `pi` / `e` も source module 名ではなく resolved runtime metadata で lower する。
- 2026-03-08: [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S3-02] `Go` は `pyMathPi` / `pyMathE` / `pyMath*` helper 名依存をやめ、runtime metadata ベースで math route を描画するようにした。`save_gif` の keyword/default ABI は前段 `adapter_kind` 正規化を消費するだけに留め、emitter 側で source module 名を解釈しない形を維持した。
- 2026-03-08: [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S3-02] `Java` は `binding_module.startswith("pytra.utils.")` による utils special-case を廃止し、call expr の canonical runtime module / symbol metadata から class helper を決めるようにした。これで `pytra.utils` leaf 名ではなく resolved runtime binding が正本になった。
- 2026-03-08: [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S3-02] `Scala` は `module_name == "math"` を見た attribute/call/type 推論の special-case をやめ、canonical runtime module `pytra.std.math` と `runtime_symbol` から `scala.math.*` / `scala.math.Pi` / `scala.math.E` を描画するようにした。
- 2026-03-08: [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S3-02] `Lua` の import lowering は `resolve_import_binding_doc(...)` を正本にし、`math` / `json` / `time` / `pathlib` / `pytra.utils` の source import 名を直接分岐しない形へ置き換えた。module import と symbol import は canonical runtime module / symbol から alias line を組み立て、未知 `pytra.*` は fail-closed を維持している。
