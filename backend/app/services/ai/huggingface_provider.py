import json
import re
from typing import Any
from urllib import error, request

from app.core.config import get_settings
from app.services.ai.mock_provider import MockAIProvider


class HuggingFaceProvider(MockAIProvider):
    def __init__(self) -> None:
        self.settings = get_settings()
        self.api_key = (self.settings.hf_api_key or '').strip()
        self.model_id = (self.settings.hf_model_id or '').strip()
        self.timeout = max(10, int(self.settings.hf_timeout_seconds))
        self.max_new_tokens = max(128, int(self.settings.hf_max_new_tokens))
        self.endpoint = 'https://router.huggingface.co/v1/chat/completions' if self.model_id else ''
        self.last_error = ''

    def _invoke_model(self, prompt: str, max_new_tokens: int | None = None) -> str | None:
        self.last_error = ''
        if not self.api_key or not self.endpoint:
            self.last_error = 'Missing HF key or model endpoint'
            return None

        payload = {
            'model': self.model_id,
            'messages': [
                {'role': 'user', 'content': prompt},
            ],
            'temperature': 0.35,
            'max_tokens': int(max_new_tokens or self.max_new_tokens),
            'stream': False,
        }

        req = request.Request(
            self.endpoint,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'school-ai-assistant/1.0',
                'Authorization': f'Bearer {self.api_key}',
            },
            method='POST',
        )

        try:
            with request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read().decode('utf-8', errors='ignore')
        except error.HTTPError as exc:
            try:
                detail = exc.read().decode('utf-8', errors='ignore')
            except Exception:
                detail = ''
            self.last_error = f'HTTP {exc.code}: {detail[:220]}'
            return None
        except (error.URLError, TimeoutError) as exc:
            self.last_error = str(exc)
            return None

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.last_error = 'HF returned non-JSON response'
            return None

        if isinstance(data, dict):
            if data.get('error'):
                self.last_error = str(data.get('error'))
                return None
            if isinstance(data.get('choices'), list) and data.get('choices'):
                first_choice = data['choices'][0]
                if isinstance(first_choice, dict):
                    message = first_choice.get('message')
                    if isinstance(message, dict) and isinstance(message.get('content'), str):
                        return message['content'].strip()
                    if isinstance(first_choice.get('text'), str):
                        return first_choice['text'].strip()
            if isinstance(data.get('generated_text'), str):
                return data['generated_text'].strip()
            if isinstance(data.get('text'), str):
                return data['text'].strip()
            self.last_error = 'No usable text in HF response payload'
            return None

        if isinstance(data, list) and data:
            first = data[0]
            if isinstance(first, dict):
                if isinstance(first.get('generated_text'), str):
                    return first['generated_text'].strip()
                if isinstance(first.get('text'), str):
                    return first['text'].strip()

        return None

    def _extract_json_block(self, text: str) -> Any | None:
        text = text.strip()

        for opener, closer in [('{', '}'), ('[', ']')]:
            start = text.find(opener)
            end = text.rfind(closer)
            if start != -1 and end != -1 and end > start:
                candidate = text[start : end + 1]
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    continue

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            self.last_error = 'HF returned non-JSON response'
            return None

    def _ask_json(self, system: str, user: str, max_new_tokens: int | None = None) -> Any | None:
        prompt = (
            'You are a strict JSON API generator. Respond with JSON only. No markdown, no prose.\n\n'
            f'SYSTEM:\n{system}\n\n'
            f'USER:\n{user}\n\n'
            'ASSISTANT(JSON ONLY):'
        )
        raw = self._invoke_model(prompt, max_new_tokens=max_new_tokens)
        if not raw:
            return None
        return self._extract_json_block(raw)

    def _list_of_strings(self, value: Any, limit: int = 8) -> list[str]:
        if not isinstance(value, list):
            return []
        out: list[str] = []
        for item in value:
            if isinstance(item, str) and item.strip():
                out.append(item.strip())
            if len(out) >= limit:
                break
        return out

    def solve_problem(self, question: str, mode: str) -> dict:
        fallback = super().solve_problem(question, mode)
        data = self._ask_json(
            'Solve the student question. Provide direct answer + step-by-step + 4 explanation modes.',
            (
                'Return object with keys: final_answer(str), steps(list[str]), explanations(object with eli5,normal,advanced,teacher), '
                'confidence_score(int 0-100).\n'
                f'Question: {question}\nPreferred mode: {mode}'
            ),
            max_new_tokens=650,
        )
        if not isinstance(data, dict):
            return fallback

        explanations = data.get('explanations') if isinstance(data.get('explanations'), dict) else {}
        result = {
            'final_answer': str(data.get('final_answer') or fallback['final_answer']),
            'steps': self._list_of_strings(data.get('steps'), limit=8) or fallback['steps'],
            'explanations': {
                'eli5': str(explanations.get('eli5') or fallback['explanations']['eli5']),
                'normal': str(explanations.get('normal') or fallback['explanations']['normal']),
                'advanced': str(explanations.get('advanced') or fallback['explanations']['advanced']),
                'teacher': str(explanations.get('teacher') or fallback['explanations']['teacher']),
            },
            'confidence_score': int(data.get('confidence_score') or fallback['confidence_score']),
        }
        result['confidence_score'] = max(0, min(100, result['confidence_score']))
        return result

    def generate_practice(self, seed_text: str, difficulty: str) -> dict:
        fallback = super().generate_practice(seed_text, difficulty)
        data = self._ask_json(
            'Generate practice questions aligned to the seed solution and difficulty.',
            (
                'Return object with keys title(str), questions(list of {level,question}), answer_key(list), worked_solutions(list).\n'
                f'Seed: {seed_text}\nDifficulty: {difficulty}'
            ),
            max_new_tokens=650,
        )
        if not isinstance(data, dict):
            return fallback

        questions = data.get('questions') if isinstance(data.get('questions'), list) else []
        answer_key = data.get('answer_key') if isinstance(data.get('answer_key'), list) else []
        worked = data.get('worked_solutions') if isinstance(data.get('worked_solutions'), list) else []

        if not questions:
            return fallback

        return {
            'title': str(data.get('title') or fallback['title']),
            'questions': questions,
            'answer_key': answer_key or fallback['answer_key'],
            'worked_solutions': worked or fallback['worked_solutions'],
        }

    def generate_flashcards(self, source_text: str) -> list[dict]:
        fallback = super().generate_flashcards(source_text)
        topic = self._extract_topic(source_text)
        data = self._ask_json(
            'Generate high-quality flashcards from notes.',
            (
                'Return array of objects with keys: question, answer, topic_tags(list[str]), difficulty_tag. '
                'Questions must be specific and directly tied to the source notes.\n'
                f'Topic: {topic}\nNotes:\n{source_text}'
            ),
            max_new_tokens=700,
        )
        if not isinstance(data, list):
            return fallback

        cards: list[dict] = []
        for item in data[:8]:
            if not isinstance(item, dict):
                continue
            q = str(item.get('question') or '').strip()
            a = str(item.get('answer') or '').strip()
            tags = item.get('topic_tags') if isinstance(item.get('topic_tags'), list) else []
            diff = str(item.get('difficulty_tag') or 'medium').strip().lower()
            if not q or not a:
                continue
            cards.append(
                {
                    'question': q,
                    'answer': a,
                    'topic_tags': [str(t).strip() for t in tags if str(t).strip()][:4] or [topic.lower()],
                    'difficulty_tag': diff if diff in {'easy', 'medium', 'hard'} else 'medium',
                }
            )

        return cards or fallback

    def summarize_lecture(self, content: str) -> dict:
        fallback = super().summarize_lecture(content)
        data = self._ask_json(
            'Summarize lecture content for studying.',
            'Return object with summary, key_concepts(list), flashcards(list), practice_questions(list), revision_notes(list).\n'
            f'Content:\n{content}',
            max_new_tokens=800,
        )
        if not isinstance(data, dict):
            return fallback

        return {
            'summary': str(data.get('summary') or fallback['summary']),
            'key_concepts': self._list_of_strings(data.get('key_concepts')) or fallback['key_concepts'],
            'flashcards': data.get('flashcards') if isinstance(data.get('flashcards'), list) else fallback['flashcards'],
            'practice_questions': data.get('practice_questions') if isinstance(data.get('practice_questions'), list) else fallback['practice_questions'],
            'revision_notes': self._list_of_strings(data.get('revision_notes')) or fallback['revision_notes'],
        }

    def tutor_chat(self, message: str, subject: str, mode: str) -> dict:
        fallback = super().tutor_chat(message, subject, mode)
        data = self._ask_json(
            'Act as an adaptive tutor. Be specific and instructional, not generic.',
            (
                'Return object with keys: reply(str), follow_up_question(str), mini_quiz(list of {question,answer}), '
                'adaptive_path(list[str]). Tailor depth to mode and subject.\n'
                f'Subject: {subject}\nMode: {mode}\nStudent message: {message}'
            ),
            max_new_tokens=650,
        )
        if not isinstance(data, dict):
            return fallback

        return {
            'reply': str(data.get('reply') or fallback['reply']),
            'follow_up_question': str(data.get('follow_up_question') or fallback['follow_up_question']),
            'mini_quiz': data.get('mini_quiz') if isinstance(data.get('mini_quiz'), list) else fallback['mini_quiz'],
            'adaptive_path': self._list_of_strings(data.get('adaptive_path')) or fallback['adaptive_path'],
        }

    def analyze_mistake(self, question: str, user_answer: str, correct_answer: str) -> dict:
        fallback = super().analyze_mistake(question, user_answer, correct_answer)
        data = self._ask_json(
            'Analyze a student mistake with actionable coaching.',
            (
                'Return object with keys: why_wrong, logic_break, correct_thinking, avoid_next_time(list[str]).\n'
                f'Question: {question}\nUser answer: {user_answer}\nCorrect answer: {correct_answer}'
            ),
            max_new_tokens=500,
        )
        if not isinstance(data, dict):
            return fallback

        return {
            'why_wrong': str(data.get('why_wrong') or fallback['why_wrong']),
            'logic_break': str(data.get('logic_break') or fallback['logic_break']),
            'correct_thinking': str(data.get('correct_thinking') or fallback['correct_thinking']),
            'avoid_next_time': self._list_of_strings(data.get('avoid_next_time')) or fallback['avoid_next_time'],
        }

    def generate_study_plan(self, payload: dict) -> list[dict]:
        fallback = super().generate_study_plan(payload)
        data = self._ask_json(
            'Generate a personalized study plan from exam constraints and weak topics.',
            (
                'Return array of tasks with keys: subject, topic, due_date(YYYY-MM-DD), minutes, priority, task_type, recommendations(list[str]).\n'
                f'Payload: {json.dumps(payload)}'
            ),
            max_new_tokens=700,
        )
        if not isinstance(data, list):
            return fallback

        tasks: list[dict] = []
        for item in data[:12]:
            if not isinstance(item, dict):
                continue
            if not item.get('subject') or not item.get('topic') or not item.get('due_date'):
                continue
            tasks.append(
                {
                    'subject': str(item['subject']),
                    'topic': str(item['topic']),
                    'due_date': str(item['due_date']),
                    'minutes': int(item.get('minutes') or 45),
                    'priority': str(item.get('priority') or 'medium'),
                    'task_type': str(item.get('task_type') or 'practice'),
                    'recommendations': self._list_of_strings(item.get('recommendations')) or ['Active recall'],
                }
            )

        return tasks or fallback

    def generate_hints(self, question: str) -> list[str]:
        fallback = super().generate_hints(question)
        data = self._ask_json(
            'Generate progressive hints from weakest to strongest.',
            f'Return a JSON array of exactly 4 hints for this question: {question}',
            max_new_tokens=260,
        )
        hints = self._list_of_strings(data, limit=4)
        return hints if len(hints) == 4 else fallback

    def detect_learning_style(self, telemetry: dict) -> dict:
        fallback = super().detect_learning_style(telemetry)
        data = self._ask_json(
            'Infer likely learning style from telemetry.',
            'Return object with style, confidence (0-1), evidence(list[str]).\n'
            f'Telemetry: {json.dumps(telemetry)}',
            max_new_tokens=300,
        )
        if not isinstance(data, dict):
            return fallback

        confidence = data.get('confidence')
        if not isinstance(confidence, (float, int)):
            confidence = fallback['confidence']

        return {
            'style': str(data.get('style') or fallback['style']),
            'confidence': float(max(0.0, min(1.0, float(confidence)))),
            'evidence': self._list_of_strings(data.get('evidence')) or fallback['evidence'],
        }

    def scan_knowledge_gaps(self, profile: dict) -> dict:
        fallback = super().scan_knowledge_gaps(profile)
        data = self._ask_json(
            'Find prerequisite knowledge gaps.',
            (
                'Return object with missing_prerequisites(list[str]), foundational_review(list[str]), '
                'prerequisite_practice(list[object]).\n'
                f'Profile: {json.dumps(profile)}'
            ),
            max_new_tokens=420,
        )
        if not isinstance(data, dict):
            return fallback

        return {
            'missing_prerequisites': self._list_of_strings(data.get('missing_prerequisites')) or fallback['missing_prerequisites'],
            'foundational_review': self._list_of_strings(data.get('foundational_review')) or fallback['foundational_review'],
            'prerequisite_practice': data.get('prerequisite_practice') if isinstance(data.get('prerequisite_practice'), list) else fallback['prerequisite_practice'],
        }

    def generate_exam_questions(
        self,
        subject: str,
        topic: str,
        difficulty: str,
        style: str,
        question_count: int,
    ) -> list[dict] | None:
        target_count = max(1, min(25, int(question_count or 5)))

        def normalize(payload: Any) -> list[dict]:
            if isinstance(payload, dict):
                if isinstance(payload.get('questions'), list):
                    questions = payload.get('questions')
                elif isinstance(payload.get('items'), list):
                    questions = payload.get('items')
                elif isinstance(payload.get('data'), list):
                    questions = payload.get('data')
                else:
                    questions = None
            elif isinstance(payload, list):
                questions = payload
            else:
                questions = None

            if not isinstance(questions, list):
                return []

            out: list[dict] = []
            for item in questions[:target_count]:
                if not isinstance(item, dict):
                    continue

                prompt = str(item.get('prompt') or item.get('question') or item.get('stem') or '').strip()
                explanation = str(item.get('explanation') or item.get('rationale') or '').strip()

                raw_choices: Any
                if isinstance(item.get('choices'), list):
                    raw_choices = item.get('choices')
                elif isinstance(item.get('options'), list):
                    raw_choices = item.get('options')
                elif isinstance(item.get('options'), dict):
                    opt_map = item.get('options')
                    raw_choices = [opt_map.get(k) for k in ['A', 'B', 'C', 'D']]
                else:
                    raw_choices = []

                choices = [str(choice).strip() for choice in raw_choices if str(choice).strip()]
                choices = choices[:4]
                while len(choices) < 4:
                    choices.append(f'Option {chr(65 + len(choices))}')

                raw_answer = str(item.get('correct_answer') or item.get('answer') or item.get('correct') or '').strip()
                upper_answer = raw_answer.upper()

                if upper_answer in {'A', 'B', 'C', 'D'}:
                    correct = upper_answer
                elif upper_answer and upper_answer[0] in {'A', 'B', 'C', 'D'} and (len(upper_answer) == 1 or upper_answer[1] in {')', '.', ':', ' '}):
                    correct = upper_answer[0]
                elif raw_answer in choices:
                    correct = chr(65 + choices.index(raw_answer))
                elif any(raw_answer.lower() == choice.lower() for choice in choices):
                    match_idx = next(i for i, choice in enumerate(choices) if raw_answer.lower() == choice.lower())
                    correct = chr(65 + match_idx)
                elif raw_answer.isdigit() and 1 <= int(raw_answer) <= 4:
                    correct = chr(64 + int(raw_answer))
                else:
                    correct = 'A'

                if not prompt:
                    continue
                if not explanation:
                    explanation = f'Review the key concept behind {topic} and eliminate distractors carefully.'

                out.append(
                    {
                        'prompt': prompt,
                        'choices': choices,
                        'correct_answer': correct,
                        'explanation': explanation,
                    }
                )

            return out

        def merge_unique(primary: list[dict], secondary: list[dict]) -> list[dict]:
            seen = {q.get('prompt', '').strip().lower() for q in primary if isinstance(q, dict)}
            merged = list(primary)
            for item in secondary:
                if not isinstance(item, dict):
                    continue
                key = str(item.get('prompt') or '').strip().lower()
                if not key or key in seen:
                    continue
                merged.append(item)
                seen.add(key)
                if len(merged) >= target_count:
                    break
            return merged[:target_count]

        def parse_structured_text(raw_text: str) -> list[dict]:
            if not isinstance(raw_text, str) or not raw_text.strip():
                return []

            pattern = re.compile(
                r'Q\s*[:\-]\s*(.+?)\s*\n\s*A\)\s*(.+?)\s*\n\s*B\)\s*(.+?)\s*\n\s*C\)\s*(.+?)\s*\n\s*D\)\s*(.+?)\s*\n\s*(?:ANSWER|CORRECT)\s*[:\-]\s*([ABCD])\s*\n\s*(?:EXPLANATION|WHY)\s*[:\-]\s*(.+?)(?=\n\s*Q\s*[:\-]|\Z)',
                re.IGNORECASE | re.DOTALL,
            )

            out: list[dict] = []
            for match in pattern.finditer(raw_text):
                prompt = match.group(1).strip()
                choices = [match.group(i).strip() for i in range(2, 6)]
                correct = match.group(6).strip().upper()
                explanation = match.group(7).strip()

                if not prompt:
                    continue
                while len(choices) < 4:
                    choices.append(f'Option {chr(65 + len(choices))}')
                if correct not in {'A', 'B', 'C', 'D'}:
                    correct = 'A'
                if not explanation:
                    explanation = f'Review the key concept behind {topic} and eliminate distractors carefully.'

                out.append(
                    {
                        'prompt': prompt,
                        'choices': choices[:4],
                        'correct_answer': correct,
                        'explanation': explanation,
                    }
                )

            return out[:target_count]

        token_budget = min(900, max(420, target_count * 130))
        data = self._ask_json(
            'Generate realistic multiple-choice exam questions with strong distractors and one correct option.',
            (
                'Return JSON object {"questions": [{"prompt": str, "choices": [4 strings], "correct_answer": "A|B|C|D", "explanation": str}]}. '
                'Questions must be specific to topic and age-appropriate; avoid generic placeholders. '
                f'Create exactly {target_count} questions.\n'
                f'Subject: {subject}\nTopic: {topic}\nDifficulty: {difficulty}\nTeacher style: {style}'
            ),
            max_new_tokens=token_budget,
        )

        out = normalize(data)

        if len(out) < target_count:
            raw = self._invoke_model(
                (
                    'Return ONLY a JSON array. No markdown. '
                    f'Create {target_count} high-quality multiple-choice questions for {subject} on {topic} '
                    f'({difficulty}, style: {style}). '
                    'Each item must include prompt, choices(4), correct_answer(A-D), explanation.'
                ),
                max_new_tokens=token_budget,
            )
            parsed = self._extract_json_block(raw) if isinstance(raw, str) and raw.strip() else None
            out = merge_unique(out, normalize(parsed))

        if len(out) < target_count:
            raw_structured = self._invoke_model(
                (
                    f'Create {target_count} multiple-choice questions for {subject} on {topic}. '
                    f'Difficulty: {difficulty}. Teacher style: {style}. '
                    'Do NOT use JSON. Use this exact format for each question:\n'
                    'Q: <question text>\n'
                    'A) <choice A>\n'
                    'B) <choice B>\n'
                    'C) <choice C>\n'
                    'D) <choice D>\n'
                    'ANSWER: <A|B|C|D>\n'
                    'EXPLANATION: <one short explanation>\n'
                ),
                max_new_tokens=token_budget,
            )
            if isinstance(raw_structured, str) and raw_structured.strip():
                out = merge_unique(out, parse_structured_text(raw_structured))

        # Final reliability path: generate one question at a time if batch generation is weak.
        if len(out) < target_count:
            remaining = target_count - len(out)
            max_single_calls = min(remaining, 6)
            for idx in range(max_single_calls):
                single = self._ask_json(
                    'Generate exactly one strong multiple-choice exam question.',
                    (
                        'Return JSON object with key "questions" and exactly one item. '
                        'Item shape: {"prompt": str, "choices": [4 strings], "correct_answer": "A|B|C|D", "explanation": str}.\n'
                        f'Subject: {subject}\nTopic: {topic}\nDifficulty: {difficulty}\nTeacher style: {style}\n'
                        f'Question number: {len(out) + idx + 1} of {target_count}'
                    ),
                    max_new_tokens=380,
                )
                out = merge_unique(out, normalize(single))
                if len(out) >= target_count:
                    break

        return out if out else None








    def generate_classroom_plan(self, payload: dict) -> dict:
        fallback = super().generate_classroom_plan(payload)
        data = self._ask_json(
            'Generate a teacher-led class plan with visuals.',
            (
                'Return object with keys: lesson_plan(list[{name,minutes}]), teacher_turn({phase,message,question,feedback}), '
                'visuals({slides,diagram,timeline,whiteboard_steps}), adaptive_difficulty(str).\n'
                f'Payload: {json.dumps(payload)}'
            ),
            max_new_tokens=800,
        )
        if not isinstance(data, dict):
            return fallback
        if not isinstance(data.get('lesson_plan'), list) or not isinstance(data.get('teacher_turn'), dict):
            return fallback
        return {
            'lesson_plan': data.get('lesson_plan') or fallback['lesson_plan'],
            'teacher_turn': data.get('teacher_turn') or fallback['teacher_turn'],
            'visuals': data.get('visuals') if isinstance(data.get('visuals'), dict) else fallback['visuals'],
            'adaptive_difficulty': str(data.get('adaptive_difficulty') or fallback['adaptive_difficulty']),
        }

    def classroom_next_turn(self, payload: dict) -> dict:
        fallback = super().classroom_next_turn(payload)
        data = self._ask_json(
            'Act like a real teacher continuing an in-progress class.',
            (
                'Return object with keys: teacher_turn({phase,message,question,feedback}), adaptive_difficulty(str), '
                'visuals(object), phase_advanced(bool), current_phase_index(int).\n'
                f'Payload: {json.dumps(payload)}'
            ),
            max_new_tokens=700,
        )
        if not isinstance(data, dict):
            return fallback
        if not isinstance(data.get('teacher_turn'), dict):
            return fallback
        return {
            'teacher_turn': data.get('teacher_turn') or fallback['teacher_turn'],
            'adaptive_difficulty': str(data.get('adaptive_difficulty') or fallback['adaptive_difficulty']),
            'visuals': data.get('visuals') if isinstance(data.get('visuals'), dict) else fallback['visuals'],
            'phase_advanced': bool(data.get('phase_advanced')),
            'current_phase_index': int(data.get('current_phase_index') or fallback.get('current_phase_index', 0)),
        }

    def generate_classroom_report(self, payload: dict) -> dict:
        fallback = super().generate_classroom_report(payload)
        data = self._ask_json(
            'Generate end-of-class report and next action plan.',
            (
                'Return object with keys: class_summary(str), key_concepts(list[str]), weak_areas(list[str]), '
                'suggested_next_topic(str), recommended_practice_tasks(list[str]).\n'
                f'Payload: {json.dumps(payload)}'
            ),
            max_new_tokens=600,
        )
        if not isinstance(data, dict):
            return fallback
        return {
            'class_summary': str(data.get('class_summary') or fallback['class_summary']),
            'key_concepts': self._list_of_strings(data.get('key_concepts')) or fallback['key_concepts'],
            'weak_areas': self._list_of_strings(data.get('weak_areas')) or fallback['weak_areas'],
            'suggested_next_topic': str(data.get('suggested_next_topic') or fallback['suggested_next_topic']),
            'recommended_practice_tasks': self._list_of_strings(data.get('recommended_practice_tasks')) or fallback['recommended_practice_tasks'],
        }
