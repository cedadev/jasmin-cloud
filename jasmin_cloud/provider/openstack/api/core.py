"""
Module containing helpers for interacting with the OpenStack API.
"""

import collections
import logging
import re
from urllib.parse import urlsplit
import json

import requests

import rackit


logger = logging.getLogger(__name__)


class AuthParams:
    """
    Builder object for setting authentication parameters.
    """
    def __init__(self, params = None):
        self.params = params or dict()

    def use_token(self, token):
        """
        Returns an auth object using the given token for authentication.
        """
        params = self.params.copy()
        params.update(identity = dict(methods = ['token'], token = dict(id = token)))
        return self.__class__(params)

    def use_password(self, domain, username, password):
        """
        Returns an auth object using the given domain, username and password
        for authentication.
        """
        params = self.params.copy()
        params.update(
            identity = dict(
                methods = ['password'],
                password = dict(
                    user = dict(
                        domain = dict(name = domain),
                        name = username,
                        password = password
                    )
                )
            )
        )
        return self.__class__(params)

    def use_project_id(self, project_id):
        """
        Returns an auth object scoped to the given project.
        """
        params = self.params.copy()
        params.update(scope = dict(project = dict(id = project_id)))
        return self.__class__(params)

    def as_dict(self):
        """
        Returns the auth parameters as a dict.
        """
        return self.params.copy()


class UnmanagedResourceOptions(rackit.resource.Options):
    def __init__(self, options = None):
        options = options or dict()
        endpoint = options.get('endpoint')
        if endpoint:
            if 'resource_key' not in options:
                options.update(
                    resource_key = endpoint.strip('/')
                )
        super().__init__(options)


class UnmanagedResource(rackit.UnmanagedResource):
    """
    Base class for unmanaged OpenStack resources.
    """
    class Meta:
        options_cls = UnmanagedResourceOptions

    def _fetch(self):
        # The data is under a key, which we need to extract
        return super()._fetch()[self._opts.resource_key]


class ResourceManager(rackit.ResourceManager):
    """
    Base class for an OpenStack resource manager.
    """
    def related_manager(self, resource_cls):
        # Modify related manager discovery to handle cross-service relationships
        resource_cls = self.related_resource(resource_cls)
        # Get the catalog type of the related resource
        catalog_type = resource_cls._connection_cls.catalog_type
        # Use the main connection to get the service for the resource
        service_name = catalog_type.replace('-', '_')
        service = getattr(self.connection.session.auth, service_name)
        # Then return the root manager for the resource class in that service
        root = service.root_manager(resource_cls)
        if root:
            return root
        else:
            raise RuntimeError('Unable to locate manager for embedded resource')

    def extract_list(self, response):
        # OpenStack responses have the list under a named key
        # If there is a next page, that is provided under a links attribute
        json = response.json()
        data = json[self.resource_cls._opts.resource_list_key]
        next_url = next(
            (
                link['href']
                for link in json.get(self.resource_cls._opts.resource_links_key, [])
                if link['rel'] == 'next'
            ),
            None
        )
        return data, next_url

    def extract_one(self, response):
        # Some OpenStack responses have the instance under a named key
        if self.resource_cls._opts.resource_key:
            return response.json()[self.resource_cls._opts.resource_key]
        else:
            return response.json()

    def prepare_params(self, params):
        # If there is a resource key, nest the parameters using it
        params = super().prepare_params(params)
        if self.resource_cls._opts.resource_key:
            return { self.resource_cls._opts.resource_key: params }
        else:
            return params


class ResourceWithDetailManager(ResourceManager):
    """
    Base class for a resource where lists can be fetched with or without detail.

    When a list is fetched without detail, partial entities will be returned.
    """
    def all(self, detail = True, **params):
        endpoint = self.prepare_url()
        if detail:
            endpoint = endpoint + '/detail'
        return self._fetch_all(endpoint, params, not detail)


class ResourceOptions(rackit.resource.Options):
    """
    Custom options class derives default options for OpenStack resources.
    """
    def __init__(self, options = None):
        options = options or dict()
        endpoint = options.get('endpoint')
        if endpoint:
            # Derive default values for response keys, if not given
            if 'resource_list_key' not in options:
                options.update(
                    resource_list_key = endpoint.strip('/')
                )
            if 'resource_links_key' not in options:
                options.update(
                    resource_links_key = '{}_links'.format(options['resource_list_key'])
                )
            if 'resource_key' not in options:
                options.update(
                    # By default, assume the list key ends with an 's' that we trim
                    resource_key = options['resource_list_key'][:-1]
                )
        super().__init__(options)


class Resource(rackit.Resource):
    """
    Base class for OpenStack resources.
    """
    class Meta:
        options_cls = ResourceOptions
        manager_cls = ResourceManager
        update_http_verb = 'put'


