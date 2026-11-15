from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from ai_app.ai.documents.tools import context_handler


def _question(question_id, difficulty="medium"):
	return (
		question_id,
		f"Question {question_id}",
		"",
		"Backend Developer",
		"any",
		difficulty,
		[],
		1,
		[],
	)


class InterviewQuestionRetrievalTests(SimpleTestCase):
	def test_initial_search_embeds_role_and_randomly_selects_top_matches(self):
		session = SimpleNamespace(current_difficulty="easy")
		questions = [_question(1, "easy"), _question(2, "easy")]
		with (
			patch.object(context_handler, "_role_for_session", return_value="Backend Developer"),
			patch.object(context_handler, "embed_text", return_value=[0.1] * 768) as embed,
			patch.object(context_handler, "_retrieve_questions", return_value=questions) as retrieve,
			patch.object(context_handler.random, "choice", return_value=questions[1]) as choose,
		):
			result = context_handler.get_question_for_state(object(), session, "introduction")

		embed.assert_called_once_with("Backend Developer")
		retrieve.assert_called_once_with(
			session, "Backend Developer", top_k=3,
			category="introduction", query_embedding=[0.1] * 768,
		)
		choose.assert_called_once_with(questions)
		self.assertEqual(result["status"], "success")

	def test_followup_search_embeds_answer_and_ignores_prefetch_pool(self):
		session = SimpleNamespace(current_state="technical", current_difficulty="medium")
		questions = [_question(1), _question(2)]
		with (
			patch.object(context_handler, "_role_for_session", return_value="Backend Developer"),
			patch.object(context_handler, "embed_text", return_value=[0.2] * 768) as embed,
			patch.object(context_handler, "_retrieve_questions", return_value=questions) as retrieve,
			patch.object(
				context_handler,
				"_generate_better_response",
				return_value={"success": False},
			) as generate,
			patch.object(context_handler.random, "choice", return_value=questions[1]),
		):
			result = context_handler.get_next_questions(
				object(),
				"I would start by checking the service logs.",
				1,
				candidate_ids=[10, 11, 12],
				session=session,
				prev_question="How would you investigate an outage?",
			)

		embed.assert_called_once_with(
			"Backend Developer\nHow would you investigate an outage?\n"
			"I would start by checking the service logs."
		)
		retrieve.assert_called_once_with(
			session, "Backend Developer", 3, candidate_ids=None,
			category="technical", query_embedding=[0.2] * 768,
		)
		generate.assert_called_once()
		self.assertEqual(generate.call_args.kwargs["next_question"], questions[1])
		self.assertEqual(result["status"], "success")

	def test_missing_embedding_preserves_prefetch_fallback(self):
		session = SimpleNamespace(current_state="technical", current_difficulty="medium")
		question = _question(1)
		with (
			patch.object(context_handler, "_role_for_session", return_value="Backend Developer"),
			patch.object(context_handler, "embed_text", return_value=None),
			patch.object(context_handler, "_retrieve_questions", side_effect=[[], [question]]) as retrieve,
			patch.object(
				context_handler,
				"_generate_better_response",
				return_value={"success": False},
			) as generate,
			patch.object(context_handler.random, "choice", return_value=question),
		):
			result = context_handler.get_next_questions(
				object(),
				"I would start by checking the service logs.",
				1,
				candidate_ids=[10, 11, 12],
				session=session,
			)

		self.assertEqual(retrieve.call_count, 2)
		self.assertEqual(retrieve.call_args_list[0].kwargs["candidate_ids"], [10, 11, 12])
		self.assertNotIn("candidate_ids", retrieve.call_args_list[1].kwargs)
		generate.assert_called_once()
		self.assertEqual(generate.call_args.kwargs["next_question"], question)
		self.assertEqual(result["status"], "success")

	def test_retrieval_keeps_filters_and_orders_by_embedding_similarity(self):
		session = SimpleNamespace(current_difficulty="medium", id=7)
		cursor = MagicMock()
		cursor_context = MagicMock()
		cursor_context.__enter__.return_value = cursor
		connection = MagicMock()
		connection.cursor.return_value = cursor_context
		with patch.object(context_handler, "connection", connection):
			context_handler._retrieve_questions(
				session,
				"Backend Developer",
				top_k=2,
				candidate_ids=[10, 11],
				category="technical",
				query_embedding=[0.3] * 768,
			)

		query, params = cursor.execute.call_args.args
		self.assertIn("ORDER BY iq.embedding <=> %s::vector, RANDOM()", query)
		self.assertIn("iq.difficulty = %s", query)
		self.assertIn("LOWER(category) = LOWER(%s)", query)
		self.assertIn("AND iq.id IN (%s, %s)", query)
		self.assertIn("asked_questions_id", query)
		self.assertEqual(params, ["Backend Developer", "medium", "technical", 7, 10, 11, [0.3] * 768, 2])
