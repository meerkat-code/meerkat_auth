from meerkat_auth.user import User
from meerkat_auth import app
from meerkat_libs.auth_client import Authorise as libs_auth
import jwt


class Authorise(libs_auth):
    """
    Extension of the meerkat_libs auth_client Authorise class. We override one
    of its functions so that it works smoothly in meerkat_auth.
    """
    # Override the get user method
    # Since we have direct access to the user model here.
    def get_user(self, token):
        """
        A function that get's the details of the specified user and combines it
        with the specified token's payload.

        Args:
            token (str): The JWT token corresponding to the requested user.

        Returns:
            (dict) The combined payload of the authentication token and the
                remote user token i.e. complete set of information about the
                use specified in the token.
        """

        # Decode the jwt.
        payload = jwt.decode(
            token,
            app.config['JWT_PUBLIC_KEY'],
            algorithms=[app.config['JWT_ALGORITHM']]
        )

        # Get the user details directly from the db.
        user = User.from_db(payload['usr']).get_payload(payload['exp'])

        # Return the combined information
        return {**user, **payload}

# Create an instance of the class to import into the rest of the package.
auth = Authorise()
