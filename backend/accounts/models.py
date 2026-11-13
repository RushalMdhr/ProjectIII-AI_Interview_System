from django.contrib.auth.models import AbstractUser
from django.db import models
from pgvector.django import VectorField
from django.contrib.postgres.fields import ArrayField

class User(AbstractUser):

    email = models.EmailField(unique=True)
    google_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True
    )
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        blank=True,
        null=True
    )

    profile_picture_url = models.URLField(
        blank=True,
        null=True
    )

    highest_score = models.FloatField(null=True, blank=True)
    highest_introduction_score = models.FloatField(null=True, blank=True)
    highest_experience_score = models.FloatField(null=True, blank=True)
    highest_behavioral_score = models.FloatField(null=True, blank=True)
    highest_situational_score = models.FloatField(null=True, blank=True)
    highest_technical_score = models.FloatField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email


class UserProfile(models.Model):

    class ExperienceLevel(models.TextChoices):
        NONE = "none", "None"
        INTERN = "intern", "Intern"
        JUNIOR = "junior", "Junior"
        MID_LEVEL = "mid_level", "Mid-level"
        SENIOR = "senior", "Senior"

    class Role(models.TextChoices):

        BIZOPS_STRATEGY = "BizOps & Strategy", "BizOps & Strategy"
        COMMON = "common", "common"
        DATA_ANALYST = "Data Analyst", "Data Analyst"
        DATA_ENGINEER = "Data Engineer", "Data Engineer"
        DATA_SCIENTIST = "Data Scientist", "Data Scientist"
        ENGINEERING_MANAGER = "Engineering Manager", "Engineering Manager"
        INVESTMENT_BANKING = "Investment Banking", "Investment Banking"
        MACHINE_LEARNING_ENGINEER = (
            "Machine Learning Engineer",
            "Machine Learning Engineer"
        )
        PRODUCT_MANAGER = "Product Manager", "Product Manager"
        SOFTWARE_ENGINEER = "Software Engineer", "Software Engineer"
        TECHNICAL_PROGRAM_MANAGER = (
            "Technical Program Manager",
            "Technical Program Manager"
        )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
        )

    # Career Information



    target_roles = ArrayField(
        models.CharField(
            max_length=150,
            choices=Role.choices
        ),
        default=list,
        blank=True
    )

    primary_role = models.CharField(
        max_length=150,
        choices=Role.choices,
        blank=True
    )

    experience_level = models.CharField(
        max_length=20,
        choices=ExperienceLevel.choices,
        blank=True
    )

    # Education

    education = models.JSONField(
        default=list,
        blank=True
    )

    # Example:
    # [
    #     {
    #         "degree": "Bachelor of Computer Engineering",
    #         "institution": "XYZ University",
    #         "field": "Computer Engineering",
    #         "start_year": 2022,
    #         "end_year": 2026
    #     }
    # ]

    #skills

    skills = models.JSONField(
        default=list,
        blank=True
    )

    # Example:
    # [
    #     {"name": "Python", "level": "Advanced"},
    #     {"name": "Django", "level": "Intermediate"},
    #     {"name": "React", "level": "Intermediate"},
    #     {"name": "PostgreSQL", "level": "Intermediate"},
    #     {"name": "Machine Learning", "level": "Beginner"}
    # ]

    # Projects
    projects = models.JSONField(
        default=list,
        blank=True
    )

    # Example:
    # [
    #     {
    #         "title": "AI Interview System",
    #         "description": "...",
    #         "technologies": ["Django", "React", "PostgreSQL"],
    #         "role": "Backend Developer"
    #     }
    # ]

    # Professional Experience


    experience = models.JSONField(
        default=list,
        blank=True
    )

    # Example:
    # [
    #     {
    #         "company": "ABC",
    #         "position": "Software Intern",
    #         "description": "...",
    #         "start_date": "2025-06-01",
    #         "end_date": "2025-08-30"
    #     }
    # ]

    certifications = models.JSONField(
        default=list,
        blank=True
    )

    # AI / Vector Search

    profile_embedding = VectorField(
        dimensions=768,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.user.email}'s Profile"