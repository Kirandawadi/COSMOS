import json
import urllib.parse

import requests
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from model_utils import FieldTracker
from slugify import slugify

from config_generation.db_to_xml import XmlEditor

from ..utils.github_helper import GitHubHandler
from ..utils.slack_utils import (
    STATUS_CHANGE_NOTIFICATIONS,
    format_slack_message,
    send_slack_message,
)
from .collection_choice_fields import (
    ConnectorChoices,
    CurationStatusChoices,
    Divisions,
    DocumentTypes,
    SourceChoices,
    UpdateFrequencies,
    WorkflowStatusChoices,
)
from .delta_url import CuratedUrl, DeltaUrl, DumpUrl

User = get_user_model()
DELTA_COMPARISON_FIELDS = ["scraped_title"]  # Add more fields as needed


class Collection(models.Model):
    """Model definition for Collection."""

    name = models.CharField("Name", max_length=1024)
    config_folder = models.CharField("Config Folder", max_length=2048, unique=True, editable=False)
    url = models.URLField("URL", max_length=2048)
    division = models.IntegerField(choices=Divisions.choices)
    turned_on = models.BooleanField("Turned On", default=True)
    connector = models.IntegerField(choices=ConnectorChoices.choices, default=ConnectorChoices.CRAWLER2)

    source = models.IntegerField(choices=SourceChoices.choices, default=SourceChoices.BOTH)
    update_frequency = models.IntegerField(choices=UpdateFrequencies.choices, default=UpdateFrequencies.WEEKLY)
    document_type = models.IntegerField(choices=DocumentTypes.choices, default=DocumentTypes.DOCUMENTATION)
    tree_root_deprecated = models.CharField("Tree Root", max_length=1024, default="", blank=True)
    delete = models.BooleanField(default=False)
    is_multi_division = models.BooleanField("Is Multi-Division?", default=False)

    # audit columns for production
    audit_hierarchy = models.CharField("Audit Hierarchy", max_length=2048, default="", blank=True)
    audit_url = models.CharField("Audit URL", max_length=2048, default="", blank=True)
    audit_mapping = models.CharField("Audit Mapping", max_length=2048, default="", blank=True)
    audit_label = models.CharField("Audit Label", max_length=2048, default="", blank=True)
    audit_query = models.CharField("Audit Query", max_length=2048, default="", blank=True)
    audit_duplicate_results = models.CharField("Audit Duplicate Results", max_length=2048, default="", blank=True)
    audit_metrics = models.CharField("Audit Metrics", max_length=2048, default="", blank=True)

    cleaning_assigned_to = models.CharField("Cleaning Assigned To", max_length=128, default="", blank=True)

    github_issue_number = models.IntegerField("Issue Number in Github", default=0)
    notes = models.TextField("Notes", blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    new_collection = models.BooleanField(default=False)
    cleaning_order = models.IntegerField(default=0, blank=True)

    curation_status = models.IntegerField(
        choices=CurationStatusChoices.choices,
        default=CurationStatusChoices.NEEDS_SCRAPING,
    )
    workflow_status = models.IntegerField(
        choices=WorkflowStatusChoices.choices,
        default=WorkflowStatusChoices.RESEARCH_IN_PROGRESS,
    )
    tracker = FieldTracker(fields=["workflow_status"])

    curated_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, blank=True)
    curation_started = models.DateTimeField("Curation Started", null=True, blank=True)

    class Meta:
        """Meta definition for Collection."""

        verbose_name = "Collection"
        verbose_name_plural = "Collections"

    def clear_delta_urls(self):
        """Clears all DeltaUrls for this collection."""
        DeltaUrl.objects.filter(collection=self).delete()

    def clear_dump_urls(self):
        """Clears all DumpUrls for this collection."""
        DumpUrl.objects.filter(collection=self).delete()

    def refresh_url_lists_for_all_patterns(self):
        """
        Updates pattern relations for all patterns associated with this collection.
        """
        # List of pattern models to update
        pattern_models = [
            "DeltaExcludePattern",
            "DeltaIncludePattern",
            "DeltaTitlePattern",
            "DeltaDocumentTypePattern",
            "DeltaDivisionPattern",
        ]

        # Loop through each model and update its relations
        for model_name in pattern_models:
            # Get the model dynamically
            model = ContentType.objects.get(app_label="sde_collections", model=model_name.lower()).model_class()

            # Filter patterns for the current collection and update relations
            for pattern in model.objects.filter(collection=self):
                pattern.update_affected_delta_urls_list()
                pattern.update_affected_curated_urls_list()

    def migrate_dump_to_delta(self):
        """
        Migrates data from DumpUrls to DeltaUrls, preserving all fields.
        Creates DeltaUrls that reflect:
        1. Changes from DumpUrls vs CuratedUrls
        2. Missing URLs in DumpUrls that exist in CuratedUrls (marked for deletion)
        """
        # Step 1: Clear existing DeltaUrls for this collection
        self.clear_delta_urls()

        # Step 2: Fetch all current DumpUrls and CuratedUrls for this collection
        dump_urls = {url.url: url for url in DumpUrl.objects.filter(collection=self)}
        curated_urls = {url.url: url for url in CuratedUrl.objects.filter(collection=self)}

        # Step 3: Process each URL in DumpUrls to migrate as needed
        for url, dump in dump_urls.items():
            curated = curated_urls.get(url)

            if curated:
                # Check if any of the comparison fields differ
                if any(getattr(curated, field) != getattr(dump, field) for field in DELTA_COMPARISON_FIELDS):
                    self.create_or_update_delta_url(dump, to_delete=False)
            else:
                # New URL, not in CuratedUrls; move it entirely to DeltaUrls
                self.create_or_update_delta_url(dump, to_delete=False)

        # Step 4: Identify CuratedUrls missing in DumpUrls and flag them for deletion in DeltaUrls
        for curated in curated_urls.values():
            if curated.url not in dump_urls:
                self.create_or_update_delta_url(curated, to_delete=True)

        # Step 5: Clear DumpUrls after migration is complete
        self.clear_dump_urls()

        # Step 6: Apply all patterns to DeltaUrls
        # self.refresh_url_lists_for_all_patterns() # TODO: I'm pretty confident we shouldn't be running this
        self.apply_all_patterns()

    def create_or_update_delta_url(self, url_instance, to_delete=False):
        """
        Creates or updates a DeltaUrl entry based on the given DumpUrl or CuratedUrl object.
        Always copies all fields, even for deletion cases.

        Args:
            url_instance: DumpUrl or CuratedUrl instance to copy from
            to_delete: Whether to mark the resulting DeltaUrl for deletion
        """
        # Get all copyable fields from the source instance
        fields_to_copy = {
            field.name: getattr(url_instance, field.name)
            for field in url_instance._meta.fields
            if field.name not in ["id", "collection"]
        }

        # Set deletion status
        fields_to_copy["to_delete"] = to_delete

        # Update or create the DeltaUrl
        DeltaUrl.objects.update_or_create(collection=self, url=url_instance.url, defaults=fields_to_copy)

    def promote_to_curated(self):
        """
        Promotes all DeltaUrls in this collection to CuratedUrls.
        Updates, adds, or removes CuratedUrls as necessary to match the latest DeltaUrls.
        """
        # Step 1: Fetch all current DeltaUrls and CuratedUrls for this collection
        delta_urls = {url.url: url for url in DeltaUrl.objects.filter(collection=self)}
        curated_urls = {url.url: url for url in CuratedUrl.objects.filter(collection=self)}

        # Step 2: Process each DeltaUrl to update or create the corresponding CuratedUrl
        for url, delta in delta_urls.items():
            curated = curated_urls.get(url)

            # Delete the CuratedUrl if the DeltaUrl is marked for deletion
            if delta.to_delete:
                if curated:
                    curated.delete()
                continue

            if curated:
                updated_fields = {}
                for field in delta._meta.fields:
                    field_name = field.name
                    if field_name == "to_delete":
                        continue

                    delta_value = getattr(delta, field_name)
                    if delta_value not in [None, ""] and getattr(curated, field_name) != delta_value:
                        updated_fields[field_name] = delta_value

                if updated_fields:
                    CuratedUrl.objects.filter(pk=curated.pk).update(**updated_fields)
            else:
                # If no matching CuratedUrl, create a new one using all non-null and non-empty fields
                new_data = {
                    field.name: getattr(delta, field.name)
                    for field in delta._meta.fields
                    if field.name not in ["to_delete", "collection"] and getattr(delta, field.name) not in [None, ""]
                }
                CuratedUrl.objects.create(collection=self, **new_data)

        # Step 3: Clear all DeltaUrls for this collection since they've been promoted
        DeltaUrl.objects.filter(collection=self).delete()

        # Step 4: Reapply patterns to DeltaUrls
        self.refresh_url_lists_for_all_patterns()

    def add_to_public_query(self):
        """Add the collection to the public query."""
        if self.workflow_status not in [
            WorkflowStatusChoices.QUALITY_CHECK_PERFECT,
            WorkflowStatusChoices.QUALITY_CHECK_MINOR,
        ]:
            raise ValueError(f"{self.config_folder} is not ready for public prod, you can't add it to the public query")

        gh = GitHubHandler()
        query_path = "webservices/query-smd-primary.xml"
        scraper_content = gh._get_file_contents(query_path)
        scraper_editor = XmlEditor(scraper_content.decoded_content.decode("utf-8"))

        collections = scraper_editor.get_tag_value("CollectionSelection", strict=True)
        collections = collections.split(";")
        collections.append(f"/SDE/{self.config_folder}/")
        collections = list(set(collections))
        collections.sort()
        collections = ";".join(collections)

        scraper_editor.update_or_add_element_value("CollectionSelection", collections)
        scraper_content = scraper_editor.update_config_xml()
        gh.create_or_update_file(query_path, scraper_content)

    @property
    def included_urls_count(self):
        return self.candidate_urls.filter(excluded=False).count()

    @property
    def delta_urls_count(self):
        """get the total number of delta urls"""
        return self.delta_urls.filter(excluded=False).count()

    @property
    def included_curated_urls_count(self):
        """get the number of included, curated urls"""
        return self.curated_urls.filter(excluded=False).count()

    @property
    def _scraper_config_path(self) -> str:
        return f"sources/scrapers/{self.config_folder}/default.xml"

    @property
    def _plugin_config_path(self) -> str:
        return f"sources/SDE/{self.config_folder}/default.xml"

    @property
    def _indexer_config_path(self) -> str:
        return f"jobs/collection.indexer.{self.config_folder}.xml"

    @property
    def tree_root(self) -> str:
        return f"/{self.get_division_display()}/{self.name}/"

    @property
    def server_url_secret_prod(self) -> str:
        base_url = "https://sciencediscoveryengine.nasa.gov"  # noqa: E231
        payload = {
            "name": "secret-prod",
            "scope": "All",
            "text": "",
            "advanced": {
                "collection": f"/SDE/{self.config_folder}/",
            },
        }
        encoded_payload = urllib.parse.quote(json.dumps(payload))
        return f"{base_url}/app/secret-prod/#/search?query={encoded_payload}"

    @property
    def server_url_prod(self) -> str:
        base_url = "https://sciencediscoveryengine.nasa.gov"  # noqa: E231
        payload = {
            "name": "query-smd-primary",
            "scope": "All",
            "text": "",
            "advanced": {
                "collection": f"/SDE/{self.config_folder}/",
            },
        }
        encoded_payload = urllib.parse.quote(json.dumps(payload))
        return f"{base_url}/app/nasa-sba-smd/#/search?query={encoded_payload}"

    @property
    def curation_status_button_color(self) -> str:
        color_choices = {
            1: "btn-light",
            2: "btn-danger",
            3: "btn-warning",
            4: "btn-info",
            5: "btn-success",
            6: "btn-primary",
            7: "btn-info",
            8: "btn-secondary",
        }
        return color_choices[self.curation_status]

    @property
    def workflow_status_button_color(self) -> str:
        color_choices = {
            1: "btn-light",
            2: "btn-danger",
            3: "btn-warning",
            4: "btn-info",
            5: "btn-success",
            6: "btn-primary",
            7: "btn-info",
            8: "btn-secondary",
            9: "btn-light",
            10: "btn-danger",
            11: "btn-warning",
            12: "btn-info",
            13: "btn-success",
            14: "btn-primary",
            15: "btn-info",
            16: "btn-secondary",
            17: "btn-light",
            18: "btn-success",
            19: "btn-warning",
            20: "btn-info",
            21: "btn-success",
            22: "btn-light",
            23: "btn-light",
        }
        return color_choices[self.workflow_status]

    def _process_exclude_list(self):
        """Process the exclude list."""
        return [pattern._process_match_pattern() for pattern in self.excludepattern.all()]

    def _process_include_list(self):
        """Process the include list."""
        return [pattern._process_match_pattern() for pattern in self.includepattern.all()]

    def _process_title_list(self):
        """Process the title list"""
        title_rules = []
        for title_pattern in self.titlepattern.all():
            processed_pattern = {
                "title_criteria": title_pattern._process_match_pattern(),
                "title_value": title_pattern.title_pattern,
            }
            title_rules.append(processed_pattern)
        return title_rules

    def _process_document_type_list(self):
        """Process the document type list"""
        document_type_rules = []
        for document_type_pattern in self.documenttypepattern.all():
            processed_pattern = {
                "criteria": document_type_pattern._process_match_pattern(),
                "document_type": document_type_pattern.get_document_type_display(),
            }
            document_type_rules.append(processed_pattern)
        return document_type_rules

    def _write_to_github(self, path, content, overwrite):
        gh = GitHubHandler()
        if overwrite:
            gh.create_or_update_file(path, content)
        else:
            gh.create_file(path, content)

    def create_scraper_config(self, overwrite: bool = False):
        """
        Reads from the model data and creates the initial scraper config xml file

        if overwrite is True, it will overwrite the existing file
        """

        scraper_template = open("config_generation/xmls/webcrawler_initial_crawl.xml").read()
        editor = XmlEditor(scraper_template)
        scraper_config = editor.convert_template_to_scraper(self)
        self._write_to_github(self._scraper_config_path, scraper_config, overwrite)

    def create_plugin_config(self, overwrite: bool = False):
        """
        Reads from the model data and creates the plugin config xml file that calls the api

        if overwrite is True, it will overwrite the existing file
        """

        # there needs to be a scraper config file before creating the plugin config
        gh = GitHubHandler()
        scraper_exists = gh.check_file_exists(self._scraper_config_path)
        if not scraper_exists:
            raise ValueError(f"Scraper does not exist for the collection {self.config_folder}")
        else:
            scraper_content = gh._get_file_contents(self._scraper_config_path)
            scraper_content = scraper_content.decoded_content.decode("utf-8")
            scraper_editor = XmlEditor(scraper_content)

        plugin_template = open("config_generation/xmls/plugin_indexing_template.xml").read()
        plugin_editor = XmlEditor(plugin_template)
        plugin_config = plugin_editor.convert_template_to_plugin_indexer(scraper_editor)
        self._write_to_github(self._plugin_config_path, plugin_config, overwrite)

    def create_indexer_config(self, overwrite: bool = False):
        """
        Reads from the model data and creates indexer job that calls the plugin config

        if overwrite is True, it will overwrite the existing file
        """
        indexer_template = open("config_generation/xmls/job_template.xml").read()
        editor = XmlEditor(indexer_template)
        indexer_config = editor.convert_template_to_indexer(self)
        self._write_to_github(self._indexer_config_path, indexer_config, overwrite)

    def update_config_xml(self, original_config_string):
        """
        reads from the model data and creates a config that mirrors the
            - excludes
            - title rules
            - doc types
            - tree root
        """
        editor = XmlEditor(original_config_string)

        URL_EXCLUDES = self._process_exclude_list()
        URL_INCLUDES = self._process_include_list()
        TITLE_RULES = self._process_title_list()
        DOCUMENT_TYPE_RULES = self._process_document_type_list()

        # TODO: this was creating duplicates so it was temporarily disabled
        # if self.tree_root:
        #     editor.update_or_add_element_value("TreeRoot", self.tree_root)

        for url in URL_EXCLUDES:
            editor.add_url_exclude(url)
        for url in URL_INCLUDES:
            editor.add_url_include(url)
        for title_rule in TITLE_RULES:
            editor.add_title_mapping(**title_rule)
        for rule in DOCUMENT_TYPE_RULES:
            editor.add_document_type_mapping(**rule)

        updated_config_xml_string = editor.update_config_xml()
        return updated_config_xml_string

    def _compute_config_folder_name(self) -> str:
        """
        Take the human readable `self.name` and create a standardized machine format
        The output will be the self.name, but only alphanumeric with _ instead of spaces
        """

        return slugify(self.name, separator="_")

    def import_metadata_from_sinequa_config(self) -> bool:
        """Import metadata from Sinequa."""
        if not self.config_folder:
            return False

        gh = GitHubHandler(collections=[self])
        metadata = gh.fetch_metadata()

        try:
            metadata[self.config_folder]
        except KeyError:
            return False

        print(f"Updating metadata for {self.name}")
        # tree root
        tree_root = metadata[self.config_folder]["tree_root"]
        if tree_root != self.tree_root:
            print(f"Updating tree root for {self.name} to {tree_root}")
        self.tree_root = tree_root

        # document type
        document_type = metadata[self.config_folder]["document_type"]
        if document_type != self.document_type:
            print(f"Updating document type for {self.name} to {document_type}")
        self.document_type = document_type

        # connector
        # connector = metadata[self.config_folder]["connector"]
        # if connector != self.connector:
        #     print(f"Updating connector for {self.name} to {connector}")
        # self.connector = connector

        self.save()
        print("\n\n")

        return True

    def __str__(self) -> str:
        """Unicode representation of Collection."""
        return self.name

    @property
    def has_folder(self) -> bool:
        return self.config_folder != ""

    @property
    def candidate_urls_count(self) -> int:
        return self.candidate_urls.count()

    @property
    def sinequa_configuration(self) -> str:
        URL = f"https://github.com/NASA-IMPACT/sde-backend/blob/production/sources/SDE/{self.config_folder}/default.xml"  # noqa: E231, E501
        return URL

    @property
    def github_issue_link(self) -> str:
        return f"https://github.com/NASA-IMPACT/sde-project/issues/{self.github_issue_number}"  # noqa: E231

    @classmethod
    def _fetch_json_results(cls, url):
        response = requests.get(url)

        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            return

        return response.json()

    @classmethod
    def _create_from_json(cls, json_results):
        for collection in json_results:
            print("Creating collection: ", collection["name"])
            collection.pop("curated_by")
            cls.objects.create(**collection)

    @classmethod
    def purge_and_reset_collections(cls) -> None:
        """Delete all collections from local, and get the whole list of collections from prod."""
        cls.objects.all().delete()

        BASE_URL = "https://sde-indexing-helper.nasa-impact.net/api/collections-read/"

        response_json = cls._fetch_json_results(BASE_URL)
        cls._create_from_json(response_json["results"])

        while response_json["next"]:
            response_json = cls._fetch_json_results(response_json["next"])
            cls._create_from_json(response_json["results"])

    def sync_with_production_webapp(self) -> None:
        """Sync with the production webapp.
        This is useful when syncing a particular collection.
        To delete all existing collections from local, and get the whole list of collections from prod,
        use the purge_and_reset_collections function."""

        BASE_URL = "https://sde-indexing-helper.nasa-impact.net"
        url = f"{BASE_URL}/api/collections-read/{self.id}/"
        response = requests.get(url)

        if response.status_code == 404:  # collection was deleted
            self.delete = True
            self.save()
            return

        if response.status_code != 200:
            print(f"Error: {response.status_code} for {self.name}")
            return

        response_json = response.json()
        print(f"Syncing collection: {self.name}")

        self.audit_duplicate_results = response_json["audit_duplicate_results"]
        self.audit_hierarchy = response_json["audit_hierarchy"]
        self.audit_label = response_json["audit_label"]
        self.audit_mapping = response_json["audit_mapping"]
        self.audit_metrics = response_json["audit_metrics"]
        self.audit_query = response_json["audit_query"]
        self.audit_url = response_json["audit_url"]
        self.cleaning_order = response_json["cleaning_order"]
        self.connector = response_json["connector"]
        self.curation_started = response_json["curation_started"]
        self.curation_status = response_json["curation_status"]
        self.delete = response_json["delete"]
        self.division = response_json["division"]
        self.document_type = response_json["document_type"]
        self.github_issue_number = response_json["github_issue_number"]
        self.name = response_json["name"]
        self.new_collection = response_json["new_collection"]
        self.notes = response_json["notes"]
        self.source = response_json["source"]
        self.tree_root_deprecated = response_json["tree_root_deprecated"]
        self.turned_on = response_json["turned_on"]
        self.update_frequency = response_json["update_frequency"]
        self.updated_at = response_json["updated_at"]
        self.url = response_json["url"]
        self.workflow_status = response_json["workflow_status"]

        self.save()

    def apply_all_patterns(self):
        """Apply all the patterns with debug information."""

        for pattern in self.deltaexcludepatterns.all():
            pattern.apply()

        for pattern in self.deltaincludepatterns.all():
            pattern.apply()

        for pattern in self.deltatitlepatterns.all():
            pattern.apply()

        for pattern in self.deltadocumenttypepatterns.all():
            pattern.apply()

        for pattern in self.deltadivisionpatterns.all():
            pattern.apply()

    def save(self, *args, **kwargs):
        # Call the function to generate the value for the generated_field based on the original_field
        if not self.config_folder:
            self.config_folder = self._compute_config_folder_name()

        if not self._state.adding:
            old_status = Collection.objects.get(id=self.id).workflow_status
            new_status = self.workflow_status
            if old_status != new_status:
                transition = (old_status, new_status)
                if transition in STATUS_CHANGE_NOTIFICATIONS:
                    details = STATUS_CHANGE_NOTIFICATIONS[transition]
                    message = format_slack_message(self.name, details, self.id)
                    try:
                        # TODO: find a better way to allow this to work on dev environments with
                        # no slack integration
                        send_slack_message(message)
                    except Exception as e:
                        print(f"Error sending Slack message: {e}")

        # Call the parent class's save method
        super().save(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        # Create a cached version of the last workflow_status to compare against
        super().__init__(*args, **kwargs)
        self.old_workflow_status = self.workflow_status


class RequiredUrls(models.Model):
    """
    URLs listed during the research and iteration phases by a curator for a collection,
    which are expected to be indexed by that collection's scraper and indexer
    """

    url = models.URLField(
        help_text="URL which is expected to be brought in by the scraper and indexer",
    )
    collection = models.ForeignKey("Collection", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.url


class Comments(models.Model):
    collection = models.ForeignKey("Collection", related_name="comments", on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text


class WorkflowHistory(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name="workflow_history", null=True)
    workflow_status = models.IntegerField(
        choices=WorkflowStatusChoices.choices,
        default=WorkflowStatusChoices.RESEARCH_IN_PROGRESS,
    )
    old_status = models.IntegerField(choices=WorkflowStatusChoices.choices, null=True)
    curated_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.collection) + str(self.workflow_status)

    @property
    def workflow_status_button_color(self) -> str:
        color_choices = {
            1: "btn-light",
            2: "btn-danger",
            3: "btn-warning",
            4: "btn-info",
            5: "btn-success",
            6: "btn-primary",
            7: "btn-info",
            8: "btn-secondary",
            9: "btn-light",
            10: "btn-danger",
            11: "btn-warning",
            12: "btn-info",
            13: "btn-success",
            14: "btn-primary",
            15: "btn-info",
            16: "btn-secondary",
            17: "btn-light",
            18: "btn-success",
            19: "btn-warning",
            20: "btn-info",
            21: "btn-success",
            22: "btn-light",
            23: "btn-light",
        }
        return color_choices[self.workflow_status]


@receiver(post_save, sender=Collection)
def log_workflow_history(sender, instance, created, **kwargs):
    if instance.workflow_status != instance.old_workflow_status:
        WorkflowHistory.objects.create(
            collection=instance,
            workflow_status=instance.workflow_status,
            curated_by=instance.curated_by,
            old_status=instance.old_workflow_status,
        )


@receiver(post_save, sender=Collection)
def create_configs_on_status_change(sender, instance, created, **kwargs):
    """
    Creates various config files on certain workflow status changes
    """

    if "workflow_status" in instance.tracker.changed():
        if instance.workflow_status == WorkflowStatusChoices.READY_FOR_CURATION:
            instance.create_plugin_config(overwrite=True)
        elif instance.workflow_status == WorkflowStatusChoices.CURATED:
            instance.promote_to_curated()
        elif instance.workflow_status == WorkflowStatusChoices.READY_FOR_ENGINEERING:
            instance.create_scraper_config(overwrite=False)
            instance.create_indexer_config(overwrite=False)
        elif instance.workflow_status in [
            WorkflowStatusChoices.QUALITY_CHECK_PERFECT,
            WorkflowStatusChoices.QUALITY_CHECK_MINOR,
        ]:
            instance.add_to_public_query()
