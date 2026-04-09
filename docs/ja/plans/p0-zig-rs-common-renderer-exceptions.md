<a href="../../en/plans/p0-zig-rs-common-renderer-exceptions.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0-ZIG-RS-COMMON-RENDERER-EXC: Zig / Rust の `with`・例外 lowering を CommonRenderer へ押し戻す

最終更新: 2026-04-10
ステータス: 進行中

## 背景

- Zig と Rust は target language 側に Python 互換の例外機構がないため、現在の emitter が `raise` / `try` / `with` の意味論を直接抱え込んでいる。
- Zig は exception slot + block escape を emitter が直接生成している。
- Rust は `panic!` / `catch_unwind` / `resume_unwind` を emitter が直接生成している。
- この状態では emitter guide の意図から外れやすく、backend ごとの control-flow runtime が emitter に増殖する。

## 問題設定

いま backend emitter に残っている責務は大きく 3 種類ある。

1. target syntax への写像
2. runtime/mapping に基づく呼び出し解決
3. `with` / `raise` / `try` / handler dispatch / propagation protocol そのものの実装

このうち 3 は emitter の責務として重すぎる。最低でも CommonRenderer + lowering metadata へ押し戻し、backend emitter には target-specific syntax 断片だけを残すべきである。

## 方針

### S1. `with` を CommonRenderer 正本へ戻す

- `with_enter_*` / `with_exit_*` metadata を CommonRenderer の `emit_with_stmt()` が消費する。
- Rust / Zig emitter は `With` 専用の body walk をやめ、必要なら以下の hook だけ override する。
  - context binding の宣言形 (`const` / `var` / `let mut`)
  - same-type bind の扱い
  - finalizer 呼び出しの target syntax
- 複数 item の `with` は CommonRenderer 側で正規化するか、前段 lowering で nested `With` に落とす。

### S2. `try` / `raise` は CommonRenderer の strategy hook に分離する

- CommonRenderer は `Try` / `Raise` の構造を walk する。
- backend は strategy hook で以下だけ返す。
  - raise setup
  - try setup / teardown
  - handler open
  - propagation statement
- Rust の `panic!/catch_unwind`、Zig の exception slot + block escape は hook 実装に閉じ込める。

### S3. profile / metadata で例外 lowering 方針を宣言する

- `lowering.exception_style` を profile で宣言できるようにする。
- 例:
  - `native_throw`
  - `panic_catch_unwind`
  - `manual_exception_slot`
- CommonRenderer は style と metadata を読んで骨格を選ぶ。

### S4. parity で回帰を固定する

- まず fixture の代表ケース:
  - `with_statement`
  - `with_context_manager`
  - `exception_types`
  - `try_raise`
  - `exception_bare_reraise`
- 次に sample / stdlib の重いケースへ広げる。

## 実施順

1. Rust の `with` を CommonRenderer へ戻す
2. Zig の `with` を CommonRenderer へ戻す
3. CommonRenderer に exception strategy hook を追加する
4. Rust の `try/raise` を hook 化する
5. Zig の `try/raise` を hook 化する
6. profile / lint / parity を更新する

## 受け入れ基準

1. Rust / Zig emitter に `With` 専用の full custom lowering が残っていないこと
2. Rust / Zig emitter に `Try` / `Raise` の構造 walk が残っていないこと
3. CommonRenderer が `with` と `try/raise` の骨格を担当していること
4. fixture parity が維持されること

## 進捗メモ

