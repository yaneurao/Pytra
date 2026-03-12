// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/pathlib.py
// generated-by: tools/gen_runtime_from_manifest.py

import * as fs from "fs";
import * as nodepath from "path";

function _coercePathText(value: unknown): string {
    const maybePath = value as { __fspath__?: () => unknown; toString?: () => string } | null | undefined;
    if (maybePath && typeof maybePath.__fspath__ === "function") {
        return String(maybePath.__fspath__());
    }
    if (maybePath && typeof maybePath.toString === "function" && maybePath.toString !== Object.prototype.toString) {
        return String(maybePath.toString());
    }
    return String(value ?? "");
}

function _globSegmentToRegExp(segment: string): RegExp {
    const escaped = String(segment).replace(/[|\\{}()[\]^$+?.]/g, "\\$&");
    return new RegExp("^" + escaped.replace(/\*/g, ".*") + "$");
}

function _globPaths(pattern: string): string[] {
    const text = _coercePathText(pattern);
    if (text.indexOf("*") === -1) {
        return fs.existsSync(text) ? [text] : [];
    }
    const normalized = text.replace(/\\/g, "/");
    const lastSlash = normalized.lastIndexOf("/");
    const baseDir = lastSlash >= 0 ? normalized.slice(0, lastSlash) : ".";
    const leafPattern = lastSlash >= 0 ? normalized.slice(lastSlash + 1) : normalized;
    const dirPath = baseDir === "" ? "." : baseDir;
    if (!fs.existsSync(dirPath) || !fs.statSync(dirPath).isDirectory()) {
        return [];
    }
    const leafRe = _globSegmentToRegExp(leafPattern);
    const out: string[] = [];
    for (const entry of fs.readdirSync(dirPath, { withFileTypes: true })) {
        if (!leafRe.test(entry.name)) {
            continue;
        }
        out.push(nodepath.join(dirPath, entry.name));
    }
    return out;
}

export class PathValue {
    _value: string;

    constructor(value: unknown) {
        this._value = _coercePathText(value);
    }

    __str__(): string {
        return this._value;
    }

    __repr__(): string {
        return "Path(" + this._value + ")";
    }

    __fspath__(): string {
        return this._value;
    }

    __truediv__(rhs: unknown): PathValue {
        return new PathValue(nodepath.join(this._value, _coercePathText(rhs)));
    }

    parent(): PathValue {
        let parentTxt = nodepath.dirname(this._value);
        if (parentTxt === "") {
            parentTxt = ".";
        }
        return new PathValue(parentTxt);
    }

    parents(): PathValue[] {
        const out: PathValue[] = [];
        let current = nodepath.dirname(this._value);
        while (true) {
            if (current === "") {
                current = ".";
            }
            out.push(new PathValue(current));
            let nextCurrent = nodepath.dirname(current);
            if (nextCurrent === "") {
                nextCurrent = ".";
            }
            if (nextCurrent === current) {
                break;
            }
            current = nextCurrent;
        }
        return out;
    }

    name(): string {
        return nodepath.basename(this._value);
    }

    suffix(): string {
        return nodepath.extname(this._value);
    }

    stem(): string {
        return nodepath.parse(this._value).name;
    }

    resolve(): PathValue {
        return new PathValue(nodepath.resolve(this._value));
    }

    exists(): boolean {
        return fs.existsSync(this._value);
    }

    mkdir(parents: boolean = false, exist_ok: boolean = false): void {
        if (parents) {
            fs.mkdirSync(this._value, { recursive: true });
            return;
        }
        try {
            fs.mkdirSync(this._value);
        } catch (err: unknown) {
            const e = err as { code?: string };
            if (!(exist_ok && e.code === "EEXIST")) {
                throw err;
            }
        }
    }

    read_text(_encoding: string = "utf-8"): string {
        return fs.readFileSync(this._value, "utf8");
    }

    write_text(text: unknown, _encoding: string = "utf-8"): number {
        const rendered = String(text);
        fs.writeFileSync(this._value, rendered, "utf8");
        return rendered.length;
    }

    glob(pattern: string): PathValue[] {
        const matches = _globPaths(nodepath.join(this._value, _coercePathText(pattern)));
        return matches.map((item) => new PathValue(item));
    }

    toString(): string {
        return this._value;
    }

    static cwd(): PathValue {
        return new PathValue(process.cwd());
    }
}

function _wrap_path_obj(obj: PathValue): PathValue {
    if (!Object.prototype.hasOwnProperty.call(obj, "parent")) {
        Object.defineProperty(obj, "parent", { get: function(this: PathValue) { return _wrap_path_obj(PathValue.prototype.parent.call(this)); }, configurable: true });
    }
    if (!Object.prototype.hasOwnProperty.call(obj, "parents")) {
        Object.defineProperty(obj, "parents", { get: function(this: PathValue) { return PathValue.prototype.parents.call(this).map(_wrap_path_obj); }, configurable: true });
    }
    if (!Object.prototype.hasOwnProperty.call(obj, "name")) {
        Object.defineProperty(obj, "name", { get: function(this: PathValue) { return PathValue.prototype.name.call(this); }, configurable: true });
    }
    if (!Object.prototype.hasOwnProperty.call(obj, "suffix")) {
        Object.defineProperty(obj, "suffix", { get: function(this: PathValue) { return PathValue.prototype.suffix.call(this); }, configurable: true });
    }
    if (!Object.prototype.hasOwnProperty.call(obj, "stem")) {
        Object.defineProperty(obj, "stem", { get: function(this: PathValue) { return PathValue.prototype.stem.call(this); }, configurable: true });
    }
    return obj;
}

export const Path: ((value?: unknown) => PathValue) & { cwd(): PathValue } = Object.assign(
    function Path(value: unknown = ""): PathValue {
        return _wrap_path_obj(new PathValue(value));
    },
    {
        cwd(): PathValue {
            return _wrap_path_obj(PathValue.cwd());
        },
    },
);

export function pathJoin(base: unknown, child: unknown): PathValue {
    return _wrap_path_obj(new PathValue(nodepath.join(_coercePathText(base), _coercePathText(child))));
}
