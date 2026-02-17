#include "cpp_module/py_runtime.h"


void __pytra_main() {
    Path root = Path("test/obj/pathlib_case32");
    root.mkdir(true, true);
    
    Path child = root / "values.txt";
    child.write_text("42");
    
    py_print(child.exists());
    py_print(child.name());
    py_print(child.stem());
    py_print((child.parent() / "values.txt").exists());
    py_print(child.read_text());
}

int main() {
    __pytra_main();
    return 0;
}
