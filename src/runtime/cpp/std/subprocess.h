#ifndef PYTRA_RUNTIME_STD_SUBPROCESS_H
#define PYTRA_RUNTIME_STD_SUBPROCESS_H

#include "core/py_runtime.h"

struct CompletedProcess {
    int64 returncode = 0;
    str stdout;
    str stderr;

    CompletedProcess() = default;
    CompletedProcess(int64 returncode, const str& stdout, const str& stderr);
};

CompletedProcess run(
    const Object<list<str>>& cmd,
    const str& cwd = str(""),
    bool capture_output = false,
    const Object<dict<str, str>>& env = rc_dict_new<str, str>()
);

#endif  // PYTRA_RUNTIME_STD_SUBPROCESS_H
