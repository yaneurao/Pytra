final class _07_game_of_life_loop {
    private _07_game_of_life_loop() {
    }


    // 07: Sample that outputs Game of Life evolution as a GIF.

    public static java.util.ArrayList<java.util.ArrayList<Long>> next_state(java.util.ArrayList<java.util.ArrayList<Long>> grid, long w, long h) {
        java.util.ArrayList<java.util.ArrayList<Long>> nxt = new java.util.ArrayList<java.util.ArrayList<Long>>();
        for (long y = 0L; y < h; y += 1L) {
            java.util.ArrayList<Long> row = new java.util.ArrayList<Long>();
            for (long x = 0L; x < w; x += 1L) {
                long cnt = 0L;
                for (long dy = (-(1L)); dy < 2L; dy += 1L) {
                    for (long dx = (-(1L)); dx < 2L; dx += 1L) {
                        if ((((dx) != (0L)) || ((dy) != (0L)))) {
                            long nx = (x + dx + w) % w;
                            long ny = (y + dy + h) % h;
                            cnt += ((Long)(((java.util.ArrayList<Object>)(Object)(grid.get((int)((((ny) < 0L) ? (((long)(grid.size())) + (ny)) : (ny)))))).get((int)((((nx) < 0L) ? (((long)(((java.util.ArrayList<Object>)(Object)(grid.get((int)((((ny) < 0L) ? (((long)(grid.size())) + (ny)) : (ny)))))).size())) + (nx)) : (nx))))));
                        }
                    }
                }
                long alive = ((Long)(((java.util.ArrayList<Object>)(Object)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).get((int)((((x) < 0L) ? (((long)(((java.util.ArrayList<Object>)(Object)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).size())) + (x)) : (x))))));
                if ((((alive) == (1L)) && (((cnt) == (2L)) || ((cnt) == (3L))))) {
                    row.add(1L);
                } else {
                    if ((((alive) == (0L)) && ((cnt) == (3L)))) {
                        row.add(1L);
                    } else {
                        row.add(0L);
                    }
                }
            }
            nxt.add(row);
        }
        return nxt;
    }

    public static java.util.ArrayList<Long> render(java.util.ArrayList<java.util.ArrayList<Long>> grid, long w, long h, long cell) {
        long width = w * cell;
        long height = h * cell;
        java.util.ArrayList<Long> frame = PyRuntime.__pytra_bytearray(width * height);
        for (long y = 0L; y < h; y += 1L) {
            for (long x = 0L; x < w; x += 1L) {
                long v = (((((Long)(((java.util.ArrayList<Object>)(Object)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).get((int)((((x) < 0L) ? (((long)(((java.util.ArrayList<Object>)(Object)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).size())) + (x)) : (x)))))) != 0L)) ? (255L) : (0L));
                for (long yy = 0L; yy < cell; yy += 1L) {
                    long base = (y * cell + yy) * width + x * cell;
                    for (long xx = 0L; xx < cell; xx += 1L) {
                        frame.set((int)((((base + xx) < 0L) ? (((long)(frame.size())) + (base + xx)) : (base + xx))), v);
                    }
                }
            }
        }
        return PyRuntime.__pytra_bytearray(frame);
    }

    public static void run_07_game_of_life_loop() {
        long w = 144L;
        long h = 108L;
        long cell = 4L;
        long steps = 105L;
        String out_path = "sample/out/07_game_of_life_loop.gif";
        double start = time.perf_counter();
        java.util.ArrayList<java.util.ArrayList<Long>> grid = new java.util.ArrayList<java.util.ArrayList<Long>>();
        for (long __ = 0L; __ < h; __ += 1L) {
            grid.add(PyRuntime.__pytra_list_repeat(0L, w));
        }
        for (long y = 0L; y < h; y += 1L) {
            for (long x = 0L; x < w; x += 1L) {
                long noise = (x * 37L + y * 73L + x * y % 19L + (x + y) % 11L) % 97L;
                if (((noise) < (3L))) {
                    ((java.util.ArrayList<Object>)(Object)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).set((int)((((x) < 0L) ? (((long)(((java.util.ArrayList<Object>)(Object)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).size())) + (x)) : (x))), 1L);
                }
            }
        }
        java.util.ArrayList<java.util.ArrayList<Long>> glider = new java.util.ArrayList<java.util.ArrayList<Long>>(java.util.Arrays.asList(new java.util.ArrayList<Long>(java.util.Arrays.asList(0L, 1L, 0L)), new java.util.ArrayList<Long>(java.util.Arrays.asList(0L, 0L, 1L)), new java.util.ArrayList<Long>(java.util.Arrays.asList(1L, 1L, 1L))));
        java.util.ArrayList<java.util.ArrayList<Long>> r_pentomino = new java.util.ArrayList<java.util.ArrayList<Long>>(java.util.Arrays.asList(new java.util.ArrayList<Long>(java.util.Arrays.asList(0L, 1L, 1L)), new java.util.ArrayList<Long>(java.util.Arrays.asList(1L, 1L, 0L)), new java.util.ArrayList<Long>(java.util.Arrays.asList(0L, 1L, 0L))));
        java.util.ArrayList<java.util.ArrayList<Long>> lwss = new java.util.ArrayList<java.util.ArrayList<Long>>(java.util.Arrays.asList(new java.util.ArrayList<Long>(java.util.Arrays.asList(0L, 1L, 1L, 1L, 1L)), new java.util.ArrayList<Long>(java.util.Arrays.asList(1L, 0L, 0L, 0L, 1L)), new java.util.ArrayList<Long>(java.util.Arrays.asList(0L, 0L, 0L, 0L, 1L)), new java.util.ArrayList<Long>(java.util.Arrays.asList(1L, 0L, 0L, 1L, 0L))));
        for (long gy = 8L; gy < h - 8L; gy += 18L) {
            for (long gx = 8L; gx < w - 8L; gx += 22L) {
                long kind = (gx * 7L + gy * 11L) % 3L;
                long ph = 0L;
                long pw = 0L;
                long px = 0L;
                long py = 0L;
                if (((kind) == (0L))) {
                    ph = ((long)(glider.size()));
                    for (py = 0L; py < ph; py += 1L) {
                        pw = ((long)(((java.util.ArrayList<Object>)(Object)(glider.get((int)((((py) < 0L) ? (((long)(glider.size())) + (py)) : (py)))))).size()));
                        for (px = 0L; px < pw; px += 1L) {
                            if (((((Long)(((java.util.ArrayList<Object>)(Object)(glider.get((int)((((py) < 0L) ? (((long)(glider.size())) + (py)) : (py)))))).get((int)((((px) < 0L) ? (((long)(((java.util.ArrayList<Object>)(Object)(glider.get((int)((((py) < 0L) ? (((long)(glider.size())) + (py)) : (py)))))).size())) + (px)) : (px))))))) == (1L))) {
                                ((java.util.ArrayList<Object>)(Object)(grid.get((int)(((((gy + py) % h) < 0L) ? (((long)(grid.size())) + ((gy + py) % h)) : ((gy + py) % h)))))).set((int)(((((gx + px) % w) < 0L) ? (((long)(((java.util.ArrayList<Object>)(Object)(grid.get((int)(((((gy + py) % h) < 0L) ? (((long)(grid.size())) + ((gy + py) % h)) : ((gy + py) % h)))))).size())) + ((gx + px) % w)) : ((gx + px) % w))), 1L);
                            }
                        }
                    }
                } else {
                    if (((kind) == (1L))) {
                        ph = ((long)(r_pentomino.size()));
                        for (py = 0L; py < ph; py += 1L) {
                            pw = ((long)(((java.util.ArrayList<Object>)(Object)(r_pentomino.get((int)((((py) < 0L) ? (((long)(r_pentomino.size())) + (py)) : (py)))))).size()));
                            for (px = 0L; px < pw; px += 1L) {
                                if (((((Long)(((java.util.ArrayList<Object>)(Object)(r_pentomino.get((int)((((py) < 0L) ? (((long)(r_pentomino.size())) + (py)) : (py)))))).get((int)((((px) < 0L) ? (((long)(((java.util.ArrayList<Object>)(Object)(r_pentomino.get((int)((((py) < 0L) ? (((long)(r_pentomino.size())) + (py)) : (py)))))).size())) + (px)) : (px))))))) == (1L))) {
                                    ((java.util.ArrayList<Object>)(Object)(grid.get((int)(((((gy + py) % h) < 0L) ? (((long)(grid.size())) + ((gy + py) % h)) : ((gy + py) % h)))))).set((int)(((((gx + px) % w) < 0L) ? (((long)(((java.util.ArrayList<Object>)(Object)(grid.get((int)(((((gy + py) % h) < 0L) ? (((long)(grid.size())) + ((gy + py) % h)) : ((gy + py) % h)))))).size())) + ((gx + px) % w)) : ((gx + px) % w))), 1L);
                                }
                            }
                        }
                    } else {
                        ph = ((long)(lwss.size()));
                        for (py = 0L; py < ph; py += 1L) {
                            pw = ((long)(((java.util.ArrayList<Object>)(Object)(lwss.get((int)((((py) < 0L) ? (((long)(lwss.size())) + (py)) : (py)))))).size()));
                            for (px = 0L; px < pw; px += 1L) {
                                if (((((Long)(((java.util.ArrayList<Object>)(Object)(lwss.get((int)((((py) < 0L) ? (((long)(lwss.size())) + (py)) : (py)))))).get((int)((((px) < 0L) ? (((long)(((java.util.ArrayList<Object>)(Object)(lwss.get((int)((((py) < 0L) ? (((long)(lwss.size())) + (py)) : (py)))))).size())) + (px)) : (px))))))) == (1L))) {
                                    ((java.util.ArrayList<Object>)(Object)(grid.get((int)(((((gy + py) % h) < 0L) ? (((long)(grid.size())) + ((gy + py) % h)) : ((gy + py) % h)))))).set((int)(((((gx + px) % w) < 0L) ? (((long)(((java.util.ArrayList<Object>)(Object)(grid.get((int)(((((gy + py) % h) < 0L) ? (((long)(grid.size())) + ((gy + py) % h)) : ((gy + py) % h)))))).size())) + ((gx + px) % w)) : ((gx + px) % w))), 1L);
                                }
                            }
                        }
                    }
                }
            }
        }
        java.util.ArrayList<java.util.ArrayList<Long>> frames = new java.util.ArrayList<java.util.ArrayList<Long>>();
        for (long __ = 0L; __ < steps; __ += 1L) {
            frames.add(render(grid, w, h, cell));
            grid = next_state(grid, w, h);
        }
        gif.save_gif(out_path, w * cell, h * cell, frames, gif.grayscale_palette(), 4L, 0L);
        double elapsed = time.perf_counter() - start;
        System.out.println(String.valueOf("output:") + " " + String.valueOf(out_path));
        System.out.println(String.valueOf("frames:") + " " + String.valueOf(steps));
        System.out.println(String.valueOf("elapsed_sec:") + " " + String.valueOf(elapsed));
    }

    public static void _case_main() {
        run_07_game_of_life_loop();
    }
}
