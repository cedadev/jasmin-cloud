"""
Module containing service and resource definitions for the OpenStack image API.
"""

from rackit import RootResource

from .core import Resource, Service


class Image(Resource):
    """
    Resource for accessing images.
    """

    class Meta:
        endpoint = "/images"
        # The image service returns the image data directly when fetching by id
        resource_key = None


class ImageService(Service):
    """
    OpenStack service class for the image service.
    """

    catalog_type = "image"
    path_prefix = "/v2"

    images = RootResource(Image)
