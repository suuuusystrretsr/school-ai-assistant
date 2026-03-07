from datetime import date, timedelta

from app.services.ai.base import AIProvider


class MockAIProvider(AIProvider):
    def solve_problem(self, question: str, mode: str) -> dict:
        steps = [
            'Parse the question and identify known variables.',
            'Apply the relevant concept or formula.',
            'Compute the result and verify units/logic.',
        ]
        explanation = {
            'eli5': f'Think of it like a puzzle. Break it into pieces: {question[:80]}',
            'normal': f'Use structured reasoning for: {question[:140]}',
            'advanced': f'Formal derivation and edge-case checks for: {question[:140]}',
            'teacher': 'Socratic prompt sequence plus misconception checks.',
        }
        return {
            'final_answer': 'Mock answer: 42 (replace with real model output).',
            'steps': steps,
            'explanations': explanation,
            'confidence_score': 78,
        }

    def generate_practice(self, seed_text: str, difficulty: str) -> dict:
        levels = ['easy', 'medium', 'hard']
        questions = [
            {'level': level, 'question': f'{level.title()} variant based on: {seed_text[:60]}'}
            for level in levels
        ]
        return {
            'title': f'Practice Pack ({difficulty})',
            'questions': questions,
            'answer_key': [{'q': i + 1, 'answer': f'Answer {i + 1}'} for i in range(3)],
            'worked_solutions': [{'q': i + 1, 'solution': f'Worked solution {i + 1}'} for i in range(3)],
        }

    def generate_flashcards(self, source_text: str) -> list[dict]:
        return [
            {
                'question': 'What is the core definition from the notes?',
                'answer': source_text[:100],
                'topic_tags': ['core-concept'],
                'difficulty_tag': 'easy',
            },
            {
                'question': 'How does this concept apply in practice?',
                'answer': 'Apply it step-by-step with an example.',
                'topic_tags': ['application'],
                'difficulty_tag': 'medium',
            },
        ]

    def summarize_lecture(self, content: str) -> dict:
        return {
            'summary': f'Concise lecture summary: {content[:160]}',
            'key_concepts': ['Concept A', 'Concept B', 'Concept C'],
            'flashcards': self.generate_flashcards(content),
            'practice_questions': [
                {'question': 'Explain Concept A in your own words.'},
                {'question': 'Compare Concept B and C.'},
            ],
            'revision_notes': ['Revise formulas', 'Review example problems', 'Self-test in 24h'],
        }

    def tutor_chat(self, message: str, subject: str, mode: str) -> dict:
        return {
            'reply': f'Tutor ({subject}, {mode}) says: break down "{message[:80]}" with examples.',
            'follow_up_question': 'Can you solve a similar problem now?',
            'mini_quiz': [
                {'question': f'{subject} quick check #1', 'answer': 'Sample answer'},
                {'question': f'{subject} quick check #2', 'answer': 'Sample answer'},
            ],
            'adaptive_path': ['Review fundamentals', 'Practice medium set', 'Do timed quiz'],
        }

    def analyze_mistake(self, question: str, user_answer: str, correct_answer: str) -> dict:
        return {
            'why_wrong': f'Your answer "{user_answer}" does not match expected result "{correct_answer}".',
            'logic_break': 'The error happened during transformation from step 2 to step 3.',
            'correct_thinking': f'Start from definitions, then validate each operation for "{question[:80]}".',
            'avoid_next_time': [
                'Underline units and signs before calculation.',
                'Do a reverse-check on the final answer.',
                'Write one sentence explaining your strategy first.',
            ],
        }

    def generate_study_plan(self, payload: dict) -> list[dict]:
        today = date.today()
        weak_topics = payload.get('weak_topics', ['Foundations'])
        return [
            {
                'subject': exam['subject'],
                'topic': weak_topics[idx % len(weak_topics)],
                'due_date': (today + timedelta(days=idx + 1)).isoformat(),
                'minutes': 45 + (idx % 2) * 15,
                'priority': 'high' if idx < 2 else 'medium',
                'task_type': 'practice',
                'recommendations': ['Active recall', 'Timed practice', 'Error log review'],
            }
            for idx, exam in enumerate(payload.get('exams', []))
        ]

    def generate_hints(self, question: str) -> list[str]:
        return [
            f'Small hint: identify what the question asks in "{question[:60]}".',
            'Medium hint: write the governing formula or rule before solving.',
            'Strong hint: substitute known values and isolate the unknown.',
            'Almost-there hint: verify arithmetic and sign conventions.',
        ]

    def detect_learning_style(self, telemetry: dict) -> dict:
        if telemetry.get('practice_completed', 0) > telemetry.get('videos_watched', 0):
            style = 'practice-based'
        else:
            style = 'visual'
        return {
            'style': style,
            'confidence': 0.67,
            'evidence': ['completion behavior', 'time-on-task pattern', 'quiz interaction preference'],
        }

    def scan_knowledge_gaps(self, profile: dict) -> dict:
        weak = profile.get('weak_topics', ['algebra basics'])
        return {
            'missing_prerequisites': [f'Prerequisite for {topic}' for topic in weak],
            'foundational_review': ['Linear equations', 'Fractions and ratios', 'Core vocabulary'],
            'prerequisite_practice': [
                {'topic': 'Linear equations', 'set': 'Foundation Pack 1'},
                {'topic': 'Core vocabulary', 'set': 'Concept Drill 1'},
            ],
        }
