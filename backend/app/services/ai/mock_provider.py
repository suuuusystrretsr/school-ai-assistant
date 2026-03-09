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



    # classroom patch marker


    def _classroom_sections(self, duration_minutes: int) -> list[dict]:
        if duration_minutes < 30:
            intro = max(2, round(duration_minutes * 0.14))
            core = max(4, round(duration_minutes * 0.28))
            interactive = max(3, round(duration_minutes * 0.24))
            practice = max(3, round(duration_minutes * 0.22))
            summary = max(2, duration_minutes - (intro + core + interactive + practice))
            return [
                {'name': 'Introduction', 'minutes': intro},
                {'name': 'Core Explanation', 'minutes': core},
                {'name': 'Interactive Questions', 'minutes': interactive},
                {'name': 'Practice Problems', 'minutes': practice},
                {'name': 'Summary and Key Takeaways', 'minutes': summary},
            ]
        if duration_minutes < 50:
            intro = max(4, round(duration_minutes * 0.12))
            core = max(8, round(duration_minutes * 0.24))
            walkthrough = max(7, round(duration_minutes * 0.2))
            interactive = max(6, round(duration_minutes * 0.2))
            practice = max(4, round(duration_minutes * 0.14))
            summary = max(3, duration_minutes - (intro + core + walkthrough + interactive + practice))
            return [
                {'name': 'Introduction', 'minutes': intro},
                {'name': 'Core Explanation', 'minutes': core},
                {'name': 'Example Walkthrough', 'minutes': walkthrough},
                {'name': 'Interactive Questions', 'minutes': interactive},
                {'name': 'Practice Problems', 'minutes': practice},
                {'name': 'Summary and Key Takeaways', 'minutes': summary},
            ]
        return [
            {'name': 'Introduction', 'minutes': 6},
            {'name': 'Core Explanation', 'minutes': 12},
            {'name': 'Example Walkthrough', 'minutes': 12},
            {'name': 'Interactive Questions', 'minutes': 12},
            {'name': 'Practice Problems', 'minutes': 8},
            {'name': 'Quick Quiz', 'minutes': 5},
            {'name': 'Summary and Key Takeaways', 'minutes': max(3, duration_minutes - 55)},
        ]

    def generate_classroom_plan(self, payload: dict) -> dict:
        subject = str(payload.get('subject') or 'General')
        topic = str(payload.get('topic') or subject)
        grade = str(payload.get('grade_level') or 'Middle School')
        duration = int(payload.get('duration_minutes') or 45)
        difficulty = str(payload.get('difficulty') or 'standard').lower()
        goal = str(payload.get('learning_goal') or 'first time learning')
        style = str(payload.get('custom_teacher_style') or payload.get('teacher_style') or 'Standard teacher')

        lesson_plan = self._classroom_sections(duration)
        teacher_turn = {
            'phase': lesson_plan[0]['name'],
            'message': f'Welcome class. Today in {subject} we will learn {topic}. Goal: {goal}.',
            'question': f'What do you already know about {topic}?',
            'feedback': f'I will teach this at a {difficulty} level for {grade}.',
        }
        visuals = {
            'slides': [f'{subject}: {topic}', f'Goal: {goal}', f'Teacher style: {style}'],
            'diagram': {
                'nodes': [f'{topic} concept', f'{topic} example', f'{topic} review'],
                'edges': ['concept -> example', 'example -> review'],
            },
            'timeline': [{'step': i + 1, 'phase': p['name'], 'minutes': p['minutes']} for i, p in enumerate(lesson_plan)],
            'whiteboard_steps': [f'Define {topic}', f'Solve one {topic} example', 'Explain each step'],
        }
        return {
            'lesson_plan': lesson_plan,
            'teacher_turn': teacher_turn,
            'visuals': visuals,
            'adaptive_difficulty': difficulty,
        }

    def classroom_next_turn(self, payload: dict) -> dict:
        lesson_plan = payload.get('lesson_plan') if isinstance(payload.get('lesson_plan'), list) else []
        index = int(payload.get('current_phase_index') or 0)
        adaptive = str(payload.get('adaptive_difficulty') or 'standard').lower()
        topic = str(payload.get('topic') or 'this topic')
        confidence = payload.get('self_confidence')
        was_correct = bool(payload.get('was_correct'))

        if not was_correct or (isinstance(confidence, int) and confidence < 45):
            adaptive = 'simplified'
            feedback = f'Let us simplify {topic} with one more example.'
        elif was_correct and isinstance(confidence, int) and confidence >= 75:
            adaptive = 'advanced'
            feedback = f'Great work. We will go deeper into {topic}.'
        else:
            feedback = f'Good effort. We continue building {topic}.'
        phase_advanced = False
        if (was_correct or (isinstance(confidence, int) and confidence >= 60)) and lesson_plan and index < len(lesson_plan) - 1:
            index += 1
            phase_advanced = True

        phase_name = lesson_plan[index]['name'] if lesson_plan else 'Core Explanation'
        question = f'{phase_name}: explain one key idea about {topic}.'
        if adaptive == 'advanced':
            question = f'{phase_name}: why does {topic} work, and when does it fail?'

        teacher_turn = {
            'phase': phase_name,
            'message': f'{feedback} Current phase: {phase_name}.',
            'question': question,
            'feedback': feedback,
        }
        visuals = {
            'slides': [f'Phase: {phase_name}', f'Adaptive level: {adaptive}', f'Focus: {topic}'],
            'diagram': {
                'nodes': [f'{topic} idea', f'{topic} application', f'{topic} check'],
                'edges': ['idea -> application', 'application -> check'],
            },
            'timeline': [{'step': i + 1, 'phase': p.get('name'), 'minutes': p.get('minutes')} for i, p in enumerate(lesson_plan)],
            'whiteboard_steps': [f'Restate {topic}', f'Work one step on {topic}', 'Check the reasoning'],
        }

        return {
            'teacher_turn': teacher_turn,
            'adaptive_difficulty': adaptive,
            'visuals': visuals,
            'phase_advanced': phase_advanced,
            'current_phase_index': index,
        }

    def generate_classroom_report(self, payload: dict) -> dict:
        topic = str(payload.get('topic') or 'the topic')
        transcript = payload.get('transcript') if isinstance(payload.get('transcript'), list) else []
        struggle = sum(
            1
            for turn in transcript
            if isinstance(turn, dict)
            and turn.get('role') == 'teacher'
            and 'simplify' in str(turn.get('message', '')).lower()
        )
        weak = [f'{topic} application'] if struggle else [f'{topic} higher-level reasoning']
        return {
            'class_summary': f'Completed guided classroom session on {topic}.',
            'key_concepts': [f'Core idea of {topic}', f'Applied steps for {topic}', f'Self-check strategy for {topic}'],
            'weak_areas': weak,
            'suggested_next_topic': f'{topic} mixed practice',
            'recommended_practice_tasks': [f'10-minute recall on {topic}', f'Two medium {topic} problems', 'One explain-your-steps reflection'],
        }