- 2026-04-08: Zig / Rust ともに emitter 側へ `with` / `raise` / `try` の lowering policy が残っていることを確認。特に Rust は `panic!` / `catch_unwind`、Zig は exception slot + block label escape を emitter 本体が直接生成している。最初の slice は Rust の `with` を CommonRenderer に戻すことにする。
- 2026-04-08: `with` は user-defined context manager と `try/raise` の入口まで CommonRenderer へ戻した。次のボトルネックは `TextIOWrapper` 系で、fallback を単純に外すと Rust は `PyFile` 実体と `TextIOWrapper` 宣言型のズレで崩れ、Zig は `with ... as f` の alias hoist が不足して崩れる。S4 は custom lowering の単純削除ではなく、`io` 系 metadata / type lane / alias hoist の整理として進める。
- 2026-04-08: S4 を継続。Rust は `Try` statement entry を CommonRenderer renderer 経由へ切り替え、`catch_unwind` wrapper、`match __try_result` arms、user/string handler chain、no-handler fallback まで hook ベースへ寄せた。未使用の `_emit_try()` は削除済み。
- 2026-04-09: Zig は handler dispatch loop、`try`/`with` body post-stmt propagation、body/orelse wrapper、bare re-raise restore、raise propagation、raise state writes、handler capture を CommonRenderer hook に寄せた。Rust / Zig の emit profile には `exception_style` を実態どおり宣言し、hook 側で style guard も入れた。
- 2026-04-09: S4 をさらに継続。Zig の global exception slot 宣言と slot 名そのものの抽象化は CommonRenderer hook 化済みで、`dict.get(..., default)` の bogus optional unwrap も修正した。現時点の残件は、expression/helper 内に散っている inline exception escape の共通化と、manual exception slot protocol を backend line 単位ではなく profile/strategy 単位へさらに寄せること。
- 2026-04-09: Rust も `__try_*` / `__with_*` / `__catch_*` / `__err_*` の固定 temp 名を CommonRenderer hook 化し、`catch_unwind` wrapper、`resume_unwind`、user-defined exception raise の `panic_any` も hook 経由へ寄せた。Rust emitter に残る panic protocol 文字列は、実質 hook 実装そのものだけになっている。
- 2026-04-09: Rust の `with` custom path も追加で縮小した。hoist 収集、protocol call builder、`Rc<RefCell<...>>` bind/clone 分岐、`__exit__` / `close()` fallback、entry tuple と exit target 選択を CommonRenderer helper に寄せており、残る本体は item loop と Rust 型判定中心になっている。
- 2026-04-09: Zig の expression helper 側も追加で整理した。guarded inline exception block と simple block expression の skeleton を CommonRenderer helper に寄せ、`str.index` / bounds-check index / list concat / list repeat / tuple-list literal / splitext / sum / zip / comprehension / compare callable block まで移行済み。Zig emitter から `render_block_expr_open/close` の直組みは消えている。
- 2026-04-10: Zig の `manual_exception_slot` もさらに薄くした。bound exception value、raise state write、inline exception state、active exception type slot access、handler capture、bare re-raise restore を CommonRenderer の generic builder / helper に寄せ、fallback `with` 側も `__enter__` bind、fallback `__enter__` / `__exit__` / `file_close`、`TextIOWrapper` bind を helper 経由へ統一した。現時点の Zig custom lowering は、主に labeled block / `break :label` といった Zig 構文断片が中心になっている。
- 2026-04-10: Rust の `with` item loop もさらに縮小した。item metadata の bind 名 / enter target / enter/exit metadata 解決、`with_enter_runtime_call`、`Rc<RefCell<...>>` の enter/exit fallback predicate、context capture、bound 変数の新規宣言判定と state registration、bound target naming まで CommonRenderer helper に寄せている。現時点で Rust 側に残るのは、item loop 自体と final emit の接続、そして Rust 型系の最終判断だけである。
- 2026-04-10: 追加で大きめの batch を進めた。Rust は `with` の outer wrapper と hoisted binding 宣言も renderer helper に移し、`With` の direct custom path を削除して renderer entry に一本化した。Zig は naming override 群、stmt renderer 同期、protocol constant、fallback `with` body、handler binding、propagation check、labeled block primitive、`try` wrapper の handler/orelse/finalbody を CommonRenderer helper / accessor 経由へ寄せた。現時点で Zig に残る custom lowering は、manual exception slot を Zig 構文へ写す最終 adapter としての最小限の hook 群が中心である。
- 2026-04-10: S4 終盤の棚卸しを継続。Zig の dispatch condition / handler guard condition / dispatch state stmt / handled mark stmt / propagation check も CommonRenderer に寄せ、冗長な `super()` pass-through override を削除した。Rust 側は `emit_custom_with_stmt()` の orchestration も CommonRenderer へ吸収し、`With` の direct custom path は消えている。現在 Zig emitter に残っている例外系 hook は、slot 名、exception match 条件、labeled block / `break :label`、fallback `with` protocol call、handler prelude/teardown といった Zig 構文 adapter にほぼ限定される。
