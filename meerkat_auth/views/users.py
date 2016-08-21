"""
users.py

A Flask Blueprint module for the user manager page.
"""
from flask import Blueprint, render_template, current_app, request, Response, jsonify
import json, datetime
from meerkat_auth.user import User, InvalidCredentialException
from meerkat_auth.role import Role, InvalidRoleException
from meerkat_auth.require_jwt import require_jwt

users = Blueprint('users', __name__, url_prefix="/<language>")


@users.route('/create_user', methods=['POST'])
def create_user():
    return "stub"

@users.route('/get_users')
def get_users():
    countries = []
    attributes = ["email", "roles", "username", "countries", "creation", "data"]
    return jsonify( {'rows': User.get_all( countries, attributes )} )

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

@users.route('/check_username/<username>')
def check_username(username):
    return jsonify( {'valid':not User.check_username(username)} )

@users.route('/update_user/<username>', methods=['POST'])
@users.route('/update_user/', methods=['POST'])
def update_user(username='new'):

    current_app.logger.warning( username )
    current_app.logger.warning( request.json )
    
    #Load the form's data.
    data = request.json

    #Form password field defaults to empty, only update password if something is entered.
    #Original password hash is stored in form hidden input to avoid having to reload user here.
    if data["password"]:
        data["password"] = User.hash_password(data["password"])
    else:
        data["password"] = data["original_password"]

    current_app.logger.warning( type(data["data"]) )
    current_app.logger.warning( data["data"] )

    #Create a user object represented by the form input.
    user = User(
        data["username"],
        data["email"],
        data["password"],
        data["countries"],
        data["roles"],
        state = data["state"],
        updated = datetime.datetime.now().isoformat(),
        creation = data["creation"],
        data = data["data"]
    )   


    #If username has changed, then we are creating a new record for the purposes of validation.
    #...because validation will say "username already exists" unless user state is "new".
    if username != data["username"]:
        user.state = "new"

    #Validate the new user object.     
    try:
        user.validate()
    except (InvalidRoleException, InvalidCredentialException) as e:
        return str(e)
    except Exception as e:
        return str(e)
        raise

    #If username has changed, then we are creating a new db record so delete the old one.
    #Reset state once validation complete, so changing username doesn't wipe the user's state.
    if username != data["username"]:
        user.state = data["state"]
        User.delete( username )

    current_app.logger.warning( user.data )

    #If succesfully validated, write the changes to the database.
    user.to_db()
    return "Successfully Updated"

@users.route('/delete_users', methods=['POST'])
def delete_users():

    current_app.logger.warning( request.json )
    
    #Load the list of users to be deleted.
    users = request.json
    
    #Try to delete users
    try:
        for username in users:
            User.delete(username)
    except Exception as e:
        return ("Unfortunately there was an error:\n " + str(e) + 
                "\nContact the administrator if the problem persists.")

    return "Users succesfully deleted."

    

@users.route('/')
@require_jwt(['manager'])
def index(payload):

    return render_template( 
        'users/index.html', 
        user = payload 
    )
