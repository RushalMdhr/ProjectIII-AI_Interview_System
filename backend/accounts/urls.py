from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView, TokenRefreshView,)
from .views import (
    confirm_password_reset,
    get_profile,
    google_login,
    google_callback,
    login_account,
    register_account,
    request_password_reset,
    test_account,
    me,
    update_profile,
)

urlpatterns = [
    path('test/', test_account),

    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', me, name='me'),
    path('google/login/', google_login, name='google_login'),
    path('google/callback/', google_callback, name='google_callback'),
    path('register/',register_account, name='register_account'),
    path('login/',login_account, name='login_account'),
    path('password-reset/', request_password_reset, name='password_reset'),
    path('password-reset/confirm/', confirm_password_reset, name='password_reset_confirm'),
    path('profile/', get_profile, name='user_profile'),
    path('profile/update/', update_profile, name='update_profile'),
]