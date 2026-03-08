from abc import ABC, abstractmethod


class AIProvider(ABC):
    @abstractmethod
    def solve_problem(self, question: str, mode: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def generate_practice(self, seed_text: str, difficulty: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def generate_flashcards(self, source_text: str) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def summarize_lecture(self, content: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def tutor_chat(self, message: str, subject: str, mode: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def analyze_mistake(self, question: str, user_answer: str, correct_answer: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def generate_study_plan(self, payload: dict) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def generate_hints(self, question: str) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def detect_learning_style(self, telemetry: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def scan_knowledge_gaps(self, profile: dict) -> dict:
        raise NotImplementedError

    def generate_exam_questions(
        self,
        subject: str,
        topic: str,
        difficulty: str,
        style: str,
        question_count: int,
    ) -> list[dict] | None:
        return None

