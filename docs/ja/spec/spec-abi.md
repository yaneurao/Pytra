# Pytra トランスパイラ仕様: @extern 関数と固定 ABI 型（C++ バックエンド）

## 1. 目的

Pytra は Python から C++ 等へ変換するトランスパイラであり、C++ 側では参照カウント付きラッパ `rc<T>` によりオブジェクト寿命を管理する。

一方、変換時の最適化により `rc<T>` が縮退（除去）され、同じ Python 型が複数の C++ 表現を取りうる。例:

- `rc<list<rc<bytearray>>>`  →  `list<rc<bytearray>>`
- `list<rc<bytearray>>`      →  `list<bytearray>`

この揺れは、外部実装（C++ 側で定義する関数）に委譲する `@extern` 関数の呼び出し時に問題となる。`@extern` 関数は「呼び出し点における内部表現」に依存せず、常に同一の ABI（引数・戻り値の型）で呼べる必要がある。

本仕様は、`@extern` 関数に **固定 ABI 型**を与え、呼び出し点で必要に応じて **ABI 変換（アダプト）** を挿入することで、この問題を解決する。

本仕様において `@extern` は **デコレータ引数なし**のみをサポートする。


## 2. 用語

- **内部型 (Internal Type)**  
  最適化・変換過程で用いられる C++ 側の実際の表現型。縮退により複数パターンがありうる。

- **ABI 型 (ABI Type)**  
  `@extern` 関数呼び出しの境界で用いる固定の C++ 型。外部実装（ランタイム/ターゲット言語側）で定義される関数シグネチャと一致する。

- **ABI 変換 (ABI Adaptation)**  
  呼び出し点の内部型から ABI 型へ変換する処理。必要なときのみ挿入される。恒等変換（no-op）も含む。


## 3. @extern の基本仕様

### 3.1 記法
Python ソース上では以下のみを許可する。

```python
@extern
def write_png(image: list[bytearray]) -> None: ...
```

```python
# py_stdlib/math.py
from pytra.std import extern

@extern
def write_png(image: list[bytearray]) -> None: ...
```

externは単なるマーカーで以下のように定義してあるものとする。
```python
def extern(fn):
    return fn
```

@extern は Python 実行時に import を成立させるためのダミー定義として存在してよいが、意味論はトランスパイラが解釈する。
@extern の引数付き呼び出し（@extern(...)）はサポートしない。

3.2 意味

@extern が付与された関数は、ターゲット言語（ここでは C++）側で提供される関数に委譲される。

Pytra は @extern 関数に対し、外部名（シンボル名） と ABI 型 を決定する。

呼び出し点では、実引数が内部型で表現されていても、ABI 型へ変換して外部関数を呼ぶ。

4. 外部名（シンボル名）の決定規約

@extern 関数 M.f に対し、外部名は以下で決定する。

外部名: pytra_<module>_<function>

<module> は Python モジュール名（例: pytra.std.math, pytra.utils.png 等）

<function> は関数名

例:

pytra.std.math.sin → pytra_std_math_sin
pytra.utils.png.write_png → pytra_utils_png_write_png

注意:

モジュール名の決定は、パッケージ名に基づき一意に決める。
ネスト関数・ローカル関数は対象外（@extern はトップレベル関数のみ許可、等の制約を設けてもよい）。

5. ABI 型の決定規約
5.1 基本方針

ABI 型は Python 型（注釈）から決定される固定の C++ 型であり、内部の最適化で揺れない。

ABI 型は “境界の正規形” として扱う。

5.2 例（推奨の正規形）

本仕様では、オブジェクトは ABI 境界では基本的に rc<> で保持する（寿命・所有権を境界で安定化させるため）。

推奨の正規形（例）:

```
bytearray → rc<bytearray>

list[T] → rc<list<ABI(T)>>

dict[K,V] → rc<dict<ABI(K), ABI(V)>>

str → rc<py_str>

bytes → rc<py_bytes>

int → int64_t
※ Pytraの言語仕様で変換元のintはint64(符号付き64bit整数)と決まっている。

float → double（推奨）
```

ここで ABI(T) は要素型の ABI 正規形を表す。

具体例

write_png(image: list[bytearray]) の ABI 型は以下とする:

image: list[bytearray]

bytearray の ABI 正規形: rc<bytearray>

list[rc<bytearray>] の ABI 正規形: rc<list<rc<bytearray>>>

よって外部関数は次のような形を要求する:

```
extern "C" void pytra_utils_png_write_png(rc<list<rc<bytearray>>> image);
```

※ extern "C" の採用は推奨（名前修飾を避け、他言語連携も容易にする）。

6. ABI 変換（アダプト）の仕様
6.1 変換の挿入点

@extern 関数呼び出しを外部名へ lowering する段階（例: CppLower）で、各引数について以下を行う:

実引数の内部型 Tin を得る（最適化結果の型）

対応する ABI 型 Tabi を得る（固定規約により決定）

Tin と Tabi が一致すればそのまま渡す

一致しなければ adapt(Tin → Tabi) を挿入し、その結果を渡す

