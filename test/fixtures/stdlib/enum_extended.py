from pylib.assertions import py_assert_stdout
from pylib.enum import Enum, IntEnum, IntFlag


class Color(Enum):
    RED = 1
    BLUE = 2


class Status(IntEnum):
    OK = 0
    ERROR = 1


class Perm(IntFlag):
    READ = 1
    WRITE = 2
    EXEC = 4


def main() -> None:
    print(Color.RED == Color.RED)
    print(Color.RED == Color.BLUE)
    print(Status.OK == 0)
    print(int(Status.ERROR))
    rw = Perm.READ | Perm.WRITE
    print(int(rw))
    print(int(rw & Perm.WRITE))
    print(int(rw ^ Perm.WRITE))


def _case_main() -> None:
    main()


if __name__ == "__main__":
    print(py_assert_stdout(["True", "False", "True", "1", "3", "2", "1"], _case_main))
