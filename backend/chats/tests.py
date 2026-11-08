from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import User, UserProfile
from chats.models import ChatSession, InterviewFeedback


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

	@patch(
		"chats.views.get_question_for_state",
		return_value={
			"status": "success",
			"question": {
				"id": None,
				"question": "Please introduce yourself.",
				"answer": "",
				"difficulty": "easy",
			},
		},
	)
	def test_start_prefetch_and_answer_return_feedback(self, _get_question):
		start_url = reverse("start_interview", kwargs={"session_id": self.session.id})
		response = self.client.post(start_url)

		self.assertEqual(response.status_code, 201)
		opening_attempt = InterviewFeedback.objects.get(session=self.session)
		self.assertEqual(opening_attempt.question_text, "Please introduce yourself.")
		self.assertEqual(opening_attempt.category, "introduction")
		self.assertEqual(
			response.data["interview_feedback"]["question_text"],
			"Please introduce yourself.",
		)
		self.assertEqual(response.data["session"]["question_count"], 1)

		with patch(
			"chats.views.prefetch_next_questions",
			return_value={"status": "success", "question_ids": [11, 12, 13]},
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
		with (
			patch(
				"chats.views.evaluate_candidate_answer",
				return_value={
					"overall_score": 8,
					"dimension_scores": {
						"clarity": {
							"score": 8,
							"weight": 1,
							"reason": "Clear and relevant.",
						},
					},
				},
			),
			patch("chats.views.embed_text", return_value=[0.0] * 768),
			patch(
				"chats.views.get_next_questions",
				return_value={"status": "success", "question": next_question},
			),
		):
			answer_response = self.client.post(
				reverse("send_message"),
				{"session": self.session.id, "user_content": "I would start with clear resource boundaries."},
				format="json",
			)

		self.assertEqual(answer_response.status_code, 201)
		opening_attempt.refresh_from_db()
		self.assertEqual(opening_attempt.rating["overall_score"], 8)
		self.assertEqual(opening_attempt.candidate_answer, "I would start with clear resource boundaries.")
		self.assertEqual(
			answer_response.data["interview_feedback"]["feedback"],
			"Clear and relevant.",
		)
		next_attempt = InterviewFeedback.objects.get(question_text=next_question["question"])
		self.assertEqual(next_attempt.question_text, next_question["question"])
		self.assertEqual(next_attempt.category, "behavioral")
		self.assertEqual(
			answer_response.data["next_question"]["question_text"],
			next_question["question"],
		)
		self.assertEqual(
			answer_response.data["interview_feedback"]["average_overall_score"],
			8,
		)
		self.assertEqual(
			answer_response.data["next_question"]["average_overall_score"],
			8,
		)

		next_next_question = {
			"id": None,
			"question": "How do you handle production incidents?",
			"answer": "",
			"difficulty": "medium",
		}
		with (
			patch(
				"chats.views.evaluate_candidate_answer",
				return_value={
					"overall_score": 6,
					"dimension_scores": {
						"clarity": {
							"score": 6,
							"weight": 1,
							"reason": "A reasonable answer.",
						},
					},
				},
			),
			patch(
				"chats.views.get_next_questions",
				return_value={"status": "success", "question": next_next_question},
			),
		):
			second_answer_response = self.client.post(
				reverse("send_message"),
				{
					"session": self.session.id,
					"user_content": "I investigate logs, metrics, and alerts.",
				},
				format="json",
			)

		self.assertEqual(second_answer_response.status_code, 201)
		self.assertEqual(
			second_answer_response.data["interview_feedback"]["average_overall_score"],
			7,
		)
		self.assertEqual(
			InterviewFeedback.objects.filter(session=self.session)
			.exclude(average_overall_score=7)
			.count(),
			0,
		)

	def test_session_category_averages_update_user_high_scores(self):
		from chats.views import _create_question_attempt, _update_session_scores

		introduction_attempt = _create_question_attempt(
			self.session,
			{"question": "Introduction question", "difficulty": "easy"},
		)
		introduction_attempt.rating = {"overall_score": 8}
		introduction_attempt.save(update_fields=["rating"])
		self.session.current_state = "behavioral"
		behavioral_attempt = _create_question_attempt(
			self.session,
			{"question": "Behavioral question", "difficulty": "easy"},
		)
		behavioral_attempt.rating = {"overall_score": 6}
		behavioral_attempt.save(update_fields=["rating"])
		self.session.halted = True
		self.session.save(update_fields=["halted"])

		average = _update_session_scores(self.session)

		self.session.refresh_from_db()
		self.user.refresh_from_db()
		self.assertEqual(average, 7)
		self.assertEqual(self.session.average_introduction_score, 8)
		self.assertEqual(self.session.average_behavioral_score, 6)
		self.assertIsNone(self.session.average_experience_score)
		self.assertEqual(self.user.highest_score, 7)
		self.assertEqual(self.user.highest_introduction_score, 8)
		self.assertEqual(self.user.highest_behavioral_score, 6)

	@patch(
		"chats.views.get_question_for_state",
		return_value={
			"status": "success",
			"question": {
				"id": None,
				"question": "Please introduce yourself.",
				"difficulty": "easy",
			},
		},
	)
	def test_completed_interview_persists_category_averages(
		self, _get_question
	):
		self.session.max_questions = 2
		self.session.save(update_fields=["max_questions"])
		start_response = self.client.post(
			reverse("start_interview", kwargs={"session_id": self.session.id})
		)
		self.assertEqual(start_response.status_code, 201)

		next_question = {
			"id": None,
			"question": "How do you handle a team conflict?",
			"difficulty": "medium",
		}
		evaluation_results = [
			{
				"overall_score": 8,
				"dimension_scores": {
					"clarity": {"score": 8, "weight": 1, "reason": "Clear."},
				},
			},
			{
				"overall_score": 6,
				"dimension_scores": {
					"clarity": {"score": 6, "weight": 1, "reason": "Adequate."},
				},
			},
		]
		with (
			patch(
				"chats.views.evaluate_candidate_answer",
				side_effect=evaluation_results,
			),
			patch("chats.views.embed_text", return_value=[0.0] * 768),
			patch(
				"chats.views.get_next_questions",
				return_value={"status": "success", "question": next_question},
			),
		):
			first_response = self.client.post(
				reverse("send_message"),
				{
					"session": self.session.id,
					"user_content": "I would clarify the issue and find a solution.",
				},
				format="json",
			)
			second_response = self.client.post(
				reverse("send_message"),
				{
					"session": self.session.id,
					"user_content": "I listen to both sides and agree on actions.",
				},
				format="json",
			)

		self.assertEqual(first_response.status_code, 201)
		self.assertEqual(second_response.status_code, 201)
		self.session.refresh_from_db()
		self.user.refresh_from_db()
		self.assertEqual(self.session.average_overall_score, 7)
		self.assertEqual(self.session.average_introduction_score, 8)
		self.assertEqual(self.session.average_behavioral_score, 6)
		self.assertTrue(self.session.halted)
		self.assertEqual(self.user.highest_score, 7)
		self.assertEqual(self.user.highest_introduction_score, 8)
		self.assertEqual(self.user.highest_behavioral_score, 6)
		results_url = reverse(
			"interview_results",
			kwargs={"session_id": self.session.id},
		)
		summary_response = self.client.get(results_url)
		self.assertEqual(summary_response.status_code, 200)
		self.assertNotIn("questions", summary_response.data)
		results_response = self.client.get(
			results_url,
			{"include": "review"},
		)
		self.assertEqual(results_response.status_code, 200)
		self.assertIsNone(
			results_response.data["previous_high_scores"]["highest_score"]
		)
		self.assertEqual(len(results_response.data["questions"]), 2)
		self.assertEqual(
			results_response.data["questions"][0]["candidate_answer"],
			"I would clarify the issue and find a solution.",
		)
