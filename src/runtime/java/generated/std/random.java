// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/random.py
// generated-by: tools/gen_runtime_from_manifest.py

public final class random {
    private random() {
    }

    public static java.util.ArrayList<Long> _state_box = new java.util.ArrayList<Long>(java.util.Arrays.asList(2463534242L));
    public static java.util.ArrayList<Long> _gauss_has_spare = new java.util.ArrayList<Long>(java.util.Arrays.asList(0L));
    public static java.util.ArrayList<Double> _gauss_spare = new java.util.ArrayList<Double>(java.util.Arrays.asList(0.0));


    public static void seed(long value) {
        long v = value & 2147483647L;
        if (((v) == (0L))) {
            v = 1L;
        }
        _state_box.set((int)((((0L) < 0L) ? (((long)(_state_box.size())) + (0L)) : (0L))), v);
        _gauss_has_spare.set((int)((((0L) < 0L) ? (((long)(_gauss_has_spare.size())) + (0L)) : (0L))), 0L);
    }

    public static long _next_u31() {
        Object s = _state_box.get((int)((((0L) < 0L) ? (((long)(_state_box.size())) + (0L)) : (0L))));
        s = 1103515245L * s + 12345L & 2147483647L;
        _state_box.set((int)((((0L) < 0L) ? (((long)(_state_box.size())) + (0L)) : (0L))), s);
        return s;
    }

    public static double random() {
        return ((double)(_next_u31())) / 2147483648.0;
    }

    public static long randint(long a, long b) {
        long lo = a;
        long hi = b;
        if (((hi) < (lo))) {
            long __swap_0 = lo;
            lo = hi;
            hi = __swap_0;
        }
        long span = hi - lo + 1L;
        return lo + PyRuntime.__pytra_int(random() * ((double)(span)));
    }

    public static java.util.ArrayList<Long> choices(java.util.ArrayList<Long> population, java.util.ArrayList<Double> weights, long k) {
        long n = ((long)(population.size()));
        if (((n) <= (0L))) {
            return new java.util.ArrayList<Long>();
        }
        long draws = k;
        if (((draws) < (0L))) {
            draws = 0L;
        }
        java.util.ArrayList<Double> weight_vals = new java.util.ArrayList<Double>();
        java.util.ArrayList<Object> __iter_0 = ((java.util.ArrayList<Object>)(Object)(weights));
        for (long __iter_i_1 = 0L; __iter_i_1 < ((long)(__iter_0.size())); __iter_i_1 += 1L) {
            double w = ((Double)(__iter_0.get((int)(__iter_i_1))));
            weight_vals.add(w);
        }
        java.util.ArrayList<Long> out = new java.util.ArrayList<Long>();
        if (((((long)(weight_vals.size()))) == (n))) {
            double total = 0.0;
            java.util.ArrayList<Object> __iter_2 = ((java.util.ArrayList<Object>)(Object)(weight_vals));
            for (long __iter_i_3 = 0L; __iter_i_3 < ((long)(__iter_2.size())); __iter_i_3 += 1L) {
                double w = ((Double)(__iter_2.get((int)(__iter_i_3))));
                if (((w) > (0.0))) {
                    total += w;
                }
            }
            if (((total) > (0.0))) {
                for (long __ = 0L; __ < draws; __ += 1L) {
                    double r = random() * total;
                    double acc = 0.0;
                    long picked_i = n - 1L;
                    for (long i = 0L; i < n; i += 1L) {
                        double w = ((Double)(weight_vals.get((int)((((i) < 0L) ? (((long)(weight_vals.size())) + (i)) : (i))))));
                        if (((w) > (0.0))) {
                            acc += w;
                        }
                        if (((r) < (acc))) {
                            picked_i = i;
                            break;
                        }
                    }
                    out.add(((Long)(population.get((int)((((picked_i) < 0L) ? (((long)(population.size())) + (picked_i)) : (picked_i)))))));
                }
                return out;
            }
        }
        for (long __ = 0L; __ < draws; __ += 1L) {
            out.add(((Long)(population.get((int)((((randint(0L, n - 1L)) < 0L) ? (((long)(population.size())) + (randint(0L, n - 1L))) : (randint(0L, n - 1L))))))));
        }
        return out;
    }

    public static double gauss(double mu, double sigma) {
        if (((_gauss_has_spare.get((int)((((0L) < 0L) ? (((long)(_gauss_has_spare.size())) + (0L)) : (0L))))) != (0L))) {
            _gauss_has_spare.set((int)((((0L) < 0L) ? (((long)(_gauss_has_spare.size())) + (0L)) : (0L))), 0L);
            return mu + sigma * _gauss_spare.get((int)((((0L) < 0L) ? (((long)(_gauss_spare.size())) + (0L)) : (0L))));
        }
        double u1 = 0.0;
        while (((u1) <= (1e-12))) {
            u1 = random();
        }
        double u2 = random();
        double mag = math.sqrt((-(2.0)) * math.log(u1));
        double z0 = mag * math.cos(2.0 * math.pi * u2);
        double z1 = mag * math.sin(2.0 * math.pi * u2);
        _gauss_spare.set((int)((((0L) < 0L) ? (((long)(_gauss_spare.size())) + (0L)) : (0L))), z1);
        _gauss_has_spare.set((int)((((0L) < 0L) ? (((long)(_gauss_has_spare.size())) + (0L)) : (0L))), 1L);
        return mu + sigma * z0;
    }

    public static void shuffle(java.util.ArrayList<Long> xs) {
        long i = ((long)(xs.size())) - 1L;
        while (((i) > (0L))) {
            long j = randint(0L, i);
            if (((j) != (i))) {
                long tmp = ((Long)(xs.get((int)((((i) < 0L) ? (((long)(xs.size())) + (i)) : (i))))));
                xs.set((int)((((i) < 0L) ? (((long)(xs.size())) + (i)) : (i))), ((Long)(xs.get((int)((((j) < 0L) ? (((long)(xs.size())) + (j)) : (j)))))));
                xs.set((int)((((j) < 0L) ? (((long)(xs.size())) + (j)) : (j))), tmp);
            }
            i -= 1L;
        }
    }

    public static void main(String[] args) {
    }
}
