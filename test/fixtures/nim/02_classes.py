
class User:
    id: int
    name: str

    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name

    def get_info(self) -> str:
        return "User: " + self.name

if __name__ == "__main__":
    u = User(1, "Alice")
    print(u.get_info())
