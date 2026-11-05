import json
from urllib.parse import urlencode

from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from authlib.integrations.django_client import OAuth

from rest_framework.decorators import (
    api_view,
    permission_classes,
    parser_classes,
)
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import UserProfile


User = get_user_model()


# =========================================================
# GOOGLE OAUTH CONFIGURATION
# =========================================================

oauth = OAuth()

oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile',
    },
)


# =========================================================
# TEST ENDPOINT
# =========================================================

@api_view(['GET'])
def test_account(request):
    return Response({
        'message': 'Accounts API is working'
    })


# =========================================================
# CURRENT AUTHENTICATED USER
# =========================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):

    if request.user.profile_picture:
        profile_picture = request.build_absolute_uri(
            request.user.profile_picture.url
        )
    else:
        profile_picture = request.user.profile_picture_url

    return Response({
        'email': request.user.email,
        'first_name': request.user.first_name,
        'profile_picture': profile_picture,
    })


# =========================================================
# GOOGLE LOGIN
# =========================================================

def google_login(request):

    redirect_uri = settings.GOOGLE_REDIRECT_URI

    return oauth.google.authorize_redirect(
        request,
        redirect_uri
    )


# =========================================================
# GOOGLE CALLBACK
# =========================================================

@api_view(['GET'])
def google_callback(request):

    token = oauth.google.authorize_access_token(request)

    user_info = token.get('userinfo')

    google_id = user_info.get('sub')
    email = user_info.get('email')
    name = user_info.get('name', '')
    picture = user_info.get('picture')

    user, created = User.objects.get_or_create(
        google_id=google_id,
        defaults={
            'email': email,
            'first_name': name,
            'profile_picture_url': picture,
        }
    )

    # Update Google profile picture for existing users too
    if not created:
        user.profile_picture_url = picture
        user.save(update_fields=['profile_picture_url'])

    if created:
        user.set_unusable_password()
        user.save(update_fields=['password'])

    refresh = RefreshToken.for_user(user)

    # profile_picture_url is already a complete URL
    profile_picture = user.profile_picture_url

    user_data = {
        'id': user.id,
        'email': user.email,
        'first_name': user.first_name,
        'profile_picture': profile_picture,
    }

    callback_url = getattr(
        settings,
        'FRONTEND_OAUTH_CALLBACK_URL',
        'http://localhost:5173/oauth/callback',
    )

    callback_data = urlencode({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': json.dumps(user_data),
    })

    return HttpResponseRedirect(
        f'{callback_url}#{callback_data}'
    )

# =========================================================
# TEST CONNECT
# =========================================================

@csrf_exempt
def test_connect(request):

    if request.method == "POST":

        try:
            data = json.loads(request.body)

            message = data.get("message", "")

            print(
                "Message received from frontend:",
                message
            )

            return JsonResponse({
                "success": True,
                "message": f"Backend received: {message}"
            })

        except Exception:

            return JsonResponse({
                "success": False,
                "message": "Invalid request payload."
            }, status=400)

    return JsonResponse({
        "success": False,
        "message": "Only POST requests are allowed."
    }, status=405)


# =========================================================
# REGISTER ACCOUNT
# =========================================================

@api_view(['POST'])
def register_account(request):

    name = (
        request.data.get('name')
        or request.data.get('first_name')
        or ''
    )

    email = request.data.get('email')
    password = request.data.get('password')

    # Check required fields
    if not email or not password:

        return Response({
            'success': False,
            'message': 'Email and password are required.'
        }, status=400)

    # Check email
    if User.objects.filter(email=email).exists():

        return Response({
            'success': False,
            'message': 'Email already exists.'
        }, status=400)

    # Optional profile data
    profile_data = request.data.get('profile') or {}

    # Generate unique username
    username_base = email.split('@', 1)[0][:150] or 'user'

    username = username_base
    suffix = 1

    while User.objects.filter(username=username).exists():

        suffix_text = str(suffix)

        username = (
            f'{username_base[:150 - len(suffix_text)]}'
            f'{suffix_text}'
        )

        suffix += 1

    # Create user
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=name
    )

    # Create profile
    UserProfile.objects.create(
        user=user,
        primary_role=profile_data.get(
            'primary_role',
            ''
        ),
        target_roles=profile_data.get(
            'target_roles',
            []
        ),
        experience_level=profile_data.get(
            'experience_level',
            ''
        ),
        education=profile_data.get(
            'education',
            []
        ),
        skills=profile_data.get(
            'skills',
            []
        ),
        projects=profile_data.get(
            'projects',
            []
        ),
        experience=profile_data.get(
            'experience',
            []
        ),
        certifications=profile_data.get(
            'certifications',
            []
        )
    )

    return Response({

        'success': True,

        'message': 'Account created successfully.',

        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
        },

        'profile': {
            'primary_role': profile_data.get(
                'primary_role',
                ''
            ),
            'target_roles': profile_data.get(
                'target_roles',
                []
            ),
            'experience_level': profile_data.get(
                'experience_level',
                ''
            ),
            'education': profile_data.get(
                'education',
                []
            ),
            'skills': profile_data.get(
                'skills',
                []
            ),
            'projects': profile_data.get(
                'projects',
                []
            ),
            'experience': profile_data.get(
                'experience',
                []
            ),
            'certifications': profile_data.get(
                'certifications',
                []
            )
        }

    }, status=201)


