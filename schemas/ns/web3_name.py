from marshmallow import Schema, RAISE, fields


class NameServiceWeb3NamesRequestSchema(Schema):
    class Meta:
        unknown = RAISE

    wallet_address = fields.Str(required=True)
