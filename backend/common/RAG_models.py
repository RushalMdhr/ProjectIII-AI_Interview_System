from django.db import models
from pgvector.django import VectorField, HnswIndex


class Document_Source(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class InterviewQuestions(models.Model):
    question = models.TextField()
    answer = models.TextField()
    role = models.CharField(max_length=255, db_index=True)
    experience = models.CharField(max_length=50, choices=[
        ('none', 'None'),
        ('intern', 'Intern'),
        ('junior', 'Junior'),
        ('mid_level', 'Mid-level'),
        ('senior', 'Senior'),
        ('any', 'Any')
    ],db_index=True)
    difficulty = models.CharField(max_length=50, choices=[
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard')
    ])
    keywords = models.JSONField(default=list)  # or ArrayField
    source = models.ForeignKey(Document_Source, on_delete=models.CASCADE, related_name='questions')

    categories = models.JSONField(default=list, blank=True)   # list[str]  → e.g. ["behavioral"]
    weights = models.JSONField(default=list, blank=True)   # list[dict] → [{"label": ..., "score": ...}]
    
    embedding = VectorField(dimensions=768, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            HnswIndex(
                name='interview_embedding_idx',
                fields=['embedding'],
                opclasses=['vector_cosine_ops'],
                m=16,
                ef_construction=64,
            ),
        ]

    def __str__(self):
        return self.question[:50]

