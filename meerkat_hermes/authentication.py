from meerkat_hermes import app
from flask import abort, request
from functools import wraps
import json

def require_api_key(f):
    """
    @param f: flask function
    @return: decorator, return the wrapped function or abort json object.
    """
    @wraps(f)
    def decorated(*args, **kwargs):

        app.logger.warning( "request json: " + str(request.json) )
        app.logger.warning( "request data: " + str(request.data.decode('UTF-8')) )

        if request.data:
           key = json.loads(request.data.decode('UTF-8'))['api_key']
        else:
           key = request.args.get('api_key')

        app.logger.warning( "Key = " + str(key) )

        if( key == app.config["API_KEY"] or 
            app.config["API_KEY"] == "" ):
            return f(*args, **kwargs)
        else:
            app.logger.warning("Unauthorized address trying to use API: {}".format(request.remote_addr))
            abort(401)
    
    return decorated

