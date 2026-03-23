// Generated std/os.ts delegates host bindings through this native seam.

import { mkdirSync } from "node:fs";

export function getcwd(): string {
    return process.cwd();
}

export function mkdir(p: string): void {
    mkdirSync(p);
}

export function makedirs(p: string, exist_ok: boolean = false): void {
    mkdirSync(p, { recursive: exist_ok });
}
