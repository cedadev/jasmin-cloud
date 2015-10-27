"""
This module contains Pyramid view callables for the JASMIN cloud portal.
"""

__author__ = "Matt Pryor"
__copyright__ = "Copyright 2015 UK Science and Technology Facilities Council"

import bleach, markdown

from pyramid.view import view_config, forbidden_view_config, notfound_view_config
from pyramid.security import remember, forget
from pyramid.session import check_csrf_token
from pyramid.httpexceptions import HTTPSeeOther, HTTPNotFound, HTTPBadRequest

from . import cloudservices
from .cloudservices.vcloud import VCloudProvider
from .util import validate_ssh_key


################################################################################
## Exception views
##
##   Executed if an exception occurs during regular view handling
################################################################################

def _exception_redirect(request):
    """
    Returns a redirect to the most specific page accessible to the current user:
    
      * Current org machines page if user is logged in and belongs to org in URL
      * Dashboard if user is logged in but doesn't belong to org in URL
      * Login page if user is not logged in
    """
    if request.authenticated_user:
        user_orgs = request.memberships.orgs_for_user(request.authenticated_user.username)
        if request.current_org and (request.current_org in user_orgs):
            return HTTPSeeOther(location = request.route_path('machines'))
        else:
            return HTTPSeeOther(location = request.route_path('dashboard'))
    else:
        return HTTPSeeOther(location = request.route_path('login'))
    

@forbidden_view_config()
def forbidden(request):
    """
    Handler for 403 forbidden errors.
    
    Shows a suitable error on the most specific page possible.
    """
    if request.authenticated_user:
        request.session.flash('Insufficient permissions', 'error')
    else:
        request.session.flash('Log in to access this resource', 'error')
    return _exception_redirect(request)


@notfound_view_config()
def notfound(request):
    """
    Handler for 404 not found errors.
    
    Shows a suitable error on the most specific page possible.
    """
    request.session.flash('Resource not found', 'error')
    return _exception_redirect(request)


@view_config(context = cloudservices.CloudServiceError)
def cloud_service_error(context, request):
    """
    Handler for cloud service errors.
    
    Shows a suitable error on the most specific page possible.
    """
    # Convert some cloud service errors into their HTTP equivalents
    if isinstance(context, (cloudservices.AuthenticationError,
                            cloudservices.PermissionsError)):
        return forbidden(request)
    if isinstance(context, cloudservices.NoSuchResourceError):
        return notfound(request)
    # For other cloud service errors, just add their text to the error flash
    # and redirect
    request.session.flash(str(context), 'error')
    return _exception_redirect(request)


################################################################################
## Regular views
##
##   Executed when the request matches a route
################################################################################

@view_config(route_name = 'home',
             request_method = 'GET',
             renderer = 'templates/home.jinja2')
def home(request):
    """
    Handler for GET requests to ``/``.
    
    If the user is logged in, redirect to the dashboard, otherwise show a splash page.
    """
    if request.authenticated_user:
        return HTTPSeeOther(location = request.route_url('dashboard'))
    return {}


@view_config(route_name = 'login',
             request_method = ('GET', 'POST'),
             renderer = 'templates/login.jinja2')
def login(request):
    """
    Handler for ``/login``.
    
    GET request
        Show a login form.
        
    POST request
        Attempt to authenticate the user.
        
        If authentication is successful, try to start a vCloud Director session
        for each organisation that the user belongs to. Login is only considered
        successful if we successfully obtain a session for every organisation.
        
        Redirect to the dashboard on success, otherwise show the login form with
        errors.
    """
    if request.method == 'POST':
        # When we get a POST request, clear any existing cloud sessions
        request.cloud_sessions.clear()
        # Try to authenticate the user
        username = request.params['username']
        password = request.params['password']
        if request.users.authenticate(username, password):
            # Try to create a session for each of the user's orgs
            # If any of them fail, bail with the error message
            try:
                provider = VCloudProvider(request.registry.settings['vcloud.endpoint'])
                for org in request.memberships.orgs_for_user(username):
                    session = provider.new_session('{}@{}'.format(username, org), password)
                    request.cloud_sessions[org] = session
            except cloudservices.CloudServiceError as e:
                request.cloud_sessions.clear()
                request.session.flash(str(e), 'error')
                return {}
            # When a user logs in successfully, force a refresh of the CSRF token
            request.session.new_csrf_token()
            return HTTPSeeOther(location = request.route_url('dashboard'),
                                headers  = remember(request, username))
        else:
            request.session.flash('Invalid credentials', 'error')
    return {}
            

@view_config(route_name = 'logout')
def logout(request):
    """
    Handler for ``/logout``.
    
    If the user is logged in, forget them and redirect to splash page.
    """
    request.cloud_sessions.clear()
    request.session.flash('Logged out successfully', 'success')
    return HTTPSeeOther(location = request.route_url('home'),
                        headers = forget(request))
    
    
