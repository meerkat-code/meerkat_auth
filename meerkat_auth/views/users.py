"""
users.py

A Flask Blueprint module for the user manager page.
"""
from flask import Blueprint, render_template, current_app, request, Response, jsonify
import json
from meerkat_auth.util.user import User, InvalidCredentialException
from meerkat_auth.util.role import Role, InvalidRoleException

users = Blueprint('users', __name__, url_prefix="/<language>")


@users.route('/create_user', methods=['POST'])
def create_user():
    return "stub"

@users.route('/get_users')
def get_users():
    countries = []
    attributes = ["email", "roles", "creation", "data", "countries"]
    return jsonify( User.get_all( countries, attributes ) )

@users.route('/get_user/')
@users.route('/get_user/<username>')
def get_user(username=""):
    if username == "":
        return jsonify({
          "countries": [],
          "creation": "",
          "data": {},
          "email": "",
          "password": "",
          "roles": [],
          "state": "",
          "updated": "",
          "username": ""
        })

    else:
        return jsonify( User.from_db(username).to_dict() )

@users.route('/')
def index():

    #For testing/development purposes insert a payload here:
    payload = {
        u'acc': {
            u'demo': [u'manager', u'registered', u'personal', u'shared'], 
            u'jordan': [u'registered', u'personal']
        }, 
        u'data': {u'name': u'Testy McTestface'}, 
        u'usr': u'testUser',   
        u'email': u'test@test.org.uk'
    }

    return render_template( 
        'users/index.html', 
        users = json.loads(get_users().data.decode('UTF-8')),
        user = payload 
    )
