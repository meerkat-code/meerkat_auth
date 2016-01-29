from flask import abort, request, app
from functools import wraps

def require_api_key(f):
    """
    @param f: flask function
    @return: decorator, return the wrapped function or abort json object.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        app.logger.warning("Request made with api key: " + str(request.form['api_key']) )

        if( request.form['api_key'] == app.config["API_KEY"] 
            or request.args.get('api_key') == app.config["API_KEY"] 
            or app.config["API_KEY"] == "" ):
            return f(*args, **kwargs)
        else:
            app.logger.warning("Unauthorized address trying to use API: {}".format(request.remote_addr))
            abort(401)
    return decorated

