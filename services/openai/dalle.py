import traceback
import sentry_sdk
from pydash import get
from config import Config
import openai


class DalleServices:
    @classmethod
    def generate_image_from_prompt(cls, prompt, quantity):
        try:
            openai.api_key = Config.OPENAI_API_KEY

            response = openai.Image.create(
                prompt=prompt,
                n=quantity,
                size="512x512"
            )
            _data = get(response, 'data', [])
            _result = []
            for item in _data:
                if get(item, 'url'):
                    _result.append(get(item, 'url'))

            return _result
        except:
            sentry_sdk.capture_exception()
            traceback.print_exc()
            return []
