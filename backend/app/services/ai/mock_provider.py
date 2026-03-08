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

    def _extract_topic(self, text: str) -> str:
        match = re.search(r'^\s*topic\s*:\s*(.+)$', text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip()[:80]
        return 'this topic'

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
        topic = self._extract_topic(source_text)
        sentences = self._extract_sentences(source_text)
        if not sentences:
            sentences = ['Review the core concept and define it in your own words.']

        cards: list[dict] = []
        for idx, sentence in enumerate(sentences[:6]):
            keywords = self._extract_keywords(sentence)
            first_keyword = keywords[0].replace('-', ' ') if keywords else 'concept'

            if ' is ' in sentence.lower():
                question = f'In {topic}, what does "{first_keyword}" mean?'
            elif ' converts ' in sentence.lower() or ' into ' in sentence.lower():
                question = f'In {topic}, what process is described here: "{sentence[:60]}"?'
            else:
                question = f'What is the main {topic} idea in this statement: "{sentence[:60]}"?'

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
        mode_hint = {
            'eli5': 'very simple words and one concrete analogy',
            'normal': 'clear steps plus one quick checkpoint',
            'advanced': 'formal reasoning and edge-case check',
            'teacher': 'lesson style, guided example, then mini-quiz',
        }.get(mode.lower(), 'clear explanation and guided practice')

        return {
            'reply': (
                f"Let's learn {subject} step-by-step using {mode_hint}. "
                f'First concept from your prompt: "{seed}".'
            ),
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

        grade = payload.get('grade_level')
        grade_tag = f' ({grade})' if grade else ''

        return [
            {
                'subject': exam['subject'],
                'topic': weak_topics[idx % len(weak_topics)],
                'due_date': (today + timedelta(days=idx + 1)).isoformat(),
                'minutes': 45 + (idx % 2) * 15,
                'priority': 'high' if idx < 2 else 'medium',
                'task_type': 'practice',
                'recommendations': [
                    f'Active recall{grade_tag}',
                    'Timed practice',
                    'Error log review',
                ],
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

    def generate_exam_questions(
        self,
        subject: str,
        topic: str,
        difficulty: str,
        style: str,
        question_count: int,
    ) -> list[dict] | None:
        level = difficulty.lower().strip()
        s = subject.lower().strip()

        def q(prompt: str, choices: list[str], correct: str, explanation: str) -> dict:
            return {
                'prompt': f'[{style}] {prompt}',
                'choices': choices,
                'correct_answer': correct,
                'explanation': explanation,
            }

        templates: list[dict]
        if 'math' in s:
            templates = [
                q(
                    f'For {topic}, what is the most reliable first step?',
                    [
                        'Identify known values, unknowns, and constraints.',
                        'Guess an answer and verify later.',
                        'Skip setup and do random operations.',
                        'Only memorize the final formula name.',
                    ],
                    'A',
                    'Structured setup reduces algebra and sign errors before solving.',
                ),
                q(
                    f'Which error most commonly causes wrong answers in {topic}?',
                    [
                        'Checking units and signs at the end.',
                        'Applying a rule without checking conditions.',
                        'Writing down givens clearly.',
                        'Estimating a sanity-check range.',
                    ],
                    'B',
                    'Using a rule out of context is a frequent source of incorrect results.',
                ),
                q(
                    f'What review method best strengthens {topic} retention?',
                    [
                        'Read notes once and move on.',
                        'Do only easy questions repeatedly.',
                        'Use spaced recall plus mixed practice.',
                        'Skip review and rely on intuition.',
                    ],
                    'C',
                    'Spaced retrieval and mixed problems build durable recall and transfer.',
                ),
            ]
        elif 'history' in s:
            templates = [
                q(
                    f'In {topic}, what makes evidence strongest?',
                    [
                        'A single vague claim.',
                        'Specific source + context + relevance to argument.',
                        'Only personal opinion.',
                        'A quote without explanation.',
                    ],
                    'B',
                    'History answers score higher when evidence is specific and explicitly linked to the claim.',
                ),
                q(
                    f'Which approach is best for a causation question on {topic}?',
                    [
                        'List facts without linking them.',
                        'Explain short-term and long-term causes with priority.',
                        'Use one cause only.',
                        'Ignore counter-arguments.',
                    ],
                    'B',
                    'Causation requires structured reasoning across multiple interacting factors.',
                ),
                q(
                    f'How should you conclude an argument about {topic}?',
                    [
                        'Repeat the introduction word-for-word.',
                        'State final judgment and weigh strongest evidence.',
                        'Add unrelated facts.',
                        'Avoid making a clear judgment.',
                    ],
                    'B',
                    'A high-quality conclusion weighs evidence and gives a clear final judgment.',
                ),
            ]
        else:
            templates = [
                q(
                    f'In {topic}, which strategy improves accuracy most?',
                    [
                        'Define key terms before solving.',
                        'Skip interpretation and answer quickly.',
                        'Ignore constraints in the question.',
                        'Avoid checking the final result.',
                    ],
                    'A',
                    'Clarifying terms and constraints prevents interpretation mistakes.',
                ),
                q(
                    f'When answering {topic} questions, what should be done before submitting?',
                    [
                        'Nothing, first answer is always best.',
                        'Quickly verify reasoning and key assumptions.',
                        'Delete intermediate steps.',
                        'Change answer randomly.',
                    ],
                    'B',
                    'A final verification catches logic gaps and small mistakes.',
                ),
                q(
                    f'What practice pattern is strongest for {topic} at {level} difficulty?',
                    [
                        'Only reread notes.',
                        'Only practice easiest items.',
                        'Alternate concept recall and applied questions.',
                        'Avoid timed work entirely.',
                    ],
                    'C',
                    'Combining recall and application improves both understanding and exam performance.',
                ),
            ]

        out: list[dict] = []
        for idx in range(question_count):
            base = templates[idx % len(templates)]
            out.append(
                {
                    'prompt': f"{base['prompt']} (Q{idx + 1}, {level})",
                    'choices': base['choices'],
                    'correct_answer': base['correct_answer'],
                    'explanation': base['explanation'],
                }
            )

        return out


