import re

from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import models

from ..utils.title_resolver import (
    is_valid_fstring,
    is_valid_xpath,
    parse_title,
    resolve_title,
)
from .collection_choice_fields import Divisions, DocumentTypes


class BaseMatchPattern(models.Model):
    class MatchPatternTypeChoices(models.IntegerChoices):
        INDIVIDUAL_URL = 1, "Individual URL Pattern"
        MULTI_URL_PATTERN = 2, "Multi-URL Pattern"

    collection = models.ForeignKey(
        "Collection",
        on_delete=models.CASCADE,
        related_name="%(class)s",
        related_query_name="%(class)ss",
    )
    match_pattern = models.CharField(
        "Pattern",
        help_text="This pattern is compared against the URL of all the documents in the collection "
        "and matching documents will be returned",
    )
    match_pattern_type = models.IntegerField(choices=MatchPatternTypeChoices.choices, default=1)
    delta_urls = models.ManyToManyField(
        "DeltaUrl",
        related_name="%(class)s_delta_urls",
    )
    curated_urls = models.ManyToManyField(
        "CuratedUrl",
        related_name="%(class)s_curated_urls",
    )

    def matched_urls(self):
        """Find all the urls matching the pattern."""
        escaped_match_pattern = re.escape(self.match_pattern)
        regex_pattern = (
            f"{escaped_match_pattern}$"
            if self.match_pattern_type == self.MatchPatternTypeChoices.INDIVIDUAL_URL
            else escaped_match_pattern.replace(r"\*", ".*")
        )
        return {
            "matching_delta_urls": self.delta_urls.filter(url__regex=regex_pattern),
            "matching_curated_urls": self.curated_urls.filter(url__regex=regex_pattern),
        }

    def generate_delta_url(self, curated_url, fields_to_copy=None):
        """
        Generates or updates a DeltaUrl based on a CuratedUrl.
        Only specified fields are copied if fields_to_copy is provided.
        """
        # Import DeltaUrl dynamically to avoid circular import issues
        DeltaUrl = apps.get_model("sde_collections", "DeltaUrl")

        delta_url, created = DeltaUrl.objects.get_or_create(
            collection=self.collection,
            url=curated_url.url,
            defaults={field: getattr(curated_url, field) for field in (fields_to_copy or [])},
        )
        if not created and fields_to_copy:
            # Update only if certain fields are missing in DeltaUrl
            for field in fields_to_copy:
                if getattr(delta_url, field, None) in [None, ""]:
                    setattr(delta_url, field, getattr(curated_url, field))
            delta_url.save()

    def apply(self, fields_to_copy=None, update_fields=None):
        matched_urls = self.matched_urls()

        # Iterate over matched CuratedUrls to create or update DeltaUrls as needed
        for curated_url in matched_urls["matching_curated_urls"]:
            self.generate_delta_url(curated_url, fields_to_copy)

        # Apply any updates to DeltaUrls based on update_fields
        if update_fields:
            for field, value in update_fields.items():
                matched_urls["matching_delta_urls"].update(**{field: value})

        # Populate through tables for DeltaUrl and CuratedUrl relationships
        for field_name, url_ids in {
            "delta_urls": matched_urls["matching_delta_urls"].values_list("id", flat=True),
            "curated_urls": matched_urls["matching_curated_urls"].values_list("id", flat=True),
        }.items():
            through_model = getattr(self, field_name).through
            bulk_data = [
                through_model(**{f"{field_name[:-1]}_id": url_id, f"{self.__class__.__name__.lower()}_id": self.id})
                for url_id in url_ids
            ]
            through_model.objects.bulk_create(bulk_data, ignore_conflicts=True)

    def unapply(self):
        """Default unapply behavior."""
        self.delta_urls.clear()
        self.curated_urls.clear()

    def save(self, *args, **kwargs):
        """Save the pattern and apply it."""
        super().save(*args, **kwargs)
        self.apply()

    def delete(self, *args, **kwargs):
        """Delete the pattern and unapply it."""
        self.unapply()
        super().delete(*args, **kwargs)

    class Meta:
        abstract = True
        ordering = ["match_pattern"]
        unique_together = ("collection", "match_pattern")

    def __str__(self):
        return self.match_pattern


class DeltaExcludePattern(BaseMatchPattern):
    reason = models.TextField("Reason for excluding", default="", blank=True)

    # No need to override `apply`—we use the base class logic as-is.
    # This pattern's functionality is handled by the `excluded` annotation in the manager.

    class Meta:
        verbose_name = "Exclude Pattern"
        verbose_name_plural = "Exclude Patterns"
        unique_together = ("collection", "match_pattern")


