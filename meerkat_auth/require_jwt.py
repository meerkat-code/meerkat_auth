from flask import abort, request, current_app
from functools import wraps
import jwt, meerkat_auth

def require_jwt(access):
    """
    Returns decorator to require valid JWT for authentication .
    
    Args: 
        access: a list of role titles that have access to this function.
    Returns:
       function: The decorator or abort(401)
    """
    def decorator(f):

        @wraps(f)
        def decorated(*args, **kwargs):
            auth_prefix = "Bearer "
            token = request.headers.get('authorization')[len(auth_prefix):]
            
            #Decode the jwt and check it is structured as expected.
            payload = jwt.decode(
                token, 
                meerkat_auth.app.config['PUBLIC'], 
                algorithms=[meerkat_auth.app.config['ALGORITHM']]
            )

            #TODO: Check that the jwt has required access.
            #TODO: Abort if doesn't have required access, or problem with JWT.
            #TODO: Otherwise, call function with details of the user provided.
            
            current_app.logger.warning("Payload: " + str(payload))
            current_app.logger.warning("Access: " + str(access) )

            return f(*args, **kwargs)
       
        return decorated

    return decorator
