<a href="../../en/plans/p2-runtime-sot-linked-program-integration.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P2案: runtime SoT を linked program へ統合する

最終更新: 2026-03-07

関連:
- [p0-linked-program-global-optimizer-and-program-writer.md](./p0-linked-program-global-optimizer-and-program-writer.md)
- [p1-runtime-abi-decorator-for-generated-helpers.md](./p1-runtime-abi-decorator-for-generated-helpers.md)
- [p1-cpp-py-runtime-core-slimming.md](./p1-cpp-py-runtime-core-slimming.md)

注記:

- この文書は未スケジュールの構想メモであり、現時点では `docs/ja/todo/index.md` へは積まない。
- 目的は「あとで文脈を忘れないこと」であり、直ちに着手することではない。

背景:
- 現在の runtime SoT（`src/pytra/built_in/*.py`, `src/pytra/std/*.py`, `src/pytra/utils/*.py`）は、主に事前生成 artifact として各 target runtime へ落とし込まれる。
- この方式では、generated helper も user program とは別境界になるため、C++ のように internal 表現が ref-first な backend では helper 境界に固定 ABI を与える必要が出る。`@abi` はそのための実務的な解である。
- しかし、より本質的には、pure Python で書かれた runtime helper を linked program の一部として普通の module と同じように取り込み、global optimizer が user code と一緒に解析・最適化できる方が自然である。
- そうなれば、`str.join` のような helper は external/helper boundary ではなく ordinary function call として扱えるため、`@abi` 依存を大きく減らせる。さらに call graph / SCC / alias / escape / ownership を runtime helper まで含めて解けるため、より積極的な最適化も可能になる。

目的:
- pure Python runtime SoT を linked program の module 集合へ統合し、user module と同じ IR/optimizer pipeline に載せられる形を設計する。
- generated runtime helper を「事前生成済みの別 artifact」ではなく「program の一部」として扱える経路を用意する。
- `@abi` を「本命の常設機能」ではなく、「prebuilt runtime を残す期間の移行注釈」へ縮退させる。
- `py_runtime` 縮小や runtime 重複削減を、target-specific ABI wrapper ではなく whole-program 最適化の延長として実現できるようにする。

対象:
- linked-program loader / manifest schema
- runtime module collection / dependency resolution
- linked-program optimizer の解析対象範囲
- backend lower / ProgramWriter の runtime 扱い
- runtime SoT module の build/restart/debug 導線
- docs/spec の責務境界

非対象:
- 今すぐ実装すること
- `@abi` の即時撤去
- native runtime (`native/core`, `native/std`, `native/utils`) の pure Python 化
- OS / SDK / filesystem / regex / image codec など truly native な処理の linked-program 化
- 모든 target を同時に切り替えること

受け入れ基準（将来着手時の目安）:
- runtime SoT の pure Python module を linked program の module として読み込める。
- global optimizer が user module と runtime helper module を同一 call graph / SCC / non-escape / ownership 解析の対象にできる。
- `str.join` など representative helper が pre-generated helper ABI に頼らず ordinary call として最適化できる。
- `@abi` は still useful でもよいが、runtime helper 一般に必須ではなくなる。
- native companion が必要な箇所だけ `@extern` / `native/*` に残り、それ以外は linked runtime module へ寄せられる。

## 1. 問題の本質

現状の runtime 導線は、ざっくり次の二層に分かれている。

1. user program
   - `py2x -> EAST -> linked program -> backend`
2. runtime SoT
   - `emit-runtime-*` や事前生成により、target ごとの artifact として別管理

この分離は packaging には都合がよいが、optimizer 視点では不自然である。

- runtime helper も pure Python で書かれているのに、ordinary call graph に入らない
- runtime helper 呼び出しが artificial boundary になる
- helper ごとの ABI/adapter 設計が必要になる
- user code と runtime helper のあいだで alias / escape / ownership を一貫して解けない

つまり、`@abi` が必要になる理由の一部は「runtime helper を別 artifact として事前に切り出している」ことにある。

## 2. 本命アーキテクチャ

目標は次の形である。

```text
user .py
runtime SoT .py
  -> EAST1/EAST2/EAST3 (per module)
  -> LinkedProgramLoader (user + runtime modules)
  -> LinkedProgramOptimizer
  -> BackendLower/Optimize
  -> ModuleEmitter / ProgramWriter
```

ここで重要なのは、runtime SoT を

- backend にとっての「特別な runtime module」

ではなく

- linked program に含まれる ordinary module

として扱うことである。

## 3. `@abi` との関係

この案では `@abi` は不要になる、というより「必要範囲が大きく縮む」。

### 3.1 不要になりやすいケース

- pure Python runtime helper
- helper 内部の `list/dict/set/bytearray` 引数
- user code から helper への普通の call

