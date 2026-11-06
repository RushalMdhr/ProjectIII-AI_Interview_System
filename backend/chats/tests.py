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
		UserProfile.objects.create(user=self.user, target_role="Software Engineer")
		self.session = ChatSession.objects.create(
			user=self.user,
			use_case="interview_assessment",
			interview_difficulty="medium",
			current_difficulty="easy",
			max_questions=8,
		)
		self.client = APIClient()
		self.client.force_authenticate(user=self.user)

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
			patch("chats.views.evaluate_interview_answer", return_value=(8, "Clear and relevant.")),
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
		self.assertEqual(opening_attempt.rating, 8)
		self.assertEqual(opening_attempt.candidate_answer, "I would start with clear resource boundaries.")
		self.assertEqual(
			answer_response.data["interview_feedback"]["feedback"],
			"Clear and relevant.",
		)
		next_attempt = InterviewFeedback.objects.get(question_text=next_question["question"])
		self.assertEqual(next_attempt.question_text, next_question["question"])
		self.assertEqual(
			answer_response.data["next_question"]["question_text"],
			next_question["question"],
		)
