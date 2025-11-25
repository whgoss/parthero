from django.db import models
from models.organizations import Organization


class Musician(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Section(models.Model):
    name = models.CharField(max_length=255)
    instrument = models.CharField(max_length=255)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name}"


class MusicianSection(models.Model):
    musician = models.ForeignKey(Musician, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    principal = models.BooleanField(default=False)

    class Meta:
        unique_together = ("musician", "section")

    def __str__(self):
        return f"{self.musician} ({self.section})"
