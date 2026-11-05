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

        NETWORK_ENGINEER = "Network Engineer", "Network Engineer"
        ENGINEERING_MANAGER = "Engineering Manager", "Engineering Manager"
        PENETRATION_TESTER_OR_ETHICAL_HACKER = (
            "Penetration Tester / Ethical Hacker",
            "Penetration Tester / Ethical Hacker"
        )
        SCRUM_MASTER_OR_AGILE_COACH = (
            "Scrum Master / Agile Coach",
            "Scrum Master / Agile Coach"
        )       
        SOLUTIONS_ARCHITECT = "Solutions Architect", "Solutions Architect"
        PLATFORM_ENGINEER = "Platform Engineer", "Platform Engineer"
        DATABASE_ADMINISTRATOR = "Database Administrator (DBA)", "Database Administrator (DBA)"
        BLOCKCHAIN_SMART_CONTRACT_DEVELOPER = (
            "Blockchain / Smart Contract Developer",
            "Blockchain / Smart Contract Developer"
        )
        MLOPS_ENGINEER = "MLOps Engineer", "MLOps Engineer"
        COMPUTER_VISION_ENGINEER = "Computer Vision Engineer", "Computer Vision Engineer"
        GAME_DEVELOPER = "Game Developer", "Game Developer"
        DATA_SCIENTIST = "Data Scientist", "Data Scientist"
        SALES_SOLUTIONS_ENGINEER = "Sales / Solutions Engineer", "Sales / Solutions Engineer"
        TECHNICAL_PRODUCT_MANAGER = "Technical Product Manager", "Technical Product Manager"
        SECURITY_OPERATIONS_SOC_ANALYST = (
            "Security Operations (SOC) Analyst",
            "Security Operations (SOC) Analyst"
        )
        UX_UI_DESIGNER = "UX/UI Designer", "UX/UI Designer"
        BUSINESS_INTELLIGENCE_BI_ANALYST = (
            "Business Intelligence (BI) Analyst",
            "Business Intelligence (BI) Analyst"
        )
        DATA_ENGINEER = "Data Engineer", "Data Engineer"
        NLP_ENGINEER = "NLP Engineer", "NLP Engineer"
        TEST_AUTOMATION_ENGINEER = "Test Automation Engineer", "Test Automation Engineer"
        CLOUD_INFRASTRUCTURE_ENGINEER = (
            "Cloud Infrastructure Engineer",
            "Cloud Infrastructure Engineer"
        )
        FRAUD_ANALYST = "Fraud Analyst", "Fraud Analyst"
        SITE_RELIABILITY_ENGINEER = (
            "Site Reliability Engineer (SRE)",
            "Site Reliability Engineer (SRE)"
        )
        DEVOPS_ENGINEER = "DevOps Engineer", "DevOps Engineer"
        MOBILE_APP_DEVELOPER = (
            "Mobile App Developer (iOS/Android)",
            "Mobile App Developer (iOS/Android)"
        )
        QA_ENGINEER = "QA Engineer", "QA Engineer"
        ROBOTICS_ENGINEER = "Robotics Engineer", "Robotics Engineer"
        FRONTEND_DEVELOPER = "Frontend Developer", "Frontend Developer"
        FULL_STACK_DEVELOPER = "Full Stack Developer", "Full Stack Developer"
        AI_ML_ENGINEER = "AI/ML Engineer", "AI/ML Engineer"
        BACKEND_DEVELOPER = "Backend Developer", "Backend Developer"
        IOT_SOLUTIONS_ENGINEER = "IoT Solutions Engineer", "IoT Solutions Engineer"
        APPLICATION_SECURITY_APPSEC_ENGINEER = (
            "Application Security (AppSec) Engineer",
            "Application Security (AppSec) Engineer"
        )
        DATA_ANALYST = "Data Analyst", "Data Analyst"
        EMBEDDED_SYSTEMS_DEVELOPER = "Embedded Systems Developer", "Embedded Systems Developer"
        SYSTEMS_ANALYST = "Systems Analyst", "Systems Analyst"
        QA_AUTOMATION_ENGINEER = "QA Automation Engineer", "QA Automation Engineer"
        SDET_SOFTWARE_DEVELOPMENT_ENGINEER_IN_TEST ="SDET (Software Development Engineer in Test)","SDET (Software Development Engineer in Test)"

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