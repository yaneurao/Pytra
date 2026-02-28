// Auto-generated Java native source from EAST3.
public final class Pytra_07_game_of_life_loop {
    private Pytra_07_game_of_life_loop() {
    }


    // 07: Sample that outputs Game of Life evolution as a GIF.

    public static java.util.ArrayList<Object> next_state(java.util.ArrayList<Object> grid, long w, long h) {
        java.util.ArrayList<Object> nxt = new java.util.ArrayList<Object>(java.util.Arrays.asList());
        long __step_0 = 1L;
        for (long y = 0L; (__step_0 >= 0L) ? (y < h) : (y > h); y += __step_0) {
            java.util.ArrayList<Object> row = new java.util.ArrayList<Object>(java.util.Arrays.asList());
            long __step_1 = 1L;
            for (long x = 0L; (__step_1 >= 0L) ? (x < w) : (x > w); x += __step_1) {
                long cnt = 0L;
                long __step_2 = 1L;
                for (long dy = (-1L); (__step_2 >= 0L) ? (dy < 2L) : (dy > 2L); dy += __step_2) {
                    long __step_3 = 1L;
                    for (long dx = (-1L); (__step_3 >= 0L) ? (dx < 2L) : (dx > 2L); dx += __step_3) {
                        if (((dx != 0L) || (dy != 0L))) {
                            long nx = (((x + dx) + w) % w);
                            long ny = (((y + dy) + h) % h);
                            cnt += ((Long)(((java.util.ArrayList<Object>)(grid.get((int)((((ny) < 0L) ? (((long)(grid.size())) + (ny)) : (ny)))))).get((int)((((nx) < 0L) ? (((long)(((java.util.ArrayList<Object>)(grid.get((int)((((ny) < 0L) ? (((long)(grid.size())) + (ny)) : (ny)))))).size())) + (nx)) : (nx))))));
                        }
                    }
                }
                long alive = ((Long)(((java.util.ArrayList<Object>)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).get((int)((((x) < 0L) ? (((long)(((java.util.ArrayList<Object>)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).size())) + (x)) : (x))))));
                if (((alive == 1L) && ((cnt == 2L) || (cnt == 3L)))) {
                    row.add(1L);
                } else {
                    if (((alive == 0L) && (cnt == 3L))) {
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

    public static java.util.ArrayList<Long> render(java.util.ArrayList<Object> grid, long w, long h, long cell) {
        long width = (w * cell);
        long height = (h * cell);
        java.util.ArrayList<Long> frame = PyRuntime.__pytra_bytearray((width * height));
        long __step_0 = 1L;
        for (long y = 0L; (__step_0 >= 0L) ? (y < h) : (y > h); y += __step_0) {
            long __step_1 = 1L;
            for (long x = 0L; (__step_1 >= 0L) ? (x < w) : (x > w); x += __step_1) {
                long v = (((((Long)(((java.util.ArrayList<Object>)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).get((int)((((x) < 0L) ? (((long)(((java.util.ArrayList<Object>)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).size())) + (x)) : (x)))))) != 0L)) ? (255L) : (0L));
                long __step_2 = 1L;
                for (long yy = 0L; (__step_2 >= 0L) ? (yy < cell) : (yy > cell); yy += __step_2) {
                    long base = ((((y * cell) + yy) * width) + (x * cell));
                    long __step_3 = 1L;
                    for (long xx = 0L; (__step_3 >= 0L) ? (xx < cell) : (xx > cell); xx += __step_3) {
                        frame.set((int)(((((base + xx)) < 0L) ? (((long)(frame.size())) + ((base + xx))) : ((base + xx)))), v);
                    }
                }
            }
        }
        return new java.util.ArrayList<Long>(frame);
    }

    public static void run_07_game_of_life_loop() {
        long w = 144L;
        long h = 108L;
        long cell = 4L;
        long steps = 105L;
        String out_path = "sample/out/07_game_of_life_loop.gif";
        double start = (System.nanoTime() / 1000000000.0);
        java.util.ArrayList<Object> grid = new java.util.ArrayList<Object>();
        long __step_0 = 1L;
        for (long __ = 0L; (__step_0 >= 0L) ? (__ < h) : (__ > h); __ += __step_0) {
            grid.add(PyRuntime.__pytra_list_repeat(0L, w));
        }
        long __step_1 = 1L;
        for (long y = 0L; (__step_1 >= 0L) ? (y < h) : (y > h); y += __step_1) {
            long __step_2 = 1L;
            for (long x = 0L; (__step_2 >= 0L) ? (x < w) : (x > w); x += __step_2) {
                long noise = (((((x * 37L) + (y * 73L)) + ((x * y) % 19L)) + ((x + y) % 11L)) % 97L);
                if ((noise < 3L)) {
                    ((java.util.ArrayList<Object>)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).set((int)((((x) < 0L) ? (((long)(((java.util.ArrayList<Object>)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).size())) + (x)) : (x))), 1L);
                }
            }
        }
        java.util.ArrayList<Object> glider = new java.util.ArrayList<Object>(java.util.Arrays.asList(new java.util.ArrayList<Object>(java.util.Arrays.asList(0L, 1L, 0L)), new java.util.ArrayList<Object>(java.util.Arrays.asList(0L, 0L, 1L)), new java.util.ArrayList<Object>(java.util.Arrays.asList(1L, 1L, 1L))));
        java.util.ArrayList<Object> r_pentomino = new java.util.ArrayList<Object>(java.util.Arrays.asList(new java.util.ArrayList<Object>(java.util.Arrays.asList(0L, 1L, 1L)), new java.util.ArrayList<Object>(java.util.Arrays.asList(1L, 1L, 0L)), new java.util.ArrayList<Object>(java.util.Arrays.asList(0L, 1L, 0L))));
        java.util.ArrayList<Object> lwss = new java.util.ArrayList<Object>(java.util.Arrays.asList(new java.util.ArrayList<Object>(java.util.Arrays.asList(0L, 1L, 1L, 1L, 1L)), new java.util.ArrayList<Object>(java.util.Arrays.asList(1L, 0L, 0L, 0L, 1L)), new java.util.ArrayList<Object>(java.util.Arrays.asList(0L, 0L, 0L, 0L, 1L)), new java.util.ArrayList<Object>(java.util.Arrays.asList(1L, 0L, 0L, 1L, 0L))));
        long __step_3 = 18L;
        for (long gy = 8L; (__step_3 >= 0L) ? (gy < (h - 8L)) : (gy > (h - 8L)); gy += __step_3) {
            long __step_4 = 22L;
            for (long gx = 8L; (__step_4 >= 0L) ? (gx < (w - 8L)) : (gx > (w - 8L)); gx += __step_4) {
                long kind = (((gx * 7L) + (gy * 11L)) % 3L);
                if ((kind == 0L)) {
                    long ph = ((long)(glider.size()));
                    long __step_5 = 1L;
                    for (long py = 0L; (__step_5 >= 0L) ? (py < ph) : (py > ph); py += __step_5) {
                        long pw = ((long)(((java.util.ArrayList<Object>)(glider.get((int)((((py) < 0L) ? (((long)(glider.size())) + (py)) : (py)))))).size()));
                        long __step_6 = 1L;
                        for (long px = 0L; (__step_6 >= 0L) ? (px < pw) : (px > pw); px += __step_6) {
                            if ((((Long)(((java.util.ArrayList<Object>)(glider.get((int)((((py) < 0L) ? (((long)(glider.size())) + (py)) : (py)))))).get((int)((((px) < 0L) ? (((long)(((java.util.ArrayList<Object>)(glider.get((int)((((py) < 0L) ? (((long)(glider.size())) + (py)) : (py)))))).size())) + (px)) : (px)))))) == 1L)) {
                                ((java.util.ArrayList<Object>)(grid.get((int)((((((gy + py) % h)) < 0L) ? (((long)(grid.size())) + (((gy + py) % h))) : (((gy + py) % h))))))).set((int)((((((gx + px) % w)) < 0L) ? (((long)(((java.util.ArrayList<Object>)(grid.get((int)((((((gy + py) % h)) < 0L) ? (((long)(grid.size())) + (((gy + py) % h))) : (((gy + py) % h))))))).size())) + (((gx + px) % w))) : (((gx + px) % w)))), 1L);
                            }
                        }
                    }
                } else {
                    if ((kind == 1L)) {
                        long ph = ((long)(r_pentomino.size()));
                        long __step_7 = 1L;
                        for (long py = 0L; (__step_7 >= 0L) ? (py < ph) : (py > ph); py += __step_7) {
                            long pw = ((long)(((java.util.ArrayList<Object>)(r_pentomino.get((int)((((py) < 0L) ? (((long)(r_pentomino.size())) + (py)) : (py)))))).size()));
                            long __step_8 = 1L;
                            for (long px = 0L; (__step_8 >= 0L) ? (px < pw) : (px > pw); px += __step_8) {
                                if ((((Long)(((java.util.ArrayList<Object>)(r_pentomino.get((int)((((py) < 0L) ? (((long)(r_pentomino.size())) + (py)) : (py)))))).get((int)((((px) < 0L) ? (((long)(((java.util.ArrayList<Object>)(r_pentomino.get((int)((((py) < 0L) ? (((long)(r_pentomino.size())) + (py)) : (py)))))).size())) + (px)) : (px)))))) == 1L)) {
                                    ((java.util.ArrayList<Object>)(grid.get((int)((((((gy + py) % h)) < 0L) ? (((long)(grid.size())) + (((gy + py) % h))) : (((gy + py) % h))))))).set((int)((((((gx + px) % w)) < 0L) ? (((long)(((java.util.ArrayList<Object>)(grid.get((int)((((((gy + py) % h)) < 0L) ? (((long)(grid.size())) + (((gy + py) % h))) : (((gy + py) % h))))))).size())) + (((gx + px) % w))) : (((gx + px) % w)))), 1L);
                                }
                            }
                        }
                    } else {
                        long ph = ((long)(lwss.size()));
                        long __step_9 = 1L;
                        for (long py = 0L; (__step_9 >= 0L) ? (py < ph) : (py > ph); py += __step_9) {
                            long pw = ((long)(((java.util.ArrayList<Object>)(lwss.get((int)((((py) < 0L) ? (((long)(lwss.size())) + (py)) : (py)))))).size()));
                            long __step_10 = 1L;
                            for (long px = 0L; (__step_10 >= 0L) ? (px < pw) : (px > pw); px += __step_10) {
                                if ((((Long)(((java.util.ArrayList<Object>)(lwss.get((int)((((py) < 0L) ? (((long)(lwss.size())) + (py)) : (py)))))).get((int)((((px) < 0L) ? (((long)(((java.util.ArrayList<Object>)(lwss.get((int)((((py) < 0L) ? (((long)(lwss.size())) + (py)) : (py)))))).size())) + (px)) : (px)))))) == 1L)) {
                                    ((java.util.ArrayList<Object>)(grid.get((int)((((((gy + py) % h)) < 0L) ? (((long)(grid.size())) + (((gy + py) % h))) : (((gy + py) % h))))))).set((int)((((((gx + px) % w)) < 0L) ? (((long)(((java.util.ArrayList<Object>)(grid.get((int)((((((gy + py) % h)) < 0L) ? (((long)(grid.size())) + (((gy + py) % h))) : (((gy + py) % h))))))).size())) + (((gx + px) % w))) : (((gx + px) % w)))), 1L);
                                }
                            }
                        }
                    }
                }
            }
        }
        java.util.ArrayList<Object> frames = new java.util.ArrayList<Object>(java.util.Arrays.asList());
        long __step_11 = 1L;
        for (long __ = 0L; (__step_11 >= 0L) ? (__ < steps) : (__ > steps); __ += __step_11) {
            frames.add(render(grid, w, h, cell));
            grid = next_state(grid, w, h);
        }
        PyRuntime.__pytra_noop(out_path, (w * cell), (h * cell), frames, new java.util.ArrayList<Long>());
        double elapsed = ((System.nanoTime() / 1000000000.0) - start);
        System.out.println(String.valueOf("output:") + " " + String.valueOf(out_path));
        System.out.println(String.valueOf("frames:") + " " + String.valueOf(steps));
        System.out.println(String.valueOf("elapsed_sec:") + " " + String.valueOf(elapsed));
    }

    public static void main(String[] args) {
        run_07_game_of_life_loop();
    }
}
