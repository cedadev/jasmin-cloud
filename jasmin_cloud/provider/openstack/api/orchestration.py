"""
Module containing service and resource definitions for the OpenStack image API.
"""

__author__ = "Matt Pryor"
__copyright__ = "Copyright 2020 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENSE file in top-level package directory"

from rackit import RootResource

from .core import Resource, Service


class Stack(Resource):
    """
    Resource for accessing stacks.
    """

    class Meta:
        endpoint = "/stacks"


class OrchestrationService(Service):
    """
    OpenStack service class for the orchestration service.
    """

    catalog_type = "orchestration"
    path_prefix = "/v1/{project_id}"

    stacks = RootResource(Stack)
