from django.db import models
from core.models.musicians import Section
from core.models.organizations import Organization


class Piece(models.Model):
    title = models.CharField(max_length=255)
    composer = models.CharField(max_length=255)
    arranger = models.CharField(max_length=255, blank=True, null=True)
    duration = models.DurationField(blank=True, null=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.title} by {self.composer}"


class Part(models.Model):
    piece = models.ForeignKey(Piece, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    file = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.piece.title} ({self.section})"
