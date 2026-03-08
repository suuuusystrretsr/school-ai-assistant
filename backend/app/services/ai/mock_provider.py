import re
from datetime import date, timedelta

from app.services.ai.base import AIProvider


class MockAIProvider(AIProvider):
    def _extract_sentences(self, text: str) -> list[str]:
        parts = re.split(r'[\.\!\?\n]+', text)
        sentences = [p.strip() for p in parts if len(p.strip()) >= 12]
        return sentences[:6]

    def _extract_keywords(self, text: str) -> list[str]:
        words = re.findall(r'[A-Za-z]{5,}', text.lower())
        seen: list[str] = []
        for w in words:
            if w not in seen:
                seen.append(w)
        return seen[:3] or ['core-concept']

    def solve_problem(self, question: str, mode: str) -> dict:
        clean = question.strip()

        # Solve simple linear forms like "2x + 8 = 20"
        linear_match = re.search(r'([+-]?\d*)x\s*([+-]\s*\d+)?\s*=\s*([+-]?\d+)', clean.replace(' ', ''))
        if linear_match:
            a_raw, b_raw, c_raw = linear_match.groups()
            a = -1 if a_raw == '-' else 1 if a_raw in ('', '+') else int(a_raw)
            b = int(b_raw.replace(' ', '')) if b_raw else 0
            c = int(c_raw)
            x_val = (c - b) / a
            final = f'x = {x_val:g}'
            steps = [
                f'Start with: {clean}',
                f'Subtract {b} from both sides -> {a}x = {c - b}',
                f'Divide both sides by {a} -> x = {(c - b) / a:g}',
            ]
        else:
            final = 'Use the shown steps to compute the final value.'
            steps = [
                'Identify the unknown and known values.',
                'Apply the correct rule/formula to isolate the unknown.',
                'Substitute values carefully and verify the final result.',
            ]

        explanation = {
            'eli5': f'Break it into tiny steps. We isolate the unknown in: {clean[:80]}',
            'normal': f'Solve systematically: isolate variable, compute, then verify for: {clean[:140]}',
            'advanced': f'Use algebraic transformations with validation checks for: {clean[:140]}',
            'teacher': 'Model the full method, ask a check question, and explain common mistakes.',
        }
        return {
            'final_answer': final,
            'steps': steps,
            'explanations': explanation,
            'confidence_score': 82 if linear_match else 68,
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
        sentences = self._extract_sentences(source_text)
        if not sentences:
            sentences = ['Review the core concept and define it in your own words.']

        cards: list[dict] = []
        for idx, sentence in enumerate(sentences[:6]):
            keywords = self._extract_keywords(sentence)
            first_keyword = keywords[0].replace('-', ' ') if keywords else 'concept'

            if ' is ' in sentence.lower():
                question = f'What does "{first_keyword}" mean in this topic?'
            elif ' converts ' in sentence.lower() or ' into ' in sentence.lower():
                question = f'What process is being described here: "{sentence[:60]}"?'
            else:
                question = f'What is the main idea in this statement: "{sentence[:60]}"?'

            cards.append(
                {
                    'question': question,
                    'answer': sentence,
                    'topic_tags': keywords,
                    'difficulty_tag': 'easy' if idx < 2 else 'medium',
                }
            )

        return cards

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
        seed = message.strip()[:120]
        return {
            'reply': f'Let's learn {subject} step-by-step. First concept from your prompt: "{seed}". I will explain, then quiz you.',
            'follow_up_question': f'In one sentence, what is the key idea behind "{seed[:50]}"?',
            'mini_quiz': [
                {'question': f'{subject}: quick check #1 on the core idea', 'answer': 'State the rule in your own words.'},
                {'question': f'{subject}: quick check #2 with application', 'answer': 'Apply the rule to a simple example.'},
            ],
            'adaptive_path': ['Concept explanation', 'Guided example', 'You solve one', 'Timed check'],
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
        exams = payload.get('exams', [])
        if not exams:
            exams = [{'subject': 'General'}]

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
            for idx, exam in enumerate(exams)
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
