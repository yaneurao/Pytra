def fmt(step: int, num_steps: int, loss: float) -> str:
    return f"step {step+1:4d} / {num_steps:4d} | loss {loss:.4f}"


if __name__ == "__main__":
    print(fmt(0, 100, 2.3456))
