# TASK GROUP: TG-P2-MICROGPT-COMPAT

最終更新: 2026-02-22

関連 TODO:
- `docs-ja/todo.md` の `ID: P2-MGPT-01`
- `docs-ja/todo.md` の `ID: P2-MGPT-02`
- `docs-ja/todo.md` の `ID: P2-MGPT-03`
- `docs-ja/todo.md` の `ID: P2-MGPT-04`

背景:
- `work/tmp/microgpt-20260222-lite.py` を `python3 src/py2cpp.py ...` で変換すると、self_hosted parser が型注釈なし引数を受理できず停止する。
- 試験的に型注釈付き最小入力で `random.choices` / `random.gauss` / `random.shuffle` を変換すると、生成 C++ は `pytra::std::random::*` 呼び出しを出力するが、`src/runtime/cpp/pytra/std/random.h` に未実装のためコンパイルエラーになる。
- `os.path.exists` は同条件で変換・C++ 構文チェックが通ることを確認済み。

確認コマンド（実行済み）:
- `python3 src/py2cpp.py work/tmp/microgpt-20260222-lite.py -o work/out/microgpt-20260222.cpp`
- `python3 src/py2cpp.py /tmp/pytra_probe_random_choices.py -o work/out/pytra_probe_random_choices.cpp`
- `python3 src/py2cpp.py /tmp/pytra_probe_random_gauss.py -o work/out/pytra_probe_random_gauss.cpp`
- `python3 src/py2cpp.py /tmp/pytra_probe_random_shuffle.py -o work/out/pytra_probe_random_shuffle.cpp`
- `g++ -std=c++20 -I src -I src/runtime/cpp -fsyntax-only work/out/pytra_probe_random_choices.cpp`
- `g++ -std=c++20 -I src -I src/runtime/cpp -fsyntax-only work/out/pytra_probe_random_gauss.cpp`
- `g++ -std=c++20 -I src -I src/runtime/cpp -fsyntax-only work/out/pytra_probe_random_shuffle.cpp`
- `g++ -std=c++20 -I src -I src/runtime/cpp -fsyntax-only work/out/pytra_probe_os_exists.cpp`

目的:
- `microgpt` 相当コードの `py2cpp` 変換可否を、現行仕様（型注釈必須）とのギャップを明示しながら段階的に改善する。

対象:
- self_hosted parser の型注釈要件の扱い整理（仕様維持か機能拡張か）。
- `pytra.std.random` / C++ runtime random の API 拡張。
- `microgpt` 相当入力に対する transpile -> compile の回帰導線整備。

非対象:
- 学習アルゴリズム自体の最適化。
- ネットワークアクセス（`urllib`）の runtime 実装追加。

受け入れ基準:
- 型注釈要件に関する運用方針が仕様として明文化されている。
- `random.choices` / `random.gauss` / `random.shuffle` を使う最小ケースで C++ 構文チェックが通る。
- `microgpt` 相当ケースの変換失敗原因を再現可能に追跡できる（fixture か手順）。
- `work/tmp/microgpt-20260222-lite.py` を `py2cpp.py` で変換し、生成 C++ が `g++ -std=c++20 -I src -I src/runtime/cpp` でコンパイル可能である。

決定ログ:
- 2026-02-22: 初版作成。`microgpt` 変換試験で判明したギャップ（型注釈、random API）を TODO 化。
- 2026-02-22: `P2-MGPT-02` を実装。`src/pytra/std/random.py` へ `choices/gauss/shuffle` を追加し、`--emit-runtime-cpp` で `src/runtime/cpp/pytra/std/random.*` を更新。`choices(population, weights)` 呼び出し互換のため C++ runtime 側に2引数 overload（`choices(population, weights, 1)` へ委譲）を追加し、`shuffle` 宣言を実装シグネチャ（`list<int64>&`）に整合させた。
- 2026-02-22: `P2-MGPT-03` を実装。`test/fixtures/microgpt/microgpt_compat_min.py` を追加し、`test/unit/test_py2cpp_features.py` に transpile -> `g++ -fsyntax-only` 導線（`test_microgpt_compat_min_syntax_check`）を追加した。`microgpt` 本体の未対応要素（型注釈なし引数、`random.choices(range(...), ...)` 経路）とは分離し、型注釈付き最小ケースで回帰検知できる構成を採用。
- 2026-02-22: `P2-MGPT-01` は「型注釈必須の仕様維持」を採用。`src/pytra/compiler/east_parts/core.py` で無注釈引数（`def f(x): ...`）を専用メッセージ（`requires type annotation`）で拒否する分岐を追加し、`test/fixtures/signature/ng_untyped_param.py` + `test/unit/test_self_hosted_signature.py::test_reject_untyped_parameter` で回帰検知を追加した。仕様文書は `docs-ja/spec/spec-user.md` に明文化した。
- 2026-02-22: `P2-MGPT-04` を実装。`work/tmp/microgpt-20260222-lite.py` を self_hosted parser / runtime 制約に合わせて `microgpt-lite` へ再構成し、`random.choices` / `random.gauss` / `random.shuffle` を利用した training/inference 導線を維持。`python3 src/py2cpp.py work/tmp/microgpt-20260222-lite.py -o work/out/microgpt-20260222.cpp` と `g++ -std=c++20 -I src -I src/runtime/cpp -fsyntax-only work/out/microgpt-20260222.cpp` の通過を確認した。
