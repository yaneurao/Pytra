// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/sys.py
// generated-by: tools/gen_runtime_from_manifest.py

#ifndef PYTRA_GEN_STD_SYS_H
#define PYTRA_GEN_STD_SYS_H

// forward declarations
void exit(int64 code = 0);
void set_argv(const list<str>& values);
void set_path(const list<str>& values);
void write_stderr(const str& text);
void write_stdout(const str& text);

list<str> argv;
list<str> path;
object stderr;
object stdout;

/* pytra.std.sys: extern-marked sys API with Python runtime fallback. */

void exit(int64 code = 0) {
    __s.exit(code);
}

void set_argv(const list<str>& values) {
    argv.clear();
    for (str v : values) {
        argv.append(v);
    }
}

void set_path(const list<str>& values) {
    path.clear();
    for (str v : values) {
        path.append(v);
    }
}

void write_stderr(const str& text) {
    __s.stderr.write(text);
}

void write_stdout(const str& text) {
    __s.stdout.write(text);
}

#endif  // PYTRA_GEN_STD_SYS_H
