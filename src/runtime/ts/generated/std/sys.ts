// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/sys.py
// generated-by: tools/gen_runtime_from_manifest.py

import * as sys_native from "../../native/std/sys_native";

export const sys = sys_native.sys;
export const argv = sys_native.argv;
export const path = sys_native.path;
export const stderr = sys_native.stderr;
export const stdout = sys_native.stdout;

export function exit(code: number = 0): never {
    return sys_native.exit(code);
}

export function set_argv(values: unknown): void {
    return sys_native.set_argv(values);
}

export function set_path(values: unknown): void {
    return sys_native.set_path(values);
}

export function write_stderr(text: unknown): void {
    return sys_native.write_stderr(text);
}

export function write_stdout(text: unknown): void {
    return sys_native.write_stdout(text);
}
