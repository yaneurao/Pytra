// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/random.py
// generated-by: tools/gen_runtime_from_manifest.py

mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::pytra::std::math as _math;

fn seed(value: i64) {
    let mut v = value & 2147483647;
    if v == 0 {
        v = 1;
    }
    let __idx_1 = ((0) as usize);
    _state_box[__idx_1] = v;
    let __idx_2 = ((0) as usize);
    _gauss_has_spare[__idx_2] = 0;
}

fn _next_u31() -> i64 {
    let mut s = _state_box[((0) as usize)];
    s = 1103515245 * s + 12345 & 2147483647;
    let __idx_3 = ((0) as usize);
    _state_box[__idx_3] = s;
    return s;
}

fn random() -> f64 {
    return ((_next_u31()) as f64) / 2147483648.0;
}

fn randint(a: i64, b: i64) -> i64 {
    let mut lo = a;
    let mut hi = b;
    if hi < lo {
        std::mem::swap(&mut lo, &mut hi);
    }
    let span = hi - lo + 1;
    return lo + ((random() * ((span) as f64)) as i64);
}

fn choices(population: &[i64], weights: &[f64], k: i64) -> Vec<i64> {
    let n = population.len() as i64;
    if n <= 0 {
        return vec![];
    }
    let mut draws = k;
    if draws < 0 {
        draws = 0;
    }
    let mut weight_vals: Vec<f64> = vec![];
    for w in (weights).iter().copied() {
        weight_vals.push(w);
    }
    let mut out: Vec<i64> = vec![];
    if weight_vals.len() as i64 == n {
        let mut total = 0.0;
        for w in (weight_vals).iter().copied() {
            if w > 0.0 {
                total += w;
            }
        }
        if total > 0.0 {
            for py_underscore in (0)..(draws) {
                    let r = random() * total;
                    let mut acc = 0.0;
                    let mut picked_i = n - 1;
                    for i in (0)..(n) {
                            let mut w = weight_vals[((i) as usize)];
                            if w > 0.0 {
                                acc += w;
                            }
                            if r < acc {
                                picked_i = i;
                                break;
                            }
                    }
                    out.push(population[((picked_i) as usize)]);
            }
            return out;
        }
    }
    for py_underscore in (0)..(draws) {
            out.push(population[((if ((randint(0, n - 1)) as i64) < 0 { (population.len() as i64 + ((randint(0, n - 1)) as i64)) } else { ((randint(0, n - 1)) as i64) }) as usize)]);
    }
    return out;
}

fn gauss(mu: f64, sigma: f64) -> f64 {
    if _gauss_has_spare[((0) as usize)] != 0 {
        let __idx_7 = ((0) as usize);
        _gauss_has_spare[__idx_7] = 0;
        return mu + sigma * _gauss_spare[((0) as usize)];
    }
    let mut u1 = 0.0;
    while u1 <= 1.0e-12 {
        u1 = random();
    }
    let u2 = random();
    let mag = pytra::std::math::sqrt(-2.0 * pytra::std::math::log(u1));
    let z0 = mag * pytra::std::math::cos(2.0 * pytra::std::math::pi * u2);
    let z1 = mag * pytra::std::math::sin(2.0 * pytra::std::math::pi * u2);
    let __idx_8 = ((0) as usize);
    _gauss_spare[__idx_8] = z1;
    let __idx_9 = ((0) as usize);
    _gauss_has_spare[__idx_9] = 1;
    return mu + sigma * z0;
}

fn shuffle(mut xs: Vec<i64>) {
    let mut i = xs.len() as i64 - 1;
    while i > 0 {
        let j = randint(0, i);
        if j != i {
            let tmp = xs[((if ((i) as i64) < 0 { (xs.len() as i64 + ((i) as i64)) } else { ((i) as i64) }) as usize)];
            let __idx_i64_11 = ((i) as i64);
            let __idx_10 = if __idx_i64_11 < 0 { (xs.len() as i64 + __idx_i64_11) as usize } else { __idx_i64_11 as usize };
            xs[__idx_10] = xs[((if ((j) as i64) < 0 { (xs.len() as i64 + ((j) as i64)) } else { ((j) as i64) }) as usize)];
            let __idx_i64_13 = ((j) as i64);
            let __idx_12 = if __idx_i64_13 < 0 { (xs.len() as i64 + __idx_i64_13) as usize } else { __idx_i64_13 as usize };
            xs[__idx_12] = tmp;
        }
        i -= 1;
    }
}

fn main() {
    ("pytra.std.random: minimal deterministic random helpers.\n\nThis module is intentionally self-contained and avoids Python stdlib imports,\nso it can be transpiled to target runtimes.\n").to_string();
    let _state_box: Vec<i64> = vec![2463534242];
    let _gauss_has_spare: Vec<i64> = vec![0];
    let _gauss_spare: Vec<f64> = vec![0.0];
}
