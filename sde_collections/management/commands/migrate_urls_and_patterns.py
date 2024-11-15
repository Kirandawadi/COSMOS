from django.apps import apps
from django.core.management.base import BaseCommand
from django.db.models import Count

from sde_collections.models.candidate_url import CandidateURL
from sde_collections.models.collection import Collection
from sde_collections.models.collection_choice_fields import WorkflowStatusChoices
from sde_collections.models.delta_patterns import (
    DeltaDivisionPattern,
    DeltaDocumentTypePattern,
    DeltaExcludePattern,
    DeltaIncludePattern,
    DeltaTitlePattern,
)
from sde_collections.models.delta_url import CuratedUrl, DeltaUrl
from sde_collections.models.pattern import (
    DivisionPattern,
    DocumentTypePattern,
    ExcludePattern,
    IncludePattern,
    TitlePattern,
)

STATUSES_TO_MIGRATE = [
    WorkflowStatusChoices.CURATED,
    WorkflowStatusChoices.QUALITY_FIXED,
    WorkflowStatusChoices.SECRET_DEPLOYMENT_STARTED,
    WorkflowStatusChoices.SECRET_DEPLOYMENT_FAILED,
    WorkflowStatusChoices.READY_FOR_LRM_QUALITY_CHECK,
    WorkflowStatusChoices.READY_FOR_FINAL_QUALITY_CHECK,
    WorkflowStatusChoices.QUALITY_CHECK_FAILED,
    WorkflowStatusChoices.QUALITY_CHECK_MINOR,
    WorkflowStatusChoices.QUALITY_CHECK_PERFECT,
    WorkflowStatusChoices.PROD_PERFECT,
    WorkflowStatusChoices.PROD_MINOR,
    WorkflowStatusChoices.PROD_MAJOR,
]


class Command(BaseCommand):
    help = """Migrate CandidateURLs to DeltaUrl, apply the matching patterns,
            and then promote to CuratedUrl based on collection workflow status"""

    def handle(self, *args, **kwargs):
        # Clear all Delta instances
        CuratedUrl.objects.all().delete()
        DeltaUrl.objects.all().delete()
        DeltaExcludePattern.objects.all().delete()
        DeltaIncludePattern.objects.all().delete()
        DeltaTitlePattern.objects.all().delete()
        DeltaDocumentTypePattern.objects.all().delete()
        DeltaDivisionPattern.objects.all().delete()

        # Get collections with Candidate URLs
        all_collections_with_urls = Collection.objects.annotate(url_count=Count("candidate_urls")).filter(
            url_count__gt=0
        )

        # Migrate all CandidateURLs to DeltaUrl using bulk creation
        for collection in all_collections_with_urls:
            delta_urls = [
                DeltaUrl(
                    collection=candidate_url.collection,
                    url=candidate_url.url,
                    scraped_title=candidate_url.scraped_title,
                    generated_title=candidate_url.generated_title,
                    visited=candidate_url.visited,
                    document_type=candidate_url.document_type,
                    division=candidate_url.division,
                    delete=False,
                )
                for candidate_url in CandidateURL.objects.filter(collection=collection)
            ]
            DeltaUrl.objects.bulk_create(delta_urls)

        # Migrate Patterns
        self.migrate_patterns(ExcludePattern)
        self.migrate_patterns(IncludePattern)
        self.migrate_patterns(TitlePattern)
        self.migrate_patterns(DocumentTypePattern)
        self.migrate_patterns(DivisionPattern)
        self.stdout.write(self.style.SUCCESS("Patterns migration complete."))

        # Promote DeltaUrls to CuratedUrl for collections with relevant statuses
        all_curated_collections_with_urls = all_collections_with_urls.filter(workflow_status__in=STATUSES_TO_MIGRATE)
        self.stdout.write(
            f"""Migrating URLs for {all_curated_collections_with_urls.count()} collections
            with CURATED or higher status..."""
        )
        for collection in all_curated_collections_with_urls:
            collection.promote_to_curated()

    def migrate_patterns(self, non_delta_model):
        """Migrate patterns from a non-delta model to the corresponding delta model."""
        # Determine the delta model name and fetch the model class
        delta_model_name = "Delta" + non_delta_model.__name__
        delta_model = apps.get_model(non_delta_model._meta.app_label, delta_model_name)

        self.stdout.write(f"Migrating patterns from {non_delta_model.__name__} to {delta_model_name}...")

        # Get all field names from both models except 'id' (primary key)
        non_delta_fields = {field.name for field in non_delta_model._meta.fields if field.name != "id"}
        delta_fields = {field.name for field in delta_model._meta.fields if field.name != "id"}

        # Find shared fields
        shared_fields = non_delta_fields.intersection(delta_fields)

        for pattern in non_delta_model.objects.all():
            # Build the dictionary of shared fields to copy
            delta_fields_data = {field: getattr(pattern, field) for field in shared_fields}

            # Create an instance of the delta model and save it to call the custom save() method
            delta_instance = delta_model(**delta_fields_data)
            delta_instance.save()  # Explicitly call save() to trigger custom logic

        self.stdout.write(f"Migration completed for {non_delta_model.__name__} to {delta_model_name}.")
