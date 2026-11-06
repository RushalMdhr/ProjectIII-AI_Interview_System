from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import User, UserProfile
from ai_app.ai.documents.tools.context_handler import (
	_parse_interviewer_response,
	generate_interviewer_response,
	interview_category_sequence,
)
from ai_app.ai.utils.Evaluator import evaluate_interview_answer
from chats.models import ChatSession, InterviewFeedback
from chats.views import _find_similar_answer


class InterviewFlowTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			username="candidate",
			email="candidate@example.test",
			password="test-password",
		)
		UserProfile.objects.create(user=self.user, primary_role="Backend Developer")
		self.session = ChatSession.objects.create(
			user=self.user,
			use_case="interview_assessment",
			interview_difficulty="medium",
			current_difficulty="easy",
			max_questions=8,
		)
		self.client = APIClient()
		self.client.force_authenticate(user=self.user)

	def test_interviewer_response_fields_depend_on_action(self):
		self.assertEqual(
			_parse_interviewer_response({"action": "SKIP"})["feedback"],
			"",
		)
		self.assertEqual(
			_parse_interviewer_response({"action": "CONTINUE"})["question"],
			"",
		)
		self.assertEqual(
			_parse_interviewer_response({"action": "CONTINUE"})["action"],
			"CONTINUE",
		)
		with self.assertRaises(ValueError):
			_parse_interviewer_response(
				{"action": "CONTINUE"},
				require_feedback=True,
			)
		with self.assertRaises(ValueError):
			_parse_interviewer_response({"action": "REPEAT"})

	def test_interview_history_endpoint_returns_attempts_and_timestamps(self):
		attempt = InterviewFeedback.objects.create(
			session=self.session,
			question_text="Tell me about a project.",
			question_answer="Explain your contribution.",
			candidate_answer="I built an API.",
			rating=7,
			feedback='{"feedback_text":"Good detail."}',
		)

		response = self.client.get(
			reverse("interview_history", kwargs={"session_id": self.session.id})
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["session"]["id"], self.session.id)
		self.assertEqual(len(response.data["interview_feedback"]), 1)
		entry = response.data["interview_feedback"][0]
		self.assertEqual(entry["question_text"], "Tell me about a project.")
		self.assertEqual(entry["question_answer"], "Explain your contribution.")
		self.assertEqual(entry["candidate_answer"], "I built an API.")
		self.assertEqual(entry["rating"], 7)
		self.assertEqual(entry["feedback"], {"feedback_text": "Good detail."})
		self.assertIn("created_at", entry)
		self.assertIn("updated_at", entry)
		self.assertEqual(entry["id"], attempt.id)

	def test_interview_history_is_scoped_to_session_owner(self):
		other_user = User.objects.create_user(
			username="other-candidate",
			email="other-candidate@example.test",
			password="test-password",
		)
		self.client.force_authenticate(user=other_user)

		response = self.client.get(
			reverse("interview_history", kwargs={"session_id": self.session.id})
		)

		self.assertEqual(response.status_code, 404)

	def test_similar_prior_answers_are_detected(self):
		self.assertTrue(
			_find_similar_answer(
				"I designed a scalable payments API for the company.",
				["I designed a scalable payments API for the company!"],
			)
		)
		self.assertTrue(
			_find_similar_answer(
				"I designed a scalable payments API for the company.",
				["I designed a scalable payments API for our company."],
			)
		)
		self.assertFalse(
			_find_similar_answer(
				"I designed a scalable payments API for the company.",
				["I learned about teamwork and resolving conflict."],
			)
		)

	def test_interviewer_varies_natural_response_for_repeated_answers(self):
		with patch(
			"ai_app.ai.documents.tools.context_handler.ai",
			return_value='{"action":"CONTINUE","feedback":"Let’s try a different example.","question":"Next question"}',
		) as generate:
			generate_interviewer_response(
				result={"overall_score": 6},
				prev_question="Describe a challenge.",
				next_question="Next question",
				candidate_answer="I built a payment API.",
				repetition_count=4,
				matching_previous_answer="I built a payment API.",
			)

		prompt = generate.call_args.kwargs["msg"][0]["content"]
		self.assertIn("Repetition Count: 4", prompt)
		self.assertIn("Similar Previous Answer: I built a payment API.", prompt)
		self.assertIn("Vary the wording and tone", prompt)
		self.assertEqual(generate.call_args.kwargs["temperature"], 0.7)
		self.assertEqual(
			generate.call_args.kwargs["format"]["properties"]["action"]["enum"],
			["CONTINUE", "REPEAT", "SKIP", "REVIEW"],
		)

	def test_interviewer_uses_safe_feedback_if_both_model_responses_are_invalid(self):
		with patch(
			"ai_app.ai.documents.tools.context_handler.ai",
			side_effect=["not json", '{"action":"CONTINUE"}'],
		) as generate:
			response = generate_interviewer_response(
				result={"overall_score": 6},
				prev_question="Describe a challenge.",
				next_question="Next question",
				candidate_answer="I built a payment API.",
				repetition_count=4,
				matching_previous_answer="I built a payment API.",
			)

		self.assertEqual(response["action"], "CONTINUE")
		self.assertTrue(response["feedback"])
		self.assertEqual(response["question"], "")
		self.assertEqual(generate.call_count, 2)

	def test_evaluator_receives_previous_interview_answers_as_context(self):
		history = [{
			"question_text": "Tell me about a project.",
			"candidate_answer": "I built an API.",
		}]

		with patch("ai_app.ai.utils.Evaluator.create_evaluator") as create_evaluator:
			create_evaluator.return_value.score = 0.8
			create_evaluator.return_value.reason = "Clear answer."
			evaluate_interview_answer(
				question="How did you handle a challenge?",
				answer="I built an API.",
				ideal_answer="",
				dimensions=[{"label": "behavioral", "score": 1.0}],
				model=None,
				history=history,
			)

		test_case = create_evaluator.return_value.measure.call_args.args[0]
		self.assertIn("Previous interview responses", test_case.input)
		self.assertIn("I built an API.", test_case.input)

	def test_interview_sequences_match_difficulty_and_start_with_introduction(self):
		expected_categories = {
			"easy": {
				"introduction": 1,
				"experience": 1,
				"behavioral": 1,
				"situational": 1,
				"technical": 1,
			},
			"medium": {
				"introduction": 1,
				"experience": 2,
				"behavioral": 2,
				"situational": 1,
				"technical": 2,
			},
			"hard": {
				"introduction": 2,
				"experience": 2,
				"behavioral": 2,
				"situational": 2,
				"technical": 2,
			},
		}
		for difficulty, expected_counts in expected_categories.items():
			self.session.interview_difficulty = difficulty
			self.session.max_questions = sum(expected_counts.values())
			sequence = interview_category_sequence(self.session)
			self.assertEqual(sequence[0], "introduction")
			self.assertEqual(len(sequence), self.session.max_questions)
			self.assertEqual(
				{category: sequence.count(category) for category in expected_counts},
				expected_counts,
			)

	@patch("chats.views.generate_interview_intro", return_value="Please introduce yourself.")
	def test_start_prefetch_and_answer_return_feedback(self, _generate_intro):
		start_url = reverse("start_interview", kwargs={"session_id": self.session.id})
		response = self.client.post(start_url)

		self.assertEqual(response.status_code, 201)
		opening_attempt = InterviewFeedback.objects.get(session=self.session)
		self.assertEqual(opening_attempt.question_text, "Please introduce yourself.")
		self.assertEqual(
			response.data["interview_feedback"]["question_text"],
			"Please introduce yourself.",
		)
		self.assertEqual(response.data["session"]["question_count"], 1)

		def prefetch_question_ids(_user, _session_id, attempt, top_k):
			attempt.prefetched_question_ids = [11, 12, 13]
			attempt.save(update_fields=["prefetched_question_ids", "updated_at"])
			return {"status": "success", "question_ids": attempt.prefetched_question_ids}

		with patch(
			"chats.views.prefetch_next_questions",
			side_effect=prefetch_question_ids,
		):
			prefetch_url = reverse(
				"prefetch_interview_questions",
				kwargs={"session_id": self.session.id},
			)
			prefetch_response = self.client.post(prefetch_url)

		self.assertEqual(prefetch_response.status_code, 200)
		opening_attempt.refresh_from_db()
		self.assertEqual(opening_attempt.prefetched_question_ids, [11, 12, 13])

		next_question = {
			"id": None,
			"question": "How would you design a reliable API?",
			"answer": "",
			"difficulty": "medium",
		}
		geval_result = {
			"overall_score": 8.0,
			"dimension_scores": {
				"behavioral": {
					"score": 8.0,
					"weight": 1.0,
					"reason": "A clear example with a specific result.",
				},
			},
		}
		with (
			patch("chats.views.evaluate_candidate_answer", return_value=geval_result),
			patch(
				"chats.views.get_next_questions",
				return_value={"status": "success", "question": next_question},
			),
			patch(
				"chats.views.generate_interviewer_response",
				side_effect=[
					{"action": "CONTINUE", "feedback": "", "question": ""},
					{
						"action": "CONTINUE",
						"feedback": "A clear example with a specific result.",
						"question": next_question["question"],
					},
				],
			),
		):
			answer_response = self.client.post(
				reverse("send_message"),
				{"session": self.session.id, "user_content": "I would start with clear resource boundaries."},
				format="json",
			)

		self.assertEqual(answer_response.status_code, 201)
		opening_attempt.refresh_from_db()
		self.assertEqual(opening_attempt.rating, 8)
		self.assertEqual(opening_attempt.candidate_answer, "I would start with clear resource boundaries.")
		self.assertEqual(
			answer_response.data["interview_feedback"]["feedback"],
			{
				"feedback_text": "A clear example with a specific result.",
				"overall_score": 8.0,
				"dimension_scores": geval_result["dimension_scores"],
			},
		)
		next_attempt = InterviewFeedback.objects.get(question_text=next_question["question"])
		self.assertEqual(next_attempt.question_text, next_question["question"])
		self.assertEqual(
			answer_response.data["next_question"]["question_text"],
			next_question["question"],
		)
		self.session.refresh_from_db()
		self.assertEqual(answer_response.data["session"]["current_state"], self.session.current_state)

	def test_repeat_rephrases_pending_question_without_evaluation_or_feedback(self):
		attempt = InterviewFeedback.objects.create(
			session=self.session,
			question_text="Describe your experience.",
		)
		self.session.question_count = 1
		self.session.save(update_fields=["question_count"])

		with (
			patch(
				"chats.views.generate_interviewer_response",
				return_value={
					"action": "REPEAT",
					"feedback": "",
					"question": "Could you explain your relevant experience?",
				},
			),
			patch("chats.views.evaluate_candidate_answer") as evaluate,
			patch("chats.views.get_next_questions") as get_next_questions,
		):
			response = self.client.post(
				reverse("send_message"),
				{"session": self.session.id, "user_content": "Could you repeat that?"},
				format="json",
			)

		self.assertEqual(response.status_code, 201)
		attempt.refresh_from_db()
		self.session.refresh_from_db()
		self.assertEqual(attempt.question_text, "Could you explain your relevant experience?")
		self.assertEqual(attempt.candidate_answer, "")
		self.assertIsNone(attempt.feedback)
		self.assertIsNone(attempt.rating)
		self.assertEqual(self.session.question_count, 1)
		evaluate.assert_not_called()
		get_next_questions.assert_not_called()

	def test_skip_advances_category_without_evaluation_or_feedback(self):
		attempt = InterviewFeedback.objects.create(
			session=self.session,
			question_text="Describe your experience.",
		)
		self.session.question_count = 1
		self.session.save(update_fields=["question_count"])
		next_question = {
			"id": None,
			"question": "How do you approach teamwork?",
			"answer": "",
			"difficulty": "medium",
		}

		with (
			patch(
				"chats.views.generate_interviewer_response",
				return_value={"action": "SKIP", "feedback": "", "question": ""},
			),
			patch("chats.views.evaluate_candidate_answer") as evaluate,
			patch(
				"chats.views.get_next_questions",
				return_value={"status": "success", "question": next_question},
			),
		):
			response = self.client.post(
				reverse("send_message"),
				{"session": self.session.id, "user_content": "I don't know; skip."},
				format="json",
			)

		self.assertEqual(response.status_code, 201)
		attempt.refresh_from_db()
		self.session.refresh_from_db()
		self.assertEqual(attempt.candidate_answer, "I don't know; skip.")
		self.assertIsNone(attempt.feedback)
		self.assertIsNone(attempt.rating)
		self.assertEqual(self.session.question_count, 2)
		self.assertEqual(
			self.session.current_state,
			response.data["session"]["current_state"],
		)
		evaluate.assert_not_called()

	def test_fourth_similar_answer_ends_interview(self):
		repeated_answer = "I built a reliable payment API for our customers."
		for index in range(3):
			InterviewFeedback.objects.create(
				session=self.session,
				question_text=f"Previous question {index + 1}",
				candidate_answer=repeated_answer,
				rating=6,
			)
		attempt = InterviewFeedback.objects.create(
			session=self.session,
			question_text="Describe a challenge.",
		)

		with (
			patch(
				"chats.views.evaluate_candidate_answer",
				return_value={
					"overall_score": 6.0,
					"dimension_scores": {},
				},
			),
			patch(
				"chats.views.get_next_questions",
				return_value={
					"status": "success",
					"question": {
						"id": None,
						"question": "Next question",
						"answer": "",
						"difficulty": "medium",
					},
				},
			),
			patch(
				"chats.views.generate_interviewer_response",
				side_effect=[
					{"action": "CONTINUE", "feedback": "", "question": ""},
					{
						"action": "CONTINUE",
						"feedback": "I notice this answer has come up before.",
						"question": "Next question",
					},
				],
			) as interviewer_response,
		):
			response = self.client.post(
				reverse("send_message"),
				{"session": self.session.id, "user_content": repeated_answer},
				format="json",
			)

		self.assertEqual(response.status_code, 201)
		self.session.refresh_from_db()
		attempt.refresh_from_db()
		self.assertTrue(self.session.halted)
		self.assertTrue(self.session.archived)
		self.assertIsNone(response.data["next_question"])
		self.assertEqual(attempt.rating, 6)
		self.assertEqual(
			response.data["interview_feedback"]["feedback"]["feedback_text"],
			"I notice this answer has come up before.",
		)
		self.assertEqual(
			interviewer_response.call_args.kwargs["repetition_count"],
			4,
		)
		self.assertEqual(response.data["message"], "Interview ended.")
