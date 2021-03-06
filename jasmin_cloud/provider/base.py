"""
This module defines the interface for a cloud provider.
"""

from . import dto, errors, validation


class Provider:
    """
    Class for a cloud provider.
    """
    def authenticate(self, username, password):
        """
        Creates a new unscoped session for this provider using the given credentials.

        Args:
            username: The username to authenticate with.
            password: The password to authenticate with.

        Returns:
            An :py:class:`UnscopedSession` for the user.
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def from_token(self, token):
        """
        Creates an unscoped session from the given token as returned from the
        ``token`` method of the corresponding :py:class:`UnscopedSession`.

        Args:
            token: The token to use.

        Returns:
            A :py:class:`UnscopedSession`.
        """
        raise NotImplementedError


class UnscopedSession:
    """
    Class for an authenticated session with a cloud provider. It is unscoped in
    the sense that is not bound to a particular tenancy.
    """
    def token(self):
        """
        Returns the token for this session.

        The returned token should be consumable by the ``from_token`` method of the
        corresponding :py:class:`Provider`.

        Returns:
            A string token.
        """
        raise NotImplementedError

    def username(self):
        """
        Returns the username for this session.

        Returns:
            A string username.
        """
        raise NotImplementedError

    def tenancies(self):
        """
        Get the tenancies available to the authenticated user.

        Returns:
            An iterable of :py:class:`~.dto.Tenancy` objects.
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def scoped_session(self, tenancy):
        """
        Get a scoped session for the given tenancy.

        Args:
            tenancy: The tenancy to get a scoped session for. Can be a tenancy id
                or a :py:class:`~.dto.Tenancy` object.

        Returns:
            A :py:class:`~ScopedSession` for the tenancy.
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def close(self):
        """
        Closes the session and performs any cleanup.
        """
        # This is a NOOP by default

    def __enter__(self):
        """
        Called when entering a context manager block.
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Called when exiting a context manager block. Ensures that close is called.
        """
        self.close()

    def __del__(self):
        """
        Ensures that close is called when the session is garbage collected.
        """
        self.close()


class ScopedSession:
    """
    Class for a tenancy-scoped session.
    """
    def quotas(self):
        """
        Returns quota information for the tenancy.

        Quota information for the following resources should always be present:

          * ``cpus``: The vCPUs available to the tenancy.
          * ``ram``: The RAM available to the tenancy.
          * ``external_ips``: The external IPs available to the tenancy.
          * ``storage``: The storage available to the tenancy.

        Some implementations may also include:

          * ``machines``: The number of machines in the tenancy.
          * ``volumes``: The number of volumes in the tenancy.

        The absence of these resources indicates that there is no specific limit.

        Returns:
            An iterable of :py:class:`~.dto.Quota` objects.
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def images(self):
        """
        Lists the images available to the tenancy.

        Returns:
            An iterable of :py:class:`~.dto.Image` objects.
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def find_image(self, id):
        """
        Finds an image by id.

        Args:
            id: The id of the image to find.

        Returns:
            An :py:class:`~.dto.Image` object.
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def sizes(self):
        """
        Lists the machine sizes available to the tenancy.

        Returns:
            An iterable of :py:class:`~.dto.Size` objects.
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def find_size(self, id):
        """
        Finds a size by id.

        Args:
            id: The id of the size to find.

        Returns:
            A :py:class:`~.dto.Size` object.
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def machines(self):
        """
        Lists the machines in the tenancy.

        Returns:
            An iterable of :py:class:`~.dto.Machine`\ s.
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def find_machine(self, id):
        """
        Finds a machine by id.

        Args:
            id: The id of the machine to find.

        Returns:
            A :py:class:`~.dto.Machine` object.
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def create_machine(self, name, image, size, ssh_key):
        """
        Create a new machine in the tenancy.

        Args:
            name: The name of the machine.
            image: The image to use. Can be an image id or a :py:class:`~.dto.Image`.
            size: The size to use. Can be a size id or a :py:class:`~.dto.Size`.
            ssh_key: The SSH key to inject into the machine.

        Returns:
            The created :py:class:`~.dto.Machine`.
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def resize_machine(self, machine, size):
        """
        Change the size of a machine.

        Args:
            machine: The machine. Can be a machine id or a :py:class:`~.dto.Machine`.
            size: The size to use. Can be a size id or a :py:class:`~.dto.Size`.

        Returns:
            The updated :py:class:`~.dto.Machine`.
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def start_machine(self, machine):
        """
        Start the specified machine.

        Args:
            machine: The machine. Can be a machine id or a :py:class:`~.dto.Machine`.

        Returns:
            The updated :py:class:`~.dto.Machine`.
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def stop_machine(self, machine):
        """
        Stop the specified machine.

        Args:
            machine: The machine. Can be a machine id or a :py:class:`~.dto.Machine`.

        Returns:
            The updated :py:class:`~.dto.Machine`.
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def restart_machine(self, machine):
        """
        Restart the specified machine.

        Args:
            machine: The machine. Can be a machine id or a :py:class:`~.dto.Machine`.

        Returns:
            The updated :py:class:`~.dto.Machine`.
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def delete_machine(self, machine):
        """
        Delete the specified machine.

        Args:
            machine: The machine. Can be a machine id or a :py:class:`~.dto.Machine`.

        Returns:
            The updated :py:class:`~.dto.Machine` if it has transitioned to a
            deleting status, or ``None`` if it has already been deleted.
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def external_ips(self):
        """
        Returns the external IP addresses that are currently allocated to the
        tenancy.

        Returns:
            An iterable of :py:class:`~.dto.ExternalIp`\ s.
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def find_external_ip(self, ip):
        """
        Finds external IP details by IP address.

        Returns:
            A :py:class:`~.dto.ExternalIp` object.
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def allocate_external_ip(self):
        """
        Allocates a new external IP address for the tenancy from a pool and returns
        it.

        Returns:
            The allocated :py:class:`~.dto.ExternalIp` (should raise on failure).
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def attach_external_ip(self, ip, machine):
        """
        Attaches an external IP to a machine.

        Args:
            ip: The IP address to attach. Can be an external IP address as a string
                or a :py:class:`~.dto.ExternalIp`.
            machine: The machine. Can be a machine id or a :py:class:`~.dto.Machine`.

        Returns:
            The updated :py:class:`~.dto.ExternalIp` object (should raise on failure).
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def detach_external_ip(self, ip):
        """
        Detaches the given external IP from whichever machine it is currently
        attached to.

        Args:
            ip: The IP address to detach. Can be an external IP address as a string
                or a :py:class:`~.dto.ExternalIp`.

        Returns:
            The updated :py:class:`~.dto.ExternalIp` object (should raise on failure).
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def volumes(self):
        """
        Lists the volumes currently available to the tenancy.

        Returns:
            An iterable of :py:class:`~.dto.Volume`\ s.
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def find_volume(self, id):
        """
        Finds a volume by id.

        Args:
            id: The id of the volume to find.

        Returns:
            A :py:class:`~.dto.Volume` object.
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def create_volume(self, name, size):
        """
        Create a new volume in the tenancy.

        Args:
            name: The name of the volume.
            size: The size of the volume in GB.

        Returns:
            A :py:class:`~.dto.Volume` object.
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def delete_volume(self, volume):
        """
        Delete the specified volume.

        Args:
            volume: The volume to delete. Can be a volume id or a :py:class:`~.dto.Volume`.

        Returns:
            The updated :py:class:`~.dto.Volume` if it has transitioned to a
            deleting status, or ``None`` if it has already been deleted.
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def attach_volume(self, volume, machine):
        """
        Attaches the specified volume to the specified machine.

        Args:
            volume: The volume to attach. Can be a volume id or a :py:class:`~.dto.Volume`.
            machine: The machine. Can be a machine id or a :py:class:`~.dto.Machine`.

        Returns:
            The updated :py:class:`~.dto.Volume`.
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def detach_volume(self, volume):
        """
        Detaches the specified volume from the machine it is attached to.

        Args:
            volume: The volume to detach. Can be a volume id or a :py:class:`~.dto.Volume`.

        Returns:
            The updated :py:class:`~.dto.Volume`.
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def cluster_types(self):
        """
        Lists the available cluster types.

        Returns:
            An iterable of :py:class:`~.dto.ClusterType`s.
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def find_cluster_type(self, name):
        """
        Find a cluster type by name.

        Args:
            name: The name of the cluster type.

        Returns:
            A :py:class:`~.dto.ClusterType`.
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def clusters(self):
        """
        List the clusters that are deployed.

        Returns:
            An iterable of :py:class:`~.dto.Cluster`s.
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def find_cluster(self, id):
        """
        Find a cluster by id.

        Args:
            id: The id of the cluster.

        Returns:
            A :py:class:`~.dto.Cluster`.
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def validate_cluster_params(self, cluster_type, params, prev_params = {}):
        """
        Validates the given parameter values against the given cluster type.

        Args:
            cluster_type: The cluster type to validate against.
                          Can be a name or a :py:class:`~.dto.ClusterType`.
            params: Dictionary of parameters to validate.
            prev_params: The previous parameters if applicable.
                         Used to validate immutability constraints.

        Returns:
            The validated parameters.

        Raises:
            If validation fails, a :py:class:`~.errors.ValidationError` is raised.
        """
        if not isinstance(cluster_type, dto.ClusterType):
            cluster_type = self.find_cluster_type(cluster_type)
        validator = validation.build_validator(
            self,
            cluster_type.parameters,
            prev_params
        )
        return validator(params)

    def create_cluster(self, name, cluster_type, params, ssh_key):
        """
        Creates a new cluster with the given name, type and parameters.

        Args:
            name: The name of the cluster.
            cluster_type: The cluster type.
                          Can be a name or a :py:class:`~.dto.ClusterType`.
            params: Dictionary of parameter values as required by the
                    cluster type.
            ssh_key: The SSH public key for access to cluster nodes.

        Returns:
            A :py:class:`~.dto.Cluster`.
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def update_cluster(self, cluster, params):
        """
        Updates an existing cluster with the given parameters.

        Args:
            cluster: The cluster to update.
                     Can be an id or a :py:class:`~.dto.Cluster`.
            params: Dictionary of parameters values as required by the
                    cluster type.

        Returns:
            The updated :py:class:`~.dto.Cluster`.
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def patch_cluster(self, cluster):
        """
        Patches an existing cluster.

        Args:
            cluster: The cluster to update.
                     Can be an id or a :py:class:`~.dto.Cluster`.

        Returns:
            The :py:class:`~.dto.Cluster` being patched.
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def delete_cluster(self, cluster):
        """
        Deletes an existing cluster.

        Args:
            cluster: The cluster to update.
                     Can be an id or a :py:class:`~.dto.Cluster`.

        Returns:
            The deleted :py:class:`~.dto.Cluster`.
        """
        raise errors.UnsupportedOperationError(
            "Operation not supported for provider '{}'".format(self.provider_name)
        )

    def close(self):
        """
        Closes the session and performs any cleanup.
        """
        # This is a NOOP by default

    def __enter__(self):
        """
        Called when entering a context manager block.
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Called when exiting a context manager block. Ensures that close is called.
        """
        self.close()

    def __del__(self):
        """
        Ensures that close is called when the session is garbage collected.
        """
        self.close()
