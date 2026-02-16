// fallback: class is not supported in native Rust mode
// このファイルは自動生成です。編集しないでください。
// 入力 Python: case14_inheritance.py

#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;

fn main() {
    let source: &str = r#"# このファイルは `test/py/case14_inheritance.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

class Animal:
    def sound(self) -> str:
        return "generic"


class Dog(Animal):
    def bark(self) -> str:
        return self.sound() + "-bark"


if __name__ == "__main__":
    d: Dog = Dog()
    print(d.bark())
"#;
    std::process::exit(py_runtime::run_embedded_python(source));
}
