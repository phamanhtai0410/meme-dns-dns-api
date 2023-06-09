from marshmallow import Schema, EXCLUDE, fields, validate
from lib import ObjectIdField


class SMCSignatureBuyNftRequestSchema(Schema):
    class Meta:
        unknown = EXCLUDE
        ordered = True

    chain_id = fields.Integer(required=True)
    to_address = fields.String(required=True)
    nft_id = ObjectIdField(required=True)


class SMCSignatureBuyNftResponseObj(Schema):
    class Meta:
        unknown = EXCLUDE
        ordered = True

    order_id = fields.Integer(required=True)
    from_to = fields.List(fields.String, validate=validate.Length(equal=2))
    nft_and_token = fields.List(fields.String, validate=validate.Length(equal=2))
    id_and_amount = fields.List(fields.String, validate=validate.Length(equal=2))
    additional_token_receivers = fields.List(fields.String, default=[], missing=[])
    all_amounts = fields.List(fields.String, validate=validate.Length(min=1))


class SMCSignatureBuyNftResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE
        ordered = True

    signature = fields.String(required=True)
    deadline = fields.Integer(required=True)
    data = fields.Nested(SMCSignatureBuyNftResponseObj())
