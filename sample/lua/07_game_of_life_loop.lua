-- from __future__ import annotations as annotations (not yet mapped)
-- from time import perf_counter as perf_counter (not yet mapped)
-- from pytra.utils.gif import grayscale_palette as grayscale_palette (not yet mapped)
-- from pytra.utils.gif import save_gif as save_gif (not yet mapped)

-- 07: Sample that outputs Game of Life evolution as a GIF.

function next_state(grid, w, h)
    local nxt = {  }
    for y = 0, (h) - 1, 1 do
        local row = {  }
        for x = 0, (w) - 1, 1 do
            cnt = 0
            for dy = (-1), (2) - 1, 1 do
                for dx = (-1), (2) - 1, 1 do
                    if ((dx ~= 0) or (dy ~= 0)) then
                        nx = (((x + dx) + w) % w)
                        ny = (((y + dy) + h) % h)
                        cnt = cnt + grid[(ny) + 1][(nx) + 1]
                    end
                end
            end
            alive = grid[(y) + 1][(x) + 1]
            if ((alive == 1) and ((cnt == 2) or (cnt == 3))) then
                row:append(1)
            else
                if ((alive == 0) and (cnt == 3)) then
                    row:append(1)
                else
                    row:append(0)
                end
            end
        end
        nxt:append(row)
    end
    return nxt
end

function render(grid, w, h, cell)
    width = (w * cell)
    height = (h * cell)
    frame = bytearray((width * height))
    for y = 0, (h) - 1, 1 do
        for x = 0, (w) - 1, 1 do
            v = ((grid[(y) + 1][(x) + 1]) and (255) or (0))
            for yy = 0, (cell) - 1, 1 do
                base = ((((y * cell) + yy) * width) + (x * cell))
                for xx = 0, (cell) - 1, 1 do
                    frame[((base + xx)) + 1] = v
                end
            end
        end
    end
    return bytes(frame)
end

function run_07_game_of_life_loop()
    w = 144
    h = 108
    cell = 4
    steps = 105
    out_path = "sample/out/07_game_of_life_loop.gif"
    
    start = perf_counter()
    local grid = (function() local __lc_out_2 = {}; for __lc_i_1 = 0, (h) - 1, 1 do table.insert(__lc_out_2, ({ 0 } * w)) end; return __lc_out_2 end)()
    
    -- Lay down sparse noise so the whole field is less likely to stabilize too early.
    -- Avoid large integer literals so all transpilers handle the expression consistently.
    for y = 0, (h) - 1, 1 do
        for x = 0, (w) - 1, 1 do
            noise = (((((x * 37) + (y * 73)) + ((x * y) % 19)) + ((x + y) % 11)) % 97)
            if (noise < 3) then
                grid[(y) + 1][(x) + 1] = 1
            end
        end
    end
    -- Place multiple well-known long-lived patterns.
    glider = { { 0, 1, 0 }, { 0, 0, 1 }, { 1, 1, 1 } }
    r_pentomino = { { 0, 1, 1 }, { 1, 1, 0 }, { 0, 1, 0 } }
    lwss = { { 0, 1, 1, 1, 1 }, { 1, 0, 0, 0, 1 }, { 0, 0, 0, 0, 1 }, { 1, 0, 0, 1, 0 } }
    
    for gy = 8, ((h - 8)) - 1, 18 do
        for gx = 8, ((w - 8)) - 1, 22 do
            kind = (((gx * 7) + (gy * 11)) % 3)
            if (kind == 0) then
                ph = len(glider)
                for py = 0, (ph) - 1, 1 do
                    pw = len(glider[(py) + 1])
                    for px = 0, (pw) - 1, 1 do
                        if (glider[(py) + 1][(px) + 1] == 1) then
                            grid[(((gy + py) % h)) + 1][(((gx + px) % w)) + 1] = 1
                        end
                    end
                end
            else
                if (kind == 1) then
                    ph = len(r_pentomino)
                    for py = 0, (ph) - 1, 1 do
                        pw = len(r_pentomino[(py) + 1])
                        for px = 0, (pw) - 1, 1 do
                            if (r_pentomino[(py) + 1][(px) + 1] == 1) then
                                grid[(((gy + py) % h)) + 1][(((gx + px) % w)) + 1] = 1
                            end
                        end
                    end
                else
                    ph = len(lwss)
                    for py = 0, (ph) - 1, 1 do
                        pw = len(lwss[(py) + 1])
                        for px = 0, (pw) - 1, 1 do
                            if (lwss[(py) + 1][(px) + 1] == 1) then
                                grid[(((gy + py) % h)) + 1][(((gx + px) % w)) + 1] = 1
                            end
                        end
                    end
                end
            end
        end
    end
    local frames = {  }
    for _ = 0, (steps) - 1, 1 do
        frames:append(render(grid, w, h, cell))
        grid = next_state(grid, w, h)
    end
    save_gif(out_path, (w * cell), (h * cell), frames, grayscale_palette())
    elapsed = (perf_counter() - start)
    print("output:", out_path)
    print("frames:", steps)
    print("elapsed_sec:", elapsed)
end


run_07_game_of_life_loop()
