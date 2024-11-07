import re

from django.core.exceptions import ValidationError
# models
from django.db import models

from .collection_choice_fields import Divisions, DocumentTypes


class BaseUrl(models.Model):
    """Abstract base class for Urls with shared fields and methods."""

    collection = models.ForeignKey("Collection", on_delete=models.CASCADE, related_name="%(class)s_urls")
    url = models.CharField("Url", unique=True)
    scraped_title = models.CharField("Scraped Title", blank=True, default="")
    generated_title = models.CharField("Generated Title", blank=True, default="")
    visited = models.BooleanField(default=False)
    document_type = models.IntegerField(choices=DocumentTypes.choices, null=True)
    division = models.IntegerField(choices=Divisions.choices, null=True)

    class Meta:
        abstract = True
        ordering = ["url"]

    def __str__(self):
        return self.url


class DeltaUrl(BaseUrl):
    """Urls that are being curated. Only deltas are stored in this model."""

    delete = models.BooleanField(default=False)


class CuratedUrl(BaseUrl):
    """Urls that are curated and ready for production"""

    pass
