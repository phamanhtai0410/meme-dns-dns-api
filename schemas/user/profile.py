from marshmallow import Schema, EXCLUDE, fields


class UserProfileRequestSchema(Schema):
    class Meta:
        unknown = EXCLUDE
        ordered = True

    owner = fields.String(required=True)
