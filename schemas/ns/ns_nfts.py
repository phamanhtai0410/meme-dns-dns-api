from marshmallow import Schema, EXCLUDE, fields, validate
from lib import ObjectIdField, SUPPORTED_CHAINS
from lib.schema import DatetimeField

from schemas.request import RequestSchema


class NsNFTsRequestSchema(RequestSchema):
    class Meta:
        unknown = EXCLUDE


    owner = fields.String(required=True)
    # sort_field = fields.String(allow_none=True, default='created_time')
    # sort_type = fields.String(validate=validate.OneOf([
    #     'desc',
    #     'asc'
    # ]), allow_none=True, default='desc')



class NsNFTSchema(Schema):
    class Meta:
        unknown = EXCLUDE
        ordered = True

    _id = ObjectIdField(required=True)
    tx_hash = fields.String(allow_none=True, default='', missing='')
    order_id = fields.Integer(required=False, allow_none=True)
    token_id = fields.String(required=True)
    domain_name = fields.String(required=True)
    owner = fields.String(required=True)
    expires = fields.Integer(required=True)
    chain_id = fields.Integer(required=True)
    metadata_link = fields.String(default='', missing='', allow_none=True)
    image_url = fields.String(default='', missing='', allow_none=True)
    price = fields.String(default='0', missing='0', allow_none=True)
    base_cost = fields.String(default='0', missing='0')
    buy_deadline = DatetimeField(allow_none=True)
    on_market = fields.Boolean(default=False, missing=False)
    created_time = DatetimeField(allow_none=True)


class NsNFTsResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE
        ordered = True

    items = fields.List(fields.Nested(NsNFTSchema()), data_key='items', missing=[])
    num_of_page = fields.Integer(data_key='num_of_page', missing=0)
    page_size = fields.Integer(data_key='page_size', missing=10)
    page = fields.Integer(data_key='page', missing=1)
