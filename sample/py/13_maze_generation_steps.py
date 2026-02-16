# 13: DFS迷路生成の進行状況をGIF出力するサンプル。

from __future__ import annotations

from time import perf_counter

from py_module.gif_helper import grayscale_palette, save_gif


def capture(grid: list[list[int]], w: int, h: int, scale: int) -> bytes:
    width = w * scale
    height = h * scale
    frame = bytearray(width * height)
    y = 0
    while y < h:
        x = 0
        while x < w:
            v = 255 if grid[y][x] == 0 else 40
            yy = 0
            while yy < scale:
                base = (y * scale + yy) * width + x * scale
                xx = 0
                while xx < scale:
                    frame[base + xx] = v
                    xx += 1
                yy += 1
            x += 1
        y += 1
    return bytes(frame)


def run_13_maze_generation_steps() -> None:
    cell_w = 61
    cell_h = 45
    scale = 4
    out_path = "sample/out/13_maze_generation_steps.gif"

    start = perf_counter()
    grid: list[list[int]] = []
    gy = 0
    while gy < cell_h:
        row: list[int] = []
        gx = 0
        while gx < cell_w:
            row.append(1)
            gx += 1
        grid.append(row)
        gy += 1
    stack: list[tuple[int, int]] = [(1, 1)]
    grid[1][1] = 0

    dirs: list[tuple[int, int]] = [(2, 0), (-2, 0), (0, 2), (0, -2)]
    frames: list[bytes] = []
    step = 0

    while len(stack) > 0:
        x, y = stack[-1]
        candidates: list[tuple[int, int, int, int]] = []
        k = 0
        while k < 4:
            dx, dy = dirs[k]
            nx = x + dx
            ny = y + dy
            if nx >= 1 and nx < cell_w - 1 and ny >= 1 and ny < cell_h - 1 and grid[ny][nx] == 1:
                if dx == 2:
                    candidates.append((nx, ny, x + 1, y))
                elif dx == -2:
                    candidates.append((nx, ny, x - 1, y))
                elif dy == 2:
                    candidates.append((nx, ny, x, y + 1))
                else:
                    candidates.append((nx, ny, x, y - 1))
            k += 1

        if len(candidates) == 0:
            stack.pop()
        else:
            sel = candidates[(x * 17 + y * 29 + len(stack) * 13) % len(candidates)]
            nx, ny, wx, wy = sel
            grid[wy][wx] = 0
            grid[ny][nx] = 0
            stack.append((nx, ny))

        if step % 25 == 0:
            frames.append(capture(grid, cell_w, cell_h, scale))
        step += 1

    frames.append(capture(grid, cell_w, cell_h, scale))
    save_gif(out_path, cell_w * scale, cell_h * scale, frames, grayscale_palette(), delay_cs=4, loop=0)
    elapsed = perf_counter() - start
    print("output:", out_path)
    print("frames:", len(frames))
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_13_maze_generation_steps()