@view_config(route_name = 'dashboard',
             request_method = 'GET',
             renderer = 'templates/dashboard.jinja2', permission = 'view')
def dashboard(request):
    """
    Handler for GET requests to ``/dashboard``.
    
    The user must be authenticated to reach here, which means that there should be
    a cloud session for each organisation that the user belongs to.
    
    Shows a list of organisations available to the user with the number of
    machines in each.
    """
    # Pass the per-org counts to the template
    return {
        'machine_counts' : {
            org : sess.count_machines() for org, sess in request.cloud_sessions.items()
        }
    }
    

@view_config(route_name = 'org_home', request_method = 'GET', permission = 'org_view')
def org_home(request):
    """
    Handler for GET requests to ``/{org}``.
    
    The user must be authenticated for the organisation in the URL to reach here.
    
    Just redirect the user to ``/{org}/machines``.
    """
    return HTTPSeeOther(location = request.route_url('machines'))


@view_config(route_name = 'users',
             request_method = 'GET',
             renderer = 'templates/users.jinja2', permission = 'org_view')
def users(request):
    """
    Handler for GET requests to ``/{org}/users``.
    
    The user must be authenticated for the organisation in the URL to reach here.
    
    Show the users belonging to the organisation in the URL.
    """
    # Get the users for the org
    member_ids = request.memberships.members_for_org(request.current_org)
    # Convert the usernames to user objects
    return { 'users' : [request.users.find_by_username(uid) for uid in member_ids] }

   
@view_config(route_name = 'catalogue',
             request_method = 'GET',
             renderer = 'templates/catalogue.jinja2', permission = 'org_view')
def catalogue(request):
    """
    Handler for GET requests to ``/{org}/catalogue``.
    
    The user must be authenticated for the organisation in the URL to reach here.
    
    Show the catalogue items available to the organisation in the URL.
    """
    # Get the available catalogue items
    return { 'items' : request.catalogue.available_items() }


@view_config(route_name = 'catalogue_new',
             request_method = ('GET', 'POST'),
             renderer = 'templates/catalogue_new.jinja2', permission = 'org_edit')
def catalogue_new(request):
    """
    Handler for ``/{org}/catalogue/new/{id}``
    
    The user must be authenticated for the organisation in the URL to reach here.
    
    ``{id}`` is the uuid of the machine to use as a template.
    
    GET request
        Show a form to gather information required to create a new catalogue item.
        
    POST request
        Attempt to create a new catalogue item using the provided information.
        
        On success, redirect the user to ``/{org}/catalogue`` with a success message.
        
        On a duplicate name error, show the form with an error message.        
    """
    # Get the cloud session for the current org
    cloud_session = request.cloud_sessions[request.current_org]
    # Get the machine details from the id
    machine = cloud_session.get_machine(request.matchdict['id'])
    # On a POST request, we must try to create the catalogue item
    if request.method == 'POST':
        # All POST requests need a csrf token
        check_csrf_token(request)
        item_info = {
            'name'          : request.params.get('name', ''),
            'description'   : request.params.get('description', ''),
            'allow_inbound' : request.params.get('allow_inbound', 'false'),
        }
        # Convert markdown in the description and sanitize the result using the
        # default, conservative set of allowed tags and attributes
        description = bleach.clean(
            markdown.markdown(item_info['description']), strip = True,
            tags = bleach.ALLOWED_TAGS + ['p', 'span', 'div'],
            attributes = dict(bleach.ALLOWED_ATTRIBUTES, **{ '*' : 'class' }),
        )
        try:
            # Create the catalogue item
            request.catalogue.item_from_machine(
                machine, item_info['name'],
                description, item_info['allow_inbound'] == "true"
            )
            request.session.flash('Catalogue item created successfully', 'success')
        except cloudservices.DuplicateNameError:
            request.session.flash('There are errors with one or more fields', 'error')
            return {
                'machine' : machine,
                'item'    : item_info,
                'errors'  : { 'name' : ['Catalogue item name is already in use'] }
            }
        # If creating the catalogue item is successful, try to delete the machine
        try:
            cloud_session.delete_machine(machine.id)
        except cloudservices.CloudServiceError as e:
            request.session.flash('Error deleting machine: {}'.format(e), 'error')
        return HTTPSeeOther(location = request.route_url('catalogue'))
    # Only a get request should get this far
    return {
        'machine'       : machine,
        'item' : {
            'name'          : '',
            'description'   : '',
            'allow_inbound' : 'false'
        },
        'errors' : {}
    }
    
    
@view_config(route_name = 'catalogue_delete',
             request_method = 'POST', permission = 'org_edit')
