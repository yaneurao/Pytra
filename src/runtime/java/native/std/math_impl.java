// Java math_impl bridge for pytra.std.math.

final class _m {
    private _m() {
    }

    static final double pi = Math.PI;
    static final double e = Math.E;

    static double sqrt(double x) {
        return Math.sqrt(x);
    }

    static double sin(double x) {
        return Math.sin(x);
    }

    static double cos(double x) {
        return Math.cos(x);
    }

    static double tan(double x) {
        return Math.tan(x);
    }

    static double exp(double x) {
        return Math.exp(x);
    }

    static double log(double x) {
        return Math.log(x);
    }

    static double log10(double x) {
        return Math.log10(x);
    }

    static double fabs(double x) {
        return Math.abs(x);
    }

    static double floor(double x) {
        return Math.floor(x);
    }

    static double ceil(double x) {
        return Math.ceil(x);
    }

    static double pow(double x, double y) {
        return Math.pow(x, y);
    }
}
