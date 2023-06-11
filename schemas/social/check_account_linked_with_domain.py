from marshmallow import Schema, RAISE, fields, validate
from lib.enums.social import SocialNames


class CheckAccountLinkedWithDomainRequestSchema(Schema):
    class Meta:
        unknown = RAISE

    social_name = fields.String(required=True, validate=validate.OneOf([
        SocialNames.TWITTER,
        SocialNames.DISCORD,
        SocialNames.FACEBOOK
    ]))
    social_account = fields.String(required=True)
