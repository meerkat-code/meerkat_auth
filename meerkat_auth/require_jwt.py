from flask import abort, request, current_app
from functools import wraps
from jwt import InvalidTokenError
import jwt, meerkat_auth, inspect

def check_access(access, countries, acc):
    """
    Compares the access levels specified in the require_jwt decorator with the access
    levels specified in the given jwt. Returns a boolean stating whether there is a match.

    Accepts "" as a wildcard country, meaning any country.

    Args:
        access ([str]) A list of role titles that meet the qauthorisation requirements.
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
            if access[i] in acc[country]:
                #...then authorise.
                authorised = True
                break

        #...Else if the country specified by the decorator is "" (the wildcard)...
        elif country == "":
            #...Look through all countries specified in the jwt...
            for c in acc:
                #...if any access level in jwt matches a level in the decorator...
                if access[i] in acc[c]:
                    #....then authorise.
                    authorised = True
                    break

    return authorised

def require_jwt(access, countries=[""] ):
    """
    Returns decorator to require valid JWT for authentication .
    
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

    Returns:
       function: The decorator or abort(401)
    """
    def decorator(f):

        @wraps(f)
        def decorated(*args, **kwargs):

            #Extract the token from the cookies
            token = request.cookies.get(meerkat_auth.app.config['COOKIE_NAME'])

            try:
                #Decode the jwt and check it is structured as expected.
                payload = jwt.decode(
                    token, 
                    meerkat_auth.app.config['PUBLIC'], 
                    algorithms=[meerkat_auth.app.config['ALGORITHM']]
                )

                #Check that the jwt has required access.
                if check_access(access, countries, payload['acc'] ):
                    
                    #If the function specifies an argument entitled 'payload'...
                    if 'payload' in inspect.getargspec(f).args:
                        #...add the user object to the args.
                        kwargs['payload'] = payload

                    return f(*args, **kwargs)

                #Token is invalid if it doesn't have the required accesss levels.
                else:
                    raise InvalidTokenError(
                        message="Token doesn't have required access levels for this page."
                    )

            #Return 401 if the jwt isn't valid.   
            except InvalidTokenError as e:
                return Response( 
                    json.dumps( {'message':str(e)} ), 
                    status=401, 
                    mimetype='application/json'  
                )
                
        return decorated

    return decorator
