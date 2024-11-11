import json
from typing import Any

import requests
import urllib3
from django.conf import settings

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

server_configs = {
    "dev": {
        "app_name": "nasa-sba-smd",
        "query_name": "query-smd-primary",
        "base_url": "http://sde-renaissance.nasa-impact.net",
    },
    "test": {
        "app_name": "nasa-sba-smd",
        "query_name": "query-smd-primary",
        "base_url": "https://sciencediscoveryengine.test.nasa.gov",
    },
    "production": {
        "app_name": "nasa-sba-smd",
        "query_name": "query-smd-primary",
        "base_url": "https://sciencediscoveryengine.nasa.gov",
    },
    "secret_test": {
        "app_name": "nasa-sba-sde",
        "query_name": "query-sde-primary",
        "base_url": "https://sciencediscoveryengine.test.nasa.gov",
    },
    "secret_production": {
        "app_name": "nasa-sba-sde",
        "query_name": "query-sde-primary",
        "base_url": "https://sciencediscoveryengine.nasa.gov",
    },
    "xli": {
        "app_name": "nasa-sba-smd",
        "query_name": "query-smd-primary",
        "base_url": "http://sde-xli.nasa-impact.net",
    },
    "lrm_dev": {
        "app_name": "sde-init-check",
        "query_name": "query-init-check",
        "base_url": "https://sde-lrm.nasa-impact.net",
    },
    "lrm_qa": {
        "app_name": "sde-init-check",
        "query_name": "query-init-check",
        "base_url": "https://sde-qa.nasa-impact.net",
    },
}


class Api:
    def __init__(self, server_name: str) -> None:
        self.server_name = server_name
        config = server_configs[server_name]
        self.app_name: str = config["app_name"]
        self.query_name: str = config["query_name"]
        self.base_url: str = config["base_url"]
        self.user = getattr(settings, f"{server_name}_USER".upper(), None)
        self.password = getattr(settings, f"{server_name}_PASSWORD".upper(), None)
        self.token = getattr(settings, f"{server_name}_TOKEN".upper(), None)

    def process_response(self, url: str, payload: dict[str, Any]) -> Any:
        response = requests.post(url, headers={}, json=payload, verify=False)

        if response.status_code == requests.status_codes.codes.ok:
            meaningful_response = response.json()
        else:
            raise Exception(response.text)

        return meaningful_response

    def query(self, page: int, collection_config_folder: str = "") -> Any:
        if self.server_name:
            url = f"{self.base_url}/api/v1/search.query?Password={self.password}&User={self.user}"
        else:
            url = f"{self.base_url}/api/v1/search.query"
        payload = {
            "app": self.app_name,
            "query": {
                "name": self.query_name,
                "text": "",
                "page": page,
                "pageSize": 1000,
                "advanced": {},
            },
        }

        if collection_config_folder:
            if self.server_name in ["xli", "lrm_dev", "lrm_qa"]:
                payload["query"]["advanced"]["collection"] = f"/scrapers/{collection_config_folder}/"
            else:
                payload["query"]["advanced"]["collection"] = f"/SDE/{collection_config_folder}/"

        response = self.process_response(url, payload)

        return response

    def sql_query(self, sql: str) -> Any:
        """Executes an SQL query on the configured server using token-based authentication."""
        if not self.token:
            raise ValueError("You must have a token to use the SQL endpoint")

        url = f"{self.base_url}/api/v1/engine.sql"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.token}"}
        payload = json.dumps(
            {
                "method": "engine.sql",
                "sql": sql,
                "pretty": True,
                "log": False,
                "output": "json",
                "resolveIndexList": "false",
                "engines": "default",
            }
        )
        try:
            response = requests.post(url, headers=headers, data=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")

    def get_full_texts(self, collection_config_folder: str) -> Any:
        sql = f"SELECT url1, text, title FROM sde_index WHERE collection = '/SDE/{collection_config_folder}/'"
        return self.sql_query(sql)
