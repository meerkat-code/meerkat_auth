"""
roles.py

A Flask Blueprint module for the role manager page.
"""
from flask import Blueprint, render_template, current_app, jsonify
import json
from meerkat_auth.user import User, InvalidCredentialException
from meerkat_auth.role import Role, InvalidRoleException
from meerkat_auth.authorise import authorise

roles = Blueprint('roles', __name__, url_prefix="/<language>")

@roles.route('/get_roles')
@roles.route('/get_roles/<country>')
def get_roles( country=None ):
    return jsonify( {'roles': Role.get_all(country)} )

@roles.route('/get_all_access/<country>/<role>')
def get_all_access( country=None, role=None ):
    access = Role.from_db( country, role).all_access()
    return jsonify( {'access': access} )

@roles.route('/')
@authorise(['manager'])
def index(payload):
    return render_template(
        'roles/index.html',
        user = payload,    
        root = current_appp.config["ROOT_URL"]
    )
