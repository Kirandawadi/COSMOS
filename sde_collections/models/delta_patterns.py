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
        if self.match_pattern_type == self.MatchPatternTypeChoices.INDIVIDUAL_URL:
            regex_pattern = f"{escaped_match_pattern}$"
        elif self.match_pattern_type == self.MatchPatternTypeChoices.MULTI_URL_PATTERN:
            regex_pattern = escaped_match_pattern.replace(r"\*", ".*")  # allow * wildcards
        else:
            raise NotImplementedError

        # Filter both DeltaUrls and CuratedUrls
        matching_delta_urls = self.delta_urls.filter(url__regex=regex_pattern)
        matching_curated_urls = self.curated_urls.filter(url__regex=regex_pattern)

        return {
            "matching_delta_urls": matching_delta_urls,
            "matching_curated_urls": matching_curated_urls,
        }

    def _process_match_pattern(self) -> str:
        """
        Multi-Url patterns need a star at the beginning and at the end
        Individual Url Patterns need a star at the beginning
        """
        # we don't trust the bracketing stars from the system, so we remove any
        processed_pattern = self.match_pattern.strip().strip("*").strip()
        if not processed_pattern.startswith("http"):
            # if it doesn't begin with http, it must need a star at the beginning
            processed_pattern = f"*{processed_pattern}"
        if self.match_pattern_type == BaseMatchPattern.MatchPatternTypeChoices.MULTI_URL_PATTERN:
            # all multi urls should have a star at the end, but individuals should not
            processed_pattern = f"{processed_pattern}*"
        return processed_pattern

    def apply(self):
        raise NotImplementedError

    def unapply(self):
        raise NotImplementedError

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

    def apply(self) -> None:
        matched_urls = self.matched_urls()

        # Define a mapping of model attributes to their related URL fields
        url_mappings = {
            "delta_urls": matched_urls["matching_delta_urls"].values_list("id", flat=True),
            "curated_urls": matched_urls["matching_curated_urls"].values_list("id", flat=True),
        }

        for field_name, url_ids in url_mappings.items():
            through_model = getattr(self, field_name).through  # Access the through model dynamically
            bulk_data = [
                through_model(**{f"{field_name[:-1]}_id": url_id, "deltaexcludepattern_id": self.id})
                for url_id in url_ids
            ]
            through_model.objects.bulk_create(bulk_data)

    def unapply(self) -> None:
        # this is the new, suggested code
        # self.delta_urls.clear()
        # self.curated_urls.clear()
        # this is the old code
        # need to study later and decide which is better
        "Unapplies automatically by deleting include pattern through objects in a cascade"
        return

    class Meta:
        verbose_name = "Exclude Pattern"
        verbose_name_plural = "Exclude Patterns"
        unique_together = ("collection", "match_pattern")


