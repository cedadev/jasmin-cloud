"""
Base definitions for the ``jasmin_cloud.keystore`` package.
"""

__author__ = "Matt Pryor"
__copyright__ = "Copyright 2020 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENSE file in top-level package directory"


class KeyStore:
    """
    Abstract base class for a key store.

    A key store allows the locating of an SSH public key for a username.
    """

    def get_key(self, username):
        """
        Returns the SSH public key for the given username.

        Args:
            username: The username to locate an SSH key for.

        Returns:
            The SSH public key as a string, or ``None`` if no key was found.
        """
        raise NotImplementedError()
