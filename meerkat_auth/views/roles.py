"""
roles.py

A Flask Blueprint module for the role manager page.
"""
from flask import Blueprint, render_template, current_app, jsonify, g
import json
from meerkat_auth.user import User, InvalidCredentialException
from meerkat_auth.role import Role, InvalidRoleException
from meerkat_auth import authorise as auth

roles = Blueprint('roles', __name__, url_prefix="/<language>")

@roles.before_request
def requires_auth():
    """
    Checks that the user has authenticated before returning any page from 
    this Blueprint.
    """
    auth.check_auth( ['manager'] )

@roles.route('/get_roles')
@roles.route('/get_roles/<country>')
def get_roles( country=None ):
    """
    Get all the roles for a given country.
    Args:
        country (str) The country for which we want all the roles.

    Returns:
        A json object containing a single property 'roles' which is 
        a list of the roles for that country.
    """
    return jsonify( {'roles': Role.get_all(country)} )

@roles.route('/get_all_access/<country>/<role>')
def get_all_access( country=None, role=None ):
    """
    Get's the complete access list for a given role.

    Args: 
        country (str) The country that the role belongs to.
        role (str) The role that we want to get the complete access.
    
    Returns:
        A json object which has a single property 'access' which is the
        list of access roles inherited by the specified role (including itself).
    """
    access = Role.from_db( country, role).all_access()
    return jsonify( {'access': access} )

@roles.route('/')
@authorise(['manager'])
def index():
    """Renders the page showing the viewer/editor for access roles."""
    return render_template(
        'roles/index.html',
        user = g.payload,    
        root = current_app.config["ROOT_URL"]
    )
