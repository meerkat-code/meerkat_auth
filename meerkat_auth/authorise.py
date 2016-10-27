from flask import abort, request, make_response, jsonify, g
from functools import wraps
from jwt import InvalidTokenError
from flask.ext.babel import gettext
import jwt, inspect, logging, os, requests, calendar, time, json

#Need this module to be importable without the whole of meerkat_auth config.
#Directly load the secret settings file from which to import required variables.
#File must include JWT_COOKIE_NAME, JWT_ALGORITHM and JWT_PUBLIC_KEY variables.
filename = os.environ.get( 'MEERKAT_AUTH_SETTINGS' )
exec( compile(open(filename, "rb").read(), filename, 'exec') )

def check_access(access, countries, acc):
    """
    Compares the access levels specified in the require_jwt decorator with the access
    levels specified in the given jwt. Returns a boolean stating whether there is a match.

    Accepts "" as a wildcard country, meaning any country.

    Args:
        access ([str]) A list of role titles that meet the authorisation requirements.
        countries ([str]) An optional list of countries for which each role
            title correspond to. access[0] corresponds to country[0] and so on...
            If the length of countries is smaller than the length of access, then
            the final element of countries is repeated to make the length match. 
            Accepts wildcard value "" for any country.  Default value is [""], meaning
            all specified access levels will be valid for any country if countires is
            not specified.

    Returns:
        bool True if authorised, False if unauthorised.   
    """
    #Set the countries array to match the length of the access array.
    if len(countries) < len(access):
        j = len(countries)
        for i in range(j,len(access)):
            countries.append( countries[j-1] )

    authorised = False
        
    #For each country specified by the decorator...
    for i in range(0,len(countries)):
        country = countries[i]
        #...if that country is specified in the token...
        if country in acc:
            #...and if the corresponding country's role is specified in the token...
            if access[i] in acc[country] or access[i] == "":
                #...then authorise.
                authorised = True
                break

        #...Else if the country specified by the decorator is "" (the wildcard)...
        elif country == "":
            #...Look through all countries specified in the jwt...
            for c in acc:
                #...if any access level in jwt matches a level in the decorator...
                if access[i] in acc[c] or access[i] == "":
                    #....then authorise.
                    authorised = True
                    break

    return authorised

def get_token():
    """
    Get's the Json Web Token. From the cookies or authorization headers.

    This function defines how the token should be retrieved.  It exists because 
    we need to look for the token in multiple places depending on the type of request. 
    
    Returns:
        The token or an empty string.
    """
    #Extract the token from the cookies
    token = request.cookies.get(JWT_COOKIE_NAME)

    #Extract the token from the headers if it doesn't exist in the cookies.
    if not token and request.headers.get('authorization'):
        token = request.headers.get('authorization')[len(JWT_HEADER_PREFIX):]

    return token if token else ""

def check_auth( access, countries ):
    """
    A function that checks whether the user is authorised to continue with the current
    request. It does this by verifying the jwt stored as a cookie. If the user isn't 
    authorised the request is aborted with an Invalid Token Error. 
    
    If access is granted the user details is stored in flask g, under the property "payload", i.e.
    `g.payload`.

    NOTE: The roles specifed are ORed to figure out access. i.e. ANY of the given access roles will
    grant access (we don't require ALL of them).

    Args: 
        access ([str]) A list of role titles that have access to this function.
        countries ([str]) An optional list of countries for which each role
            title correspond to. access[0] corresponds to country[0] and so on...
            If the length of countries is smaller than the length of access, then
            the final element of countries is repeated to make the length match. 
            Accepts wildcard value "" for any country.  Default value is [""], meaning
            all specified access levels will be valid for any country if countires is
            not specified.

            E.g. require_jwt(['manager', 'shared'], countries=['jordan','demo'])
            Would give access to managers in jordan, and shared accounts in demo.
            E.g. require_jwt(['manager', 'shared']) 
            Would give access to managers and shared accounts from any country.
            E.g. require_jwt(['manager','shared'], countries=['jordan'])
            Would give access to managers and shared accounts only from Jordan.
    """

    #Only translate error strings if Bable is up and running.
    #Bable runs in frontend but not API - both import this module and musn't fail.
    not_authenticated = ( "You have not authenticated yet. "
                          "Please login before viewing this page." )
    incorrect_access = "User doesn't have required access levels for this page: {}."

    try:
        not_authenticated = gettext( not_authenticated )
        incorrect_access = gettext( incorrect_access )
    except KeyError:
        pass
        
    #Get the jwt.
    token = get_token()

    #If no token is found return an "not authenticated" message
    if not token:
        abort( 401, not_authenticated )

    try:
        #Decode the jwt and check it is structured as expected.
        payload = jwt.decode(
            token,
            JWT_PUBLIC_KEY, 
            algorithms=[JWT_ALGORITHM]
        )

        #Get the user's data, directly if we are in auth module, or remotely otherwise.
        try:
            from meerkat_auth.user import User
            user = User.from_db( payload['usr'] ).get_payload( payload['exp'] )

        #Feels hacky.  If we can't get data directly, then try a request to the url.
        except Exception as e:
            try:
                r = requests.post( AUTH_ROOT +'/api/get_user', json = {'jwt': token} )
                user_token = r.json()['jwt'] 
                user = jwt.decode(
                    user_token,
                    JWT_PUBLIC_KEY, 
                    algorithms=[JWT_ALGORITHM]
                )
            except Exception as e:
                logging.warning( "Failed to get remote user token: " + repr(e) )
                user = {}

        #Merge user details into payload
        payload = {**user, **payload}

        #Check that the user has required access, and if so, store user details in g.
        if check_access(access, countries, payload['acc'] ):
            g.payload = payload

        #Token is invalid if it doesn't have the required accesss levels.
        else:
            raise InvalidTokenError( incorrect_access.format(', '.join(map(str, access))) )

    #Return 403 if logged in but the jwt isn't valid.   
    except InvalidTokenError as e:
        abort( 403, str(e) ) 

    #Otherwise abort with an internal server error page.
    except Exception as e:
        abort( 500, str(e) )
    

def authorise( access, countries ):
    """
    Returns decorator that wraps a route function with another function that
    requires a valid jwt.

    Args:
        access ([str]) A list of role titles that have access to this function.
        countries ([str]) An optional list of countries for which each role
            title correspond to. access[0] corresponds to country[0] and so on...
            If the length of countries is smaller than the length of access, then
            the final element of countries is repeated to make the length match. 
            Accepts wildcard value "" for any country.  Default value is [""], meaning
            all specified access levels will be valid for any country if countires is
            not specified.

    Returns:
        function: The decorator or abort(401)
    """
    def decorator(f):

        @wraps(f)
        def decorated(*args, **kwargs):

            check_auth( access, countries )
            return f(*args, **kwargs)

        return decorated

    return decorator

