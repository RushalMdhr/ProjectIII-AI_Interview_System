from django.urls import path
from common.views import *
from common.evaluation_views import evaluation_generate
urlpatterns = [
    path("health/", health_check),
    path("Rushal/", say_hello),
    path("chat/", chat),
    path("embed/", SimpleSave),
    path("talktoai/", TalkToAi),
    path("evaluation/generate/", evaluation_generate),
]