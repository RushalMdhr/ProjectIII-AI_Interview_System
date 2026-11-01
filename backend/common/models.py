from django.db import models
from pgvector.django import VectorField
from .RAG_models import *

class SimpleTextEmbedding(models.Model):
    text = models.TextField()
    embedding = VectorField(
        dimensions=768,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text[:50]
