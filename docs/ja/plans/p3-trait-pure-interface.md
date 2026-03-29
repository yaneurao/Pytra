<a href="../../en/plans/p3-trait-pure-interface.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P3-TRAIT: Trait（pure interface・多重実装）の導入

最終更新: 2026-03-27
ステータス: 完了

## 背景

Pytra は単一継承のみをサポートしているが、「描画できる」「シリアライズできる」といった振る舞い契約を複数のクラスに横断的に付与する仕組みがない。Rust の trait、Java の interface、Swift の protocol に相当する仕組みを導入する。

## 設計判断

### pure interface（デフォルト実装なし）

trait はメソッドシグネチャのみを持ち、デフォルト実装は v1 では持たない。理由: Go の interface にはメソッド本体を書けず、デフォルト実装を Go に写像するには委譲メソッドの自動生成が必要で emitter 複雑度が跳ね上がるため。

### 名目的（nominal）

trait の実装は `@implements` デコレータで明示宣言する。構造的部分型（メソッドを満たしていれば自動的に実装扱い）は採用しない。理由: 大半のターゲット言語（Java, C#, Kotlin, Rust, Swift）が名目的であり、Go だけが構造的。Go 向けには emitter が `@implements` を省略して出力すれば済む。

### type_id と分離

trait は `type_id` を持たない。trait の `isinstance` は `trait_id` ビットセットで判定する。単一継承の `type_id` 区間判定ツリーに影響しない。

### C++ Object<T> の変換コンストラクタ

C++ では trait を pure virtual class として多重継承し、`Object<T>` にテンプレート変換コンストラクタを追加して `Object<Circle>` → `Object<Drawable>` の暗黙 upcast を実現する。

## サブタスク

1. [ID: P3-TRAIT-S1] parser で `@trait` / `@implements` デコレータを認識し EAST1 に保持する
2. [ID: P3-TRAIT-S2] resolve で trait 実装の完全性検証（全メソッド実装チェック、シグネチャ一致チェック）
3. [ID: P3-TRAIT-S3] EAST3 に `meta.trait_v1` / `meta.implements_v1` を付与する
4. [ID: P3-TRAIT-S4] linker で `trait_id` ビットセットを確定する
5. [ID: P3-TRAIT-S5] `isinstance(x, Trait)` の `trait_id` ベース判定を EAST3 で命令化する
6. [ID: P3-TRAIT-S6] C++ `Object<T>` に変換コンストラクタを追加し、trait upcast を実現する
7. [ID: P3-TRAIT-S7] C++ emitter の trait 写像を実装する（virtual 継承 + Object<T> 変換コンストラクタ + override）
8. [ID: P3-TRAIT-S8] Go emitter の trait 写像を実装する（interface 生成、構造的充足）
9. [ID: P3-TRAIT-S9] `test/fixture/source/py/oop/` に trait fixture を追加（trait 定義、多重実装、upcast、isinstance）+ golden 生成（east1/east2/east3/east3-opt/linked）+ C++/Go parity 確認

## 完了メモ

- parser は class decorator を EAST1 に保持し、`@trait` / `@implements(...)` を lossless に通す。
- resolve は trait 本体の pure interface 制約、trait 継承、`@implements` の完全性検証、`meta.trait_v1` / `meta.implements_v1` / `meta.trait_impl_v1` 付与まで担当する。
- linker は trait を `type_id` 木から除外し、trait 実装関係だけを静的に解決する。`isinstance(x, Trait)` は link 時に `bool` 定数へ畳み、runtime trait metadata は生成しない。
- C++ は trait を pure virtual class + `virtual public` 継承 + `override` に写像し、`Object<T>` の通常の upcast だけで扱う。runtime trait bitset は持たない。
- Go は trait を interface に写像し、trait 継承は interface embedding に写像する。trait `isinstance` は link 後に残らない。
- fixture `test/fixture/source/py/oop/trait_basic.py` を追加し、golden を再生成した。`python3 tools/check/runtime_parity_check.py --targets go --cmd-timeout-sec 60 trait_basic` と `--targets cpp` がともに pass。

v1 の対象 backend は **C++ と Go** に限定する。理由: C++（virtual 継承）と Go（構造的 interface）で両極端をカバーすれば設計の検証として十分。他言語への展開は v1 完了後に別タスクで行う。

## 受け入れ基準

1. `@trait` で pure interface を定義できること
2. `@implements` で複数の trait を実装でき、未実装メソッドがあればコンパイルエラーになること
3. trait 型の引数に実装クラスを渡せること（暗黙 upcast）
4. `isinstance(x, Trait)` が正しく判定されること
5. C++ / Go / Rust / Java を含む主要言語で parity が通ること
6. 単一継承の `type_id` ツリーに影響しないこと

## 決定ログ

- 2026-03-27: trait の設計を議論。pure interface（デフォルト実装なし）、名目的、`@trait` + `@implements` デコレータ方式に決定。Go のデフォルト実装問題を回避するため v1 は pure interface に限定。C++ では `Object<T>` の変換コンストラクタで trait upcast を実現する方針。