class DeltaIncludePattern(BaseMatchPattern):
    # No additional logic needed for `apply`—using base class functionality.

    class Meta:
        verbose_name = "Include Pattern"
        verbose_name_plural = "Include Patterns"
        unique_together = ("collection", "match_pattern")


def validate_title_pattern(title_pattern_string):
    parsed_title = parse_title(title_pattern_string)

    for element in parsed_title:
        element_type, element_value = element

        if element_type == "xpath":
            if not is_valid_xpath(element_value):
                raise ValidationError(f"'xpath:{element_value}' is not a valid xpath.")  # noqa: E231
        elif element_type == "brace":
            try:
                is_valid_fstring(element_value)
            except ValueError as e:
                raise ValidationError(str(e))


class DeltaTitlePattern(BaseMatchPattern):
    title_pattern = models.CharField(
        "Title Pattern",
        help_text="This is the pattern for the new title. You can either write an exact replacement string"
        " (no quotes required) or you can write sinequa-valid code",
        validators=[validate_title_pattern],
    )

    def apply(self) -> None:
        # Use `fields_to_copy` to copy `scraped_title` for any matching curated URLs.
        super().apply(fields_to_copy=["scraped_title"])

        matched = self.matched_urls()  # Separate QuerySets for delta and curated URLs
        ResolvedTitle = apps.get_model("sde_collections", "ResolvedTitle")
        ResolvedTitleError = apps.get_model("sde_collections", "ResolvedTitleError")

        for url_obj in matched["matching_delta_urls"] | matched["matching_curated_urls"]:
            context = {
                "url": url_obj.url,
                "title": url_obj.scraped_title,
                "collection": self.collection.name,
            }
            try:
                generated_title = resolve_title(self.title_pattern, context)

                # Remove existing resolved title entries for this URL
                ResolvedTitle.objects.filter(url=url_obj).delete()

                # Create a new resolved title entry
                ResolvedTitle.objects.create(title_pattern=self, url=url_obj, resolved_title=generated_title)

                # Update generated title and save it to DeltaUrl or CuratedUrl
                url_obj.generated_title = generated_title
                url_obj.save()

            except (ValueError, ValidationError) as e:
                message = str(e)
                resolved_title_error = ResolvedTitleError.objects.create(
                    title_pattern=self, url=url_obj, error_string=message
                )

                # Extract status code if present in the error message
                status_code = re.search(r"Status code: (\d+)", message)
                if status_code:
                    resolved_title_error.http_status_code = int(status_code.group(1))

                resolved_title_error.save()

    def unapply(self) -> None:
        """Clears generated titles and dissociates URLs from the pattern."""
        for url_obj in self.delta_urls.all():
            url_obj.generated_title = ""
            url_obj.save()
        self.delta_urls.clear()
        self.curated_urls.clear()

    class Meta:
        verbose_name = "Title Pattern"
        verbose_name_plural = "Title Patterns"
        unique_together = ("collection", "match_pattern")


class DeltaDocumentTypePattern(BaseMatchPattern):
    document_type = models.IntegerField(choices=DocumentTypes.choices)

    # We use `update_fields` in the base apply method to set `document_type`.
    def apply(self) -> None:
        super().apply(update_fields={"document_type": self.document_type})

    def unapply(self) -> None:
        """Clear document type from associated delta and curated URLs."""
        self.delta_urls.update(document_type=None)
        self.delta_urls.clear()
        self.curated_urls.clear()

    class Meta:
        verbose_name = "Document Type Pattern"
        verbose_name_plural = "Document Type Patterns"
        unique_together = ("collection", "match_pattern")


class DeltaDivisionPattern(BaseMatchPattern):
    division = models.IntegerField(choices=Divisions.choices)

    # We use `update_fields` in the base apply method to set `division`.
    def apply(self) -> None:
        super().apply(update_fields={"division": self.division})

    def unapply(self) -> None:
        """Clear division from associated delta and curated URLs."""
        # TODO: need to double check this logic for complicated cases
        self.delta_urls.update(division=None)

    class Meta:
        verbose_name = "Division Pattern"
        verbose_name_plural = "Division Patterns"
        unique_together = ("collection", "match_pattern")


# @receiver(post_save, sender=DeltaTitlePattern)
# def post_save_handler(sender, instance, created, **kwargs):
#     if created:
#         transaction.on_commit(lambda: resolve_title_pattern.delay(instance.pk))
