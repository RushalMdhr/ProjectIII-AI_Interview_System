import re

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from ai_app.ai.utils.embeddings import embed_text
from ai_app.ai.utils.message import assistant_talking, user_talking
from ai_app.ai.utils.chats_handler import (
    chats_handler,
    generate_chat_title,
    generate_interview_intro,
)
# Previous text-only evaluator retained for reference:
# from ai_app.ai.utils.chats_handler import evaluate_interview_answer_llm
from ai_app.ai.utils.Evaluator import evaluate_candidate_answer

from .models import ChatSession, ChatMessage, InterviewFeedback
from accounts.models import UserProfile
from .serializers import (
    ChatSessionSerializer,
    ChatMessageSerializer,
    InterviewFeedbackSerializer,
)

from ai_app.ai.documents.tools.context_handler import (
    generate_interviewer_response,
    get_next_questions,
    next_interview_category,
    prefetch_next_questions,
)


INTERVIEW_LIMITS = {
    "easy": 5,
    "medium": 8,
    "hard": 10,
}

DIFFICULTY_LEVELS = {"easy": 0, "medium": 1, "hard": 2}
MINIMUM_INTERVIEW_ANSWER_WORDS = 3


def _update_interview_level(session, rating):
    ceiling = DIFFICULTY_LEVELS[session.interview_difficulty]
    current = DIFFICULTY_LEVELS[session.current_difficulty]
    if rating >= 8:
        current += 1
    elif rating <= 4:
        current -= 1
    current = max(0, min(current, ceiling))
    session.current_difficulty = next(
        name for name, level in DIFFICULTY_LEVELS.items() if level == current
    )


def _create_question_attempt(session, question):
    print("[ CREATE QUESTION ATTEMPT ] : ",question.get("id"),flush=True)
    return InterviewFeedback.objects.create(
        session=session,
        asked_questions_id=None if not question.get("id") else question.get("id"),
        question_text=question["question"],
        candidate_answer="",
        # question_number=session.question_count + 1,
        question_difficulty=question.get("difficulty", session.current_difficulty),
    )


def _find_similar_answer(candidate_answer, previous_answers):
    normalized_answer = " ".join(re.findall(r"\w+", candidate_answer.casefold()))
    if not normalized_answer:
        return False

    return any(
        _answers_are_similar(normalized_answer, previous_answer)
        for previous_answer in previous_answers
    )


def _answers_are_similar(normalized_answer, previous_answer):
    normalized_previous = " ".join(
        re.findall(r"\w+", previous_answer.casefold())
    )
    if normalized_answer == normalized_previous:
        return True
    return (
        min(len(normalized_answer), len(normalized_previous)) >= 30
        and SequenceMatcher(
            None,
            normalized_answer,
            normalized_previous,
            autojunk=False,
        ).ratio() >= 0.9
    )


