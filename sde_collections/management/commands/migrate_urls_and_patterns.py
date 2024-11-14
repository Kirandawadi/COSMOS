from django.core.management.base import BaseCommand
from django.db import transaction
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
        all_collections_with_urls = Collection.objects.annotate(url_count=Count("candidate_urls")).filter(
            url_count__gt=0
        )

        # Migrate all CandidateURLs to DeltaUrl
        for collection in all_collections_with_urls:
            candidate_urls = CandidateURL.objects.filter(collection=collection)
            delta_urls = []
            for candidate_url in candidate_urls:
                # Check if a DeltaUrl with the same URL already exists
                if not DeltaUrl.objects.filter(url=candidate_url.url).exists():
                    delta_urls.append(
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
                    )
            if delta_urls:
                DeltaUrl.objects.bulk_create(delta_urls, ignore_conflicts=True)
            self.stdout.write(
                f"Migrated {candidate_urls.count()} URLs from collection '{collection.name}' to DeltaUrl."
            )

        # Migrate Patterns
        with transaction.atomic():
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

        curated_urls_to_create = []
        for collection in all_curated_collections_with_urls:
            candidate_urls = DeltaUrl.objects.filter(collection=collection)
            for candidate_url in candidate_urls:
                # Check if a CuratedUrl with the same URL already exists
                if not CuratedUrl.objects.filter(url=candidate_url.url).exists():
                    curated_urls_to_create.append(
                        CuratedUrl(
                            collection=candidate_url.collection,
                            url=candidate_url.url,
                            scraped_title=candidate_url.scraped_title,
                            generated_title=candidate_url.generated_title,
                            visited=candidate_url.visited,
                            document_type=candidate_url.document_type,
                            division=candidate_url.division,
                        )
                    )
            if curated_urls_to_create:
                CuratedUrl.objects.bulk_create(curated_urls_to_create, ignore_conflicts=True)
            self.stdout.write(
                f"Migrated {candidate_urls.count()} URLs from collection '{collection.name}' to CuratedUrl."
            )

    def migrate_exclude_patterns(self):
        self.stdout.write("Migrating Exclude Patterns...")
        exclude_patterns_to_create = []
        for pattern in ExcludePattern.objects.all():
            exclude_pattern = DeltaExcludePattern(
                collection=pattern.collection,
                match_pattern=pattern.match_pattern,
                match_pattern_type=pattern.match_pattern_type,
                reason=pattern.reason,
            )
            exclude_patterns_to_create.append(exclude_pattern)
            exclude_pattern.apply()
        if exclude_patterns_to_create:
            DeltaExcludePattern.objects.bulk_create(exclude_patterns_to_create)

    def migrate_include_patterns(self):
        self.stdout.write("Migrating Include Patterns...")
        include_patterns_to_create = []
        for pattern in IncludePattern.objects.all():
            include_pattern = DeltaIncludePattern(
                collection=pattern.collection,
                match_pattern=pattern.match_pattern,
                match_pattern_type=pattern.match_pattern_type,
            )
            include_patterns_to_create.append(include_pattern)
            include_pattern.apply()
        if include_patterns_to_create:
            DeltaIncludePattern.objects.bulk_create(include_patterns_to_create)

    def migrate_title_patterns(self):
        self.stdout.write("Migrating Title Patterns...")
        title_patterns_to_create = []
        for pattern in TitlePattern.objects.all():
            title_pattern = DeltaTitlePattern(
                collection=pattern.collection,
                match_pattern=pattern.match_pattern,
                match_pattern_type=pattern.match_pattern_type,
                title_pattern=pattern.title_pattern,
            )
            title_patterns_to_create.append(title_pattern)
            title_pattern.apply()
        if title_patterns_to_create:
            DeltaTitlePattern.objects.bulk_create(title_patterns_to_create)

    def migrate_document_type_patterns(self):
        self.stdout.write("Migrating Document Type Patterns...")
        doc_type_patterns_to_create = []
        for pattern in DocumentTypePattern.objects.all():
            doc_type_pattern = DeltaDocumentTypePattern(
                collection=pattern.collection,
                match_pattern=pattern.match_pattern,
                match_pattern_type=pattern.match_pattern_type,
                document_type=pattern.document_type,
            )
            doc_type_patterns_to_create.append(doc_type_pattern)
            doc_type_pattern.apply()
        if doc_type_patterns_to_create:
            DeltaDocumentTypePattern.objects.bulk_create(doc_type_patterns_to_create)

    def migrate_division_patterns(self):
        self.stdout.write("Migrating Division Patterns...")
        division_patterns_to_create = []
        for pattern in DivisionPattern.objects.all():
            division_pattern = DeltaDivisionPattern(
                collection=pattern.collection,
                match_pattern=pattern.match_pattern,
                match_pattern_type=pattern.match_pattern_type,
                division=pattern.division,
            )
            division_patterns_to_create.append(division_pattern)
            division_pattern.apply()
        if division_patterns_to_create:
            DeltaDivisionPattern.objects.bulk_create(division_patterns_to_create)

        # # Migrate CandidateURLs to DeltaUrl
        # all_collections = Collection.objects.all()
        # self.stdout.write(f"Migrating URLs for {all_collections.count()} collections...")
        # for collection in collections_for_delta:
        #     # Apply DeltaTitlePattern
        #     title_patterns = DeltaTitlePattern.objects.filter(collection=collection)
        #     for title_pattern in title_patterns:
        #         title_pattern.apply()

        # # Migrate CandidateURLs for collections with CURATED or higher workflow status to CuratedUrl
        # collections_for_curated = Collection.objects.filter(workflow_status__gte=WorkflowStatusChoices.CURATED)
        # self.stdout.write(
        #     f"Migrating URLs for {collections_for_curated.count()} collections with CURATED or higher status..."
        # )

        # for collection in collections_for_curated:
        #     candidate_urls = CandidateURL.objects.filter(collection=collection)
        #     for candidate_url in candidate_urls:
        #         # Check if a CuratedUrl with the same URL already exists
        #         if not CuratedUrl.objects.filter(url=candidate_url.url).exists():
        #             CuratedUrl.objects.create(
        #                 collection=candidate_url.collection,
        #                 url=candidate_url.url,
        #                 scraped_title=candidate_url.scraped_title,
        #                 generated_title=candidate_url.generated_title,
        #                 visited=candidate_url.visited,
        #                 document_type=candidate_url.document_type,
        #                 division=candidate_url.division,
        #             )
        #     self.stdout.write(
        #         f"Migrated {candidate_urls.count()} URLs from collection '{collection.name}' to CuratedUrl."
        #     )

        # # Migrate CandidateURLs for collections with a status lower than CURATED to DeltaUrl
        # collections_for_delta = Collection.objects.filter(workflow_status__lt=WorkflowStatusChoices.CURATED)
        # self.stdout.write(
        #     f"Migrating URLs for {collections_for_delta.count()} collections with status lower than CURATED..."
        # )

        # for collection in collections_for_delta:
        #     candidate_urls = CandidateURL.objects.filter(collection=collection)
        #     for candidate_url in candidate_urls:
        #         # Check if a DeltaUrl with the same URL already exists
        #         if not DeltaUrl.objects.filter(url=candidate_url.url).exists():
        #             DeltaUrl.objects.create(
        #                 collection=candidate_url.collection,
        #                 url=candidate_url.url,
        #                 scraped_title=candidate_url.scraped_title,
        #                 generated_title=candidate_url.generated_title,
        #                 visited=candidate_url.visited,
        #                 document_type=candidate_url.document_type,
        #                 division=candidate_url.division,
        #                 delete=False,
        #             )
        #     self.stdout.write(
        #         f"Migrated {candidate_urls.count()} URLs from collection '{collection.name}' to DeltaUrl."
        #     )

        # self.stdout.write(self.style.SUCCESS("Migration complete."))
