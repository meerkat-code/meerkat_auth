"""
roles.py

A Flask Blueprint module for the role manager page.
"""
from flask import Blueprint, render_template, current_app, jsonify
import json
from meerkat_auth.user import User, InvalidCredentialException
from meerkat_auth.role import Role, InvalidRoleException

roles = Blueprint('roles', __name__, url_prefix="/<language>")

@roles.route('/get_roles')
@roles.route('/get_roles/<country>')
def get_roles( country=None ):
    return jsonify( {'roles': Role.get_all(country)} )

@roles.route('/')
def index():
    return render_template('roles/index.html')
