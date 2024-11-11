import os
from urllib.parse import urlparse

from django.db import models

from .collection_choice_fields import Divisions, DocumentTypes
from .delta_patterns import DeltaExcludePattern, DeltaTitlePattern


class DeltaUrlQuerySet(models.QuerySet):
    def with_exclusion_status(self):
        return self.annotate(
            excluded=models.Exists(
                DeltaExcludePattern.delta_urls.through.objects.filter(deltaurl=models.OuterRef("pk"))
            )
        )


class CuratedUrlQuerySet(models.QuerySet):
    def with_exclusion_status(self):
        return self.annotate(
            excluded=models.Exists(
                DeltaExcludePattern.curated_urls.through.objects.filter(curatedurl=models.OuterRef("pk"))
            )
        )


class DeltaUrlManager(models.Manager):
    def get_queryset(self):
        return DeltaUrlQuerySet(self.model, using=self._db).with_exclusion_status()


class CuratedUrlManager(models.Manager):
    def get_queryset(self):
        return CuratedUrlQuerySet(self.model, using=self._db).with_exclusion_status()


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

    @property
    def fileext(self) -> str:
        # Parse the URL to get the path
        parsed_url = urlparse(self.url)
        path = parsed_url.path

        # Check for cases where the path ends with a slash or is empty, implying a directory or default file
        if path.endswith("/") or not path:
            return "html"

        # Extract the extension from the path
        extension = os.path.splitext(path)[1]

        # Default to .html if no extension is found
        if not extension:
            return "html"

        if extension.startswith("."):
            return extension[1:]
        return extension

    def splits(self) -> list[tuple[str, str]]:
        """Split the path into multiple collections."""
        parts = []
        part_string = ""
        for part in self.path.split("/"):
            if part:
                part_string += f"/{part}"
                parts.append((part_string, part))
        return parts

    @property
    def path(self) -> str:
        parsed = urlparse(self.url)
        path = f"{parsed.path}"
        if parsed.query:
            path += f"?{parsed.query}"
        return path

    def __str__(self):
        return self.url


class DumpUrl(BaseUrl):
    """Stores the raw dump from the server before deltas are calculated."""

    class Meta:
        verbose_name = "Dump Urls"
        verbose_name_plural = "Dump Urls"
        ordering = ["url"]


class DeltaUrl(BaseUrl):
    """Urls that are being curated. Only deltas are stored in this model."""

    objects = DeltaUrlManager()
    delete = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Delta Urls"
        verbose_name_plural = "Delta Urls"
        ordering = ["url"]


class CuratedUrl(BaseUrl):
    """Urls that are curated and ready for production"""

    objects = CuratedUrlManager()

    class Meta:
        verbose_name = "Curated Urls"
        verbose_name_plural = "Curated Urls"
        ordering = ["url"]


class DeltaResolvedTitleBase(models.Model):
    # TODO: need to understand this logic and whether we need to have thess match to CuratedUrls as well
    title_pattern = models.ForeignKey(DeltaTitlePattern, on_delete=models.CASCADE)
    delta_url = models.OneToOneField(DeltaUrl, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class DeltaResolvedTitle(DeltaResolvedTitleBase):
    resolved_title = models.CharField(blank=True, default="")

    class Meta:
        verbose_name = "Resolved Title"
        verbose_name_plural = "Resolved Titles"

    def save(self, *args, **kwargs):
        # Finds the linked delta URL and deletes DeltaResolvedTitleError objects linked to it
        DeltaResolvedTitleError.objects.filter(delta_url=self.delta_url).delete()
        super().save(*args, **kwargs)


class DeltaResolvedTitleError(DeltaResolvedTitleBase):
    error_string = models.TextField(null=False, blank=False)
    http_status_code = models.IntegerField(null=True, blank=True)
