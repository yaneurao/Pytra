#include "core/py_runtime.h"
#include "core/process_runtime.h"
#include "std/os_path.h"

/* pytra.std.os: extern-marked os subset with Python runtime fallback. */

str getcwd() {
    return os.getcwd();
}

void mkdir(const str& p) {
    os.mkdir(p);
}

void makedirs(const str& p, bool exist_ok = false) {
    os.makedirs(p, exist_ok);
}
