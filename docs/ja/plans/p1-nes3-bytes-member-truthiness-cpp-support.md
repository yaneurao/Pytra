# P1: `bytes` member truthiness の `!bytes` residual を C++ lane で止める

最終更新: 2026-03-13

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-NES3-BYTES-MEMBER-TRUTHINESS-CPP-01`

背景:
- Pytra-NES3 repro [`materials/refs/from-Pytra-NES3/cartridge_like.py`](../../../materials/refs/from-Pytra-NES3/cartridge_like.py) は `if not self.chr_rom:` を使う。
- representative `bytes` truthiness 自体は既に support されたが、2026-03-13 時点の C++ lane では member access が `!(this->chr_rom)` に漏れ、`bytes` が `list<unsigned char>` として lower されるため compile failure になる。
- 既存 task は local name と conditional expression の representative lane を固定したが、attribute/member lane はまだ同じ contract に揃っていない。

目的:
- member / attribute 経由の `bytes` truthiness を既存 representative contract と同じ `len` ベースの条件式に揃える。
- `cartridge_like.py` で露出した residual を focused regression と compile smoke で固定する。

対象:
- `bytes` field / attribute truthiness の C++ emitter / conditional lowering
- `materials/refs/from-Pytra-NES3/cartridge_like.py` の compile smoke
- `bytes` truthiness residual の regression / docs / TODO 同期

非対象:
- `bytes` runtime 型の redesign
- `bytearray` / `memoryview` への同時拡張
- non-C++ backend への横展開

受け入れ基準:
- `cartridge_like.py` の generated C++ が compile できる。
- `if not self.chr_rom` が raw `!bytes` を emit しない。
- 既存の representative `bytes` truthiness regression を壊さずに member lane も同じ contract へ揃う。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `bash ./pytra materials/refs/from-Pytra-NES3/cartridge_like.py --target cpp --output-dir /tmp/pytra_nes3_cartridge_like`
- `g++ -std=c++20 -O0 -c /tmp/pytra_nes3_cartridge_like/src/cartridge_like.cpp -I /tmp/pytra_nes3_cartridge_like/include -I /workspace/Pytra/src -I /workspace/Pytra/src/runtime/cpp`
- `git diff --check`

## 分解

- [ ] [ID: P1-NES3-BYTES-MEMBER-TRUTHINESS-CPP-01-S1-01] member/attribute lane の current failure と residual scope を focused regression / plan / TODO に固定する。
- [ ] [ID: P1-NES3-BYTES-MEMBER-TRUTHINESS-CPP-01-S2-01] member / attribute 経由の `bytes` truthiness を `len` ベースの C++ 条件式へ lower する。
- [ ] [ID: P1-NES3-BYTES-MEMBER-TRUTHINESS-CPP-01-S3-01] compile smoke と docs wording を representative contract に同期する。

決定ログ:
- 2026-03-13: Pytra-NES3 repro は archived representative support の残差なので、member lane に限定した follow-up として切り出す。
