// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/sys.py
// generated-by: tools/gen_runtime_from_manifest.py

type SysApi = {
    argv: string[];
    path: string[];
    stderr: NodeJS.WriteStream;
    stdout: NodeJS.WriteStream;
    exit: (code?: number) => never;
    set_argv: (values: unknown) => void;
    set_path: (values: unknown) => void;
    write_stderr: (text: unknown) => void;
    write_stdout: (text: unknown) => void;
};

export const sys: SysApi = {
    argv: Array.from(process.argv),
    path: [],
    stderr: process.stderr,
    stdout: process.stdout,
    exit(code: number = 0): never {
        process.exit(Number(code) || 0);
    },
    set_argv(values: unknown): void {
        sys.argv = Array.isArray(values) ? Array.from(values, (value) => String(value)) : [];
    },
    set_path(values: unknown): void {
        sys.path = Array.isArray(values) ? Array.from(values, (value) => String(value)) : [];
    },
    write_stderr(text: unknown): void {
        process.stderr.write(String(text));
    },
    write_stdout(text: unknown): void {
        process.stdout.write(String(text));
    },
};

export const argv = sys.argv;
export const path = sys.path;
export const stderr = sys.stderr;
export const stdout = sys.stdout;

export function exit(code: number = 0): never {
    return sys.exit(code);
}

export function set_argv(values: unknown): void {
    sys.set_argv(values);
}

export function set_path(values: unknown): void {
    sys.set_path(values);
}

export function write_stderr(text: unknown): void {
    sys.write_stderr(text);
}

export function write_stdout(text: unknown): void {
    sys.write_stdout(text);
}
