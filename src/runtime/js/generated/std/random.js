// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/random.py
// generated-by: tools/gen_runtime_from_manifest.py

import * as _math from "./pytra/std/math.js";

function seed(value) {
    let v = value & 2147483647;
    if (v === 0) {
        v = 1;
    }
    _state_box[0] = v;
    _gauss_has_spare[0] = 0;
}

function _next_u31() {
    let s = _state_box[0];
    s = 1103515245 * s + 12345 & 2147483647;
    _state_box[0] = s;
    return s;
}

function random() {
    return _next_u31() / 2147483648.0;
}

function randint(a, b) {
    let lo = a;
    let hi = b;
    if (hi < lo) {
        const __swap_1 = lo;
        lo = hi;
        hi = __swap_1;
    }
    let span = hi - lo + 1;
    return lo + Math.trunc(Number(random() * span));
}

function choices(population, weights, k) {
    let n = (population).length;
    if (n <= 0) {
        return [];
    }
    let draws = k;
    if (draws < 0) {
        draws = 0;
    }
    let weight_vals = [];
    for (const w of weights) {
        weight_vals.push(w);
    }
    let out = [];
    if ((weight_vals).length === n) {
        let total = 0.0;
        for (const w of weight_vals) {
            if (w > 0.0) {
                total += w;
            }
        }
        if (total > 0.0) {
            for (let _ = 0; _ < draws; _ += 1) {
                let r = random() * total;
                let acc = 0.0;
                let picked_i = n - 1;
                for (let i = 0; i < n; i += 1) {
                    let w = weight_vals[(((i) < 0) ? ((weight_vals).length + (i)) : (i))];
                    if (w > 0.0) {
                        acc += w;
                    }
                    if (r < acc) {
                        picked_i = i;
                        break;
                    }
                }
                out.push(population[(((picked_i) < 0) ? ((population).length + (picked_i)) : (picked_i))]);
            }
            return out;
        }
    }
    for (let _ = 0; _ < draws; _ += 1) {
        out.push(population[(((randint(0, n - 1)) < 0) ? ((population).length + (randint(0, n - 1))) : (randint(0, n - 1)))]);
    }
    return out;
}

function gauss(mu, sigma) {
    if (_gauss_has_spare[0] !== 0) {
        _gauss_has_spare[0] = 0;
        return mu + sigma * _gauss_spare[0];
    }
    let u1 = 0.0;
    while (u1 <= 1.0e-12) {
        u1 = random();
    }
    let u2 = random();
    let mag = _math.sqrt(-2.0 * _math.log(u1));
    let z0 = mag * _math.cos(2.0 * _math.pi * u2);
    let z1 = mag * _math.sin(2.0 * _math.pi * u2);
    _gauss_spare[0] = z1;
    _gauss_has_spare[0] = 1;
    return mu + sigma * z0;
}

function shuffle(xs) {
    let i = (xs).length - 1;
    while (i > 0) {
        let j = randint(0, i);
        if (j !== i) {
            let tmp = xs[(((i) < 0) ? ((xs).length + (i)) : (i))];
            xs[(((i) < 0) ? ((xs).length + (i)) : (i))] = xs[(((j) < 0) ? ((xs).length + (j)) : (j))];
            xs[(((j) < 0) ? ((xs).length + (j)) : (j))] = tmp;
        }
        i -= 1;
    }
}

"pytra.std.random: minimal deterministic random helpers.\n\nThis module is intentionally self-contained and avoids Python stdlib imports,\nso it can be transpiled to target runtimes.\n";
let _state_box = [2463534242];
let _gauss_has_spare = [0];
let _gauss_spare = [0.0];

module.exports = {seed, random, randint, choices, gauss, shuffle};
