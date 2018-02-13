============
Meerkat Auth
============

**Meerkat Auth** is our purpose-built authentication module, to grant users access to different parts of the Meerkat system. It uses signed JSON Web Tokens (JWTs) that are placed in a COOKIE and used to identify the user to the system. There are two significant parts to the package, the Backend User management interface and the RESTful API that distributes and removes signed tokens through cookies.

---------
Structure
---------
As a Python Flask app, Meerkat auth is structure in a similar manner to **Meerkat Frontend**. The package is made up of static assets, Jinja2 templates and Python modules.  Further folders and files exist to manage the app's testing, and to abstract country specifics into configuration files, and bundle it up as a python package.  Files and folders of particular note include:

**config.py** - Specifies a host of configuration variables used throughout Meerkat Frontend.  Allows you to distinguish between a development,testing and production environment.

**local_db.py** A script for setting up, populating and clearing the local authentication database. The dev and deployment envirnoments

**meerkat_auth/**

   **user.py** A module containing the User class, which holds a vast array of methods for use in the backend of Meerkat Auth.

   **role.py** A module containing the Role class (modelling an access role/level), which holds a vast array of methods for use in the backend of Meerkat Auth.  Together with *user.py* this forms the backend model for **Meerkat Auth**.

   **authorise.py** A module that can be imported by other modules and used to restrict access. All Meerkat access restrictions should be performed with this single module.

   **src/** A folder containing source files for building the static assets (images, Javascript, CSS etc...). These files are built by by **Gulp** and placed in the **/static** folder. You should never need to edit documents in the **/static** folder. Read "Getting Started" below for more information.

   **static/** A folder populated by **Gulp** with the static assets. You should never need to edit the contents of this folder.

   **test/** A folder containing our testing harness for **Meerkat_Auth**.

   **translations/** A folder containing the *.po* files from which we compile our translated strings for the static assets folder.  Would have been nicer to put this in **/src** but Babel required it to be in the same directory as *__init__.py*.

   **views/** A folder containing the python flask view modules. There is a different view for each component.  This is where much of the server-side work happens.  The backend user management interface is managed by *users.py* and by *roles.py* whilst the distribution/management of signed tokens is handled by *auth.py*.

   **templates/** A folder containing Jinja2 templates that are rendered in the Python view files.  There is a seperate folder of templates for each component.

      **base.html** A file containing the base template that is extended by other templates in each component. Jinja2 templates are hereditary, reducing the need to re-write the same bits of template multiple times. This base tamplate includes the header, footer, navigation bar and other core fragments of layout etc...

-----------------------
Authentication workflow
-----------------------

The process of authenticating a user for a particular page can be broken down into the following steps:

1) **The user logs in.** A secure POST request is made to the auth modules login endpoint, specified in *meerkat_auth/views/auth.py*. This POST request includes the username and password of the user.  If the username and password are correct for an account stored in the dynamodb table *auth_users* then the login request returns a response that stores a signed JWT in a cookie. This jwt simple contains the users username and an expiry time.

2) **User trys to access a secure page.** Crucially at some point early on in the request handling process, the `check_auth( roles, countries )` function should be called from the *authorise.py*. This function uses the JWT and the arguments *roles* and *countries* to determine whether the user should be allowed to proceed. The user will only be allowed to proceed if they have one of the access roles for the relevant country specified in the check_auth arguments. If the user is not authorised to view the page, an Error is thrown and the request aborted.

3) **check_auth(roles, countries) identifies and decodes the JWT.** If the token has expired or has been signed by the wrong private key then an *InvalidTokenError* is raised. This token only yields the username and expiry time. It is kept as small as possible so that it can be stored in a cookie.

4) **check_auth forwards the token to the */get_user url* endpoint.** The */get_user* end point is specified in the *auth.py* view and takes a POST request storing the JWT. If JWT is valid, it returns a much larger JWT contining all necessary user information, including what the user has access to.

5) **The user token is used to determine whether to grant the user access.** The function *check_access(roles, countries)* from the *authorise.py* module does this.  Access in the token is stored as a dictionary where each key is a country and each value is a list of access role the user has access to in that country. e.g. A user token that included the following, would have access to all root, admin and registered access levels in country_1 but only registered in country_2...

    .. code-block:: python

        'acc':{
            'country_1':['root','admin','registered'],
            'country_2':['registered']
        }

6) **If access is granted**, the users details are stored in the Flask g object, under g.payload.  The users details including its access levels is then available for the duration of the rest of the request. If access fails, then an error is raised and the request aborted with a 403 unauthorised error.  The user is offered a chance to login a second time.

-------------------------------------
Using authorise.py to restrict access
-------------------------------------

In roder to restrict access to a function, we need to use the functions in *authorise.py*, so *authorise.py* needs to be importable.  This can be done by adding the path of **Meerkat Auth** to your PYTHONPATH. Developers should only need to worry about calling `check_auth(roles,countries)` correctly as in step two of the authentication workflow.

The first argument to check_auth is a list of valid access roles, required to continue with the request, and the second argument is a list of countries that each role corresponds to. For the most part this will simply be the country the software is deployed for, but it gives us the flexibility to grant accounts from different countries access to the same page. An access role is bound to a country through simple index matching, the first role in the list of `roles` coresponds to the first country in the list of `countries`, and so on.

For example, in **Meerkat Frontend's** *technical.py* view , the *authorise.py* module from **Meerkat Auth** has been added to the python path so it can be imported. The `check_auth( roles, countries)` function is then called before handling each request to that blueprint. Because we want the role to depend upon the country, we have extracted the arguments passed to checkauth into the config files.  If we fail to load the arguments from the config files, we load some default "dud" arguments: `check_auth(['BROKEN'], [''])`. The result is the following...

.. code-block:: python

    import authorise as auth

    technical = Blueprint('technical', __name__,url_prefix='/<language>')

    @technical.before_request
    def requires_auth():
        """Checks that the user has authenticated before returning any page from this Blueprint."""
        #We load the arguments for check_auth function from the config files.
        auth.check_auth( *current_app.config['AUTH'].get('technical', [['BROKEN'],['']]) )



The arguments loaded for the demo site are `( ['registered'], ['demo'] )` thus restricting all endpoints in the technical Blueprint to only users with the *registered* access role for the country *demo*.

Note that the `check_auth( roles, countries)` function has been wrapped up as a python decorator `@authorise( roles, countries)` for use on single functions. This is used when handling a send-report-email request, because it needs different access restrictions to the rest of the reports module.

----------
Deployment
----------

**Meerkat Auth** is deployed once for the entire meerkat system. A deployment and a development docker container is specified in **Meerkat Infrastructure**. The docker container is deployed using Amazon's ECS container service.  It does not need to be deployed everytime alongside the country deployments.  It is deployed seperatly using the same deploy.py script under the name "auth".

------------------
Code Documentation
------------------

The code documentation is available here:

.. toctree::
   :maxdepth: 4

   auth/util
   auth/resources
   auth/flask

------------------
Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
