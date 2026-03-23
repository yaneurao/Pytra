// Generated std/glob.ts delegates host bindings through this native seam.

import { readdirSync, statSync } from "node:fs";
import { join } from "node:path";

export function glob(pattern: string): string[] {
    const idx = pattern.lastIndexOf("/");
    let dir = ".";
    let filePattern = pattern;
    if (idx >= 0) {
        dir = pattern.substring(0, idx);
        filePattern = pattern.substring(idx + 1);
    }
    if (filePattern === "*") {
        try {
            const entries = readdirSync(dir);
            return entries.map((e) => join(dir, e));
        } catch (_e) {
            return [];
        }
    }
    if (filePattern.startsWith("*")) {
        const suffix = filePattern.substring(1);
        try {
            const entries = readdirSync(dir);
            return entries.filter((e) => e.endsWith(suffix)).map((e) => join(dir, e));
        } catch (_e) {
            return [];
        }
    }
    try {
        statSync(pattern);
        return [pattern];
    } catch (_e) {
        return [];
    }
}
