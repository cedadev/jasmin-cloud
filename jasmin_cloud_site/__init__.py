__author__ = "Matt Pryor"
__copyright__ = "Copyright 2020 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENSE file in top-level package directory"

from pkg_resources import DistributionNotFound, get_distribution

try:
    __version__ = get_distribution("jasmin-cloud").version
except DistributionNotFound:
    # package is not installed
    pass
