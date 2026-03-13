// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/random.py
// generated-by: tools/gen_runtime_from_manifest.py

using System;
using System.Collections.Generic;
using System.Linq;
using Any = System.Object;
using int64 = System.Int64;
using float64 = System.Double;
using str = System.String;
using Pytra.CsModule;
using _math = Pytra.CsModule.math;

public static class Program
{
    public static void seed(long value)
    {
        long v = value & 2147483647;
        if ((v) == (0)) {
            v = 1;
        }
        _state_box[System.Convert.ToInt32(0)] = v;
        _gauss_has_spare[System.Convert.ToInt32(0)] = 0;
    }
    
    public static long _next_u31()
    {
        var s = _state_box[System.Convert.ToInt32(0)];
        s = 1103515245 * s + 12345 & 2147483647;
        _state_box[System.Convert.ToInt32(0)] = s;
        return s;
    }
    
    public static double random()
    {
        return System.Convert.ToDouble(_next_u31()) / System.Convert.ToDouble(2147483648.0);
    }
    
    public static long randint(long a, long b)
    {
        long lo = a;
        long hi = b;
        if ((hi) < (lo)) {
            var __swap_1 = lo;
            lo = hi;
            hi = __swap_1;
        }
        long span = hi - lo + 1;
        return lo + Pytra.CsModule.py_runtime.py_int(random() * span);
    }
    
    public static System.Collections.Generic.List<long> choices(System.Collections.Generic.List<long> population, System.Collections.Generic.List<double> weights, long k = 1)
    {
        long n = (population).Count;
        if ((n) <= (0)) {
            return new System.Collections.Generic.List<long>();
        }
        long draws = k;
        if ((draws) < (0)) {
            draws = 0;
        }
        System.Collections.Generic.List<double> weight_vals = new System.Collections.Generic.List<double>();
        foreach (var w in weights) {
            weight_vals.Add(w);
        }
        System.Collections.Generic.List<long> py_out = new System.Collections.Generic.List<long>();
        if (((weight_vals).Count) == (n)) {
            double total = 0.0;
            foreach (var w in weight_vals) {
                if ((w) > (0.0)) {
                    total += w;
                }
            }
            if ((total) > (0.0)) {
                long _ = 0;
                for (_ = 0; _ < draws; _ += 1) {
                    double r = random() * total;
                    double acc = 0.0;
                    long picked_i = n - 1;
                    long i = 0;
                    for (i = 0; i < n; i += 1) {
                        double w = Pytra.CsModule.py_runtime.py_get(weight_vals, i);
                        if ((w) > (0.0)) {
                            acc += w;
                        }
                        if ((r) < (acc)) {
                            picked_i = i;
                            break;
                        }
                    }
                    py_out.Add(Pytra.CsModule.py_runtime.py_get(population, picked_i));
                }
                return py_out;
            }
        }
        long _ = 0;
        for (_ = 0; _ < draws; _ += 1) {
            py_out.Add(Pytra.CsModule.py_runtime.py_get(population, randint(0, n - 1)));
        }
        return py_out;
    }
    
    public static double gauss(double mu = 0.0, double sigma = 1.0)
    {
        if ((_gauss_has_spare[System.Convert.ToInt32(0)]) != (0)) {
            _gauss_has_spare[System.Convert.ToInt32(0)] = 0;
            return mu + sigma * _gauss_spare[System.Convert.ToInt32(0)];
        }
        double u1 = 0.0;
        while ((u1) <= (1.0e-12)) {
            u1 = random();
        }
        double u2 = random();
        double mag = _math.sqrt(-2.0 * _math.log(u1));
        double z0 = mag * _math.cos(2.0 * _math.pi * u2);
        double z1 = mag * _math.sin(2.0 * _math.pi * u2);
        _gauss_spare[System.Convert.ToInt32(0)] = z1;
        _gauss_has_spare[System.Convert.ToInt32(0)] = 1;
        return mu + sigma * z0;
    }
    
    public static void shuffle(System.Collections.Generic.List<long> xs)
    {
        long i = (xs).Count - 1;
        while ((i) > (0)) {
            long j = randint(0, i);
            if ((j) != (i)) {
                long tmp = Pytra.CsModule.py_runtime.py_get(xs, i);
                Pytra.CsModule.py_runtime.py_set(xs, i, Pytra.CsModule.py_runtime.py_get(xs, j));
                Pytra.CsModule.py_runtime.py_set(xs, j, tmp);
            }
            i -= 1;
        }
    }
    
    public static void Main(string[] args)
    {
            System.Collections.Generic.List<long> _state_box = new System.Collections.Generic.List<long> { 2463534242 };
            System.Collections.Generic.List<long> _gauss_has_spare = new System.Collections.Generic.List<long> { 0 };
            System.Collections.Generic.List<double> _gauss_spare = new System.Collections.Generic.List<double> { 0.0 };
    }
}
