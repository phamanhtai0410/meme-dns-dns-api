from marshmallow import Schema, RAISE, fields, EXCLUDE, validate

from lib import ObjectIdField, DatetimeField
from lib.enums.social import SocialNames


class AccountsLinkWithDomainsRequestSchema(Schema):
    class Meta:
        unknown = RAISE

    # page = fields.Integer(required=False, allow_none=False, default=1)
    # page_size = fields.Integer(required=False, allow_none=False, default=10)
    social_name = fields.String(required=True, validate=validate.OneOf([
        SocialNames.TWITTER,
        SocialNames.DISCORD,
        SocialNames.FACEBOOK
    ]))


class SocialSchema(Schema):
    class Meta:
        unknown = EXCLUDE
        ordered = True

    _id = ObjectIdField(required=True)
    social_name = fields.String(required=True)
    social_account = fields.String(required=True)
    address = fields.String(required=True)
    created_time = DatetimeField(allow_none=True)


class AccountsLinkWithDomainsResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE
        ordered = True

    items = fields.List(fields.Nested(SocialSchema()), data_key='items', missing=[])


