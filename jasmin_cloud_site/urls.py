"""
Root URL configuration for the JASMIN Cloud API site.
"""

__author__ = "Matt Pryor"
__copyright__ = "Copyright 2020 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENSE file in top-level package directory"

from django.http import HttpResponse
from django.urls import include, path


def status(request):
    """
    Endpoint used for healthchecks.
    """
    # Just return 204 No Content
    return HttpResponse(status=204)


urlpatterns = [
    # Install a URL to use for health checks
    # We can't use any of the /api URLs as they either require authentication
    # or don't accept use of the GET method
    path("_status/", status, name="status"),
    path("api/", include("jasmin_cloud.urls", namespace="jasmin_cloud")),
]
