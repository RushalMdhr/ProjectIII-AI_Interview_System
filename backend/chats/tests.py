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

	def test_short_interview_answers_are_rejected_before_ai_processing(self):
		question_message = ChatMessage.objects.create(
			session=self.session,
			user=self.user,
			assistant_content="Please introduce yourself.",
		)
		InterviewFeedback.objects.create(
			session=self.session,
			message=question_message,
			question_text="Please introduce yourself.",
		)

		with (
			patch("chats.views.evaluate_interview_answer") as evaluate_answer,
			patch("chats.views.embed_text") as create_embedding,
		):
			for answer in ("next", "jzaz<", "I am"):
				response = self.client.post(
					reverse("send_message"),
					{"session": self.session.id, "user_content": answer},
					format="json",
				)

				self.assertEqual(response.status_code, 400)
				self.assertIn("at least 3 words", response.data["error"])

		evaluate_answer.assert_not_called()
		create_embedding.assert_not_called()
		self.assertEqual(ChatMessage.objects.filter(session=self.session).count(), 1)

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
