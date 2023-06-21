import xml.etree.ElementTree as ET

import xmltodict


class XmlEditor:
    """
    Class is instantiated with a path to an xml.
    An internal etree is generated, and changes are made in place.
    An ouput path is given and the etree is saved to it.
    """

    def __init__(self, xml_string: str):
        self.xml_tree = self._get_tree(xml_string)

    def _get_tree(self, xml_string) -> ET.ElementTree:
        """takes the path of an xml file and opens it as an ElementTree object"""
        return ET.ElementTree(ET.fromstring(xml_string))

    def get_tag_value(self, tag_name: str) -> list:
        """
        tag_name can be either the top level tag
        or you can get a child by saying 'parent/child'
        """
        return [element.text for element in self.xml_tree.findall(tag_name)]

    def _add_declaration(self, xml_string: str):
        """adds xml declaration to xml string"""
        declaration = """<?xml version="1.0" encoding="utf-8"?>\n"""

        return declaration + xml_string

    def update_config_xml(self):
        xml_string = ET.tostring(
            self.xml_tree.getroot(),
            encoding="utf8",
            method="html",
            xml_declaration=True,
        )
        xml_string = xml_string.decode("utf-8")

        xml_string = self._add_declaration(xml_string)
        xml_string = self._resave_pretty(xml_string)

        return xml_string

    def _resave_pretty(self, xml_string):
        """opens and resaves a file to reformat it"""

        xml = xmltodict.parse(xml_string)
        return xmltodict.unparse(xml, pretty=True)

    def update_or_add_element_value(
        self,
        element_name: str,
        element_value: str,
        parent_element_name: str = None,
    ) -> None:
        """can update the value of either a top level or secondary level value in the sinequa config

        Args:
            element_name (str): name of the sinequa element, such as "Simulate"
            element_value (str): value to be stored to element, such as "false"
            parent_element_name (str, optional): parent of the element, such as "IndexerClient"
               Defaults to None.
        """

        xml_root = self.xml_tree.getroot()
        parent_element = (
            xml_root
            if parent_element_name is None
            else xml_root.find(parent_element_name)
        )

        existing_element = parent_element.find(element_name)
        if existing_element is not None:
            existing_element.text = element_value
        else:
            ET.SubElement(parent_element, element_name).text = element_value

    def convert_indexer_to_scraper(self) -> None:
        """
        assuming this class has been instantiated with a previously constructed indexer config
        some values must now be modified so it will be an effective scraper
        """
        self.update_or_add_element_value("Indexers", "")
        self.update_or_add_element_value(
            "Plugin", "SMD_Plugins/Sinequa.Plugin.ListCandidateUrls"
        )
        self.update_or_add_element_value("ShardIndexes", "")
        self.update_or_add_element_value("ShardingStrategy", "")
        self.update_or_add_element_value("WorkerCount", "8")
        self.update_or_add_element_value("LogLevel", "0", parent_element_name="System")
        self.update_or_add_element_value(
            "Simulate", "true", parent_element_name="IndexerClient"
        )

    def convert_scraper_to_indexer(self) -> None:
        # this is specialized for the production instance right now
        self.update_or_add_element_value("Indexers", "")
        self.update_or_add_element_value("Plugin", "")
        self.update_or_add_element_value(
            "Identity", "NodeIndexer1/identity0"
        )  # maybe make this blank?
        self.update_or_add_element_value("ShardIndexes", "")
        self.update_or_add_element_value("ShardingStrategy", "")
        self.update_or_add_element_value("WorkerCount", "8")
        self.update_or_add_element_value("LogLevel", "20", parent_element_name="System")
        self.update_or_add_element_value(
            "Simulate", "false", parent_element_name="IndexerClient"
        )

    def convert_template_to_scraper(self, url: str) -> None:
        """
        assuming this class has been instantiated with the scraper_template.xml
        the only remaining step is to add the base url to be scraped
        """
        self.update_or_add_element_value("Url", url)

    def _mapping_exists(self, new_mapping: ET.Element):
        """
        Check if the mapping with given parameters already exists in the XML tree
        """
        xml_root = self.xml_tree.getroot()

        for mapping in xml_root.findall("Mapping"):
            existing_mapping = {
                child.tag: (child.text if child.text is not None else "")
                for child in mapping
            }
            new_mapping_dict = {
                child.tag: (child.text if child.text is not None else "")
                for child in new_mapping
            }
            if existing_mapping == new_mapping_dict:
                return True

        return False

    def _standardize_selection(selection):
        """
        some existing selections may use double quotes while new ones need to use single quotes
        # prior rule generations were not as selective, so some old selections used a trailing *
        #     while the new selection will not
        this function creates two selections that will match against the old format and allow it to
            be replaced by the _generic_mapping function
        """
        standardized_quotes = selection.replace('"', "'")
        # standardized_quotes_less_selective = standardized_quotes.replace(
        #     "*'</Selection>", "'</Selection>"
        # )

        return list(
            set(selection, standardized_quotes)  # , standardized_quotes_less_selective)
        )

    def _generic_mapping(
        self,
        name: str = "",
        description: str = "",
        value: str = "",
        selection: str = "",
    ):
        """
        most mappings take the same fields, so this gives a generic way to make a mapping
        """
        xml_root = self.xml_tree.getroot()

        existing_mapping = None
        for mapping in xml_root.findall("Mapping"):
            if mapping.find("Name").text == name and mapping.find(
                "Selection"
            ).text in self._standardize_selection(selection):
                existing_mapping = mapping
                break

        if existing_mapping is not None:
            # If an existing mapping is found, overwrite its values
            existing_mapping.find("Value").text = value
        else:
            # If no existing mapping is found, create a new one
            mapping = ET.Element("Mapping")
            ET.SubElement(mapping, "Name").text = name
            ET.SubElement(mapping, "Description").text = description
            ET.SubElement(mapping, "Value").text = value
            ET.SubElement(mapping, "Selection").text = selection
            ET.SubElement(mapping, "DefaultValue").text = ""
            xml_root.append(mapping)

    def add_document_type_mapping(
        self, document_type: str, criteria: str
    ) -> ET.ElementTree:
        self._generic_mapping(
            name="sourcestr56",
            value=f'"{document_type}"',
            selection=f"doc.url1 match '{criteria}'",
        )

    def add_title_mapping(
        self, title_value: str, title_criteria: str
    ) -> ET.ElementTree:
        title_criteria = title_criteria.rstrip("/")
        sinequa_code_markers = ["xpath", "Concat", "IfEmpty", "doc.title", "doc.url1"]
        if not any(marker in title_value for marker in sinequa_code_markers):
            # exact title replacements need quotes
            # sinequa code needs to NOT have quotes
            title_value = f'"{title_value}"'

        self._generic_mapping(
            name="title",
            value=title_value,
            selection=f"doc.url1 match '{title_criteria}'",
        )

    def add_job_list_item(self, job_name):
        """
        this is specifically for editing joblist templates by adding a new collection to a joblist
        config_generation/xmls/joblist_template.xml
        """
        xml_root = self.xml_tree.getroot()

        mapping = ET.Element("JobListItem")
        ET.SubElement(mapping, "Name").text = job_name
        ET.SubElement(mapping, "StopOnError").text = "false"
        xml_root.append(mapping)

    def add_id(self) -> None:
        self._generic_mapping(
            name="id",
            value="doc.url1",
        )

    def add_document_type(self, document_type: str) -> None:
        self._generic_mapping(
            name="sourcestr56",
            value=f'"{document_type}"',
        )

    def add_xpath_indexing_filter(self, xpath: str, selection: str = "") -> None:
        # TODO: take in selection as an arg
        """filters out the content of an xpath from being indexed along with the document"""

        xml_root = self.xml_tree.getroot()

        mapping = ET.Element("IndexingFilter")
        ET.SubElement(mapping, "XPath").text = xpath
        ET.SubElement(mapping, "IncludeMode").text = "false"
        ET.SubElement(mapping, "Selection").text = selection
        xml_root.append(mapping)

    def add_url_exclude(self, url_pattern: str) -> None:
        """
        excludes a url or url pattern, such as
        - https://webb.nasa.gov/content/forEducators/realworld*
        - https://webb.nasa.gov/content/features/index.html
        - *.rtf
        """

        xml_root = self.xml_tree.getroot()

        for url_index_excluded in xml_root.findall("UrlIndexExcluded"):
            if url_index_excluded.text == url_pattern:
                return  # stop the function if the url pattern already exists

        # add the url pattern if it doesn't already exist
        ET.SubElement(xml_root, "UrlIndexExcluded").text = url_pattern

    def add_url_include(self, url_pattern: str) -> None:
        """
        includes a url or url pattern, such as
        - https://webb.nasa.gov/content/forEducators/realworld*
        - https://webb.nasa.gov/content/features/index.html
        I'm not sure if exclusion rules override includes or if includes override
        exclusion rules.
        """

        xml_root = self.xml_tree.getroot()
        ET.SubElement(
            xml_root, "UrlIndexIncluded"
        ).text = url_pattern  # this adds an indexing rule (doesn't overwrite)
