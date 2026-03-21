# P5: C# multi-module emit parity

最終更新: 2026-03-21

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P5-CS-MULTIMODULE-*`

## 背景

`pytra-cli.py` を compile → link → emit パイプラインに書き換えた際、C++ 以外の backend の build/run ロジックが欠落した。JS/TS/Rust は runtime コピー追加で parity 復旧したが、C# は以下の構造的問題が残っている。

旧 CLI（`make_noncpp_build_plan`）では C# は **単一ファイル emit + 固定 runtime リスト** を `mcs` に渡す方式だったが、EAST linker によるグローバル最適化（モジュール境界を跨いだインライン化・定数伝播・不要コード除去）を活かすには **multi-module emit** が前提となる。

現状の問題:
1. `emit_all_modules` が各モジュールを独立 `.cs` として emit するが、全ファイルに `public static class Program` と `Main` が生成され、一括コンパイル時に重複エラーになる。
2. sub-module の `.cs` が `using time;` 等の短縮名で参照しており、C# の namespace 構造（`Pytra.CsModule`）と合わない。
3. `cs.py` に runtime 生成（`.east` → C# 変換 + native `.cs` コピー）を追加したが、生成される runtime `.cs` も同じ class 名/Main 重複の問題を持つ。
4. `pytra-cli.py` の C# build が `mcs` + `mono` 方式に合っていない（`dotnet-script` になっていた）。

## 対象

- `src/toolchain/emit/cs/emitter/cs_emitter.py` — multi-module emit 対応
- `src/toolchain/emit/cs.py` — runtime 生成の改善
- `src/pytra-cli.py` — C# build/run を `mcs` + `mono` 方式に修正
- `src/toolchain/misc/pytra_cli_profiles.py` — `runner_needs` の整合確認

## 非対象

- C# emitter の機能拡張（新しい構文対応等）
- 他言語 backend の変更
- EAST linker 側の変更

## 受け入れ基準

- [ ] C# multi-module emit で entry module のみ `Main` を持ち、sub-module は `Main` を emit しない。
- [ ] 各 `.cs` のクラス名がモジュール単位でユニークになり、一括コンパイルで名前衝突しない。
- [ ] sub-module 間の `using` / namespace 参照が C# の規約に沿う形で解決できる。
- [ ] runtime の generated `.cs`（`.east` → C# 変換）が `Main` / `Program` 重複なく生成される。
- [ ] `pytra-cli.py --target cs --build --run` が `mcs` + `mono` で動作する。
- [ ] `runtime_parity_check.py --targets cs` で sample/py の全 18 ケースが PASS する。

## 子タスク

1. [ID: P5-CS-MULTIMODULE-01] C# emitter に `emit_main` フラグを追加し、entry module 以外では `Main` を生成しないようにする。各モジュールのクラス名をモジュール ID ベースでユニーク化する。
2. [ID: P5-CS-MULTIMODULE-02] sub-module 間の `using` / namespace 参照を修正する。`using time;` → `using Pytra.CsModule.time;` 等、C# の namespace 規約に合わせる。
3. [ID: P5-CS-MULTIMODULE-03] `cs.py` の `_generate_cs_runtime` / `_strip_main_for_runtime_module` を S1/S2 の修正に合わせて整合させる。
4. [ID: P5-CS-MULTIMODULE-04] `pytra-cli.py` の C# build/run を `mcs` + `mono` 方式に修正する（output-dir 内の全 `.cs` を一括コンパイル）。
5. [ID: P5-CS-MULTIMODULE-05] `runtime_parity_check.py --targets cs` で sample/py の全 18 ケースが PASS することを確認する。

## 決定ログ

- 2026-03-21: JS/TS/Rust の parity 復旧作業中に C# の構造的問題を発見。multi-module emit を維持する方針で P5 として起票。
- 2026-03-21: S1〜S4 実装完了。S5 は 2/18 PASS（17, 18 番）。残り 16 件の内訳:
  - transpile failed (10件): selfhost パーサーの制約（`object receiver attribute/method access is forbidden` 等）。C# emitter 以前の段階で失敗。
  - run failed (6件): emitter が生成する C# コードのコンパイルエラー（`png_helper` / `gif_helper` 参照未解決等）。multi-module emit 基盤とは別の emitter 個別バグ。
  - S5 完了には上流のパーサー制約緩和および emitter の画像 utils 対応が必要。
