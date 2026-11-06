import json
import random

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


def interview_category_sequence(session):
	sequences = {
		"easy": [
			"introduction",
			"experience",
			"behavioral",
			"situational",
			"technical",
		],
		"medium": [
			"introduction",
			"experience",
			"experience",
			"behavioral",
			"behavioral",
			"situational",
			"technical",
			"technical",
		],
		"hard": [
			"introduction",
			"introduction",
			"experience",
			"experience",
			"behavioral",
			"behavioral",
			"situational",
			"situational",
			"technical",
			"technical",
		],
	}
	sequence = sequences[session.interview_difficulty].copy()
	remaining_categories = sequence[1:]
	random.Random(session.id).shuffle(remaining_categories)
	return [sequence[0], *remaining_categories][:session.max_questions]


def next_interview_category(session):
	sequence = interview_category_sequence(session)
	if session.question_count >= session.max_questions:
		return None
	if session.question_count >= len(sequence):
		return None
	return sequence[session.question_count]


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

def _retrieve_questions(
	session,
	role,
	top_k,
	category,
	candidate_ids=None,
	match_difficulty=True,
):
	difficulty_filter = ""
	candidate_filter = ""
	params = [role]
	if match_difficulty and session.current_difficulty is not None:
		difficulty_filter = "AND iq.difficulty = %s"
		params.append(session.current_difficulty)
	params.append(f"%{category}%")
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
				iq.difficulty, iq.keywords, iq.source_id, iq.weights
			FROM common_interviewquestions iq
			WHERE (LOWER(iq.role) = LOWER(%s) OR LOWER(iq.role) = 'common')
			{difficulty_filter}
			AND COALESCE(iq.categories::text, '') ILIKE %s
			AND iq.id NOT IN (
				SELECT asked_questions_id
				FROM chats_interviewfeedback
				WHERE session_id = %s AND asked_questions_id IS NOT NULL
			)
			{candidate_filter}
			ORDER BY RANDOM()
			LIMIT %s;
		""", params)
		print("[ FETCHING NEXT QUESTION ] : ",flush=True)
		return cur.fetchall()


def prefetch_next_questions(user, session_id, attempt, top_k=3):
	session = ChatSession.objects.get(id=session_id, user=user, archived=False)
	role = _role_for_session(user, session)
	if not role:
		return {"status": "missing_role", "question_ids": []}

	category = next_interview_category(session)
	if not category:
		attempt.prefetched_question_ids = []
		attempt.save(update_fields=["prefetched_question_ids", "updated_at"])
		return {"status": "complete", "question_ids": []}

	questions = _retrieve_questions(session, role, top_k, category)
	attempt.prefetched_question_ids = [question[0] for question in questions]
	attempt.save(update_fields=["prefetched_question_ids", "updated_at"])
	return {"status": "success", "question_ids": attempt.prefetched_question_ids}


def _parse_interviewer_response(raw_response, require_feedback=False):
	if isinstance(raw_response, dict):
		response = raw_response
	else:
		response_text = str(raw_response or "").strip()
		decoder = json.JSONDecoder()
		response = None
		for index, character in enumerate(response_text):
			if character != "{":
				continue
			try:
				candidate, _ = decoder.raw_decode(response_text[index:])
			except json.JSONDecodeError:
				continue
			if isinstance(candidate, dict):
				response = candidate
				break
		if response is None:
			raise ValueError("Interviewer response did not contain a JSON object.")

	action = response.get("action")
	if isinstance(action, str):
		action = action.strip().upper()
	feedback = response.get("feedback")
	question = response.get("question")
	if action not in {"CONTINUE", "REPEAT", "SKIP", "REVIEW"}:
		raise ValueError("Interviewer response has an unsupported action.")
	if action != "CONTINUE":
		feedback = ""
	if feedback is None:
		feedback = ""
	if question is None and action in {"CONTINUE", "SKIP"}:
		question = ""
	if (
		not isinstance(feedback, str)
		or (require_feedback and action == "CONTINUE" and not feedback.strip())
		or not isinstance(question, str)
		or (action in {"REPEAT", "REVIEW"} and not question.strip())
	):
		raise ValueError("Interviewer response is missing required action-specific fields.")

	return {"action": action, "feedback": feedback, "question": question}


def generate_interviewer_response(
	result,
	prev_question,
	next_question,
	candidate_answer,
	repetition_count=0,
	matching_previous_answer=None,
):
	output_format = {
		"type": "object",
		"properties": {
			"action": {
				"type": "string",
				"enum": ["CONTINUE", "REPEAT", "SKIP", "REVIEW"],
			},
			"feedback": {"type": "string"},
			"question": {"type": "string"},
		},
		"required": ["action", "feedback", "question"],
		"additionalProperties": False,
	}

	prompt=f"""
	You are an AI interviewer responsible for managing the interview conversation naturally and deciding the next interview action based on the candidate's response.

	### INPUT VARIABLES

	- Evaluation Result: {result}
	- Previous Question: {prev_question}
	- Next Question: {next_question}
	- Repetition Count: {repetition_count}
	- Similar Previous Answer: {matching_previous_answer}

	### YOUR RESPONSIBILITIES

	Determine exactly one action:

	**1. REPEAT**
	- If the candidate requests repetition, clarification, or says they couldn't understand the question.
	- Rephrase the previous question using simpler, clearer language.
	- Preserve the original meaning.
	- Do not provide hints or answers.
	- Do not move to the next question.

	**2. SKIP**
	- If the candidate explicitly requests to skip, pass, or says they don't know the answer.
	- Respond with a short, natural acknowledgment.
	- Proceed to the next question.

	**3. CONTINUE**
	- If the candidate has answered the question.
	- Use the evaluation result and dimension reasons to generate one short, natural sentence of feedback or encouragement.
	- Avoid generic compliments.
	- Do not invent strengths that are not supported by the evaluation.
	- Proceed to the next question.
	- If a similar previous answer is provided, acknowledge it naturally and invite a genuinely new example or a different detail.
	- If the repetition count is 4 or more, explain conversationally that the interview will end because the same answer has been repeated.
	- Vary the wording and tone to fit the conversation; do not reuse a stock warning or repeat the same sentence structure.

	**4. REVIEW**
	- If suspicious_break is true and overall_score is 0.0.
	- Do not automatically assume the candidate is cheating.
	- Request further answer verification instead of immediately proceeding.
	- Do not generate normal evaluation feedback.

	### IMPORTANT RULES

	- Return feedback only for CONTINUE. For REPEAT, SKIP, or REVIEW, return an empty feedback string.
	- Never confuse a poor answer with a request to skip.
	- A score of 0.0 alone does not indicate suspicious behavior.
	- Candidate intent takes priority when deciding whether to repeat or skip.
	- Keep responses conversational, short, and professional.
	- Never expose internal evaluation scores or classification details.

	### OUTPUT FORMAT

	Return valid JSON matching this schema, without Markdown or additional text.

	{json.dumps(output_format)}
	"""
	messages = [
		{"role": "system", "content": prompt},
		{"role": "user", "content": candidate_answer }
		]
	raw_response = ai(msg=messages, temperature=0.7, format=output_format)
	try:
		return _parse_interviewer_response(
			raw_response,
			require_feedback=result is not None,
		)
	except ValueError as first_error:
		print(
			f"[INTERVIEW] Invalid interviewer JSON; retrying once: {first_error}",
			flush=True,
		)

	retry_messages = [
		{
			"role": "system",
			"content": (
				prompt
				+ "\nYour previous response was invalid. Return exactly one valid JSON "
				"object with action, feedback, and question fields. No extra text."
			),
		},
		{"role": "user", "content": candidate_answer},
	]
	retry_response = ai(msg=retry_messages, temperature=0.7, format=output_format)
	try:
		return _parse_interviewer_response(
			retry_response,
			require_feedback=result is not None,
		)
	except ValueError as retry_error:
		print(
			f"[INTERVIEW] Invalid interviewer JSON after retry: {retry_error}",
			flush=True,
		)
		if result is not None:
			if repetition_count >= 4:
				feedback = random.choice([
					"I think we've covered this example a few times, so let's wrap up here.",
					"We've returned to the same example a few times; I'll bring the interview to a close.",
					"I hear you. Since we've revisited this answer several times, let's finish the interview here.",
				])
			elif repetition_count:
				feedback = random.choice([
					"I remember this example. Could you share a different one next time?",
					"We've touched on this example already; another experience would help me understand your range.",
					"I recognize this story. When you can, try giving me a different example.",
				])
			else:
				feedback = random.choice([
					"Thanks for walking me through that. Let's move on.",
					"I appreciate the explanation. Let's continue with the next question.",
					"That gives me a better sense of your thinking. Let's keep going.",
				])
			return {
				"action": "CONTINUE",
				"feedback": feedback,
				"question": "",
			}
		raise ValueError("Interviewer failed to return a valid response.") from retry_error

def get_next_questions(
	user,
	session_id,
	category,
	top_k=3,
	candidate_ids=None,
	session=None,
):
	if session is None:
		session = ChatSession.objects.get(id=session_id, user=user, archived=False)
	role = _role_for_session(user, session)
	if not role:
		return {"status": "missing_role", "message": "Please provide your target role first."}

	next_question = _retrieve_questions(
		session,
		role,
		top_k,
		category,
		candidate_ids=candidate_ids,
	)
	print("[context_handler] questions found: ", len(next_question), flush=True)

	if not next_question and candidate_ids:
		next_question = _retrieve_questions(session, role, top_k, category)
		print(
			"[context_handler] No questions found with candidate_ids; "
			"retried without filter",
			next_question,
			flush=True,
		)

	if not next_question and session.current_difficulty is not None:
		next_question = _retrieve_questions(
			session,
			role,
			top_k,
			category,
			match_difficulty=False,
		)
		print(
			"[context_handler] No questions found at current difficulty; "
			"retried without difficulty filter",
			next_question,
			flush=True,
		)

	if not next_question:
		return {
			"status": "no_questions",
			"category": category,
			"question": None,
		}

	question_row = next_question[0]
	selected_question = {
		"id": question_row[0],
		"question": question_row[1],
		"answer": question_row[2],
		"role": question_row[3],
		"experience": question_row[4],
		"difficulty": question_row[5],
		"keywords": question_row[6],
		"source_id": question_row[7],
		"weights": question_row[8] or [],
		"category": category,
		"distance": None,
	}

	return {
		"status": "success",
		"role": role,
		"question": selected_question,
	}