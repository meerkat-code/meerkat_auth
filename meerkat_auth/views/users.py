"""
users.py

A Flask Blueprint module for the user manager page.
"""
from flask import Blueprint, render_template, current_app, request, Response
import json
from meerkat_auth.util.user import User, InvalidCredentialException
from meerkat_auth.util.role import Role, InvalidRoleException

users = Blueprint('users', __name__, url_prefix="/<language>")

@users.route('/')
def index():
    return render_template('users/index.html')