これらは program 内 ordinary call になるため、ABI 固定より optimizer 判断を優先できる。

### 3.2 それでも残る可能性があるケース

- prebuilt runtime artifact を配る target
- runtime helper をあえて public helper API として固定したい場合
- backend-only restart/debug 経路で linked runtime を読まない場合
- native companion / external implementation との境界

したがって、`@abi` の位置づけは

- 今: helper ABI を固定するための必要機能
- 将来: prebuilt / external / public helper 境界だけに使う限定機能

へ縮退するのが自然である。

## 4. 期待できる利点

### 4.1 最適化

- runtime helper まで含めた call graph / SCC 構築
- helper をまたぐ non-escape / alias / ownership 判定
- runtime helper の inlining 候補化
- helper 専用 ABI adapter の削減

### 4.2 設計の単純化

- runtime helper を ordinary module として扱える
- `emit-runtime-*` の責務を縮小できる
- helper ABI の例外規則を減らせる
- `py_runtime` から SoT へ戻す対象が明確になる

### 4.3 他言語展開

- C++ だけの問題ではなく、他 target でも runtime helper の special handling を減らせる
- backend ごとの runtime artifact 差分を packaging 層に押し戻せる

## 5. 難所

### 5.1 packaging と ordinary module の両立

runtime helper を ordinary module として optimize しても、最終出力では

- user artifact として出すのか
- bundled runtime として出すのか
- prebuilt として差し替えるのか

を target ごとに決める必要がある。  
つまり、optimizer 統合と packaging 契約は分けて設計しなければならない。

### 5.2 native companion 境界

`native/core` や `native/std/*` のように pure Python では表現しきれない層は残る。  
したがって完全に runtime artifact が不要になるわけではない。

必要なのは次の分離である。

- pure Python runtime helper
  - linked program に統合
- native companion / ABI glue / OS access
  - 既存どおり native runtime に残す

### 5.3 restart/debug 導線

`ir2lang.py` や backend-only restart で、runtime helper module をどう供給するかを決める必要がある。

- linked output に runtime helper も materialize する
- または manifest に runtime module closure を記録する

このどちらかを定義しないと、debug/restart で user module だけを見たときに再現性が壊れる。

### 5.4 bootstrap

selfhost / host 実装の両方で runtime module 取り込みが必要になる。  
import graph が膨らみやすいため、収集対象を

- actually used runtime modules のみに絞るのか
- family ごとにまとめて入れるのか

を決める必要がある。

## 6. 実装に入るなら必要な段階

### Phase 1: runtime module collection 設計

- linked program に runtime SoT module をどう載せるか決める
- manifest 上で runtime module を明示するか、自動収集するか決める
- entry module と runtime module の区別を定義する

### Phase 2: optimizer integration

- global optimizer が runtime helper module も普通に読む
- non-escape / ownership / type_id / call graph に runtime helper を含める
- import-closure 読み込みの残差分と競合しないように整理する

### Phase 3: backend / ProgramWriter integration

- linked runtime module を ordinary module として emit できるようにする
- ただし出力 tree では runtime packaging 方針を適用できるようにする
- prebuilt fallback と coexist できるようにする

### Phase 4: `@abi` の縮退

- linked runtime path では `@abi` を不要化できる helper を洗い出す
- `@abi` を残すケースを external/prebuilt/public helper 境界に限定する

## 7. 実装時の判断ポイント

- runtime SoT module を linked program へ入れる単位は `module` か `symbol closure` か
- runtime helper を user module と同じ namespace / artifact に出すか、runtime artifact として分けるか
- linked runtime module を all target で使うか、まず C++ only で試すか
- `@abi` を optional hint として残すか、linked runtime path では禁止するか

## 8. 先にやるべきこと

この案に本格着手する前に、少なくとも次が必要である。

1. `P0-LINKED-PROGRAM-OPT-01`
   - linked program と ProgramWriter の土台
2. `P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01`
   - backend が runtime module 名を直に見ない形への整理
3. `P1-RUNTIME-ABI-DECORATOR-01`
   - 移行期の helper ABI 固定手段
4. `P2-LINKED-RUNTIME-TEMPLATE-01`
   - linked runtime helper generics の v1 syntax / metadata / validation を `@template("T", ...)` 基準で先に固定する

つまり、この案は本命ではあるが、実装順としては後段である。

## 決定ログ

- 2026-03-07: `@abi` は helper ABI 固定の実務解として必要だが、長期の本命は pure Python runtime SoT を linked program に取り込み、helper を ordinary call として optimize できる形だと判断した。
- 2026-03-07: そのため `@abi` は「恒久的に helper 全般へ付け続ける前提」ではなく、「pre-generated runtime を残す期間や external/public helper 境界のための移行機能」として捉える方針を記録した。