# =========================================================
# LOGIN ACCOUNT
# =========================================================

@api_view(['POST'])
def login_account(request):

    email = request.data.get('email')
    password = request.data.get('password')

    try:
        user = User.objects.get(
            email=email
        )

    except User.DoesNotExist:

        return Response({
            'message': 'Invalid email or password'
        }, status=400)

    if not user.check_password(password):

        return Response({
            'message': 'Invalid email or password'
        }, status=400)

    refresh = RefreshToken.for_user(user)

    # Determine profile picture
    if user.profile_picture:
        profile_picture = request.build_absolute_uri(
            user.profile_picture.url
        )
    else:
        profile_picture = user.profile_picture_url

    return Response({

        'success': True,

        'message': 'Login successful',

        'user': {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'profile_picture': profile_picture,
        },

        'access': str(refresh.access_token),
        'refresh': str(refresh),
    })


# =========================================================
# GET PROFILE
# =========================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile(request):

    profile, created = UserProfile.objects.get_or_create(
        user=request.user
    )

    # Determine profile picture
    if request.user.profile_picture:

        profile_picture = request.build_absolute_uri(
            request.user.profile_picture.url
        )

    else:

        profile_picture = request.user.profile_picture_url

    return Response({

        'success': True,

        'user': {
            'username': request.user.username,
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'profile_picture': profile_picture,
            'profile_picture_url': request.user.profile_picture_url,
        },

        'profile': {
            'primary_role': profile.primary_role,
            'target_roles': profile.target_roles,
            'experience_level': profile.experience_level,
            'education': profile.education,
            'skills': profile.skills,
            'projects': profile.projects,
            'experience': profile.experience,
            'certifications': profile.certifications,
        }
    })


# =========================================================
# UPDATE PROFILE
# =========================================================

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def update_profile(request):

    user = request.user

    profile, created = UserProfile.objects.get_or_create(
        user=user
    )

    # =====================================================
    # USER MODEL FIELDS
    # =====================================================

    if 'username' in request.data:
        user.username = request.data['username']

    if 'email' in request.data:
        user.email = request.data['email']

    if 'first_name' in request.data:
        user.first_name = request.data['first_name']

    if 'last_name' in request.data:
        user.last_name = request.data['last_name']

    # =====================================================
    # UPLOADED IMAGE
    # =====================================================

    if 'profile_picture' in request.FILES:
        user.profile_picture = request.FILES['profile_picture']
        user.profile_picture_url = ''

    # =====================================================
    # IMAGE URL
    # =====================================================

    if 'profile_picture_url' in request.data:
        user.profile_picture_url = request.data['profile_picture_url']

        if user.profile_picture_url:
            user.profile_picture = None

    user.save()

    # =====================================================
    # USER PROFILE FIELDS
    # =====================================================

    if 'primary_role' in request.data:

        profile.primary_role = request.data[
            'primary_role'
        ]

    if 'target_roles' in request.data:

        profile.target_roles = json.loads(
            request.data['target_roles']
        )

    if 'experience_level' in request.data:

        profile.experience_level = request.data[
            'experience_level'
        ]

    if 'education' in request.data:

        profile.education = json.loads(
            request.data['education']
        )

    if 'skills' in request.data:

        profile.skills = json.loads(
            request.data['skills']
        )

    if 'projects' in request.data:

        profile.projects = json.loads(
            request.data['projects']
        )

    if 'experience' in request.data:

        profile.experience = json.loads(
            request.data['experience']
        )

    if 'certifications' in request.data:

        profile.certifications = json.loads(
            request.data['certifications']
        )

    profile.save()

    # =====================================================
    # DETERMINE PROFILE PICTURE
    # =====================================================

    if user.profile_picture:

        profile_picture = request.build_absolute_uri(
            user.profile_picture.url
        )

    else:

        profile_picture = user.profile_picture_url

    # =====================================================
    # RESPONSE
    # =====================================================

    return Response({

        'success': True,

        'message': 'Profile updated successfully.',

        'user': {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'profile_picture': profile_picture,
            'profile_picture_url': request.user.profile_picture_url,
        },

        'profile': {
            'primary_role': profile.primary_role,
            'target_roles': profile.target_roles,
            'experience_level': profile.experience_level,
            'education': profile.education,
            'skills': profile.skills,
            'projects': profile.projects,
            'experience': profile.experience,
            'certifications': profile.certifications,
        }
    })