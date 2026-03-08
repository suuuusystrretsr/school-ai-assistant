import json
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
        self.endpoint = f'https://api-inference.huggingface.co/models/{self.model_id}' if self.model_id else ''
        self.last_error = ''

    def _invoke_model(self, prompt: str, max_new_tokens: int | None = None) -> str | None:
        self.last_error = ''
        if not self.api_key or not self.endpoint:
            self.last_error = 'Missing HF key or model endpoint'
            return None

        payload = {
            'inputs': prompt,
            'parameters': {
                'max_new_tokens': int(max_new_tokens or self.max_new_tokens),
                'temperature': 0.35,
                'return_full_text': False,
            },
            'options': {
                'wait_for_model': True,
                'use_cache': False,
            },
        }

        req = request.Request(
            self.endpoint,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
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
            if isinstance(data.get('generated_text'), str):
                return data['generated_text'].strip()
            if isinstance(data.get('text'), str):
                return data['text'].strip()
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
        data = self._ask_json(
            'Generate multiple-choice exam questions with valid options and a single correct answer.',
            (
                'Return object: {"questions": [ {"prompt": str, "choices": [4 strings], "correct_answer": "A|B|C|D", "explanation": str} ]}. '
                f'Create exactly {question_count} questions.\n'
                f'Subject: {subject}\nTopic: {topic}\nDifficulty: {difficulty}\nTeacher style: {style}'
            ),
            max_new_tokens=1200,
        )
        if not isinstance(data, dict) or not isinstance(data.get('questions'), list):
            return None

        out: list[dict] = []
        for item in data['questions'][:question_count]:
            if not isinstance(item, dict):
                continue
            choices = item.get('choices') if isinstance(item.get('choices'), list) else []
            if len(choices) != 4:
                continue
            correct = str(item.get('correct_answer') or '').strip().upper()
            if correct not in {'A', 'B', 'C', 'D'}:
                continue
            prompt = str(item.get('prompt') or '').strip()
            explanation = str(item.get('explanation') or '').strip()
            if not prompt or not explanation:
                continue
            out.append(
                {
                    'prompt': prompt,
                    'choices': [str(c) for c in choices],
                    'correct_answer': correct,
                    'explanation': explanation,
                }
            )

        return out if len(out) >= 3 else None




