// Generated std/os_path.ts delegates host bindings through this native seam.

import nodePath from "node:path";
import { existsSync } from "node:fs";

export function join(a: string, b: string): string {
    return nodePath.join(a, b);
}

export function dirname(p: string): string {
    return nodePath.dirname(p);
}

export function basename(p: string): string {
    return nodePath.basename(p);
}

export function splitext(p: string): [string, string] {
    const ext = nodePath.extname(p);
    const root = ext !== "" ? p.substring(0, p.length - ext.length) : p;
    return [root, ext];
}

export function abspath(p: string): string {
    return nodePath.resolve(p);
}

export function exists(p: string): boolean {
    return existsSync(p);
}
