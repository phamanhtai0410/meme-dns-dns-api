import traceback
import sentry_sdk
from firebase_admin import auth


class GoogleServices:

    @staticmethod
    def verify(token):
        try:
            decoded_token = auth.verify_id_token(token)
            uid = decoded_token['uid']
            user = auth.get_user(uid)
            return user
        except:
            sentry_sdk.capture_exception()
            traceback.print_exc()

        return False
