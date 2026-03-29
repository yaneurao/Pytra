use std::time::Instant;

pub fn perf_counter() -> f64 {
    static INIT: std::sync::Once = std::sync::Once::new();
    static mut START: Option<Instant> = None;
    INIT.call_once(|| unsafe {
        START = Some(Instant::now());
    });
    unsafe { START.as_ref().expect("perf counter start must be initialized").elapsed().as_secs_f64() }
}