6.2 変換関数の形

ABI 変換は、生成コード上で以下として表現する:

ジェネリックなテンプレート関数を用意
例: adapt<rc<list<rc<bytearray>>>>(x)


6.3 必須の変換ケース（例: list[bytearray]）

Tabi = rc<list<rc<bytearray>>> に対し、少なくとも以下を扱えること:

Tin = rc<list<rc<bytearray>>>
→ no-op（参照をそのまま渡す）

Tin = list<rc<bytearray>>
→ rc<> で外側をラップする（実体を共有するかコピーするかは実装方針で決める）

推奨: rc<list<rc<bytearray>>>(move_or_share(x))

Tin = list<bytearray>
→ 各要素を rc<bytearray> にラップし、さらに外側も rc<list<...>> とする

要素ラップがコピーを伴うかどうかは bytearray 実装に依存

推奨: “参照共有 bytearray” を前提に rc 化は shallow で済むように設計する

Tin = rc<list<bytearray>>
→ 外側はそのまま使い、要素のみ rc 化して rc<list<rc<bytearray>>> を生成

上記以外の型が来た場合はコンパイルエラーとしてよい。

6.4 変換コストに関する方針

ABI 変換はコストを伴う可能性があるが、以下の原則で許容する:

外部境界で ABI を固定することを優先する

変換は「必要なときのみ」挿入する（型一致なら no-op）

I/O 的な write_png のような関数は変換コストが支配的になりにくい

もし性能上問題が出た場合は、個別に “専用 ABI” を設計する（例: span/ポインタ+サイズなど）

7. 生成される C++ 宣言とリンク
7.1 宣言の提供方法

外部関数の宣言は、次のいずれかで提供される:

方式1: トランスパイラが使用された外部関数だけ forward 宣言を自動生成する

方式2: 共通ヘッダ（例: pytra_runtime.hpp）を常に include し、そこに宣言を置く

いずれも許可するが、初期は方式1を推奨する（依存を最小化できるため）。

7.2 ABI（extern "C"）

本仕様では外部関数は原則 extern "C" とする。
これにより、シンボル名の安定化と他言語連携が容易になる。

注意: extern "C" 自体はインライン化を阻害しないが、別翻訳単位に実装される場合は LTO なしではインライン化されない。性能が必要ならヘッダ内 static inline 実装や LTO を検討する。

8. 仕様上の制約

@extern 関数は Python 側に実装を持たず ... のスタブでよい。

@extern 関数は型注釈（引数・戻り値）を必須とすることを推奨する（ABI 型決定のため）。

@extern の対象はトップレベル関数のみ、などの追加制約は実装簡素化のために許容される。

9. 例（write_png）

Python:

from pytra import extern

@extern
def write_png(image: list[bytearray]) -> None: ...

ABI 型（規約）:

image: rc<list<rc<bytearray>>>

戻り値: void

生成（概念）:

// forward decl（方式1の例）
extern "C" void pytra_utils_png_write_png(rc<list<rc<bytearray>>> image);

void callsite(...) {
    // image_in は最適化により型が揺れる（例: list<bytearray> 等）
    auto image_abi = adapt_to_rc_list_rc_bytearray(image_in);
    pytra_utils_png_write_png(image_abi);
}

外部実装（C++ 側）:

extern "C" void pytra_utils_png_write_png(rc<list<rc<bytearray>>> image) {
    // PNG 書き出し処理
}
10. 実装チェックリスト

 @extern 付与関数を AST から検出できる

 Python 型注釈から ABI 型を一意に決められる

 外部名 pytra_<module>_<func> を一意に決められる

 呼び出し点で (Tin, Tabi) を比較し、必要なら adapt を挿入できる

 list[bytearray] など代表例で、縮退後の複数内部型を ABI に正規化できる

 外部関数宣言（forward decl or runtime header）を生成できる

11. runtime ディレクトリ構成（本仕様での前提）

`runtime/` は廃止しない。言語別 runtime は以下の 2 層で構成する。

- `runtime/<lang>/core/`
  - 事前配置する手書き runtime（言語固有実装）
  - 例: `*-impl.*` など
- `runtime/<lang>/gen/`
  - `src/pytra/...` の pure Python 実装をトランスパイルして生成するファイル

`runtime/<lang>/pytra/` は shim 層としては採用しない（廃止）。

manifest（ビルド入力一覧）は `core/` と `gen/` のみを参照する。

12. pytra.std.math の例

`pytra/std/math.py` から、`outdir = runtime/cpp/gen/` の場合:

- `runtime/cpp/gen/std/math.h`
- `runtime/cpp/gen/std/math.cpp`

がトランスパイラ生成物になる。

`@export` を含むので、事前配置 runtime:

- `runtime/cpp/core/std/math-impl.cpp`

もビルドに含める。

manifest（gcc でのビルド入力）には、このとき次が出力される:

- `runtime/cpp/gen/std/math.h`
- `runtime/cpp/gen/std/math.cpp`
- `runtime/cpp/core/std/math-impl.cpp`
