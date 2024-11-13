# noqa: F841
# docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_migrate_dump.py

import pytest

from sde_collections.models.delta_url import DeltaUrl, DumpUrl
from sde_collections.tests.factories import (
    CollectionFactory,
    CuratedUrlFactory,
    DeltaUrlFactory,
    DumpUrlFactory,
)

DELTA_COMPARISON_FIELDS = ["scraped_title"]  # Assuming a central definition


@pytest.mark.django_db
class TestMigrationHelpers:
    def test_clear_delta_urls(self):
        collection = CollectionFactory()
        DeltaUrlFactory.create_batch(5, collection=collection)
        collection.clear_delta_urls()
        assert DeltaUrl.objects.filter(collection=collection).count() == 0

    def test_clear_dump_urls(self):
        collection = CollectionFactory()
        DumpUrlFactory.create_batch(5, collection=collection)
        collection.clear_dump_urls()
        assert DumpUrl.objects.filter(collection=collection).count() == 0

    def test_create_or_update_delta_url_add(self):
        collection = CollectionFactory()
        dump_url = DumpUrlFactory(collection=collection)
        collection.create_or_update_delta_url(dump_url, delete=False)
        delta = DeltaUrl.objects.get(url=dump_url.url)
        assert delta.delete is False
        for field in DELTA_COMPARISON_FIELDS:
            assert getattr(delta, field) == getattr(dump_url, field)

    def test_create_or_update_delta_url_delete(self):
        collection = CollectionFactory()
        curated_url = CuratedUrlFactory(collection=collection)
        collection.create_or_update_delta_url(curated_url, delete=True)
        delta = DeltaUrl.objects.get(url=curated_url.url)
        assert delta.delete is True
        assert delta.scraped_title == ""


@pytest.mark.django_db
class TestMigrateDumpToDelta:
    def test_new_url_in_dump_only(self):
        collection = CollectionFactory()
        dump_url = DumpUrlFactory(collection=collection)
        collection.migrate_dump_to_delta()
        delta = DeltaUrl.objects.get(url=dump_url.url)
        assert delta.delete is False
        for field in DELTA_COMPARISON_FIELDS:
            assert getattr(delta, field) == getattr(dump_url, field)

    def test_url_in_both_with_different_field(self):
        collection = CollectionFactory()
        dump_url = DumpUrlFactory(collection=collection, scraped_title="New Title")
        curated_url = CuratedUrlFactory(collection=collection, url=dump_url.url, scraped_title="Old Title")  # noqa
        collection.migrate_dump_to_delta()
        delta = DeltaUrl.objects.get(url=dump_url.url)
        assert delta.delete is False
        assert delta.scraped_title == "New Title"

    def test_url_in_curated_only(self):
        collection = CollectionFactory()
        curated_url = CuratedUrlFactory(collection=collection)
        collection.migrate_dump_to_delta()
        delta = DeltaUrl.objects.get(url=curated_url.url)
        assert delta.delete is True
        assert delta.scraped_title == ""

    def test_identical_url_in_both(self):
        collection = CollectionFactory()
        dump_url = DumpUrlFactory(collection=collection, scraped_title="Same Title")
        curated_url = CuratedUrlFactory(collection=collection, url=dump_url.url, scraped_title="Same Title")  # noqa
        collection.migrate_dump_to_delta()
        assert not DeltaUrl.objects.filter(url=dump_url.url).exists()

    def test_full_migration_flow(self):
        collection = CollectionFactory()
        dump_url_new = DumpUrlFactory(collection=collection)  # New URL
        dump_url_update = DumpUrlFactory(collection=collection, scraped_title="Updated Title")
        CuratedUrlFactory(collection=collection, url=dump_url_update.url, scraped_title="Old Title")
        curated_url_delete = CuratedUrlFactory(collection=collection)  # Missing in Dump

        collection.migrate_dump_to_delta()

        # New URL moved to DeltaUrls
        assert DeltaUrl.objects.filter(url=dump_url_new.url, delete=False).exists()

        # Updated URL moved to DeltaUrls
        delta_update = DeltaUrl.objects.get(url=dump_url_update.url)
        assert delta_update.scraped_title == "Updated Title"
        assert delta_update.delete is False

        # Deleted URL in CuratedUrls marked as delete in DeltaUrls
        delta_delete = DeltaUrl.objects.get(url=curated_url_delete.url)
        assert delta_delete.delete is True

    def test_empty_collections(self):
        collection = CollectionFactory()
        collection.migrate_dump_to_delta()
        assert DeltaUrl.objects.filter(collection=collection).count() == 0

    def test_partial_data_in_dump_urls(self):
        collection = CollectionFactory()
        dump_url = DumpUrlFactory(collection=collection, scraped_title="")
        collection.migrate_dump_to_delta()
        delta = DeltaUrl.objects.get(url=dump_url.url)
        assert delta.scraped_title == ""
        assert delta.delete is False


