"""
roles.py

A Flask Blueprint module for the role manager page.
"""
from flask import Blueprint, render_template, current_app, request, Response
import json
from meerkat_auth.util.user import User, InvalidCredentialException
from meerkat_auth.util.role import Role, InvalidRoleException

roles = Blueprint('roles', __name__, url_prefix="/<language>")

@roles.route('/')
def index():
    return render_template('roles/index.html')
