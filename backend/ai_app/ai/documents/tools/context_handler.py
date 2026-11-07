from accounts.models import UserProfile
from chats.models import ChatSession
from django.db import connection
from ai_app.ai.llm import ai
from ai_app.ai.utils.message import system_talking,user_talking
from ai_app.ai.utils.embeddings import embed_text

import json
import re


def _default_question(role, difficulty, session=None):
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
		question = str(ai([system_talking(prompt),user_talking('next question please')], session=session)).strip()
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
				iq.difficulty, iq.keywords, iq.source_id, iq.weights
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


def _generate_better_response(result, prev_question, next_question, candidate_answer, history=None):
	print("[INSIDE _generate_better_response ]",flush=True)
	jod = '''{
    "action": "REPEAT | SKIP | CONTINUE",
    "feedback": "Your natural conversational response to the candidate (do not include internal scores).",
    "question": "The text of the question to display next (Simplified previous question if REPEAT, otherwise the Next Question)."
	}'''

	if history is None:
		history = []
	if isinstance(history, (list, tuple, dict)):
		history_text = json.dumps(history, ensure_ascii=False)
	else:
		history_text = str(history) if history else "No prior conversation history."

	prompt = f"""
	You are an expert AI Interviewer managing a live interview. Your job is to read the candidate's response and decide the next conversational action.

	### INPUT VARIABLES
	- Evaluation Result: {result}
	- Previous Question: {prev_question}
	- Proposed Next Question: {next_question}
	- Conversation History: {history_text}

	### DECISION LOGIC (Choose exactly ONE action)

	**1. REPEAT**
	- Trigger: The candidate asks to repeat, simplify, clarify, or explicitly says they didn't understand. (Also trigger if they ask for a hint).
	- Action: Set action to "REPEAT". In the "question" field, provide a simplified/clearer version of the *Previous Question*. 
	- Rule: Do NOT provide the actual answer. Do NOT move to the next question.

	**2. SKIP**
	- Trigger: The candidate explicitly asks to skip, pass, or says "I don't know" / "Next question please".
	- Action: Set action to "SKIP". Provide a brief, polite acknowledgment in the "feedback" field. Move to the *Proposed Next Question*.

	**3. CONTINUE**
	- Trigger: The candidate provides a genuine attempt at an answer (even if the answer is wrong or poor).
	- Action: Set action to "CONTINUE". Use the Evaluation Result to write a brief, natural sentence of feedback (e.g., "Good point about X," or "Let's explore Y next"). Move to the *Proposed Next Question*.
	- Rule: NEVER confuse a bad answer with a SKIP. If they tried to answer, it is CONTINUE.

	### IMPORTANT RULES
	1. **Conversational Tone:** The "feedback" field must sound like a human speaking, not a grading rubric. Never mention scores, dimensions, or classifications.
	2. **No Looping:** If the history shows you have already repeated this question once, force a "SKIP" or "CONTINUE" instead. Do not get stuck in a REPEAT loop.
	3. **Strict JSON Output:** Return ONLY valid JSON. Do not use Markdown (```json). Do not add text before or after the JSON.

	### OUTPUT FORMAT
	{jod}
	"""
	messages = [
		{"role": "system", "content": prompt},
		{"role": "user", "content": candidate_answer }
		]
	raw_response = ai(msg=messages,format='json')
	print("[RAW RESPONSE] : ",raw_response,flush=True)

	# --- validate ---
	try:
		parsed = json.loads(raw_response)
		print("[ PARSED ] : ",parsed,flush=True)
	except (json.JSONDecodeError, TypeError) as e:
		return {"success": False, "error": f"Invalid JSON: {e}", "raw": raw_response}

	return {"success": True, "data": parsed}


def _explicit_interview_action(candidate_answer):
	answer = candidate_answer.strip().lower()
	if re.search(r"\b(?:do not|don't|never)\s+(?:please\s+)?(?:repeat|skip)\b", answer):
		return None
	if re.search(
		r"\b(?:"
		r"(?:please\s+)?repeat(?:\s+(?:the|that|this)\s+question)?|"
		r"(?:can|could|would)\s+you\s+(?:please\s+)?repeat|"
		r"(?:can|could|would)\s+you\s+(?:please\s+)?(?:explain|clarify|rephrase)|"
		r"say\s+(?:that|it)\s+again|"
		r"rephrase|clarify|"
		r"i\s+(?:do not|don't|did not|didn't|cannot|can't|could not|couldn't)\s+understand|"
		r"what\s+does?\s+(?:that|this)\s+mean"
		r")\b",
		answer,
	):
		return "REPEAT"
	if re.search(
		r"\b(?:"
		r"(?:please\s+)?skip(?:\s+(?:this|the question|it))?|"
		r"(?:please\s+)?pass(?:\s+on\s+(?:this|the question|it))?|"
		r"i\s+(?:do not|don't)\s+know(?:\s+the answer)?|"
		r"i have no idea"
		r")\b",
		answer,
	):
		return "SKIP"
	return None


def get_next_questions(
	user,
	user_content,
	session_id,
	top_k=3,
	candidate_ids=None,
	session=None,
	prev_question="",
	result=None,
	history=None
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
		candidate_ids=candidate_ids,
	)
	print("[context_handler] questions found: ", len(next_question), flush=True)

	if not next_question and candidate_ids:
		next_question = _retrieve_questions(session, role, top_k)
		print("[context_handler] No questions found with candidate_ids; retried without filter", next_question, flush=True)

	if not next_question and session.current_difficulty is not None:
		next_question = _retrieve_questions(
			session,
			role,
			top_k,
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
				"weights": [],
				"distance": None,
			},
		}

	selected_question = next_question[0]

	demo_question = _generate_better_response(
		result=result,
		prev_question=prev_question,
		next_question=selected_question,
		candidate_answer=user_content,
		history=history,
	)
	ai_response = demo_question.get("data", {}) if demo_question.get("success") else {}
	explicit_action = _explicit_interview_action(user_content)
	action = explicit_action or "CONTINUE"
	model_action = ai_response.get("action")
	if isinstance(model_action, str):
		model_action = model_action.strip().upper()
	action_feedback = (
		ai_response.get("feedback")
		if model_action == action
		else None
	)
	response_question = (
		ai_response.get("question")
		if action == "REPEAT"
		else selected_question[1]
	)
	if not isinstance(response_question, str) or not response_question.strip():
		response_question = prev_question if action == "REPEAT" else selected_question[1]
	if not isinstance(response_question, str) or not response_question.strip():
		response_question = selected_question[1]


	return {
		"status": "success",
		"role": role,
		"question": {
			"id": selected_question[0],
			
			"action" : action,
			"feedback" : action_feedback,
			"question": response_question,

			"answer": selected_question[2],
			"role": selected_question[3],
			"experience": selected_question[4],
			"difficulty": selected_question[5],
			"keywords": selected_question[6],
			"distance": None,
			"source_id": selected_question[7],
			"weights": selected_question[8] or [],
		},
	}