def _count_similar_answers(candidate_answer, previous_answers):
    normalized_answer = " ".join(re.findall(r"\w+", candidate_answer.casefold()))
    if not normalized_answer:
        return 0
    return sum(
        _answers_are_similar(normalized_answer, previous_answer)
        for previous_answer in previous_answers
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def start_interview(request, session_id):
    try:
        print("[ START_INTERVIEW ]session id : ",session_id,flush=True)
        session = ChatSession.objects.get(
            id=session_id,
            user=request.user,
            archived=False,
        )
    except ChatSession.DoesNotExist:
        return Response({"error": "Chat session not found."}, status=status.HTTP_404_NOT_FOUND)

    if session.use_case != "interview_assessment":
        return Response({"error": "This session is not an interview."}, status=status.HTTP_400_BAD_REQUEST)

    print("[ START_INTERVIEW ]session id : ",session_id,flush=True)
    
    print("[ START_INTERVIEW ]feedback : ",session_id,flush=True)
    existing_attempt = session.interview_feedbacks.filter(
        candidate_answer="",
        rating__isnull=True,
    ).order_by("-created_at").first()
    ### ____________________________ WARNING _________________________________________
    if existing_attempt:
        return Response(
            {
                "session": ChatSessionSerializer(session).data,
                "interview_feedback": InterviewFeedbackSerializer(existing_attempt).data,
            },
            status=status.HTTP_200_OK,
        )

    profile = (
        UserProfile.objects.filter(user=request.user)
        .only("primary_role", "target_roles")
        .first()
    )
    role = ""
    if profile:
        role = (profile.primary_role or (profile.target_roles or [""])[0]).strip()
    if not role:
        return Response(
            {"error": "Add your target role to your profile before starting an interview."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    session.interview_role = role
    candidate_name = request.user.first_name.strip() or request.user.username
    opening_question = generate_interview_intro(candidate_name, role)
    print("[ START_INTERVIEW ]opening question : ",opening_question,flush=True)

    attempt = _create_question_attempt(
        session,
        {
            "question": opening_question,
            "answer": "",
            "difficulty": session.current_difficulty,
        },
    )
    session.question_count = 1
    session.current_state = "introduction"
    session.save(
        update_fields=["interview_role", "current_state", "question_count", "updated_at"]
    )
    print("[ START_INTERVIEW ]feedback : ",session_id,flush=True)

    return Response(
        {
            "session": ChatSessionSerializer(session).data,
            "interview_feedback": InterviewFeedbackSerializer(attempt).data,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_interview_history(request, session_id):
    try:
        session = ChatSession.objects.get(
            id=session_id,
            user=request.user,
            use_case="interview_assessment",
        )
    except ChatSession.DoesNotExist:
        return Response(
            {"error": "Interview session not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    attempts = session.interview_feedbacks.order_by("created_at", "id")
    return Response(
        {
            "session": ChatSessionSerializer(session).data,
            "interview_feedback": InterviewFeedbackSerializer(
                attempts,
                many=True,
            ).data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def prefetch_interview_questions(request, session_id):
    try:
        session = ChatSession.objects.get(
            id=session_id,
            user=request.user,
            archived=False,
            use_case="interview_assessment",
        )
    except ChatSession.DoesNotExist:
        return Response({"error": "Interview session not found."}, status=status.HTTP_404_NOT_FOUND)

    attempt = session.interview_feedbacks.filter(
        candidate_answer="",
        rating__isnull=True,
    ).order_by("-created_at").first()
    if not attempt:
        return Response({"error": "There is no pending interview question."}, status=status.HTTP_409_CONFLICT)

    result = prefetch_next_questions(request.user, session.id, attempt, top_k=3)
    if result["status"] == "missing_role":
        return Response({"error": "Add your target role to your profile."}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"prefetched_count": len(result["question_ids"])}, status=status.HTTP_200_OK)


def _send_interview_answer(request, session, user_content):
    word_count = len(
        re.findall(r"[^\W\d_]+(?:['’][^\W\d_]+)*", user_content, flags=re.UNICODE)
    )
    if word_count < MINIMUM_INTERVIEW_ANSWER_WORDS:
        return Response(
            {"error": "Please enter an answer of at least 3 words. Your message was not sent."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if session.halted:
        return Response({"error": "This interview has been halted."}, status=status.HTTP_409_CONFLICT)

    attempt = session.interview_feedbacks.filter(
        candidate_answer="",
        rating__isnull=True,
    ).select_related("asked_questions").order_by("-created_at").first()
    
    if not attempt:
        print("[ MESSAGE INTERVIEW ] : no attempt : ",flush=True)
        return Response(
            {"error": "Start the interview before submitting an answer."},
            status=status.HTTP_409_CONFLICT,
        )

    question_text = attempt.question_text or (
        attempt.asked_questions.question if attempt.asked_questions_id else ""
    )
    if not question_text:
        return Response(
            {"error": "The pending question is missing its question text."},
            status=status.HTTP_409_CONFLICT,
        )
    expected_answer = attempt.question_answer or (
        attempt.asked_questions.answer if attempt.asked_questions_id else ""
    )
    previous_attempts = list(
        session.interview_feedbacks
        .exclude(id=attempt.id)
        .exclude(candidate_answer="")
        .order_by("created_at")
        .values("question_text", "candidate_answer", "rating")
    )
    prior_answer_texts = [
        previous["candidate_answer"]
        for previous in previous_attempts
        if previous["rating"] is not None
    ]
    similar_answer_count = _count_similar_answers(
        user_content,
        prior_answer_texts,
    )
    repetition_count = similar_answer_count + 1 if similar_answer_count else 0
    matching_previous_answer = next(
        (
            previous_answer
            for previous_answer in reversed(prior_answer_texts)
            if _find_similar_answer(user_content, [previous_answer])
        ),
        None,
    )
    try:
        action_response = generate_interviewer_response(
            result=None,
            prev_question=question_text,
            next_question={"question": question_text},
            candidate_answer=user_content,
            repetition_count=repetition_count,
            matching_previous_answer=matching_previous_answer,
        )
        action = action_response["action"]

        if action in {"REPEAT", "REVIEW"}:
            attempt.question_text = action_response["question"]
            attempt.feedback = None
            attempt.save(update_fields=["question_text", "feedback", "updated_at"])
            serialized_attempt = InterviewFeedbackSerializer(attempt).data
            return Response(
                {
                    "session": ChatSessionSerializer(session).data,
                    "interview_feedback": serialized_attempt,
                    "next_question": serialized_attempt,
                },
                status=status.HTTP_201_CREATED,
            )

        if action not in {"CONTINUE", "SKIP"}:
            raise ValueError(f"Unsupported interviewer action: {action}")

        next_category = next_interview_category(session)

        if action == "SKIP":
            next_question_result = (
                get_next_questions(
                    user=request.user,
                    session_id=session.id,
                    category=next_category,
                    top_k=3,
                    candidate_ids=attempt.prefetched_question_ids,
                    session=session,
                )
                if next_category else None
            )
            attempt.candidate_answer = user_content
            attempt.rating = None
            attempt.feedback = None
            attempt.save(
                update_fields=["candidate_answer", "rating", "feedback", "updated_at"]
            )
            next_attempt = None
            completion_message = None

            if next_question_result and next_question_result["status"] == "success":
                next_attempt = _create_question_attempt(
                    session,
                    next_question_result["question"],
                )
                session.question_count += 1
                session.current_state = next_category
            else:
                session.halted = True
                session.archived = True
                completion_message = (
                    "The interview ended because there are no unused questions "
                    f"for the {next_category or 'next'} category."
                    if next_category
                    else "The interview is complete."
                )

            session.save(update_fields=[
                "current_state",
                "question_count",
                "halted",
                "archived",
                "updated_at",
            ])
            return Response(
                {
                    "session": ChatSessionSerializer(session).data,
                    "interview_feedback": InterviewFeedbackSerializer(attempt).data,
                    "next_question": (
                        InterviewFeedbackSerializer(next_attempt).data
                        if next_attempt else None
                    ),
                    "message": completion_message,
                },
                status=status.HTTP_201_CREATED,
            )

        dimensions = attempt.asked_questions.weights if attempt.asked_questions_id else []
        if not dimensions:
            dimensions = [{"label": session.current_state, "score": 1.0}]
        repeated_answer = repetition_count > 0

        # Legacy evaluator replaced by the structured GEval result:
        # rating, feedback = evaluate_interview_answer_llm(
        #     question_text, expected_answer, user_content
        # )
        geval_result = evaluate_candidate_answer(
            asked_question=question_text,
            expected_answer=expected_answer,
            candidate_answer=user_content,
            dimensions=dimensions,
            history=previous_attempts,
        )
        print("[ G EVAL ] : ", geval_result)
        if not isinstance(geval_result, dict) or not isinstance(
            geval_result.get("overall_score"), (int, float)
        ):
            raise ValueError("GEval returned an invalid evaluation result.")
        rating = max(0, min(10, round(geval_result["overall_score"])))
        _update_interview_level(session, rating)

        next_question_result = (
            get_next_questions(
                user=request.user,
                session_id=session.id,
                category=next_category,
                top_k=3,
                candidate_ids=attempt.prefetched_question_ids,
                session=session,
            )
            if next_category else None
        )
        interviewer_response = generate_interviewer_response(
            result=geval_result,
            prev_question=question_text,
            next_question=(
                next_question_result["question"]
                if next_question_result and next_question_result["status"] == "success"
                else None
            ),
            candidate_answer=user_content,
            repetition_count=repetition_count,
            matching_previous_answer=matching_previous_answer,
        )
        if interviewer_response["action"] in {"REPEAT", "REVIEW"}:
            attempt.question_text = interviewer_response["question"]
            attempt.feedback = None
            attempt.save(update_fields=["question_text", "feedback", "updated_at"])
            serialized_attempt = InterviewFeedbackSerializer(attempt).data
            return Response(
                {
                    "session": ChatSessionSerializer(session).data,
                    "interview_feedback": serialized_attempt,
                    "next_question": serialized_attempt,
                },
                status=status.HTTP_201_CREATED,
            )
        if interviewer_response["action"] == "SKIP":
            attempt.candidate_answer = user_content
            attempt.rating = None
            attempt.feedback = None
            attempt.save(
                update_fields=["candidate_answer", "rating", "feedback", "updated_at"]
            )
            next_attempt = None
            if next_question_result and next_question_result["status"] == "success":
                next_attempt = _create_question_attempt(
                    session,
                    next_question_result["question"],
                )
                session.question_count += 1
                session.current_state = next_category
                completion_message = None
            else:
                session.halted = True
                session.archived = True
                completion_message = (
                    "The interview ended because there are no unused questions "
                    f"for the {next_category or 'next'} category."
                    if next_category
                    else "The interview is complete."
                )
            session.save(update_fields=[
                "current_state",
                "question_count",
                "halted",
                "archived",
                "updated_at",
            ])
            return Response(
                {
                    "session": ChatSessionSerializer(session).data,
                    "interview_feedback": InterviewFeedbackSerializer(attempt).data,
                    "next_question": (
                        InterviewFeedbackSerializer(next_attempt).data
                        if next_attempt else None
                    ),
                    "message": completion_message,
                },
                status=status.HTTP_201_CREATED,
            )
        if not interviewer_response["feedback"].strip():
            raise ValueError("CONTINUE response did not include feedback.")
        end_for_repeated_answer = (
            repeated_answer
            and repetition_count >= MAX_REPEATED_ANSWER_COUNT
        )
        if end_for_repeated_answer:
            next_attempt = None
            session.halted = True
            session.archived = True
            completion_message = "Interview ended."
        elif next_question_result and next_question_result["status"] == "success":
            next_attempt = _create_question_attempt(
                session,
                next_question_result["question"],
            )
            session.question_count += 1
            session.current_state = next_category
            completion_message = None
        else:
            next_attempt = None
            session.archived = True
            if next_category:
                session.halted = True
                completion_message = (
                    "The interview ended because there are no unused questions "
                    f"for the {next_category} category."
                )
            else:
                completion_message = "The interview is complete."

    except Exception as error:
        print(f"[INTERVIEW] Answer processing failed: {error}", flush=True)
        return Response(
            {"error": "Failed to evaluate the interview answer."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    attempt.candidate_answer = user_content
    attempt.rating = rating
    attempt.feedback = json.dumps({
        "feedback_text": interviewer_response["feedback"],
        "overall_score": geval_result["overall_score"],
        "dimension_scores": geval_result.get("dimension_scores", {}),
    })
    attempt.save(update_fields=["candidate_answer", "rating", "feedback", "updated_at"])

    session.save(update_fields=[
        "current_difficulty",
        "current_state",
        "question_count",
        "halted",
        "archived",
        "updated_at",
    ])
    return Response(
        {
            "session": ChatSessionSerializer(session).data,
            "interview_feedback": InterviewFeedbackSerializer(attempt).data,
            "next_question": (
                InterviewFeedbackSerializer(next_attempt).data
                if next_attempt else None
            ),
            "message": completion_message,
        },
        status=status.HTTP_201_CREATED,
    )

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def sessions(request):

    if request.method == 'GET':
        sessions = ChatSession.objects.filter(
            user=request.user,
            archived=False
        ).order_by('-updated_at')

        serializer = ChatSessionSerializer(
            sessions,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    if request.method == 'POST':
        use_case = request.data.get(
            'use_case',
            'general_chat'
        )

        valid_use_cases = [
            choice[0]
            for choice in ChatSession.USE_CASE_CHOICES
        ]

        if use_case not in valid_use_cases:
            return Response(
                {
                    'error': 'Invalid use_case.',
                    'valid_use_cases': valid_use_cases
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        title = request.data.get(
            'title',
            'New Chat Session')
        print(f"[INTERVIEW SESSION CREATING] CHECKING ROLES : ",use_case,flush=True)
        if use_case == "interview_assessment":
            print(f"[I M IN] CHECKING ROLES")
            profile = (
                UserProfile.objects.filter(user=request.user)
                .only("primary_role", "target_roles")
                .first()
            )
            role = (
                profile.primary_role or (profile.target_roles or [""])[0]
                if profile
                else ""
            ).strip()
            if not role:
                return Response(
                    {"error": "Add your target role to your profile before starting an interview."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            interview_difficulty = request.data.get(
                'interview_difficulty',
                'medium',
            )
            if interview_difficulty not in INTERVIEW_LIMITS:
                return Response(
                    {'error': 'Invalid interview difficulty.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        session = ChatSession.objects.create(
            user=request.user,
            use_case=use_case,
            title=title,
            interview_difficulty=interview_difficulty,
            current_difficulty='easy',
            max_questions=INTERVIEW_LIMITS[interview_difficulty],
        )
        print(
            f"[INTERVIEW] CREATED session_id={session.id} "
            f"selected_difficulty={session.interview_difficulty!r} "
            f"current_difficulty={session.current_difficulty!r} "
            f"max_questions={session.max_questions}",
            flush=True,
        )

        serializer = ChatSessionSerializer(session)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request):

    print("[send_message] Request received", flush=True)
    user_content = request.data.get('user_content')
    session_id = request.data.get('session')
    print(f"[send_message] Input received: session_id={session_id}, has_user_content={bool(user_content)}", flush=True)

    # -------------------------
    # Validate input
    # -------------------------
    if not user_content or not user_content.strip():
        print("[send_message] Validation failed: user_content is missing or empty", flush=True)
        return Response(
            {
                'error': 'user_content is required.'
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # -------------------------
        # Get existing session OR create new session
        # -------------------------
        if session_id:
            print(f"[send_message] Looking up session: {session_id}", flush=True)

            try:
                session = ChatSession.objects.get(
                    id=session_id,
                    user=request.user,
                    archived=False
                )

            except ChatSession.DoesNotExist:
                print(f"[send_message] Session not found: {session_id}", flush=True)
                return Response(
                    {
                        'error': 'Chat session not found.'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

        else:
            print("[send_message] Creating a new session", flush=True)
            session = ChatSession.objects.create(
                user=request.user)
        print(
            f"[INTERVIEW] SESSION id={session.id} use_case={session.use_case!r} "
            f"ceiling={session.interview_difficulty!r} "
            f"current={session.current_difficulty!r} "
            f"count={session.question_count}/{session.max_questions} "
            f"archived={session.archived} halted={session.halted}",
            flush=True,
        )
        if session.use_case == "interview_assessment":
            return _send_interview_answer(request, session, user_content.strip())


        # --------------------------------
        # ADDING TITLE TO THE MESSAGE 
        # --------------------------------
        if session.title == 'New Chat Session':
            try:
                print(f"[send_message] Generating title for session {session.id}", flush=True)
                session.title = generate_chat_title(user_content)
                session.save(update_fields=['title', 'updated_at'])
                print(f"[send_message] Title generated: {session.title}", flush=True)
            except Exception as e:
                print(f"Title generation error: {str(e)}", flush=True)

                # Fallback if LLM title generation fails
                session.title = "New Chat Session"
                session.save(update_fields=['title', 'updated_at'])
                print("[send_message] Using fallback title", flush=True)


        # Get chat history

        previous_messages = ChatMessage.objects.filter(
            session=session
        ).order_by('created_at')

        print(f"[send_message] Loading chat history for session {session.id}", flush=True)
        print(f"[send_message] previous name {previous_messages}", flush=True)

        chat_history = []

        for message in previous_messages:

            if message.user_content:
                chat_history.append(user_talking(message.user_content))

            if message.assistant_content:
                chat_history.append(assistant_talking(message.assistant_content))
        print(f"[send_message] Chat history prepared: {len(chat_history)} entries", flush=True)

        # -------------------------
        # Generate embedding
        # -------------------------
        try:
            print("[send_message] Generating message embedding", flush=True)

            user_content_embedding = embed_text(
                user_content
            )
            print("[send_message] Message embedding generated", flush=True)

        except Exception as e:

            print(
                f"Embedding error: {str(e)}",
                flush=True
            )

            return Response(
                {
                    'error': 'Failed to generate message embedding.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        context = ""

        # -------------------------
        # Generate AI response
        # -------------------------
        try:

            print("[send_message] Generating AI response", flush=True)

            result = chats_handler(
                user_content=user_content,
                chat_history=chat_history,
                # context=context,
                use_case=session.use_case,
            )

            assistant_content = result["assistant_content"]

            print(
                "AI response generated successfully",
                flush=True
            )

            print(
                "Assistant response length:",
                len(assistant_content),
                flush=True
            )

        except Exception as e:

            print(
                f"Error generating AI response: {str(e)}",
                flush=True
            )

            return Response(
                {
                    'error': 'Failed to generate AI response.',
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # -------------------------
        # Save message
        # -------------------------
        message = ChatMessage.objects.create(
            session=session,
            user=request.user,
            user_content=result["user_content"],
            user_content_embedding=user_content_embedding,
            assistant_content=result["assistant_content"],
        )
        print(f"[send_message] Message saved: id={message.id}, session_id={session.id}", flush=True)

        # -------------------------
        # Serialize response
        # -------------------------
        message_serializer = ChatMessageSerializer(
            message
        )

        session_serializer = ChatSessionSerializer(
            session
        )
        print("[send_message] Response serialized successfully", flush=True)

        return Response(
            {
                'session': session_serializer.data,
                'message': message_serializer.data
            },
            status=status.HTTP_201_CREATED
        )

    except Exception as e:

        print(
            f"[send_message] Unexpected error: {str(e)}",
            flush=True
        )

        return Response(
            {
                'error': 'Something went wrong while processing your message.',
                'details': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_messages(request, session_id):

    # Get the session belonging to the authenticated user
    try:
        session = ChatSession.objects.get(
            id=session_id,
            user=request.user,
            archived=False
        )
    except ChatSession.DoesNotExist:
        return Response(
            {
                'error': 'Chat session not found.'
            },
            status=status.HTTP_404_NOT_FOUND
        )

    # Get messages for this session
    messages = ChatMessage.objects.filter(
        session=session,
        user=request.user
    ).order_by('-created_at')

    # Optional limit
    limit = request.query_params.get('limit')

    if limit is not None:
        try:
            limit = int(limit)

            if limit <= 0:
                return Response(
                    {
                        'error': 'limit must be greater than 0.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Fetch latest N messages
            messages = messages[:limit]

        except ValueError:
            return Response(
                {
                    'error': 'limit must be an integer.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    # Return messages in chronological order
    messages = messages.order_by('created_at')

    serializer = ChatMessageSerializer(
        messages,
        many=True
    )

    return Response(
        serializer.data,
        status=status.HTTP_200_OK
    )

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_session(request, session_id):

    try:
        session = ChatSession.objects.get(
            id=session_id,
            user=request.user,
            archived=False
        )
    except ChatSession.DoesNotExist:
        return Response(
            {'error': 'Chat session not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    session.archived = True
    session.save()

    return Response(
        {
            'message': 'Chat session archived successfully.'
        },
        status=status.HTTP_200_OK
    )