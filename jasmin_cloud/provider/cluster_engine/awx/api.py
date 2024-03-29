"""
Module containing helpers for interacting with the AWX API.
"""

import copy

import rackit
import requests


class ResourceManager(rackit.ResourceManager):
    """
    Default resource manager for all AWX resources.
    """

    def extract_list(self, response):
        json = response.json()
        return json["results"], json.get("next")


class Resource(rackit.Resource):
    """
    Base resource for all AWX resouces.
    """

    class Meta:
        manager_cls = ResourceManager


class Organisation(Resource):
    class Meta:
        endpoint = "/organizations/"


class CredentialType(Resource):
    class Meta:
        endpoint = "/credential_types/"


class Credential(Resource):
    class Meta:
        endpoint = "/credentials/"


class Role(Resource):
    class Meta:
        endpoint = "/roles/"


class Team(Resource):
    class Meta:
        endpoint = "/teams/"

    roles = rackit.NestedResource(Role)


class JobTemplate(Resource):
    class Meta:
        endpoint = "/job_templates/"
        cache_keys = ("name",)

    credentials = rackit.NestedResource(Credential)

    def launch(self, *args, **kwargs):
        return self._action("launch", *args, **kwargs)


class JobEvent(Resource):
    class Meta:
        endpoint = "/job_events/"


class Job(Resource):
    class Meta:
        endpoint = "/jobs/"

    job_events = rackit.NestedResource(JobEvent)


class InventoryManager(ResourceManager):
    def copy(self, resource_or_key, name):
        endpoint = self.prepare_url(resource_or_key, "copy")
        response = self.connection.api_post(endpoint, json=dict(name=name))
        return self.make_instance(self.extract_one(response))


class InventoryVariableData(rackit.UnmanagedResource):
    class Meta:
        endpoint = "/variable_data/"


class Inventory(Resource):
    class Meta:
        manager_cls = InventoryManager
        endpoint = "/inventories/"

    variable_data = rackit.NestedEndpoint(InventoryVariableData)

    def copy(self, name):
        return self._manager.copy(self, name)


class Connection(rackit.Connection):
    """
    Class for a connection to an AWX API server.
    """

    path_prefix = "/api/v2"

    organisations = rackit.RootResource(Organisation)
    credential_types = rackit.RootResource(CredentialType)
    credentials = rackit.RootResource(Credential)
    teams = rackit.RootResource(Team)
    job_templates = rackit.RootResource(JobTemplate)
    jobs = rackit.RootResource(Job)
    inventories = rackit.RootResource(Inventory)
    roles = rackit.RootResource(Role)
    job_events = rackit.RootResource(JobEvent)

    def __init__(self, url, username, password, verify_ssl=True):
        # Build the session to use basic auth for requests
        session = requests.Session()
        session.auth = requests.auth.HTTPBasicAuth(username, password)
        session.verify = verify_ssl
        super().__init__(url, session)
