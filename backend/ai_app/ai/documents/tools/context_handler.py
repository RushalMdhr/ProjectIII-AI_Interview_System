from accounts.models import UserProfile
from chats.models import ChatSession
from django.db import connection
from ai_app.ai.llm import ai
from ai_app.ai.utils.message import system_talking,user_talking
from ai_app.ai.utils.embeddings import embed_text


def _default_question(role, difficulty):
	print(
		f"[INTERVIEW-RAG] FALLBACK generation started role={role!r} "
		f"difficulty={difficulty!r}",
		flush=True,
	)
	prompt = (
		"Generate one concise interview question only. Do not add an answer, "
		f"markdown, numbering, or explanation. The target role is {role} and "
		f"the difficulty is {difficulty}."
	)
	try:
		question = str(ai([system_talking(prompt),user_talking('next question please')])).strip()
		question = question.splitlines()[0].strip(" -*0123456789.:")
		if question:
			print(
				f"[INTERVIEW-RAG] FALLBACK generated question={question!r}",
				flush=True,
			)
			return question
	except Exception as error:
		print(f"[context_handler] Default question generation failed: {error}", flush=True)
	fallback = f"Describe a recent {difficulty}-level problem you solved as a {role}."
	print(f"[INTERVIEW-RAG] FALLBACK static question={fallback!r}", flush=True)
	return fallback


def _role_for_session(user, session):
	if session.interview_role:
		return session.interview_role

	profile = (
		UserProfile.objects.filter(user=user)
		.only("primary_role", "target_roles")
		.first()
	)
	role = ""
	if profile:
		role = (profile.primary_role or (profile.target_roles or [""])[0]).strip()
	if role:
		session.interview_role = role
		session.save(update_fields=["interview_role", "updated_at"])
	return role


# def _retrieve_questions(session, role, query_embedding, top_k, candidate_ids=None):
# 	candidate_filter = ""
# 	params = [query_embedding, role, session.current_difficulty, session.id]
# 	if candidate_ids:
# 		placeholders = ", ".join(["%s"] * len(candidate_ids))
# 		candidate_filter = f"AND iq.id IN ({placeholders})"
# 		params.extend(candidate_ids)
# 	params.extend([query_embedding, top_k])

# 	with connection.cursor() as cur:
# 		cur.execute(f"""
# 			SELECT
# 				iq.id, iq.question, iq.answer, iq.role, iq.experience,
# 				iq.difficulty, iq.keywords, iq.source_id,
# 				iq.embedding <=> %s::vector AS distance
# 			FROM common_interviewquestions iq
# 			WHERE LOWER(iq.role) = LOWER(%s)
# 			  AND iq.difficulty = %s
# 			  AND iq.id NOT IN (
# 				  SELECT asked_questions_id
# 				  FROM chats_interviewfeedback
# 				  WHERE session_id = %s AND asked_questions_id IS NOT NULL
# 			  )
# 			  {candidate_filter}
# 			ORDER BY iq.embedding <=> %s::vector
# 			LIMIT %s;
# 		""", params)
# 		print("[ FETCHING NEXT QUESTION ] : ",flush=True)
# 		return cur.fetchall()

def _retrieve_questions(session, role, top_k, candidate_ids=None, match_difficulty=True):
	difficulty_filter = ""
	candidate_filter = ""
	params = [role]
	if match_difficulty and session.current_difficulty is not None:
		difficulty_filter = "AND iq.difficulty = %s"
		params.append(session.current_difficulty)
	params.append(session.id)
	if candidate_ids:
		placeholders = ", ".join(["%s"] * len(candidate_ids))
		candidate_filter = f"AND iq.id IN ({placeholders})"
		params.extend(candidate_ids)
	params.append(top_k)

	with connection.cursor() as cur:
		cur.execute(f"""
			SELECT
				iq.id, iq.question, iq.answer, iq.role, iq.experience,
				iq.difficulty, iq.keywords, iq.source_id
			FROM common_interviewquestions iq
			WHERE (LOWER(iq.role) = LOWER(%s) OR LOWER(iq.role) = 'common')
			{difficulty_filter}
			AND iq.id NOT IN (
				SELECT asked_questions_id
				FROM chats_interviewfeedback
				WHERE session_id = %s AND asked_questions_id IS NOT NULL
			)
			{candidate_filter}
			LIMIT %s;
		""", params)
		print("[ FETCHING NEXT QUESTION ] : ",flush=True)
		return cur.fetchall()


def prefetch_next_questions(user, session_id, attempt, top_k=3):
	session = ChatSession.objects.get(id=session_id, user=user, archived=False)
	role = _role_for_session(user, session)
	if not role:
		return {"status": "missing_role", "question_ids": []}

	questions = _retrieve_questions(session, role, top_k)
	attempt.prefetched_question_ids = [question[0] for question in questions]
	attempt.save(update_fields=["prefetched_question_ids", "updated_at"])
	return {"status": "success", "question_ids": attempt.prefetched_question_ids}


def get_next_questions(
	user,
	user_content,
	session_id,
	top_k=3,
	candidate_ids=None,
	session=None,
):
	if session is None:
		session = ChatSession.objects.get(id=session_id, user=user, archived=False)
	role = _role_for_session(user, session)
	if not role:
		return {"status": "missing_role", "message": "Please provide your target role first."}

	questions = _retrieve_questions(
		session,
		role,
		top_k,
		candidate_ids=candidate_ids,
	)
	print("[context_handler] questions found: ", len(questions), flush=True)

	if not questions and candidate_ids:
		questions = _retrieve_questions(session, role, top_k)
		print("[context_handler] No questions found with candidate_ids; retried without filter", questions, flush=True)

	if not questions and session.current_difficulty is not None:
		questions = _retrieve_questions(
			session,
			role,
			top_k,
			match_difficulty=False,
		)
		print(
			"[context_handler] No questions found at current difficulty; "
			"retried without difficulty filter",
			questions,
			flush=True,
		)

	if not questions:
		return {
			"status": "success",
			"role": role,
			"generated": True,
			"question": {
				"id": None,
				"question": _default_question(role, session.current_difficulty),
				"answer": "",
				"role": role,
				"experience": "any",
				"difficulty": session.current_difficulty,
				"keywords": [],
				"distance": None,
			},
		}

	selected_question = questions[0]
	return {
		"status": "success",
		"role": role,
		"question": {
			"id": selected_question[0],
			"question": selected_question[1],
			"answer": selected_question[2],
			"role": selected_question[3],
			"experience": selected_question[4],
			"difficulty": selected_question[5],
			"keywords": selected_question[6],
			"distance": None,
			"source_id": selected_question[7],
		},
	}