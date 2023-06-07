from bson import ObjectId

from lib import BadRequest
from models import UsersTemplatesModel


class UserTemplateServices:
    @classmethod
    def is_user_template_exist(cls, user_template_id):
        _user_template = UsersTemplatesModel.find_one(filter={
            '_id': ObjectId(user_template_id)
        })

        if _user_template is None:
            raise BadRequest(msg='Invalid params.', errors=['Template id is not owned.'])

        return {
            'is_user_template': True
        }
