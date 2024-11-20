"""
the ej_dump is generated by running create_ej_dump.py and is scp'd to the COSMOS server
this script is then run via the dm shell on the COSMOS server to populate the database
"""

import json
import urllib.parse

from environmental_justice.models import EnvironmentalJusticeRow


def generate_source_link(doi_field):
    authority = doi_field.get("Authority")
    doi = doi_field.get("DOI")
    if authority and doi:
        return urllib.parse.urljoin(authority, doi)
    return ""


def concept_id_to_sinequa_id(concept_id: str) -> str:
    return f"/SDE/CMR_API/|{concept_id}"


def sinequa_id_to_url(sinequa_id: str) -> str:
    base_url = "https://sciencediscoveryengine.nasa.gov/app/nasa-sba-smd/#/preview"
    query = '{"name":"query-smd-primary","scope":"All","text":""}'

    encoded_id = urllib.parse.quote(sinequa_id, safe="")
    encoded_query = urllib.parse.quote(query, safe="")

    return f"{base_url}?id={encoded_id}&query={encoded_query}"


def categorize_processing_level(level):
    advanced_analysis_levels = {"0", "Level 0", "NA", "Not Provided", "Not provided"}

    basic_analysis_levels = {
        "1",
        "1A",
        "1B",
        "1C",
        "1T",
        "2",
        "2A",
        "2B",
        "2G",
        "2P",
        "Level 1",
        "Level 1A",
        "Level 1B",
        "Level 1C",
        "Level 2",
        "Level 2A",
        "Level 2B",
    }

    exploration_levels = {"3", "4", "Level 3", "Level 4", "L2"}

    if level in exploration_levels:
        return "exploration"
    elif level in basic_analysis_levels:
        return "basic analysis"
    elif level in advanced_analysis_levels:
        return "advanced analysis"
    else:
        return "advanced analysis"


# remove existing data
EnvironmentalJusticeRow.objects.filter(destination_server=EnvironmentalJusticeRow.DestinationServerChoices.DEV).delete()

ej_dump = json.load(open("backups/ej_dump_20241017_133151.json.json"))
for dataset in ej_dump:
    ej_row = EnvironmentalJusticeRow(
        destination_server=EnvironmentalJusticeRow.DestinationServerChoices.DEV,
        sde_link=sinequa_id_to_url(concept_id_to_sinequa_id(dataset.get("meta", {}).get("concept-id", ""))),
        dataset=dataset.get("umm", {}).get("ShortName", ""),
        description=dataset.get("umm", {}).get("Abstract", ""),
        limitations=dataset.get("umm", {}).get("AccessConstraints", {}).get("Description", ""),
        format=dataset.get("meta", {}).get("format", ""),
        temporal_extent=", ".join(dataset.get("umm", {}).get("TemporalExtents", [{}])[0].get("SingleDateTimes", [])),
        intended_use=categorize_processing_level(
            dataset.get("umm", {}).get("ProcessingLevel", {}).get("Id", "advanced analysis")
        ),
        source_link=generate_source_link(dataset.get("umm", {}).get("DOI", {})),
        indicators=dataset["indicators"],
        geographic_coverage="",  # Not provided in the data
        data_visualization="",  # dataset.get("umm", {}).get("RelatedUrls", [{}])[0].get("URL", ""),
        latency="",  # Not provided in the data
        spatial_resolution="",  # Not provided in the data
        temporal_resolution="",  # Not provided in the data
        description_simplified="",  # Not provided in the data
        project="",  # Not provided in the data
        strengths="",  # Not provided in the data
    )
    ej_row.save()
