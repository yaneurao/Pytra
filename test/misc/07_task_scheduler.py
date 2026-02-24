from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Job:
    name: str
    duration: int
    deps: List[str] = field(default_factory=list)


class Scheduler:
    def __init__(self, jobs: List[Job]):
        self.jobs = {job.name: job for job in jobs}

    def topo_order(self) -> List[str]:
        indeg = defaultdict(int)
        graph = defaultdict(list)
        for job in self.jobs.values():
            indeg[job.name] += 0
            for dep in job.deps:
                graph[dep].append(job.name)
                indeg[job.name] += 1

        q = deque([name for name in self.jobs if indeg[name] == 0])
        order = []
        while q:
            node = q.popleft()
            order.append(node)
            for nxt in graph[node]:
                indeg[nxt] -= 1
                if indeg[nxt] == 0:
                    q.append(nxt)

        if len(order) != len(self.jobs):
            raise RuntimeError("cycle detected")
        return order

    def total_time(self, order: List[str]) -> int:
        return sum(self.jobs[name].duration for name in order)

    def timeline(self, order: List[str]) -> Dict[str, tuple[int, int]]:
        t = 0
        windows: Dict[str, tuple[int, int]] = {}
        for name in order:
            job = self.jobs[name]
            windows[name] = (t, t + job.duration)
            t += job.duration
        return windows


def main() -> None:
    jobs = [
        Job("design", 2, []),
        Job("backend", 4, ["design"]),
        Job("frontend", 3, ["design"]),
        Job("qa", 2, ["backend", "frontend"]),
        Job("deploy", 1, ["qa"]),
    ]
    scheduler = Scheduler(jobs)
    order = scheduler.topo_order()
    print("order", order)
    print("total_time", scheduler.total_time(order))
    print("timeline", scheduler.timeline(order))


if __name__ == "__main__":
    main()


def _build_chain() -> list[str]:
    jobs = [
        Job("init", 1, []),
        Job("fetch", 1, ["init"]),
        Job("process", 2, ["fetch"]),
        Job("finalize", 1, ["process"]),
    ]
    scheduler = Scheduler(jobs)
    order = scheduler.topo_order()
    return order


def _scheduler_demo() -> None:
    print("chain_order", _build_chain())
    print("chain_total", Scheduler([Job("init", 1, []), Job("fetch", 1, ["init"])]).total_time(["init", "fetch"]))


if __name__ == "__main__":
    _scheduler_demo()