class DeltaIncludePattern(BaseMatchPattern):
    def apply(self) -> None:
        matched_urls = self.matched_urls()

        # Define a mapping of model attributes to their related URL fields
        url_mappings = {
            "delta_urls": matched_urls["matching_delta_urls"].values_list("id", flat=True),
            "curated_urls": matched_urls["matching_curated_urls"].values_list("id", flat=True),
        }

        for field_name, url_ids in url_mappings.items():
            through_model = getattr(self, field_name).through  # Access the through model dynamically
            bulk_data = [
                through_model(**{f"{field_name[:-1]}_id": url_id, "deltaincludepattern_id": self.id})
                for url_id in url_ids
            ]
            through_model.objects.bulk_create(bulk_data)

    def unapply(self) -> None:
        "Unapplies automatically by deleting includepattern through objects in a cascade"
        return

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
        matched = self.matched_urls()  # Now returns separate QuerySets for delta and curated URLs
        updated_urls = []
        ResolvedTitle = apps.get_model("sde_collections", "ResolvedTitle")
        ResolvedTitleError = apps.get_model("sde_collections", "ResolvedTitleError")

        # Process both DeltaUrls and CuratedUrls
        for url_obj in matched["matching_delta_urls"] | matched["matching_curated_urls"]:
            context = {
                "url": url_obj.url,
                "title": url_obj.scraped_title,
                "collection": self.collection.name,
            }
            try:
                generated_title = resolve_title(self.title_pattern, context)

                # Remove any existing resolved title for this URL
                ResolvedTitle.objects.filter(url=url_obj).delete()

                # Create new resolved title entry
                ResolvedTitle.objects.create(title_pattern=self, url=url_obj, resolved_title=generated_title)

                # Update generated title and save it to the DeltaUrl or CuratedUrl
                url_obj.generated_title = generated_title
                url_obj.save()
                updated_urls.append(url_obj)

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

        # Associate pattern with both delta and curated URLs
        for field_name, urls in {
            "delta_urls": matched["matching_delta_urls"],
            "curated_urls": matched["matching_curated_urls"],
        }.items():
            through_model = getattr(self, field_name).through
            pattern_url_associations = [
                through_model(deltatitlepattern_id=self.id, **{f"{field_name[:-1]}_id": url.id}) for url in urls
            ]
            through_model.objects.bulk_create(pattern_url_associations, ignore_conflicts=True)

    def unapply(self) -> None:
        """Clears generated titles and dissociates URLs from the pattern."""
        for url_obj in self.delta_urls.all() | self.curated_urls.all():
            url_obj.generated_title = ""
            url_obj.save()
        self.delta_urls.clear()
        self.curated_urls.clear()

    def delete(self, *args, **kwargs):
        """Ensures unapply is called before deletion."""
        self.unapply()
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name = "Title Pattern"
        verbose_name_plural = "Title Patterns"
        unique_together = ("collection", "match_pattern")


class DeltaDocumentTypePattern(BaseMatchPattern):
    document_type = models.IntegerField(choices=DocumentTypes.choices)

    def apply(self) -> None:
        matched = self.matched_urls()
        # Apply the document type to both DeltaUrls and CuratedUrls
        for field_name, urls in {
            "delta_urls": matched["matching_delta_urls"],
            "curated_urls": matched["matching_curated_urls"],
        }.items():
            urls.update(document_type=self.document_type)  # Update the document type for matched URLs
            # Bulk create associations in the through table
            through_model = getattr(self, field_name).through
            pattern_url_associations = [
                through_model(**{f"{field_name[:-1]}_id": url.id, "documenttypepattern_id": self.id}) for url in urls
            ]
            through_model.objects.bulk_create(pattern_url_associations, ignore_conflicts=True)

    def unapply(self) -> None:
        """Clear document type from associated delta and curated URLs."""
        for url_obj in self.delta_urls.all() | self.curated_urls.all():
            url_obj.document_type = None
            url_obj.save()
        self.delta_urls.clear()
        self.curated_urls.clear()

    class Meta:
        verbose_name = "Document Type Pattern"
        verbose_name_plural = "Document Type Patterns"
        unique_together = ("collection", "match_pattern")


class DeltaDivisionPattern(BaseMatchPattern):
    division = models.IntegerField(choices=Divisions.choices)

    def apply(self) -> None:
        matched = self.matched_urls()
        # Apply the division to both DeltaUrls and CuratedUrls
        for field_name, urls in {
            "delta_urls": matched["matching_delta_urls"],
            "curated_urls": matched["matching_curated_urls"],
        }.items():
            urls.update(division=self.division)  # Update the division for matched URLs
            # Bulk create associations in the through table
            through_model = getattr(self, field_name).through
            pattern_url_associations = [
                through_model(**{f"{field_name[:-1]}_id": url.id, "divisionpattern_id": self.id}) for url in urls
            ]
            through_model.objects.bulk_create(pattern_url_associations, ignore_conflicts=True)

    def unapply(self) -> None:
        """Clear division from associated delta and curated URLs."""
        for url_obj in self.delta_urls.all() | self.curated_urls.all():
            url_obj.division = None
            url_obj.save()
        self.delta_urls.clear()
        self.curated_urls.clear()

    class Meta:
        verbose_name = "Division Pattern"
        verbose_name_plural = "Division Patterns"
        unique_together = ("collection", "match_pattern")


# @receiver(post_save, sender=DeltaTitlePattern)
# def post_save_handler(sender, instance, created, **kwargs):
#     if created:
#         transaction.on_commit(lambda: resolve_title_pattern.delay(instance.pk))
