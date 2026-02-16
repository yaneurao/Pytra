#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{math_cos, math_exp, math_floor, math_sin, math_sqrt, perf_counter, py_bool, py_grayscale_palette, py_in, py_isalpha, py_isdigit, py_len, py_print, py_save_gif, py_slice, py_write_rgb_png};

// このファイルは自動生成です（native Rust mode）。

fn lcg_next(mut state: i64) -> i64 {
    return ((((((1664525) * (state))) + (1013904223))) % (4294967296));
}

fn run_pi_trial(mut total_samples: i64, mut seed: i64) -> f64 {
    let mut inside: i64 = 0;
    let mut state: i64 = seed;
    for _ in (0)..(total_samples) {
        state = lcg_next(state);
        let mut x: f64 = ((( state ) as f64) / (( 4294967296.0 ) as f64));
        state = lcg_next(state);
        let mut y: f64 = ((( state ) as f64) / (( 4294967296.0 ) as f64));
        let mut dx: f64 = ((x) - (0.5));
        let mut dy: f64 = ((y) - (0.5));
        if py_bool(&(((((((dx) * (dx))) + (((dy) * (dy))))) <= (0.25)))) {
            inside = inside + 1;
        }
    }
    return ((( (((( 4.0 ) as f64) * (( inside ) as f64))) ) as f64) / (( total_samples ) as f64));
}

fn run_monte_carlo_pi() -> () {
    let mut samples: i64 = 54000000;
    let mut seed: i64 = 123456789;
    let mut start: f64 = perf_counter();
    let mut pi_est: f64 = run_pi_trial(samples, seed);
    let mut elapsed: f64 = ((perf_counter()) - (start));
    println!("{} {}", "samples:".to_string(), samples);
    println!("{} {}", "pi_estimate:".to_string(), pi_est);
    println!("{} {}", "elapsed_sec:".to_string(), elapsed);
}

fn main() {
    run_monte_carlo_pi();
}