def catalogue_delete(request):
    """
    Handler for ``/{org}/catalogue/delete/{id}``
    
    The user must be authenticated for the organisation in the URL to reach here.
    
    Attempts to delete a catalogue item and redirects to the catalogue page with
    a success message.
    
    ``{id}`` is the id of the catalogue item to delete.    
    """
    # Request must pass a CSRF test
    check_csrf_token(request)
    request.catalogue.delete_item_with_id(request.matchdict['id'])
    request.session.flash('Catalogue item deleted', 'success')
    return HTTPSeeOther(location = request.route_url('catalogue'))


@view_config(route_name = 'machines',
             request_method = 'GET',
             renderer = 'templates/machines.jinja2', permission = 'org_view')
def machines(request):
    """
    Handler for GET requests to ``/{org}/machines``.
    
    The user must be authenticated for the organisation in the URL to reach here.
    
    Show the machines available to the organisation in the URL.
    """
    cloud_session = request.cloud_sessions[request.current_org]
    return { 'machines'  : cloud_session.list_machines() }


@view_config(route_name = 'new_machine',
             request_method = ('GET', 'POST'),
             renderer = 'templates/new_machine.jinja2', permission = 'org_edit')
def new_machine(request):
    """
    Handler for ``/{org}/machine/new/{id}``.
    
    The user must be authenticated for the organisation in the URL to reach here.
    
    ``{id}`` is the id of the catalogue item to use for the new machine.
    
    GET request
        Show a form to gather information required for provisioning.
         
    POST request
        Attempt to provision a machine with the given details.
        
        If the provisioning is successful, redirect the user to ``/{org}/machines``
        with a success message.
        
        If the provisioning is successful but NATing fails, redirect the user to
        ``/{org}/machines`` with an error message.
        
        If the provisioning fails completely, show the form with an error message.
    """
    # Try to load the catalogue item
    item = request.catalogue.find_item_by_id(request.matchdict['id'])
    if not item:
        raise HTTPNotFound()
    # If we have a POST request, try and provision a machine with the info
    if request.method == 'POST':
        # For a POST request, the request must pass a CSRF test
        check_csrf_token(request)
        template_info = {
            'template'    : item,
            'name'        : request.params.get('name', ''),
            'description' : request.params.get('description', ''),
            'ssh_key'     : request.params.get('ssh_key', ''),
            'errors'      : {}
        }
        # Check that the SSH key is valid
        try:
            template_info['ssh_key'] = validate_ssh_key(template_info['ssh_key'])
        except ValueError as e:
            request.session.flash('There are errors with one or more fields', 'error')
            template_info['errors']['ssh_key'] = [str(e)]
            return template_info
        # Get the cloud session for the current org
        cloud_session = request.cloud_sessions[request.current_org]
        try:
            machine = cloud_session.provision_machine(
                item.cloud_id, template_info['name'],
                template_info['description'], template_info['ssh_key'],
                'unmanaged'
            )
            request.session.flash('Machine provisioned successfully', 'success')
        # Catch specific provisioning errors here
        except cloudservices.DuplicateNameError:
            request.session.flash('There are errors with one or more fields', 'error')
            template_info['errors']['name'] = ['Machine name is already in use']
            return template_info
        except (cloudservices.BadRequestError,
                cloudservices.ProvisioningError) as e:
            # If provisioning fails, we want to report an error and show the form again
            request.session.flash('Provisioning error: {}'.format(str(e)), 'error')
            return template_info
        # Now see if we need to apply NAT and firewall rules
        if item.allow_inbound:
            try:
                machine = cloud_session.expose_machine(machine.id)
                request.session.flash('Inbound access from internet enabled', 'success')
            except cloudservices.NetworkingError as e:
                request.session.flash('Networking error: {}'.format(str(e)), 'error')
        # Whatever happens, if we get this far we are redirecting to machines
        return HTTPSeeOther(location = request.route_url('machines'))
    # Only get requests should get this far
    return {
        'template'    : item,
        'name'        : '',
        'description' : '',
        # Use the current user's SSH key as the default
        'ssh_key'     : request.authenticated_user.ssh_key or '',
        'errors'      : {}
    }


@view_config(route_name = 'machine_action',
             request_method = 'POST', permission = 'org_edit')
def machine_action(request):
    """
    Handler for POST requests to ``/{org}/machine/{id}/action``.
    
    The user must be authenticated for the organisation in the URL to reach here.
    
    Attempt to perform the specified action and redirect to ``/{org}/machines``
    with a success message.
    """
    # Request must pass a CSRF test
    check_csrf_token(request)
    action = getattr(request.cloud_sessions[request.current_org],
                     '{}_machine'.format(request.params['action']), None)
    if not callable(action):
        raise HTTPBadRequest()
    action(request.matchdict['id'])
    request.session.flash('Action completed successfully', 'success')
    return HTTPSeeOther(location = request.route_url('machines'))