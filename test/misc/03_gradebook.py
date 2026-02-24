from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean
from typing import Dict, List


@dataclass
class Student:
    name: str
    scores: Dict[str, float] = field(default_factory=dict)

    def average(self) -> float:
        return mean(self.scores.values()) if self.scores else 0.0

    def as_dict(self) -> Dict[str, float]:
        result = {subject: value for subject, value in self.scores.items()}
        result["average"] = self.average()
        return result


class GradeBook:
    def __init__(self):
        self.students: Dict[str, Student] = {}

    def add_student(self, name: str) -> None:
        self.students[name] = Student(name)

    def add_score(self, name: str, subject: str, score: float) -> None:
        if name not in self.students:
            self.add_student(name)
        self.students[name].scores[subject] = score

    def class_average(self) -> float:
        if not self.students:
            return 0.0
        return mean([s.average() for s in self.students.values()])

    def top_students(self, n: int = 3) -> List[Student]:
        return sorted(self.students.values(), key=lambda s: s.average(), reverse=True)[:n]

    def subject_report(self, subject: str) -> Dict[str, float]:
        values = [s.scores[subject] for s in self.students.values() if subject in s.scores]
        if not values:
            return {"count": 0, "avg": 0.0, "min": 0.0, "max": 0.0}
        return {
            "count": len(values),
            "avg": mean(values),
            "min": min(values),
            "max": max(values),
        }

    def printable(self) -> str:
        lines = [f"class average={self.class_average():.2f}"]
        for student in sorted(self.students.values(), key=lambda s: s.name):
            lines.append(f"{student.name}: {student.average():.2f}")
        return "\n".join(lines)


def main() -> None:
    book = GradeBook()
    book.add_score("alice", "math", 92)
    book.add_score("alice", "science", 88)
    book.add_score("bob", "math", 78)
    book.add_score("bob", "science", 80)
    book.add_score("charlie", "math", 95)
    book.add_score("charlie", "science", 99)
    book.add_score("dana", "math", 65)

    print(book.printable())
    print("top", [s.name for s in book.top_students(2)])
    print("math", book.subject_report("math"))
    print("science", book.subject_report("science"))


if __name__ == "__main__":
    main()


def _format_subject_report(book: GradeBook, subjects: list[str]) -> dict[str, dict[str, float]]:
    return {subject: book.subject_report(subject) for subject in subjects}


def _extended_grade_demo() -> None:
    book = GradeBook()
    book.add_score("emma", "math", 84)
    book.add_score("emma", "science", 91)
    book.add_score("leo", "math", 70)
    book.add_score("leo", "science", 58)
    book.add_score("mia", "math", 99)
    book.add_score("mia", "science", 100)

    print(book.printable())
    print("top_students", [s.name for s in book.top_students()])
    print("at_risk", [s.name for s in book.students.values() if s.average() < 70])
    print("subject_summary", _format_subject_report(book, ["math", "science"]))
    print("detailed", {name: student.as_dict() for name, student in book.students.items()})


if __name__ == "__main__":
    _extended_grade_demo()
