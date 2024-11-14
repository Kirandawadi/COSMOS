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


class Command(BaseCommand):
    help = """Migrate CandidateURLs to DeltaUrl, apply the matching patterns,
            and then promoting to CuratedUrl based on collection workflow status"""

    def handle(self, *args, **kwargs):
        # all_collections = Collection.objects.all()
        all_collections_with_urls = Collection.objects.annotate(url_count=Count("candidate_urls")).filter(
            url_count__gt=0
        )

        # Migrate all CandidateURLs to DeltaUrl
        for collection in all_collections_with_urls:
            candidate_urls = CandidateURL.objects.filter(collection=collection)
            for candidate_url in candidate_urls:
                # Check if a DeltaUrl with the same URL already exists
                if not DeltaUrl.objects.filter(url=candidate_url.url).exists():
                    DeltaUrl.objects.create(
                        collection=candidate_url.collection,
                        url=candidate_url.url,
                        scraped_title=candidate_url.scraped_title,
                        generated_title=candidate_url.generated_title,
                        visited=candidate_url.visited,
                        document_type=candidate_url.document_type,
                        division=candidate_url.division,
                        delete=False,
                    )
            self.stdout.write(
                f"Migrated {candidate_urls.count()} URLs from collection '{collection.name}' to DeltaUrl."
            )
            # break

        # Migrate Patterns

        self.migrate_exclude_patterns()
        self.migrate_include_patterns()
        self.migrate_title_patterns()
        self.migrate_document_type_patterns()
        self.migrate_division_patterns()
        self.stdout.write(self.style.SUCCESS("Patterns migration complete."))

        # Migrate DeltaUrl for collections with CURATED or higher workflow status to CuratedUrl
        all_curated_collections_with_urls = all_collections_with_urls.filter(
            workflow_status__gte=WorkflowStatusChoices.CURATED
        )
        self.stdout.write(
            f"""Migrating URLs for {all_curated_collections_with_urls.count()} collections
            with CURATED or higher status..."""
        )

        for collection in all_curated_collections_with_urls:
            candidate_urls = DeltaUrl.objects.filter(collection=collection)
            for candidate_url in candidate_urls:
                # Check if a CuratedUrl with the same URL already exists
                if not CuratedUrl.objects.filter(url=candidate_url.url).exists():
                    CuratedUrl.objects.create(
                        collection=candidate_url.collection,
                        url=candidate_url.url,
                        scraped_title=candidate_url.scraped_title,
                        generated_title=candidate_url.generated_title,
                        visited=candidate_url.visited,
                        document_type=candidate_url.document_type,
                        division=candidate_url.division,
                    )
            self.stdout.write(
                f"Migrated {candidate_urls.count()} URLs from collection '{collection.name}' to CuratedUrl."
            )

    def migrate_exclude_patterns(self):
        self.stdout.write("Migrating Exclude Patterns...")
        for pattern in ExcludePattern.objects.all():
            delta_pattern, created = DeltaExcludePattern.objects.get_or_create(
                collection=pattern.collection,
                match_pattern=pattern.match_pattern,
                match_pattern_type=pattern.match_pattern_type,
                reason=pattern.reason,
            )

    def migrate_include_patterns(self):
        self.stdout.write("Migrating Include Patterns...")
        for pattern in IncludePattern.objects.all():
            delta_pattern, created = DeltaIncludePattern.objects.get_or_create(
                collection=pattern.collection,
                match_pattern=pattern.match_pattern,
                match_pattern_type=pattern.match_pattern_type,
            )

    def migrate_title_patterns(self):
        self.stdout.write("Migrating Title Patterns...")
        for pattern in TitlePattern.objects.all():
            delta_pattern, created = DeltaTitlePattern.objects.get_or_create(
                collection=pattern.collection,
                match_pattern=pattern.match_pattern,
                match_pattern_type=pattern.match_pattern_type,
                title_pattern=pattern.title_pattern,
            )

    def migrate_document_type_patterns(self):
        self.stdout.write("Migrating Document Type Patterns...")
        for pattern in DocumentTypePattern.objects.all():
            delta_pattern, created = DeltaDocumentTypePattern.objects.get_or_create(
                collection=pattern.collection,
                match_pattern=pattern.match_pattern,
                match_pattern_type=pattern.match_pattern_type,
                document_type=pattern.document_type,
            )

    def migrate_division_patterns(self):
        self.stdout.write("Migrating Division Patterns...")
        for pattern in DivisionPattern.objects.all():
            delta_pattern, created = DeltaDivisionPattern.objects.get_or_create(
                collection=pattern.collection,
                match_pattern=pattern.match_pattern,
                match_pattern_type=pattern.match_pattern_type,
                division=pattern.division,
            )
