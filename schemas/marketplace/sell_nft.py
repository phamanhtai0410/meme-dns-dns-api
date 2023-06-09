from marshmallow import Schema, EXCLUDE, fields, validate, ValidationError
from lib import ObjectIdField


def validate_price(n):
    if n <= 0:
        raise ValidationError('Price must be greater than 0.')


class SellNftsSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    nft_id = ObjectIdField(required=True)
    user_address = fields.String(required=True)
    # NOTE: in day
    buy_deadline = fields.Integer(required=True, validate=validate.OneOf([
        7,
        30,
        90
    ]))
    price = fields.Float(required=True, validate=validate_price)


class SellNftBuySignatureSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    nft_id = fields.String(required=True)
    # NOTE: in day
    buy_deadline = fields.Integer(required=True, validate=validate.OneOf([
        7,
        30,
        90
    ]))
    price = fields.Integer(required=True, validate=validate_price)
    signature = fields.String(required=True, allow_none=False)

class CancelSellNftBuySignatureSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    nft_id = fields.String(required=True)
    signature = fields.String(required=True, allow_none=False)
