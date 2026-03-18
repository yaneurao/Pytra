// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/pathlib.py
// generated-by: tools/gen_runtime_from_manifest.py

const fs = require("fs");
const nodepath = require("path");

function _coercePathText(value) {
    if (value && typeof value.__fspath__ === "function") {
        return String(value.__fspath__());
    }
    if (value && typeof value.toString === "function" && value.toString !== Object.prototype.toString) {
        return String(value.toString());
    }
    return String(value ?? "");
}

function _globSegmentToRegExp(segment) {
    const escaped = String(segment).replace(/[|\\{}()[\]^$+?.]/g, "\\$&");
    return new RegExp("^" + escaped.replace(/\*/g, ".*") + "$");
}

function _globPaths(pattern) {
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
    const out = [];
    for (const entry of fs.readdirSync(dirPath, { withFileTypes: true })) {
        if (!leafRe.test(entry.name)) {
            continue;
        }
        out.push(nodepath.join(dirPath, entry.name));
    }
    return out;
}

class PathValue {
    constructor(value) {
        this._value = _coercePathText(value);
    }

    __str__() {
        return this._value;
    }

    __repr__() {
        return "Path(" + this._value + ")";
    }

    __fspath__() {
        return this._value;
    }

    __truediv__(rhs) {
        return new PathValue(nodepath.join(this._value, _coercePathText(rhs)));
    }

    parent() {
        let parentTxt = nodepath.dirname(this._value);
        if (parentTxt === "") {
            parentTxt = ".";
        }
        return new PathValue(parentTxt);
    }

    parents() {
        const out = [];
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

    name() {
        return nodepath.basename(this._value);
    }

    suffix() {
        return nodepath.extname(this._value);
    }

    stem() {
        return nodepath.parse(this._value).name;
    }

    resolve() {
        return new PathValue(nodepath.resolve(this._value));
    }

    exists() {
        return fs.existsSync(this._value);
    }

    mkdir(parents = false, exist_ok = false) {
        if (parents) {
            fs.mkdirSync(this._value, { recursive: true });
            return;
        }
        try {
            fs.mkdirSync(this._value);
        } catch (err) {
            if (!(exist_ok && err && err.code === "EEXIST")) {
                throw err;
            }
        }
    }

    read_text(_encoding = "utf-8") {
        return fs.readFileSync(this._value, "utf8");
    }

    write_text(text, _encoding = "utf-8") {
        const rendered = String(text);
        fs.writeFileSync(this._value, rendered, "utf8");
        return rendered.length;
    }

    glob(pattern) {
        const matches = _globPaths(nodepath.join(this._value, _coercePathText(pattern)));
        return matches.map((item) => new PathValue(item));
    }

    toString() {
        return this._value;
    }

    static cwd() {
        return new PathValue(process.cwd());
    }
}

function _wrap_path_obj(obj) {
    if (!(obj instanceof PathValue)) {
        return obj;
    }
    if (!Object.prototype.hasOwnProperty.call(obj, "parent")) {
        Object.defineProperty(obj, "parent", { get: function() { return _wrap_path_obj(PathValue.prototype.parent.call(this)); }, configurable: true });
    }
    if (!Object.prototype.hasOwnProperty.call(obj, "parents")) {
        Object.defineProperty(obj, "parents", { get: function() { return PathValue.prototype.parents.call(this).map(_wrap_path_obj); }, configurable: true });
    }
    if (!Object.prototype.hasOwnProperty.call(obj, "name")) {
        Object.defineProperty(obj, "name", { get: function() { return PathValue.prototype.name.call(this); }, configurable: true });
    }
    if (!Object.prototype.hasOwnProperty.call(obj, "suffix")) {
        Object.defineProperty(obj, "suffix", { get: function() { return PathValue.prototype.suffix.call(this); }, configurable: true });
    }
    if (!Object.prototype.hasOwnProperty.call(obj, "stem")) {
        Object.defineProperty(obj, "stem", { get: function() { return PathValue.prototype.stem.call(this); }, configurable: true });
    }
    return obj;
}

function Path(value = "") {
    return _wrap_path_obj(new PathValue(value));
}

Path.cwd = function() {
    return _wrap_path_obj(PathValue.cwd());
};

function pathJoin(base, child) {
    return _wrap_path_obj(new PathValue(nodepath.join(_coercePathText(base), _coercePathText(child))));
}

module.exports = { Path, pathJoin };
