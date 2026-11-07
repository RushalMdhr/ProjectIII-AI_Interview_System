import re

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from ai_app.ai.utils.embeddings import embed_text
from ai_app.ai.utils.message import assistant_talking, user_talking
from ai_app.ai.utils.chats_handler import (
    chats_handler,
    evaluate_interview_answer_llm,
    generate_chat_title,
    generate_interview_intro,
)
from ai_app.ai.utils.Evaluator import evaluate_candidate_answer

from .models import ChatSession, ChatMessage, InterviewFeedback
from accounts.models import UserProfile
from .serializers import (
    ChatSessionSerializer,
    ChatMessageSerializer,
    InterviewFeedbackSerializer,
)

from ai_app.ai.documents.tools.context_handler import (
    get_next_questions,
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
    opening_question = generate_interview_intro(
        candidate_name, role, user=request.user, session=session
    )
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
    session.save(update_fields=["interview_role", "question_count", "updated_at"])
    print("[ START_INTERVIEW ]feedback : ",session_id,flush=True)

    return Response(
        {
            "session": ChatSessionSerializer(session).data,
            "interview_feedback": InterviewFeedbackSerializer(attempt).data,
        },
        status=status.HTTP_201_CREATED,
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


def _get_chat_history(session, limit=None,use_case='general_chat'):
    # Usage (gets ALL messages):
    # history = get_chat_history(session)

    # Usage (gets only last 5):
    # history = get_chat_history(session, limit=5)

    # Base query
    if use_case == 'general_chat':
        queryset = ChatMessage.objects.filter(session=session)
    elif use_case == 'interview_assessment':
        queryset = InterviewFeedback.objects.filter(session=session)
    else:
        raise ValueError(f"Unsupported chat history use case: {use_case}")
    
    # Apply limit only if it's not None (infinity)
    if limit is not None:
        recent_messages = list(queryset.order_by('-created_at')[:limit])
        recent_messages.reverse() # Chronological order
    else:
        recent_messages = list(queryset.order_by('created_at')) # Chronological order

    # Format for LLM
    history_text = ""
    for msg in recent_messages:
        if use_case == 'general_chat':
            if msg.user_content:
                history_text += f"User: {msg.user_content}\n"
            if msg.assistant_content:
                history_text += f"Assistant: {msg.assistant_content}\n"
        else:
            if msg.question_text:
                history_text += f"Assistant: {msg.question_text}\n"
            if msg.candidate_answer:
                history_text += f"User: {msg.candidate_answer}\n"
            # if msg.feedback:
            #     history_text += f"Assistant: {msg.feedback}\n"

    return history_text.strip()

def _update_interview_state(session):
    state_sequences = {
        "easy": "IBEST",
        "medium": "IBBEESST",
        "hard": "IIBBEESSTT",
    }
    state_names = {
        "I": "INTRODUCTION",
        "B": "BEHAVIOURAL",
        "E": "EXPERIENCE",
        "S": "SITUATIONAL",
        "T": "technical",
    }
    sequence = state_sequences[session.current_difficulty]
    next_question_index = min(session.question_count, len(sequence) - 1)
    session.current_state = state_names[sequence[next_question_index]]


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
    expected_answer = attempt.asked_questions.answer if attempt.asked_questions_id else ""
    dimensions = attempt.asked_questions.weights if attempt.asked_questions_id else []
    try:
        print("[ CHECKER ] : ",flush=True)

        geval_result = evaluate_candidate_answer(
            asked_question=question_text,
            expected_answer=expected_answer,
            candidate_answer=user_content,
            dimensions=dimensions,
        )
        history = _get_chat_history(session=session,use_case='interview_assessment')
        print("[HISTORY] : ",history,flush=True)
        print("[ G EVAL ] SUCESS !", geval_result)

    except Exception as error:
        print(f"[INTERVIEW] Answer processing failed: {error}", flush=True)
        return Response(
            {"error": "Failed to evaluate the interview answer."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    print("[ CHECKER ] : ",flush=True)
# ___________________ update later __________________
    rating = geval_result["overall_score"]
    _update_interview_level(session, rating)
    feedback = next(iter(geval_result["dimension_scores"].values()))['reason']
    assistant_content = feedback
    next_question = None
    next_attempt = None

    if rating <= 1:
        session.halted = True
        session.archived = True
        assistant_content = (
            f"{feedback}\n\nInterview paused because the answer was not relevant. "
            "Please restart when you are ready to continue."
        )
    elif session.question_count >= session.max_questions:
        session.archived = True
        assistant_content = (
            f"{feedback}\n\nInterview complete. Your selected question limit has been reached."
        )
    else:
        result = get_next_questions(
            user=request.user,
            user_content=user_content,
            session_id=session.id,
            top_k=3,
            candidate_ids=attempt.prefetched_question_ids,
            session=session,
	        prev_question=question_text,
            result=geval_result,
            history=history
        )
        print("[RESULT WITH GEVAL] : ",result)
        if result.get("status") == "missing_role":
            session.halted = True
            session.archived = True
            assistant_content = (
                f"{feedback}\n\nInterview paused. Please add your target role to your profile."
            )
        else:
            next_question = result["question"]
            assistant_content = next_question.get("feedback") or feedback

    if next_question and next_question.get("action") == "REPEAT":
        attempt.candidate_answer = user_content
        attempt.feedback = "REPEAT"
        attempt.save(update_fields=["candidate_answer", "feedback", "updated_at"])
        repeated_attempt = InterviewFeedback.objects.create(
            session=session,
            asked_questions=None,
            question_text=next_question.get("question") or question_text,
            candidate_answer="",
            question_difficulty=attempt.question_difficulty or session.current_difficulty,
        )
        return Response(
                {
                    "session": ChatSessionSerializer(session).data,
                    "interview_feedback": InterviewFeedbackSerializer(attempt).data,
                    "next_question": InterviewFeedbackSerializer(repeated_attempt).data,
                },
                status=status.HTTP_201_CREATED,
            )

    _update_interview_state(session)

    attempt.candidate_answer = user_content
    attempt.rating = geval_result
    attempt.feedback = assistant_content
    attempt.save(update_fields=["candidate_answer", "rating", "feedback", "updated_at"])

    print("[ NEXT QUESTION ] : ",next_question,flush=True)
    if next_question:
        next_attempt = _create_question_attempt(session, next_question)
        session.question_count += 1
        print("[ NEXT QUESTION ] : ",next_question,flush=True)

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
                session.title = generate_chat_title(
                    user_content, user=request.user, session=session
                )
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
                user=request.user,
                session=session,
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