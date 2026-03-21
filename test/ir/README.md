# test/ir

`test/fixtures` 由来の EAST3(JSON) fixture です。

- `.py -> EAST3` の frontend 回帰とは分離し、backend-only の確認に使います。
- 更新例:
  - `python3 src/py2x.py test/fixtures/core/add.py --target cpp -o out/ir_seed_add.cpp --dump-east3-after-opt test/ir/core_add.east3.json`
  - `python3 src/py2x.py test/fixtures/stdlib/math_path_runtime_ir.py --target java -o out/ir_seed_math_path.java --dump-east3-after-opt test/ir/java_math_path_runtime.east3.json`
