# ランタイムの仕様について

### 1. 生成物と手書き実装の責務分離を明文化する

- 自動生成:
  - `pytra/std/<mod>.h`
  - `pytra/std/<mod>.cpp`
  - `pytra/runtime/<mod>.h`
  - `pytra/runtime/<mod>.cpp`
- 手書き許可:
  - `pytra/std/<mod>-impl.cpp`
  - `pytra/runtime/<mod>-impl.cpp`
- ルール:
  - `<mod>.h/.cpp` は常に再生成対象（手編集禁止）。
  - `*-impl.cpp` は手編集可能（再生成対象外）。
  - `<mod>.cpp` から `*-impl.cpp` の関数へ委譲する。

### 2. include規約を固定する

- 生成コード側で import に対応して出力する include は次で固定する。
  - `from pytra.std.glob import glob` -> `#include "pytra/std/glob.h"`
  - `from pytra.runtime.gif import save_gif` -> `#include "pytra/runtime/gif.h"`
- トランスパイラが include パスを 1 方式に固定し、旧配置との混在を禁止する。
- ルール追加:
  - Python の import 名と C++ include パスは 1 対 1 対応にする。
  - 例: `import pytra.std.math` -> `#include "pytra/std/math.h"`。
  - 例: `import pytra.runtime.png` -> `#include "pytra/runtime/png.h"`。

### 3. 自作モジュール import の生成仕様を追加する

- `import mylib` / `from mylib import f` の場合:
  - `mylib.py` -> `mylib.h` / `mylib.cpp` を生成する。
- 依存解決:
  - import グラフを先に構築し、トポロジカル順で生成する。
  - 循環 import はエラー（`input_invalid`）とする。
- 名前衝突:
  - `pytra.*` と同名のユーザーモジュールは禁止（`input_invalid`）。

### 4. `*-impl.cpp` のABI境界を固定する

- `*-impl.cpp` に置く関数は C++ 依存の最小 primitive だけに限定する。
  - 例: filesystem, regex, clock, process, OS API
- それ以外のロジック（整形・変換・検証）は Python 側 (`pytra/*.py`) に残す。
- これにより、言語間差異を `*-impl` 層へ閉じ込める。

### 5. 生成テンプレートの最小ルール

- 生成 `<mod>.h`:
  - 公開 API 宣言のみ
  - include guard / namespace 定義
- 生成 `<mod>.cpp`:
  - `#include "<mod>.h"`
  - 必要なら `#include "<mod>-impl.cpp"` は行わず、関数宣言経由でリンク解決する
  - 変換された Python ロジック本体 + `*-impl` 呼び出し

### 6. テスト要件を仕様に含める

- 各モジュールで最低限次を満たすこと:
  1. Python実行結果と C++ 実行結果が一致する
  2. `pytra/std` と `pytra/runtime` の import 形式（`import` / `from ... import ...`）の両方が通る
  3. 生成物を削除して再生成しても差分が安定する（再現可能）

### 7. 将来の多言語展開を見据えた命名

- C++ 固有名（`-impl.cpp`）の概念は維持しつつ、他言語では同等の役割名に置換する。
  - 例: `-impl.cs`, `-impl.rs` など
- 仕様文書では「ネイティブ実装層（impl層）」として抽象名で定義する。

### 8. 既存配置からの移行方針（`runtime/cpp` 整理）

- 現在 `runtime/cpp/core/*` などにある実体は、最終的に import 名準拠の配置へ寄せる。
  - 目標: `pytra/std/*.h|*.cpp` / `pytra/runtime/*.h|*.cpp` を唯一の公開配置とする。
- 移行期間:
  - 旧パス（`runtime/cpp/core/*` など）は残さず削除する。
  - 新規生成コード・既存生成コードともに新パスへ強制移行する。
- 完了条件:
  - import 名から include を機械的変換しただけでコンパイルが通る。
  - `py2cpp.py` 内の旧パス向けハードコードが除去されている。

### 9. 命名方針

- ライブラリ階層は次の2系統に統一する。
  - `pytra.std`: Python 標準ライブラリ代替
  - `pytra.runtime`: Pytra 固有ランタイム補助
- `utils` のような汎用名は使わず、責務が読める名前を優先する。