class ResourceWithDetail(Resource):
    """
    Base class for OpenStack resources that support a detail view.
    """
    class Meta:
        manager_cls = ResourceWithDetailManager


class AuthProject(Resource):
    """
    Resource for the projects for a user.

    Manipulation of projects more generally is available through the identity service.
    """
    class Meta:
        endpoint = '/auth/projects'
        resource_list_key = 'projects'


class Connection(rackit.Connection):
    """
    Class for a connection to an OpenStack API, which handles the authentication,
    project and service discovery elements.

    Can be used as an auth object for a requests session.
    """
    projects = rackit.RootResource(AuthProject)

    def __init__(self, auth_url, params, interface = 'public', verify = True):
        # Store the given parameters, as it is sometimes useful to be able to query them later
        self.auth_url = auth_url.rstrip('/')
        self.params = params
        self.interface = interface
        self.verify = verify

        # Configure the session
        session = requests.Session()
        # This object is the auth object for the session
        session.auth = self
        session.verify = verify

        # Once the superclass init is called, we can use the api_{} methods
        super().__init__(auth_url, session)

        # Attempt the authentication
        try:
            response = self.api_post('/auth/tokens', json = dict(auth = params.as_dict()))
        except rackit.ApiError:
            # If the authentication fails, make sure we close the session
            session.close()
            raise
        # Extract the token from the headers
        self.token = response.headers['X-Subject-Token']
        # Extract information from the response
        json = response.json()
        self.username = json['token']['user']['name']
        self.project_id = json['token'].get('project', {}).get('id')
        # Extract the endpoints from the catalog on the correct interface
        self.endpoints = {}
        for entry in json['token'].get('catalog', []):
            # Find the endpoint on the specified interface
            try:
                endpoint = next(
                    ep['url']
                    for ep in entry['endpoints']
                    if ep['interface'] == self.interface
                )
            except StopIteration:
                continue
            # Strip any path component from the endpoint
            self.endpoints[entry['type']] = urlsplit(endpoint)._replace(path = '').geturl()

    def __call__(self, request):
        # This is what allows the connection to be used as a requests auth
        # If there is a token, set the OpenStack auth token header
        try:
            request.headers['X-Auth-Token'] = self.token
        except AttributeError:
            pass
        return request

    def scoped_connection(self, project_or_id):
        """
        Return a new connection that is scoped to the given project.
        """
        # Extract the project id from a resource if required
        if isinstance(project_or_id, Resource):
            project_id = project_or_id.id
        else:
            project_id = project_or_id
        return Connection(
            self.auth_url,
            # Use token authentication with our token
            AuthParams().use_token(self.token).use_project_id(project_id),
            self.interface,
            self.verify
        )


class ServiceDescriptor(rackit.CachedProperty):
    """
    Property descriptor for attaching a :py:class:`Service` to a :py:class:`Connection`.

    The returned service instances are configured using the endpoints discovered from
    the service catalog.
    """
    def __init__(self, service_cls):
        self.service_cls = service_cls
        super().__init__(self.get_service)

    def get_service(self, instance):
        url = instance.endpoints[self.service_cls.catalog_type]
        return self.service_cls(url, instance.session)


class Service(rackit.Connection):
    """
    Base class for OpenStack service connections.
    """
    #: The name of the catalog type that this service is for
    #: This is used to retrieve the endpoint from the service catalog
    catalog_type = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # If the service has a catalog type, add it to the connection
        if cls.catalog_type:
            # If no explicit name is given, use the catalog type
            name = getattr(cls, 'name', cls.catalog_type.replace('-', '_'))
            descriptor = ServiceDescriptor(cls)
            setattr(Connection, name, descriptor)
            descriptor.__set_name__(Connection, name)

    def __init__(self, url, session):
        super().__init__(url, session)
        # Template the project id into the path prefix
        if self.path_prefix:
            # Template the project id into the path prefix
            project_id = session.auth.project_id
            self.path_prefix = self.path_prefix.format(project_id = project_id)

    def _find_message(self, obj):
        # Try to find a message property at any depth within the structure
        if isinstance(obj, dict):
            try:
                return obj['message']
            except KeyError:
                for item in obj.values():
                    message = self._find_message(item)
                    if message:
                        return message

    def extract_error_message(self, response):
        """
        Extract an error message from the given error response and return it.
        """
        # First, try to parse the response as JSON
        # If it fails, just use the response text
        try:
            json_obj = response.json()
        except json.decoder.JSONDecodeError:
            return response.text
        else:
            # Traverse the structure looking for a message property
            # Use the response text if not found
            return self._find_message(json_obj) or response.text
