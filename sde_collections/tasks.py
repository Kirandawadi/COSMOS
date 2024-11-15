import json
import os
import shutil

import boto3
from django.apps import apps
from django.conf import settings
from django.core import management
from django.db import IntegrityError

from config import celery_app

from .models.collection import Collection, WorkflowStatusChoices
from .models.delta_url import CuratedUrl, DeltaUrl, DumpUrl
from .sinequa_api import Api
from .utils.github_helper import GitHubHandler


def _get_data_to_import(collection, server_name):
    # ignore these because they are API collections and don't have URLs
    ignore_collections = [
        "/SMD/ASTRO_NAVO_HEASARC/",
        "/SMD/CASEI_Campaign/",
        "/SMD/CASEI_Deployment/",
        "/SMD/CASEI_Instrument/",
        "/SMD/CASEI_Platform/",
        "/SMD/CMR_API/",
        "/SMD/PDS_API_Legacy_All/",
    ]

    data_to_import = []
    api = Api(server_name=server_name)
    page = 1
    while True:
        print(f"Getting page: {page}")
        response = api.query(page=page, collection_config_folder=collection.config_folder)
        if response["cursorRowCount"] == 0:
            break

        for record in response.get("records", []):
            full_collection_name = record.get("collection")[0]
            if full_collection_name in ignore_collections:
                continue

            url = record.get("download_url")
            title = record.get("title", "")
            collection_pk = collection.pk

            if not url:
                continue

            augmented_data = {
                "model": "sde_collections.url",
                "fields": {
                    "collection": collection_pk,
                    "url": url,
                    "scraped_title": title,
                },
            }

            data_to_import.append(augmented_data)
        page += 1
    return data_to_import


def _compare_and_populate_delta_urls(collection):
    """Compare DumpUrl and CuratedUrl and populate DeltaUrl."""
    dump_urls = DumpUrl.objects.filter(collection=collection)
    curated_urls = CuratedUrl.objects.filter(collection=collection)

    DeltaUrl.objects.filter(collection=collection).delete()

    curated_urls_dict = {url.url: url for url in curated_urls}

    # Iterate over Dump URLs to find deltas
    for dump_url in dump_urls:
        curated_url = curated_urls_dict.get(dump_url.url)

        if not curated_url:
            # New URL found, add to DeltaUrl
            DeltaUrl.objects.create(
                collection=collection,
                url=dump_url.url,
                scraped_title=dump_url.scraped_title,
                generated_title=dump_url.generated_title,
                document_type=dump_url.document_type,
                division=dump_url.division,
                delete=False,
            )
        elif (
            curated_url.scraped_title != dump_url.scraped_title
            or curated_url.generated_title != dump_url.generated_title
            or curated_url.document_type != dump_url.document_type
            or curated_url.division != dump_url.division
        ):
            # Metadata changed, add to DeltaUrl
            DeltaUrl.objects.create(
                collection=collection,
                url=dump_url.url,
                scraped_title=dump_url.scraped_title,
                generated_title=dump_url.generated_title,
                document_type=dump_url.document_type,
                division=dump_url.division,
                delete=False,
            )

    # Mark any missing URLs in CuratedUrl as deleted in DeltaUrl
    dump_url_set = set(dump_urls.values_list("url", flat=True))
    for curated_url in curated_urls:
        if curated_url.url not in dump_url_set:
            DeltaUrl.objects.create(
                collection=collection,
                url=curated_url.url,
                scraped_title=curated_url.scraped_title,
                generated_title=curated_url.generated_title,
                document_type=curated_url.document_type,
                division=curated_url.division,
                delete=True,
            )


# TODO: Bishwas wrote this but it is outdated.
# def populate_dump_urls(collection):
#     urls = Url.objects.filter(collection=collection)

#     for url_instance in urls:
#         try:
#             # Create DumpUrl by passing in the parent Url fields
#             dump_url_instance = DumpUrl(
#                 id=url_instance.id,
#                 collection=url_instance.collection,
#                 url=url_instance.url,
#                 scraped_title=url_instance.scraped_title,
#                 visited=url_instance.visited,
#                 document_type=url_instance.document_type,
#                 division=url_instance.division,
#             )
#             dump_url_instance.save()  # Save both Url and DumpUrl entries

#             print(f"Created DumpUrl: {dump_url_instance.url} - {dump_url_instance.scraped_title}")

