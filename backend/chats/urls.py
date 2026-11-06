from django.urls import path

from chats.views import (
    sessions,
    get_messages,
    send_message,
    delete_session,
    start_interview,
    get_interview_history,
    prefetch_interview_questions,
)


urlpatterns = [
    path('session/', sessions, name='sessions'),
    path('message/', send_message, name='send_message'),
    path('session/<int:session_id>/start-interview/', start_interview, name='start_interview'),
    path('session/<int:session_id>/interview-history/', get_interview_history, name='interview_history'),
    path('session/<int:session_id>/prefetch-questions/', prefetch_interview_questions, name='prefetch_interview_questions'),
    path('session/<int:session_id>/messages', get_messages, name='get_messages'),
    path('session/<int:session_id>/delete', delete_session, name='delete_session')
]