@pytest.mark.django_db
class TestMigrationIdempotency:
    def test_migrate_dump_to_delta_idempotency(self):
        collection = CollectionFactory()
        dump_url = DumpUrlFactory(collection=collection)
        CuratedUrlFactory(collection=collection, url=dump_url.url, scraped_title="Different Title")

        # First migration run
        collection.migrate_dump_to_delta()
        assert DeltaUrl.objects.filter(url=dump_url.url).count() == 1

        # Run migration again
        collection.migrate_dump_to_delta()
        assert DeltaUrl.objects.filter(url=dump_url.url).count() == 1  # Ensure no duplicates

    def test_create_or_update_delta_url_idempotency(self):
        collection = CollectionFactory()
        dump_url = DumpUrlFactory(collection=collection)

        # First call
        collection.create_or_update_delta_url(dump_url, delete=False)
        assert DeltaUrl.objects.filter(url=dump_url.url).count() == 1

        # Second call with the same data
        collection.create_or_update_delta_url(dump_url, delete=False)
        assert DeltaUrl.objects.filter(url=dump_url.url).count() == 1  # Should still be one


@pytest.mark.django_db
def test_create_or_update_delta_url_field_copy():
    collection = CollectionFactory()
    dump_url = DumpUrlFactory(
        collection=collection,
        scraped_title="Test Title",
        scraped_text="Test Text",
        generated_title="Generated Test Title",
        visited=True,
        document_type=1,
        division=2,
    )

    collection.create_or_update_delta_url(dump_url, delete=False)
    delta = DeltaUrl.objects.get(url=dump_url.url)

    # Verify each field is copied correctly
    for field in DumpUrl._meta.fields:
        if field.name not in ["id", "collection", "url"]:
            assert getattr(delta, field.name) == getattr(dump_url, field.name)


@pytest.mark.django_db
class TestGranularFullMigrationFlow:
    def test_full_migration_new_url(self):
        collection = CollectionFactory()
        dump_url = DumpUrlFactory(collection=collection)  # New URL
        collection.migrate_dump_to_delta()

        # New URL should be added to DeltaUrls
        assert DeltaUrl.objects.filter(url=dump_url.url, delete=False).exists()

    def test_full_migration_updated_url(self):
        collection = CollectionFactory()
        dump_url = DumpUrlFactory(collection=collection, scraped_title="Updated Title")
        collection.migrate_dump_to_delta()

        # URL with differing fields should be updated in DeltaUrls
        delta_update = DeltaUrl.objects.get(url=dump_url.url)
        assert delta_update.scraped_title == "Updated Title"
        assert delta_update.delete is False

    def test_full_migration_deleted_url(self):
        collection = CollectionFactory()
        curated_url = CuratedUrlFactory(collection=collection)  # URL to be deleted
        collection.migrate_dump_to_delta()

        # Missing URL in DumpUrls should be marked as delete in DeltaUrls
        delta_delete = DeltaUrl.objects.get(url=curated_url.url)
        assert delta_delete.delete is True


@pytest.mark.django_db
def test_empty_delta_comparison_fields():
    collection = CollectionFactory()
    dump_url = DumpUrlFactory(collection=collection, scraped_title="Same Title")
    curated_url = CuratedUrlFactory(collection=collection, url=dump_url.url, scraped_title="Same Title")  # noqa

    global DELTA_COMPARISON_FIELDS
    original_fields = DELTA_COMPARISON_FIELDS
    DELTA_COMPARISON_FIELDS = []  # Simulate empty comparison fields

    try:
        collection.migrate_dump_to_delta()
        # No DeltaUrl should be created as there are no fields to compare
        assert not DeltaUrl.objects.filter(url=dump_url.url).exists()
    finally:
        DELTA_COMPARISON_FIELDS = original_fields  # Reset the fields after test


@pytest.mark.django_db
def test_partial_data_in_curated_urls():
    collection = CollectionFactory()
    dump_url = DumpUrlFactory(collection=collection, scraped_title="Title Exists")
    curated_url = CuratedUrlFactory(collection=collection, url=dump_url.url, scraped_title="")  # noqa

    collection.migrate_dump_to_delta()

    # Since `scraped_title` differs (None vs "Title Exists"), it should create a DeltaUrl
    delta = DeltaUrl.objects.get(url=dump_url.url)
    assert delta.scraped_title == "Title Exists"
    assert delta.delete is False