#         except Exception as e:
#             print(f"Error creating DumpUrl for {url_instance.url}: {str(e)}")
#             continue

#     print(f"Successfully populated DumpUrl model with {urls.count()} entries.")


@celery_app.task(soft_time_limit=10000)
def import_candidate_urls_from_api(server_name="test", collection_ids=[]):
    TEMP_FOLDER_NAME = "temp"
    os.makedirs(TEMP_FOLDER_NAME, exist_ok=True)

    collections = Collection.objects.filter(id__in=collection_ids)

    for collection in collections:
        urls_file = f"{TEMP_FOLDER_NAME}/{collection.config_folder}.json"

        print("Getting responses from API")
        data_to_import = _get_data_to_import(server_name=server_name, collection=collection)
        print(f"Got {len(data_to_import)} records for {collection.config_folder}")

        print("Clearing DumpUrl model...")
        DumpUrl.objects.filter(collection=collection).delete()

        print("Dumping django fixture to file")
        json.dump(data_to_import, open(urls_file, "w"))

        print("Loading data into Url model using loaddata...")
        management.call_command("loaddata", urls_file)

        # TODO: Bishwas wrote this but it is does not work.
        # print("Creating DumpUrl entries...")
        # populate_dump_urls(collection)

        print("Applying existing patterns; this may take a while")
        collection.apply_all_patterns()

        print("Comparing DumpUrl with CuratedUrl...")
        _compare_and_populate_delta_urls(collection)

        if collection.workflow_status != WorkflowStatusChoices.ENGINEERING_IN_PROGRESS:
            collection.workflow_status = WorkflowStatusChoices.ENGINEERING_IN_PROGRESS
            collection.save()

        # Finally set the status to READY_FOR_CURATION
        # collection.workflow_status = WorkflowStatusChoices.READY_FOR_CURATION
        collection.save()

    print("Deleting temp files")
    shutil.rmtree(TEMP_FOLDER_NAME)


@celery_app.task()
def push_to_github_task(collection_ids):
    collections = Collection.objects.filter(id__in=collection_ids)
    github_handler = GitHubHandler(collections)
    github_handler.push_to_github()


@celery_app.task()
def sync_with_production_webapp():
    for collection in Collection.objects.all():
        collection.sync_with_production_webapp()


@celery_app.task()
def pull_latest_collection_metadata_from_github():
    FILENAME = "github_collections.json"

    gh = GitHubHandler(collections=Collection.objects.none())
    collections = gh.get_collections_from_github()

    json.dump(collections, open(FILENAME, "w"), indent=4)

    # Upload the file to S3
    s3_bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    s3_key = FILENAME
    s3_client = boto3.client(
        "s3",
        region_name="us-east-1",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    s3_client.upload_file(FILENAME, s3_bucket_name, s3_key)


@celery_app.task()
def resolve_title_pattern(title_pattern_id):
    TitlePattern = apps.get_model("sde_collections", "TitlePattern")
    title_pattern = TitlePattern.objects.get(id=title_pattern_id)
    title_pattern.apply()


@celery_app.task
def fetch_and_replace_full_text(collection_id, server_name):
    """
    Task to fetch and replace full text and metadata for all URLs associated with a specified collection
    from a given server. This task deletes all existing DumpUrl entries for the collection and creates
    new entries based on the latest fetched data.

    Args:
        collection_id (int): The identifier for the collection in the database.
        server_name (str): The name of the server.

    Returns:
        str: A message indicating the result of the operation, including the number of URLs processed.
    """
    collection = Collection.objects.get(id=collection_id)
    api = Api(server_name)
    documents = api.get_full_texts(collection.config_folder)

    # Step 1: Delete all existing DumpUrl entries for the collection
    deleted_count, _ = DumpUrl.objects.filter(collection=collection).delete()
    print(f"Deleted {deleted_count} existing DumpUrl entries for collection '{collection.config_name}'.")

    # Step 2: Create new DumpUrl entries from the fetched documents
    processed_count = 0
    for doc in documents:
        try:
            DumpUrl.objects.create(
                url=doc["url"],
                collection=collection,
                scraped_text=doc.get("full_text", ""),
                scraped_title=doc.get("title", ""),
            )
            processed_count += 1
        except IntegrityError:
            # Handle duplicate URL case if needed
            print(f"Duplicate URL found, skipping: {doc['url']}")

    return f"Successfully processed {len(documents)} records and updated the database."
