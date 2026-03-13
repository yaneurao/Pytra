// Generated std/sys.ts delegates host bindings through this native seam.

export type SysApi = {
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

function _replaceArray(target: string[], values: unknown): void {
    const next = Array.isArray(values) ? Array.from(values, (value) => String(value)) : [];
    target.splice(0, target.length, ...next);
}

export const sys: SysApi = {
    argv: Array.from(process.argv, (value) => String(value)),
    path: [],
    stderr: process.stderr,
    stdout: process.stdout,
    exit(code: number = 0): never {
        process.exit(Number(code) || 0);
    },
    set_argv(values: unknown): void {
        _replaceArray(sys.argv, values);
    },
    set_path(values: unknown): void {
        _replaceArray(sys.path, values);
    },
    write_stderr(text: unknown): void {
        sys.stderr.write(String(text));
    },
    write_stdout(text: unknown): void {
        sys.stdout.write(String(text));
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
