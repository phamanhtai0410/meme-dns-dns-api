from bson import ObjectId
from pydash import get

from helper.template.category import TemplateCategoriesHelpers
from lib import BadRequest
from lib.utils import is_oid
from models import TemplatesModel, TemplateContentModel, UsersTemplatesModel


class TemplatesServices:

    @classmethod
    def get_templates(
            cls,
            page: int = 1,
            page_size: int = 10,
            category: str = None,
            search: str = None,
            sort_title: str = None,
            sort_price: str = None,
    ):
        _filter = {}
        _sort = {
            'priority': 1
        }
        if category is not None:
            if not is_oid(category) or not TemplateCategoriesHelpers.is_exist(category):
                raise BadRequest(msg="Invalid params.", errors=["This category doesn't exist."])
            _filter['category_id'] = ObjectId(category)

        if search is not None:
            _filter['$or'] = [
                {
                    "title": {
                        "$regex": search,
                        "$options": "i"
                    }
                },
                {
                    "description": {
                        "$regex": search,
                        "$options": "i"
                    }
                }
            ]

        if sort_title is not None:
            _sort = {
                'title': sort_title.lower() == 'asc' and 1 or -1,
                **_sort
            }
        if sort_price is not None:
            _sort = {
                'price': sort_price.lower() == 'asc' and 1 or -1,
                **_sort
            }

        _offset = page > 0 and (page - 1) * page_size or 0

        _pipeline = [
            {
                '$match': _filter
            },
            {
                '$lookup': {
                    'from': 'template_categories',
                    'localField': 'category_id',
                    'foreignField': '_id',
                    'as': 'category',
                }
            },
            {
                '$unwind': '$category'
            },
            {
                '$skip': _offset
            },
            {
                '$limit': page_size
            }
        ]

        if _sort:
            _pipeline.append({'$sort': _sort})

        _items = TemplatesModel.col.aggregate(pipeline=_pipeline)

        _items = list(_items)

        # print(_items)

        _num_of_page = (len(_items) / page_size)
        if (len(_items) % page_size) > 0:
            _num_of_page = _num_of_page + 1

        return {
            'items': _items,
            'page': page,
            'page_size': page_size,
            'num_of_page': _num_of_page
        }

    @classmethod
    def get_template_demo(cls, template_id):
        _page = 'default'   # Update later
        _template = TemplatesModel.find_one(filter={
            '_id': ObjectId(template_id)
        })

        if _template is None:
            raise BadRequest(msg='Invalid params.', errors=['Template is not exist.'])

        _content = TemplateContentModel.find(filter={
            'template_id': ObjectId(template_id),
            'page': _page
        })

        return {
            'blocks': _content
        }

    @classmethod
    def get_template_detail(cls, template_id):
        _result = TemplatesModel.find_one(filter={'_id': ObjectId(template_id)})
        return {
            'template': _result
        }
